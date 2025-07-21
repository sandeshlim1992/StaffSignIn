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
    """
    token_read_signal = Signal(int)
    error_signal = Signal(str)
    status_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True
        self.subscriber = None
        self.event_handler = None

    def run(self):
        """The main logic of the thread."""
        if not clr:
            self.error_signal.emit("The 'pythonnet' library is required but not found.")
            return

        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            all_files = os.listdir(script_dir)
            for file in all_files:
                if file.lower().endswith('.dll'):
                    try:
                        clr.AddReference(os.path.splitext(file)[0])
                    except Exception:
                        pass

            from Paxton.Net2.DesktopReaderClient import DesktopReaderSubscriber

            self.subscriber = DesktopReaderSubscriber()
            self.event_handler = self.on_token_read_event
            self.subscriber.TokenReadEvent += self.event_handler

            self.subscriber.SubscribeToReaderService()
            self.subscriber.AcceptTokenReadEvents(True)
            self.status_signal.emit("Paxton Reader is active and listening.")

            while self._is_running:
                time.sleep(0.1)

        except Exception as e:
            error_message = f"Paxton Reader Thread Error:\n{traceback.format_exc()}"
            self.error_signal.emit(error_message)
        finally:
            self.cleanup()

    def on_token_read_event(self, card_number, wiegand_no, token_type):
        """
        This is the callback function that fires when a card is read.
        It emits the signal with the token number.
        """
        self.token_read_signal.emit(card_number)

    def stop(self):
        """Stops the thread gracefully."""
        self.status_signal.emit("Stopping reader thread...")
        self._is_running = False

    def cleanup(self):
        """Unsubscribes and disposes of the reader object."""
        if self.subscriber:
            try:
                if self.event_handler:
                    self.subscriber.TokenReadEvent -= self.event_handler
                if hasattr(self.subscriber, 'UnsubscribeFromReaderService'):
                    self.subscriber.UnsubscribeFromReaderService()
                if hasattr(self.subscriber, 'Dispose'):
                    self.subscriber.Dispose()
                self.status_signal.emit("Reader thread stopped.")
            except Exception as e:
                self.error_signal.emit(f"Error during cleanup: {e}")
