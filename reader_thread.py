import time
import os
import traceback
from PySide6.QtCore import QThread, Signal

try:
    import clr
    import System
except ImportError:
    clr = None


class PaxtonReaderThread(QThread):
    """
    This thread runs in the background, listens to the Paxton reader,
    and emits a signal containing the token number when a card is swiped.
    It now includes automatic reconnection logic.
    """
    token_read_signal = Signal(int)
    error_signal = Signal(str)
    status_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True
        self.is_connected = False
        self.subscriber = None
        self.event_handler = None
        self.paxton_lib = None

    def run(self):
        """The main logic of the thread, now a connection management loop."""
        if not clr:
            self.error_signal.emit("The 'pythonnet' library is required but not found.")
            return

        try:
            # --- Load Paxton DLLs once ---
            script_dir = os.path.dirname(os.path.abspath(__file__))
            all_files = os.listdir(script_dir)
            for file in all_files:
                if file.lower().endswith('.dll'):
                    try:
                        clr.AddReference(os.path.splitext(file)[0])
                    except Exception:
                        pass

            # Import the necessary class
            from Paxton.Net2.DesktopReaderClient import DesktopReaderSubscriber
            self.paxton_lib = DesktopReaderSubscriber
        except Exception as e:
            error_message = f"Failed to load Paxton libraries:\n{traceback.format_exc()}"
            self.error_signal.emit(error_message)
            return

        # --- Main Connection Loop ---
        while self._is_running:
            if not self.is_connected:
                try:
                    self.status_signal.emit("Attempting to connect to reader...")

                    self.subscriber = self.paxton_lib()
                    self.event_handler = self.on_token_read_event
                    self.subscriber.TokenReadEvent += self.event_handler
                    self.subscriber.SubscribeToReaderService()
                    self.subscriber.AcceptTokenReadEvents(True)

                    self.is_connected = True
                    self.status_signal.emit("Paxton Reader is active and listening.")

                except Exception:
                    self.status_signal.emit("Connection failed. Retrying in 5s...")
                    self._cleanup_subscriber()  # Ensure partial connections are cleaned up
                    time.sleep(5)
            else:
                # Connection is active, sleep for a bit before checking again
                time.sleep(1)

        self._cleanup_subscriber()  # Final cleanup when the thread stops

    def on_token_read_event(self, card_number, wiegand_no, token_type):
        """
        This is the callback function. If it fails, we assume the connection
        is lost and signal the run loop to reconnect.
        """
        try:
            self.token_read_signal.emit(card_number)
        except Exception:
            # An error here likely means the connection to the service was lost.
            self.status_signal.emit("Reader connection lost. Attempting to reconnect...")
            self.is_connected = False

    def stop(self):
        """Stops the thread gracefully."""
        self.status_signal.emit("Stopping reader thread...")
        self._is_running = False

    def _cleanup_subscriber(self):
        """Unsubscribes and disposes of the reader object."""
        if self.subscriber:
            try:
                if self.event_handler:
                    self.subscriber.TokenReadEvent -= self.event_handler
                if hasattr(self.subscriber, 'UnsubscribeFromReaderService'):
                    self.subscriber.UnsubscribeFromReaderService()
                if hasattr(self.subscriber, 'Dispose'):
                    self.subscriber.Dispose()
            except Exception:
                pass  # Ignore errors during cleanup
            finally:
                self.subscriber = None
                self.event_handler = None
                self.is_connected = False