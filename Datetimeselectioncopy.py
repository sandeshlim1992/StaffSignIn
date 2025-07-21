from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QDialog, QCalendarWidget, QDialogButtonBox, QToolButton
)
from PySide6.QtGui import QFont

# --- Theme constants required for the dialog ---
WIN_COLOR_ACCENT_PRIMARY = "#0078D4"
WIN_COLOR_ACCENT_TEXT_ON_PRIMARY = "#FFFFFF"
WIN_COLOR_CONTROL_BG_HOVER = "#E9ECEF"
WIN_FONT_FAMILY = "Segoe UI Variable"
WIN_COLOR_WIDGET_BG = "#FFFFFF"
WIN_COLOR_WIDGET_BG_ALT = "#F0F0F0"
WIN_COLOR_TEXT_SECONDARY = "#4A4A4A"
WIN_COLOR_TEXT_PRIMARY = "#000000"
CALENDAR_SELECTION_COLOR = "#005FB8"


class DateSelectorDialog(QDialog):
    """A modern, two-panel dialog for selecting a date, inspired by the user's image."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date")
        self.setModal(True)
        self.setFixedSize(600, 380)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet(f"background-color: {WIN_COLOR_WIDGET_BG}; border-radius: 8px;")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left Panel ---
        left_panel = QFrame()
        left_panel.setFixedWidth(220)
        left_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {WIN_COLOR_WIDGET_BG_ALT};
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(25, 20, 25, 20)

        select_label = QLabel("Select date")
        select_label.setFont(QFont(WIN_FONT_FAMILY, 11))
        select_label.setStyleSheet(f"color: {WIN_COLOR_TEXT_SECONDARY};")

        self.full_date_label = QLabel("")
        self.full_date_label.setFont(QFont(WIN_FONT_FAMILY, 28, QFont.Bold))
        self.full_date_label.setWordWrap(True)

        left_layout.addWidget(select_label)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.full_date_label)
        left_layout.addStretch()

        main_layout.addWidget(left_panel)

        # --- Right Panel ---
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        # --- FIX: Create the calendar widget BEFORE creating the nav bar that uses it ---
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(False)
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.selectionChanged.connect(self.update_date_display)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)

        custom_nav_bar = self.create_custom_nav_bar()
        right_layout.addWidget(custom_nav_bar)

        # Hide the default navigation bar
        self.calendar.findChild(QWidget, "qt_calendar_navigationbar").setVisible(False)

        self.calendar.setStyleSheet(f"""
            QCalendarWidget QToolButton {{
                height: 32px; width: 32px; font-size: 10pt; color: {WIN_COLOR_TEXT_PRIMARY};
                background-color: transparent; border-radius: 16px;
            }}
            QCalendarWidget QToolButton:hover {{ background-color: {WIN_COLOR_CONTROL_BG_HOVER}; }}
            QCalendarWidget #qt_calendar_daybutton:hover {{
                 background-color: {WIN_COLOR_CONTROL_BG_HOVER};
            }}
            QCalendarWidget #qt_calendar_daybutton[selected="true"] {{
                 background-color: {CALENDAR_SELECTION_COLOR}; color: {WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
            }}
             QCalendarWidget #qt_calendar_daybutton[today="true"] {{
                font-weight: bold; color: {CALENDAR_SELECTION_COLOR};
            }}
            QCalendarWidget QAbstractItemView {{ selection-background-color: {CALENDAR_SELECTION_COLOR}; }}
        """)
        right_layout.addWidget(self.calendar)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("OK")
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet("border: none; color: #888;")
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet(
            f"border: none; color: {WIN_COLOR_ACCENT_PRIMARY}; font-weight: bold;")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        button_layout.addWidget(self.button_box)
        right_layout.addLayout(button_layout)

        main_layout.addWidget(right_panel)

        self.update_date_display()
        self.update_month_year_label()

    def create_custom_nav_bar(self):
        """Creates a custom widget to replace the calendar's default navigation."""
        nav_bar = QWidget()
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(5, 0, 5, 0)

        self.month_year_label = QLabel()
        self.month_year_label.setFont(QFont(WIN_FONT_FAMILY, 11, QFont.Bold))

        prev_button = QToolButton()
        prev_button.setText("‹")
        prev_button.clicked.connect(self.calendar.showPreviousMonth)

        next_button = QToolButton()
        next_button.setText("›")
        next_button.clicked.connect(self.calendar.showNextMonth)

        for btn in [prev_button, next_button]:
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(
                "QToolButton { border: none; font-size: 16pt; } QToolButton:hover { background-color: #eee; border-radius: 4px; }")

        nav_layout.addWidget(self.month_year_label)
        nav_layout.addStretch()
        nav_layout.addWidget(prev_button)
        nav_layout.addWidget(next_button)

        self.calendar.currentPageChanged.connect(self.update_month_year_label)
        return nav_bar

    def update_month_year_label(self):
        """Updates the text of the custom month/year label."""
        year = self.calendar.yearShown()
        month = self.calendar.monthShown()
        date = QDate(year, month, 1)
        self.month_year_label.setText(date.toString("MMMM yyyy"))

    def update_date_display(self):
        selected_qdate = self.calendar.selectedDate()
        self.full_date_label.setText(selected_qdate.toString("ddd, MMM d"))

    def selected_date(self):
        return self.calendar.selectedDate()
