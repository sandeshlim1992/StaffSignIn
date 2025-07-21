import time
import os
import traceback
import csv
import threading
from tkinter import simpledialog, Tk

# --- Import the .NET Runtime ---
try:
    import clr
    import System
except ImportError:
    print("FATAL ERROR: The 'pythonnet' library is not installed.")
    exit()

# --- Global state to manage data and threading ---
STAFF_FILE = 'staff_data.csv'
staff_data = {}
# A lock to prevent race conditions when accessing the file or staff_data dict
data_lock = threading.Lock()


def load_staff_data():
    """Loads the staff data from the CSV file into memory."""
    global staff_data
    try:
        with data_lock:
            if not os.path.exists(STAFF_FILE):
                # Create the file with headers if it doesn't exist
                with open(STAFF_FILE, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Token', 'StaffName'])
                staff_data = {}
                return

            with open(STAFF_FILE, 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header row
                # Load file into a dictionary {token: name}
                staff_data = {int(row[0]): row[1] for row in reader if row}

    except Exception as e:
        print(f"Error loading staff data: {e}")


def register_new_user(token):
    """Shows a dialog to register a new user and saves it."""
    global staff_data

    # --- This function needs to run in the main thread to show a GUI dialog ---
    def ask_for_name():
        # Create a hidden root window for the dialog
        root = Tk()
        root.withdraw()
        # Ask for the user's name
        user_name = simpledialog.askstring("New Card Detected", f"Please enter the name for token: {token}")
        root.destroy()

        if user_name:
            with data_lock:
                # Add to our in-memory dictionary
                staff_data[token] = user_name
                # Append to the CSV file
                with open(STAFF_FILE, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([token, user_name])
                print(f"Successfully registered {user_name} with token {token}.")
        else:
            print(f"Registration cancelled for token {token}.")

    # Since Tkinter needs to be on the main thread, we can't directly call it here.
    # For this standalone script, we'll run it directly, but this is a limitation.
    # In a full GUI app, we would emit a signal.
    ask_for_name()


def on_token_read(card_number, wiegand_no, token_type):
    """
    This is the event handler. It checks if a user is registered and acts accordingly.
    """
    print(f"\n--- CARD DETECTED (Token: {card_number}) ---")

    with data_lock:
        is_known_token = card_number in staff_data

    if is_known_token:
        user_name = staff_data[card_number]
        print(f"Welcome back, {user_name}!")
    else:
        print("New token detected. Please register the user.")
        register_new_user(card_number)

    print("\nReader is still active. Waiting for the next card...")


def read_standalone():
    """
    Initializes the reader and waits for card swipe events.
    """
    # Load existing staff data at the start
    load_staff_data()

    subscriber = None
    try:
        # --- Automatically find and load all DLLs in the script's directory ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        all_files = os.listdir(script_dir)
        for file in all_files:
            if file.lower().endswith('.dll'):
                try:
                    clr.AddReference(os.path.splitext(file)[0])
                except Exception:
                    pass

        from Paxton.Net2.DesktopReaderClient import DesktopReaderSubscriber

        subscriber = DesktopReaderSubscriber()
        subscriber.TokenReadEvent += on_token_read
        subscriber.SubscribeToReaderService()
        subscriber.AcceptTokenReadEvents(True)

        print("\nSUCCESS: Paxton Reader is active. Please present a card.")
        print("(Press Ctrl+C in this terminal to stop the script)")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nScript stopped by user.")
    except Exception:
        print(f"An error occurred: {traceback.format_exc()}")
    finally:
        if subscriber:
            print("Cleaning up...")
            try:
                subscriber.TokenReadEvent -= on_token_read
                if hasattr(subscriber, 'UnsubscribeFromReaderService'):
                    subscriber.UnsubscribeFromReaderService()
                if hasattr(subscriber, 'Dispose'):
                    subscriber.Dispose()
                print("Cleanup complete.")
            except Exception as e:
                print(f"Error during cleanup: {e}")


if __name__ == "__main__":
    print("Starting standalone reader test...")
    print("IMPORTANT: Make sure Net2 Lite is running (as Administrator) and you are logged in.")
    read_standalone()
