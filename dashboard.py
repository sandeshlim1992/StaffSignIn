import os
import csv
from datetime import date, datetime
from PySide6.QtCore import Qt, QDate, Slot, QSize, QPropertyAnimation, QEasingCurve, QPoint, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QLabel, QFrame,
    QStackedWidget, QTableWidgetItem, QCalendarWidget, QToolButton, QListWidget, QListWidgetItem,
    QGraphicsOpacityEffect
)
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QIcon

import constants as c
from table import SignInTable
from reader_thread import PaxtonReaderThread
from dialogs import ask_for_name
from toast import ToastNotification
from Generate import generate_staff_sign_in_form
from config_manager import load_path
from custom_calendar import CustomCalendar

STAFF_FILE = 'staff_data.csv'


class Scrim(QWidget):
    """A semi-transparent overlay that captures clicks to close the panel."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.3);")
        self.hide()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class CalendarContainer(QFrame):
    """A container widget for the new custom calendar."""
    selection_changed = Signal(QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG_ALT};
                border-right: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
                border-radius: 0px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Create the main calendar
        self.calendar = CustomCalendar(self)
        self.calendar.selection_changed.connect(self.selection_changed.emit)
        self.calendar.month_changed.connect(self._update_next_month_display)

        # Create the second calendar for the next month
        self.next_month_calendar = CustomCalendar(self)
        self.next_month_calendar.setEnabled(False)  # Make it non-interactive

        # Update button text, size, and font
        self.generate_button = QPushButton("Open")
        self.generate_button.setFixedHeight(36)
        self.generate_button.setFixedWidth(80)  # Set a smaller fixed width
        self.generate_button.setFont(QFont(c.WIN_FONT_FAMILY, 10, QFont.Bold))
        self.generate_button.setProperty("primary", True)

        # New layout to center the button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.generate_button)
        button_layout.addStretch()

        layout.addWidget(self.calendar)
        layout.addLayout(button_layout)  # Add centered button
        layout.addWidget(self.next_month_calendar)  # Add second calendar
        layout.addStretch()  # Move stretch to the end

        self._update_next_month_display()  # Set initial state

    def _update_next_month_display(self):
        """Updates the second calendar to show the month after the main one."""
        next_month_date = self.calendar.current_date.addMonths(1)
        self.next_month_calendar.set_date(next_month_date.year(), next_month_date.month())

    def selected_date(self):
        return self.calendar.selectedDate()


class DashboardPage(QWidget):
    def __init__(self, parent_main_window=None):
        super().__init__(parent_main_window)
        self.parent_window = parent_main_window
        self.current_file_path = None
        self.staff_data = {}
        self.is_processing_swipe = False
        self.active_toasts = []

        self.load_staff_data()
        self.setup_ui()
        self.setup_reader_thread()
        self.open_todays_sheet()

    def setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.calendar_container = CalendarContainer()
        self.calendar_container.generate_button.clicked.connect(self.on_view_sheet_clicked)
        self.calendar_container.selection_changed.connect(self.update_view_button_state)
        self.layout.addWidget(self.calendar_container)

        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(25, 25, 25, 25)

        title_bar_layout = QHBoxLayout()
        title_label = QLabel("Daily Sign-In Sheet")
        title_font = QFont(c.WIN_FONT_FAMILY, 18, QFont.Bold)
        title_label.setFont(title_font)
        title_bar_layout.addWidget(title_label, alignment=Qt.AlignLeft)
        title_bar_layout.addStretch()

        button_container = QWidget()
        button_container_layout = QHBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)

        self.members_button = QToolButton()
        self.members_button.setIcon(QIcon("icons/members_left.svg"))
        self.members_button.setIconSize(QSize(32, 32))
        self.members_button.setFixedSize(50, 50)
        self.members_button.setStyleSheet(f"""
            QToolButton {{
                border: none;
                background-color: transparent;
                border-radius: {c.WIN_BORDER_RADIUS};
            }}
            QToolButton:hover {{
                background-color: {c.WIN_COLOR_CONTROL_BG_HOVER};
            }}
        """)
        self.members_button.clicked.connect(self.toggle_side_panel)
        button_container_layout.addWidget(self.members_button)

        self.members_count_label = QLabel("0", self.members_button)
        self.members_count_label.setFont(QFont(c.WIN_FONT_FAMILY, 8, QFont.Bold))
        self.members_count_label.setFixedSize(20, 20)
        self.members_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.members_count_label.setStyleSheet(f"""
            QLabel {{
                background-color: {c.WIN_COLOR_ACCENT_PRIMARY};
                color: {c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
                border-radius: 10px;
                border: 1px solid {c.WIN_COLOR_WIDGET_BG};
            }}
        """)
        badge_x = self.members_button.width() - self.members_count_label.width()
        self.members_count_label.move(badge_x, 0)
        self.members_count_label.raise_()
        self.members_count_label.hide()

        title_bar_layout.addWidget(button_container)
        right_layout.addLayout(title_bar_layout)

        self.date_label = QLabel("Please select a date and click 'View Sheet'")
        self.date_label.setFont(QFont(c.WIN_FONT_FAMILY, c.WIN_FONT_SIZE_TITLE))
        self.date_label.setStyleSheet(f"color: {c.WIN_COLOR_TEXT_SECONDARY};")
        right_layout.addWidget(self.date_label)

        self.table_container = QFrame()
        self.table_container.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG};
                border: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
            }}
        """)
        container_layout = QVBoxLayout(self.table_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        self.table_widget = SignInTable()
        container_layout.addWidget(self.table_widget)
        right_layout.addWidget(self.table_container, 1)
        self.table_container.setVisible(False)
        self.layout.addWidget(self.right_panel, 1)

        self.scrim = Scrim(self.right_panel)
        self.scrim.clicked.connect(self.toggle_side_panel)
        self.create_side_panel()

        self.update_members_button_tooltip()

    def create_side_panel(self):
        self.side_panel = QFrame(self.right_panel)
        self.side_panel_width = 280
        self.side_panel.setFixedWidth(self.side_panel_width)
        self.side_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG};
                border-left: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
                border-radius: 0px;
            }}
        """)

        panel_layout = QVBoxLayout(self.side_panel)
        panel_layout.setContentsMargins(15, 15, 15, 15)
        panel_layout.setSpacing(10)

        title = QLabel("Staff in Building")
        title.setFont(QFont(c.WIN_FONT_FAMILY, 14, QFont.Bold))

        self.staff_list_widget = QListWidget()
        self.staff_list_widget.setStyleSheet("QListWidget { border: none; }")

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.toggle_side_panel)

        panel_layout.addWidget(title)
        panel_layout.addWidget(self.staff_list_widget, 1)
        panel_layout.addWidget(close_button, alignment=Qt.AlignRight)

        self.panel_animation = QPropertyAnimation(self.side_panel, b"pos")
        self.panel_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.panel_animation.setDuration(300)
        self.panel_animation.finished.connect(self.on_panel_animation_finished)
        self.side_panel.hide()

    def toggle_side_panel(self):
        is_opening = self.side_panel.isHidden()

        start_pos = QPoint(self.right_panel.width(), 0)
        end_pos = QPoint(self.right_panel.width() - self.side_panel_width, 0)
        self.panel_animation.setStartValue(start_pos)
        self.panel_animation.setEndValue(end_pos)

        if is_opening:
            staff_in = self.table_widget.get_staff_in_building()
            self.staff_list_widget.clear()
            if staff_in:
                for name in staff_in: self.staff_list_widget.addItem(QListWidgetItem(name))
            else:
                self.staff_list_widget.addItem(QListWidgetItem("No staff currently clocked in."))

            self.scrim.show()
            self.side_panel.show()
            self.panel_animation.setDirection(QPropertyAnimation.Forward)
            self.panel_animation.start()
        else:
            self.panel_animation.setDirection(QPropertyAnimation.Backward)
            self.panel_animation.start()

    @Slot()
    def on_panel_animation_finished(self):
        if self.panel_animation.direction() == QPropertyAnimation.Backward:
            self.side_panel.hide()
            self.scrim.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scrim.setGeometry(0, 0, self.right_panel.width(), self.right_panel.height())

        if self.side_panel.isHidden():
            self.side_panel.move(self.right_panel.width(), 0)
        self.side_panel.setFixedHeight(self.right_panel.height())
        self.reposition_toasts()

    def on_view_sheet_clicked(self):
        selected_date = self.calendar_container.selected_date()
        self.generate_or_load_sheet_for_date(selected_date.toPython())

    def setup_reader_thread(self):
        self.reader_thread = PaxtonReaderThread()
        self.reader_thread.token_read_signal.connect(self.process_card_swipe)
        self.reader_thread.error_signal.connect(self.show_reader_error)
        self.reader_thread.status_signal.connect(lambda msg: print(f"Reader Status: {msg}"))
        self.reader_thread.start()

    def load_staff_data(self):
        try:
            if not os.path.exists(STAFF_FILE):
                with open(STAFF_FILE, 'w', newline='') as f: writer = csv.writer(f); writer.writerow(
                    ['Token', 'StaffName'])
                self.staff_data = {}
                return
            with open(STAFF_FILE, 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader)
                self.staff_data = {int(row[0]): row[1] for row in reader if row}
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load staff data: {e}")

    @Slot(int)
    def process_card_swipe(self, token):
        if not self.current_file_path:
            self.show_toast("Action Required", "Please generate a sheet before swiping cards.", status='warning')
            return

        if self.is_processing_swipe: return
        try:
            self.is_processing_swipe = True
            if token in self.staff_data:
                staff_name = self.staff_data[token]
                status, row_to_highlight = self.table_widget.record_swipe(self.current_file_path, staff_name)

                parts = status.split(': ', 1)
                if len(parts) == 2:
                    action, name = parts
                    rich_message = f"{action}: <b><font color='{c.WIN_COLOR_ACCENT_PRIMARY}'>{name}</font></b>"
                else:
                    rich_message = status

                if "Clocked In" in status:
                    self.show_toast("Success", rich_message, status='success')
                elif "Clocked Out" in status:
                    self.show_toast("Information", rich_message, status='info')
                else:
                    self.show_toast("Warning", rich_message, status='warning')

                self.display_excel_content(self.current_file_path)
                self.table_widget.highlight_row(row_to_highlight)
            else:
                self.register_new_user(token)
        finally:
            self.is_processing_swipe = False
            self.update_members_button_tooltip()

    def register_new_user(self, token):
        user_name = ask_for_name(self, token)
        if not user_name:
            self.show_toast("Cancelled", "Registration cancelled.", status='info')
            return

        self.staff_data[token] = user_name
        try:
            with open(STAFF_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([token, user_name])
        except Exception as e:
            self.show_reader_error(f"Failed to save new staff member: {e}")
            return

        status, row_to_highlight = self.table_widget.record_swipe(self.current_file_path, user_name)

        parts = status.split(': ', 1)
        if len(parts) == 2:
            action, name = parts
            rich_message = f"{action}: <b><font color='{c.WIN_COLOR_ACCENT_PRIMARY}'>{name}</font></b>"
        else:
            rich_message = status

        self.show_toast("Success", rich_message, status='success')
        self.display_excel_content(self.current_file_path)
        self.table_widget.highlight_row(row_to_highlight)

    def generate_or_load_sheet_for_date(self, selected_date):
        save_dir = load_path()
        file_path = os.path.join(save_dir, f"{selected_date.strftime('%#m-%#d-%Y')}.xlsx")

        if os.path.exists(file_path):
            self.display_excel_content(file_path)
        else:
            new_file_path = generate_staff_sign_in_form(target_date=selected_date)
            if new_file_path:
                self.display_excel_content(new_file_path)

    def open_todays_sheet(self):
        todays_date = date.today()
        self.generate_or_load_sheet_for_date(todays_date)

    def display_excel_content(self, file_path):
        self.current_file_path = file_path
        file_date_str = self.table_widget.display_excel_content(file_path)

        if file_date_str:
            try:
                dt_obj = datetime.strptime(file_date_str, "%m/%d/%Y")
                formatted_date = dt_obj.strftime("%a, %B %d")
                rich_text = f"Current Sheet: <b><font color='{c.WIN_COLOR_ACCENT_PRIMARY}'>{formatted_date}</font></b>"
                self.date_label.setText(rich_text)
            except (ValueError, TypeError):
                self.date_label.setText(f"Current Sheet: {file_date_str}")

            self.table_container.setVisible(True)
        else:
            self.table_container.setVisible(False)
            self.date_label.setText("Could not load sheet.")
            QMessageBox.critical(self, "Error", f"Could not load or display the sheet for {file_path}")

        self.update_members_button_tooltip()
        self.update_view_button_state()

    @Slot(QDate)
    def update_view_button_state(self, selected_qdate=None):
        # If not called by a signal, get the date manually
        if selected_qdate is None:
            selected_qdate = self.calendar_container.selected_date()

        button = self.calendar_container.generate_button
        if not self.current_file_path:
            button.setEnabled(True)
            button.setText("Open")
            return

        try:
            base_name = os.path.basename(self.current_file_path)
            file_date_str = os.path.splitext(base_name)[0]
            file_date = datetime.strptime(file_date_str, "%m-%d-%Y").date()

            # Convert the QDate to a Python date for comparison
            py_date = selected_qdate.toPython()

            is_sheet_open = (file_date == py_date)
            button.setEnabled(not is_sheet_open)

            # Set text to "Open" for both states
            button.setText("Open")

        except (ValueError, TypeError):
            button.setEnabled(True)
            button.setText("Open")

    def update_members_button_tooltip(self):
        if not self.table_container.isVisible():
            self.members_button.setToolTip("No sheet is active.")
            self.members_count_label.hide()
            return

        staff_in_list = self.table_widget.get_staff_in_building()
        count = len(staff_in_list)

        if count > 0:
            self.members_count_label.setText(str(count))
            self.members_count_label.show()
        else:
            self.members_count_label.hide()

        if count == 1:
            self.members_button.setToolTip(f"1 staff member is currently in the building.")
        else:
            self.members_button.setToolTip(f"{count} staff members are currently in the building.")

    def show_toast(self, title, message, status='info'):
        """Creates and positions a new toast notification."""
        main_window = self.window()
        if not main_window:
            print("Error: Could not find main window to parent toast.")
            return

        toast = ToastNotification(main_window, title, message, status)

        toast.closing.connect(self.on_toast_destroyed)
        self.active_toasts.append(toast)

        self.reposition_toasts()
        toast.show_toast()

    def reposition_toasts(self):
        """Stacks all active toasts neatly in the bottom-right corner."""
        main_window = self.window()
        if not main_window: return

        parent_rect = main_window.geometry()
        y_pos = parent_rect.height() - 20

        for toast in reversed(self.active_toasts):
            if toast.isWidgetType():
                toast_size = toast.sizeHint()
                y_pos -= (toast_size.height() + 10)
                x_pos = parent_rect.width() - toast_size.width() - 20

                global_pos = main_window.mapToGlobal(QPoint(x_pos, y_pos))
                toast.move(global_pos)

    @Slot(QObject)
    def on_toast_destroyed(self, obj):
        """Removes a toast from the active list when it's closed."""
        if obj in self.active_toasts:
            self.active_toasts.remove(obj)
        self.reposition_toasts()
        obj.deleteLater()

    @Slot(str)
    def show_reader_error(self, message):
        QMessageBox.critical(self, "Paxton Reader Error", message)