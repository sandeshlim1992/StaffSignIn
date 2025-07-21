
Staff Sign-In System
This is a desktop application designed to manage and track staff sign-ins and sign-outs using an RFID card reader. The system provides a user-friendly interface for viewing daily records, managing staff members, and configuring settings. Daily sign-in sheets are automatically generated and saved as password-protected Excel files.
Key Features
•	RFID Card Integration: Connects to a Paxton Net2 desktop reader to automatically clock staff in and out.
•	Daily Sheet Generation: Creates password-protected Excel (.xlsx) files for each day's sign-in records.
•	Interactive Dashboard: Features a custom calendar for easy date selection and viewing of daily sign-in data.
•	Member Management: A dedicated page to add, edit, and delete staff members and their associated RFID tokens.
•	System Tray & Notifications: Runs in the system tray and provides toast notifications for events like successful clock-ins.
•	Customizable Settings: Allows configuration of the save directory, Excel file password, and application title.
Hardware Requirements
This application is designed to work exclusively with the Paxton Net2 desktop reader.
The integration is built specifically for the software libraries (DLL files) provided by Paxton. The code directly references Paxton's DesktopReaderSubscriber component, meaning other brands of RFID readers will not be compatible without significant code modifications to the reader_thread.py file.
Technology Stack
•	Language: Python 3
•	GUI Framework: PySide6
•	Excel Handling: openpyxl
•	Hardware Integration: pythonnet (for Paxton reader DLLs)

