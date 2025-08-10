import os
from datetime import date, datetime
from PySide6.QtCore import Qt, QDate, Slot, QSize, QPropertyAnimation, QEasingCurve, QPoint, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QLabel, QFrame,
    QListWidget, QListWidgetItem, QToolButton
)
from PySide6.QtGui import QFont, QColor, QIcon

import constants as c
from table import SignInTable
from reader_thread import PaxtonReaderThread
from dialogs import ask_for_name
from system_toast import SystemToast
from Generate import generate_staff_sign_in_form
from config_manager import load_path
from custom_calendar import CustomCalendar
from database_manager import log_tap_event, get_all_staff, add_staff_member, get_taps_for_staff_and_date


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
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        self.calendar = CustomCalendar(self)
        self.calendar.selection_changed.connect(self.selection_changed.emit)
        self.calendar.month_changed.connect(self._update_next_month_display)

        self.next_month_calendar = CustomCalendar(self)
        self.next_month_calendar.setEnabled(False)

        self.generate_button = QPushButton("Open")
        self.generate_button.setFixedHeight(36)
        self.generate_button.setFixedWidth(80)
        self.generate_button.setFont(QFont(c.WIN_FONT_FAMILY, 10, QFont.Bold))
        self.generate_button.setProperty("primary", True)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.generate_button)
        button_layout.addStretch()

        layout.addWidget(self.calendar)
        layout.addLayout(button_layout)
        layout.addWidget(self.next_month_calendar)
        layout.addStretch()

        self._update_next_month_display()

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
        right_layout.setContentsMargins(30, 30, 30, 30)

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
                background-color: transparent;
                border: none;
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
        panel_layout.setContentsMargins(25, 25, 25, 25)
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
            all_staff = get_all_staff()
            self.staff_data = {member['token']: member['name'] for member in all_staff}
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not load staff data from database: {e}")

    @Slot(int)
    def process_card_swipe(self, token):
        if not self.current_file_path:
            self.show_toast("Action Required", "Please generate a sheet before swiping cards.")
            return

        if self.is_processing_swipe: return
        try:
            self.is_processing_swipe = True
            if token in self.staff_data:
                staff_name = self.staff_data[token]

                try:
                    file_name = os.path.basename(self.current_file_path)
                    date_part = os.path.splitext(file_name)[0]
                    sheet_date = datetime.strptime(date_part, '%m-%d-%Y').date()
                    query_date_str = sheet_date.strftime('%Y-%m-%d')

                    previous_taps = get_taps_for_staff_and_date(staff_name, query_date_str)
                    total_taps_today = len(previous_taps) + 1

                    first_tap_time = previous_taps[0] if previous_taps else None

                    now_time = datetime.now().time()
                    full_datetime = datetime.combine(sheet_date, now_time)
                    db_timestamp = full_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    db_event_date = full_datetime.strftime("%Y-%m-%d")
                    log_tap_event(staff_name, token, db_timestamp, db_event_date)

                    time_now_str = full_datetime.strftime("%I:%M:%S %p")

                    # First, update the Excel file in the background
                    status, _ = self.table_widget.record_swipe(
                        self.current_file_path, staff_name, time_now_str,
                        total_taps_today, first_tap_time_str=first_tap_time
                    )

                    # MODIFICATION: Instead of reloading the whole table, update the view directly.
                    # This is faster and avoids the visual glitch.
                    row_to_highlight = self.table_widget.update_view_for_swipe(
                        staff_name, time_now_str, total_taps_today
                    )

                except Exception as e:
                    # Fallback logic remains largely the same
                    log_tap_event(staff_name, token)
                    time_now_str = datetime.now().strftime("%I:%M:%S %p")
                    total_taps_today = 1
                    status, _ = self.table_widget.record_swipe(
                        self.current_file_path, staff_name, time_now_str,
                        total_taps_today, first_tap_time_str=None
                    )
                    row_to_highlight = self.table_widget.update_view_for_swipe(
                        staff_name, time_now_str, total_taps_today
                    )
                    QMessageBox.warning(self, "Logic Error",
                                        f"Could not determine tap count, used fallback logic.\n{e}")

                parts = status.split(': ', 1)
                if len(parts) == 2:
                    action, name = parts
                    if "Clocked In" in action:
                        self.show_toast(action, name, status='success')
                    elif "Clocked Out" in action:
                        self.show_toast(action, name, status='error')
                    else:
                        self.show_toast(action, name, status='info')

                # MODIFICATION: Do NOT reload the entire table from the file anymore.
                # self.display_excel_content(self.current_file_path)

                highlight_color = QColor(c.WIN_COLOR_ACCENT_PRIMARY)
                self.table_widget.highlight_row(row_to_highlight, highlight_color)
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

        if not add_staff_member(token, user_name):
            QMessageBox.warning(self, "Registration Failed", "This token or name may already be in use.")
            return

        self.staff_data[token] = user_name

        total_taps_today = 1
        full_datetime = None
        try:
            file_name = os.path.basename(self.current_file_path)
            date_part = os.path.splitext(file_name)[0]
            sheet_date = datetime.strptime(date_part, '%m-%d-%Y').date()

            now_time = datetime.now().time()
            full_datetime = datetime.combine(sheet_date, now_time)
            db_timestamp = full_datetime.strftime("%Y-%m-%d %H:%M:%S")
            db_event_date = full_datetime.strftime("%Y-%m-%d")
            log_tap_event(user_name, token, db_timestamp, db_event_date)
        except Exception:
            log_tap_event(user_name, token)

        if self.parent_window and hasattr(self.parent_window, 'members_page'):
            self.parent_window.members_page.staff_data_changed.emit()

        time_now_str = full_datetime.strftime("%I:%M:%S %p") if full_datetime else datetime.now().strftime(
            "%I:%M:%S %p")

        # Update Excel file
        status, _ = self.table_widget.record_swipe(
            self.current_file_path, user_name, time_now_str, total_taps_today, first_tap_time_str=None
        )

        # Update view
        row_to_highlight = self.table_widget.update_view_for_swipe(user_name, time_now_str, total_taps_today)

        parts = status.split(': ', 1)
        if len(parts) == 2:
            action, name = parts
            self.show_toast(action, name, status='success')

        # Do not reload table
        # self.display_excel_content(self.current_file_path)

        highlight_color = QColor(c.WIN_COLOR_ACCENT_PRIMARY)
        self.table_widget.highlight_row(row_to_highlight, highlight_color)

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

            py_date = selected_qdate.toPython()

            is_sheet_open = (file_date == py_date)
            button.setEnabled(not is_sheet_open)
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
        toast = SystemToast(title, message, status=status)
        self.active_toasts.append(toast)
        toast.finished.connect(lambda: self.active_toasts.remove(toast))
        toast.show_toast()

    @Slot(str)
    def show_reader_error(self, message):
        QMessageBox.critical(self, "Paxton Reader Error", message)