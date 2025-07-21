import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
from PySide6.QtGui import QFont, QColor
from datetime import datetime, timedelta

import constants as c

try:
    import openpyxl
except ImportError:
    openpyxl = None


class SignInTable(QTableWidget):
    """
    A custom QTableWidget specialized for displaying and managing the sign-in sheet.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_stylesheet = f"""
            QTableWidget {{ 
                border: none; 
                gridline-color: {c.WIN_COLOR_BORDER_LIGHT};
            }}
            QHeaderView::section:horizontal {{
                background-color: {c.WIN_COLOR_WINDOW_BG};
                padding: 10px;
                border: none; 
                border-bottom: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
                font-size: 10pt; 
                font-weight: bold; 
                color: {c.WIN_COLOR_TEXT_PRIMARY};
                min-height: 40px;
            }}
            QHeaderView::section:horizontal:first {{
                border-top-left-radius: 15px;
            }}
            QHeaderView::section:horizontal:last {{
                border-top-right-radius: 15px;
            }}
        """
        self.setStyleSheet(self.original_stylesheet)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(36)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def display_excel_content(self, file_path):
        """
        Loads data from the specified Excel file and populates the table.
        Returns the date string from the file on success, otherwise None.
        """
        if not openpyxl:
            QMessageBox.critical(self, "Missing Dependency", "The 'openpyxl' library is required.")
            return None

        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook.active

            headers = [cell.value for cell in sheet[2]]
            file_date_str = sheet['C1'].value

            self.setColumnCount(len(headers))
            self.setHorizontalHeaderLabels(headers)

            all_rows = list(sheet.iter_rows(min_row=3, values_only=True))
            self.setRowCount(len(all_rows))

            for row_idx, row_data in enumerate(all_rows):
                for col_idx, cell_value in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_value) if cell_value is not None else "")
                    item.setForeground(QColor(c.WIN_COLOR_TEXT_PRIMARY))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.setItem(row_idx, col_idx, item)

            self.setColumnWidth(0, 350)
            return file_date_str

        except Exception as e:
            QMessageBox.critical(self, "Error Reading File", f"Could not read the Excel file:\n\n{e}")
            return None

    def record_swipe(self, file_path, staff_name):
        """
        Handles a card swipe. First tap clocks in. All subsequent taps update the clock-out time.
        Returns a tuple of (status_message, row_index).
        """
        if not file_path or not openpyxl:
            return "Error: File path or Excel library not available.", -1

        password = "lsst1234"
        time_now_str = datetime.now().strftime("%I:%M:%S %p")

        try:
            workbook = openpyxl.load_workbook(file_path)
            sheet = workbook.active

            sheet.protection.password = password
            sheet.protection.sheet = False

            target_row_excel = -1
            for row in range(3, sheet.max_row + 2):
                if sheet[f'A{row}'].value == staff_name:
                    target_row_excel = row
                    break

            status_message = ""
            target_row_widget = -1

            if target_row_excel != -1:
                sheet[f'C{target_row_excel}'] = time_now_str
                status_message = f"Clocked Out: {staff_name}"
                target_row_widget = target_row_excel - 3
            else:
                next_row_excel = 3
                while sheet[f'A{next_row_excel}'].value is not None:
                    next_row_excel += 1
                sheet[f'A{next_row_excel}'] = staff_name
                sheet[f'B{next_row_excel}'] = time_now_str
                status_message = f"Clocked In: {staff_name}"
                target_row_widget = next_row_excel - 3

            sheet.protection.sheet = True
            workbook.save(file_path)
            return status_message, target_row_widget

        except PermissionError:
            QMessageBox.critical(self, "Permission Denied",
                                 f"Could not save to Excel.\nPlease make sure the file is not open.")
            return "Save failed: Permission Denied.", -1
        except Exception as e:
            QMessageBox.critical(self, "Error Saving File",
                                 f"An unexpected error occurred while saving to Excel:\n\n{e}")
            return "Save failed: An unexpected error occurred.", -1

    def highlight_row(self, row_index, color=QColor("#D4EDDA")):
        """Temporarily highlights a specific row with a solid color."""
        if row_index < 0 or row_index >= self.rowCount():
            return

        highlight_stylesheet = self.original_stylesheet.replace(
            f"gridline-color: {c.WIN_COLOR_BORDER_LIGHT};",
            f"gridline-color: {color.name()};"
        )
        self.setStyleSheet(highlight_stylesheet)

        original_brushes = []
        for col in range(self.columnCount()):
            item = self.item(row_index, col)
            if not item:
                item = QTableWidgetItem()
                self.setItem(row_index, col, item)
            original_brushes.append(item.background())
            item.setBackground(color)

        QTimer.singleShot(1200, lambda: self.end_highlight(row_index, original_brushes))

    def end_highlight(self, row_index, original_brushes):
        """Reverts the background color of a row and restores the grid."""
        for col in range(self.columnCount()):
            item = self.item(row_index, col)
            if item and col < len(original_brushes):
                item.setBackground(original_brushes[col])

        self.setStyleSheet(self.original_stylesheet)

    def get_staff_in_building(self):
        """
        Scans the table and returns a list of names of staff who
        have clocked in but not clocked out.
        """
        staff_in = []
        for row in range(self.rowCount()):
            name_item = self.item(row, 0)
            clock_in_item = self.item(row, 1)
            clock_out_item = self.item(row, 2)

            if (name_item and name_item.text() and
                    clock_in_item and clock_in_item.text() and
                    (not clock_out_item or not clock_out_item.text())):
                staff_in.append(name_item.text())

        return staff_in

    def clear_table(self):
        """Clears all content from the table."""
        self.setRowCount(0)
        self.clearContents()