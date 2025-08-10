import csv
import os
import sys
from database_manager import create_tables, add_staff_member, get_db_connection

STAFF_FILE = 'staff_data.csv'


def migrate():
    """
    Reads staff data from staff_data.csv and inserts it into the SQLite database.
    """
    # 1. Ensure the database and tables exist
    print("Initializing database and tables...")
    create_tables()

    # 2. Check if the staff table is already populated
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM staff")
        count = cursor.fetchone()[0]
        conn.close()
        if count > 0:
            print("Staff table is not empty. Migration has likely already been run.")
            # Ask user if they want to proceed
            response = input("Do you want to clear the table and migrate again? THIS IS DESTRUCTIVE. (yes/no): ")
            if response.lower() != 'yes':
                print("Migration cancelled.")
                return
            else:
                # Clear the table
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM staff")
                conn.commit()
                conn.close()
                print("Staff table cleared.")

    # 3. Check if the CSV file exists
    if not os.path.exists(STAFF_FILE):
        print(f"'{STAFF_FILE}' not found. No data to migrate.")
        return

    # 4. Read the CSV and insert into the database
    print(f"Reading data from '{STAFF_FILE}'...")
    try:
        with open(STAFF_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header

            migrated_count = 0
            skipped_count = 0

            for row in reader:
                if not row: continue
                try:
                    token = int(row[0])
                    name = row[1]
                    if add_staff_member(token, name):
                        print(f"  Migrated: {name} (Token: {token})")
                        migrated_count += 1
                    else:
                        print(f"  Skipped (already exists?): {name} (Token: {token})")
                        skipped_count += 1
                except (ValueError, IndexError):
                    print(f"  Skipped invalid row: {row}")
                    skipped_count += 1

        print(f"\nMigration complete. {migrated_count} records migrated, {skipped_count} records skipped.")

    except Exception as e:
        print(f"An error occurred during migration: {e}")


if __name__ == "__main__":
    migrate()