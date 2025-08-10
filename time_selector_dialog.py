from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLabel,
    QPushButton, QButtonGroup, QCompleter, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QFont, QColor

import constants as c
from database_manager import get_all_staff


class TimeSelectorDialog(QDialog):
    """A dialog for selecting a staff member, a time, and an action (in/out)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manual Clock-In / Out")
        self.setModal(True)
        self.setFixedWidth(380)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.all_staff = get_all_staff()
        self.action = None

        # --- Main Background Frame ---
        self.background_frame = QFrame()
        self.background_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG};
                border-radius: 10px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.background_frame.setGraphicsEffect(shadow)

        # --- Main Layout ---
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.background_frame)

        main_layout = QVBoxLayout(self.background_frame)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        # --- Header with Title and Close button ---
        header_layout = QHBoxLayout()
        title_label = QLabel("Manual Clock-In / Out")
        title_label.setFont(QFont(c.WIN_FONT_FAMILY, 12, QFont.Bold))
        title_label.setStyleSheet(f"color: {c.WIN_COLOR_TEXT_PRIMARY};")

        close_button = QPushButton("✕")
        close_button.setFixedSize(28, 28)
        # MODIFICATION: Changed color to red to make it visible.
        close_button.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                color: red;
                border: none;
                background-color: transparent;
                border-radius: 5px;
            }
            QPushButton:hover {
                color: #CC0000;
                background-color: #F8E0E0;
            }
        """)
        close_button.clicked.connect(self.reject)  # Closes the dialog

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_button)
        main_layout.addLayout(header_layout)

        # --- Staff Selector ---
        staff_label = QLabel("Staff Member")
        staff_label.setStyleSheet(f"color: {c.WIN_COLOR_TEXT_SECONDARY};")
        main_layout.addWidget(staff_label)

        self.staff_combo = QComboBox()
        self.staff_combo.setEditable(True)
        self.staff_combo.setInsertPolicy(QComboBox.NoInsert)
        self.staff_combo.setFixedHeight(40)
        self.staff_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
                border-radius: 5px;
                padding-left: 10px;
                background-color: {c.WIN_COLOR_WIDGET_BG_ALT};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        for staff in self.all_staff:
            self.staff_combo.addItem(staff['name'], userData=staff)

        completer = QCompleter([staff['name'] for staff in self.all_staff], self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.staff_combo.setCompleter(completer)
        main_layout.addWidget(self.staff_combo)

        # --- Time Selector ---
        time_label = QLabel("Time")
        time_label.setStyleSheet(f"color: {c.WIN_COLOR_TEXT_SECONDARY};")
        main_layout.addWidget(time_label)

        time_container = QFrame()
        time_container.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG_ALT};
                border-radius: 8px;
                border: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
            }}
        """)
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(10, 10, 10, 10)

        self.hour_combo = QComboBox()
        self.minute_combo = QComboBox()

        combo_style = f"""
            QComboBox {{
                border: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
                border-radius: 5px;
                background-color: {c.WIN_COLOR_WIDGET_BG};
                padding: 5px;
            }}
        """
        self.hour_combo.setStyleSheet(combo_style)
        self.minute_combo.setStyleSheet(combo_style)

        self.hour_combo.addItems([f"{h:02d}" for h in range(1, 13)])
        self.minute_combo.addItems([f"{m:02d}" for m in range(0, 60, 5)])

        self.am_button = QPushButton("AM")
        self.pm_button = QPushButton("PM")
        self.am_button.setCheckable(True)
        self.pm_button.setCheckable(True)

        now = QTime.currentTime()
        if now.hour() >= 12:
            self.pm_button.setChecked(True)
        else:
            self.am_button.setChecked(True)

        self.meridiem_group = QButtonGroup(self)
        self.meridiem_group.setExclusive(True)
        self.meridiem_group.addButton(self.am_button)
        self.meridiem_group.addButton(self.pm_button)

        meridiem_style = f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
                padding: 5px 12px;
            }}
            QPushButton:checked {{
                background-color: {c.WIN_COLOR_ACCENT_PRIMARY};
                color: {c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
                border: 1px solid {c.WIN_COLOR_ACCENT_PRIMARY};
            }}
        """
        self.am_button.setStyleSheet(meridiem_style + "border-top-right-radius: 0px; border-bottom-right-radius: 0px;")
        self.pm_button.setStyleSheet(
            meridiem_style + "border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-left: none;")

        time_layout.addWidget(self.hour_combo, 1)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.minute_combo, 1)
        time_layout.addSpacing(15)
        time_layout.addWidget(self.am_button)
        time_layout.addWidget(self.pm_button)

        main_layout.addWidget(time_container)

        # --- Dialog Buttons ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.clock_out_button = QPushButton("Clock Out")
        self.clock_out_button.clicked.connect(self.on_clock_out)
        self.clock_out_button.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 18px;
                color: {c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
                background-color: #FD5E53;
                border-radius: {c.WIN_BORDER_RADIUS};
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #E04B40;
            }}
        """)
        button_layout.addWidget(self.clock_out_button)

        self.clock_in_button = QPushButton("Clock In")
        self.clock_in_button.setProperty("primary", True)
        self.clock_in_button.clicked.connect(self.on_clock_in)
        button_layout.addWidget(self.clock_in_button)

        main_layout.addLayout(button_layout)

    def on_clock_in(self):
        self.action = 'in'
        self.accept()

    def on_clock_out(self):
        self.action = 'out'
        self.accept()

    def get_selected_staff(self):
        selected_index = self.staff_combo.currentIndex()
        if selected_index >= 0:
            return self.staff_combo.itemData(selected_index)
        return None

    def get_selected_time(self):
        hour = int(self.hour_combo.currentText())
        minute = int(self.minute_combo.currentText())
        if self.pm_button.isChecked() and hour != 12:
            hour += 12
        elif self.am_button.isChecked() and hour == 12:
            hour = 0
        return QTime(hour, minute)