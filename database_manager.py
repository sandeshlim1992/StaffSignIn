# database_manager.py
import sqlite3
import os
from datetime import datetime

# Define the database file path
DB_FILE = 'tap_history.db' # This file will be created in the same directory as main.py

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def create_tables():
    """Creates all necessary tables if they don't exist."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Tap Events Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tap_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    staff_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_date TEXT NOT NULL, -- YYYY-MM-DD format for easy querying by date
                    token INTEGER NOT NULL
                )
            ''')
            # Staff Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS staff (
                    token INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE
                )
            ''')
            conn.commit()
            print("Database tables checked/created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
        finally:
            conn.close()


def log_tap_event(staff_name, token, timestamp=None, event_date=None):
    """Logs a single tap event to the database."""
    conn = get_db_connection()
    if conn:
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if event_date is None:
            event_date = datetime.now().strftime("%Y-%m-%d") # Format: YYYY-MM-DD

        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tap_events (staff_name, timestamp, event_date, token) VALUES (?, ?, ?, ?)",
                (staff_name, timestamp, event_date, token)
            )
            conn.commit()
            print(f"Tap event logged for {staff_name} at {timestamp}.")
        except sqlite3.Error as e:
            print(f"Error logging tap event: {e}")
        finally:
            conn.close()

def get_taps_for_staff_and_date(staff_name, query_date_str):
    """
    Retrieves all tap events for a given staff member on a specific date.
    query_date_str should be in 'YYYY-MM-DD' format.
    """
    conn = get_db_connection()
    taps = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp FROM tap_events WHERE staff_name = ? AND event_date = ? ORDER BY timestamp ASC",
                (staff_name, query_date_str)
            )
            rows = cursor.fetchall()
            for row in rows:
                dt_obj = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
                taps.append(dt_obj.strftime("%I:%M:%S %p"))
        except sqlite3.Error as e:
            print(f"Error retrieving taps: {e}")
        finally:
            conn.close()
    return taps

# --- NEW STAFF MANAGEMENT FUNCTIONS ---

def add_staff_member(token, name):
    """Adds a new staff member to the database."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO staff (token, name) VALUES (?, ?)", (token, name))
            conn.commit()
            return True
        except sqlite3.IntegrityError: # Handles duplicate token or name
            return False
        finally:
            conn.close()

def get_all_staff():
    """Retrieves all staff members from the database."""
    conn = get_db_connection()
    staff_list = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT token, name FROM staff ORDER BY name ASC")
            rows = cursor.fetchall()
            for row in rows:
                staff_list.append({'token': row['token'], 'name': row['name']})
        finally:
            conn.close()
    return staff_list

def get_staff_by_token(token):
    """Retrieves a single staff member by their token."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT token, name FROM staff WHERE token = ?", (token,))
            row = cursor.fetchone()
            if row:
                return {'token': row['token'], 'name': row['name']}
        finally:
            conn.close()
    return None


def update_staff_member(original_token, new_token, new_name):
    """Updates a staff member's details in the database."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE staff SET token = ?, name = ? WHERE token = ?", (new_token, new_name, original_token))
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()


def delete_staff_member(token):
    """Deletes a staff member from the database by their token."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM staff WHERE token = ?", (token,))
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()