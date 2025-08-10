from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QDialogButtonBox, QComboBox
)
from PySide6.QtGui import QFont

import constants as c


class TimePickerDialog(QDialog):
    """A custom dialog for selecting a time (hour, minute, AM/PM)."""

    def __init__(self, parent=None, initial_time=None):
        super().__init__(parent)
        self.setWindowTitle("Select Time")
        self.setModal(True)
        self.setMinimumWidth(300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet(f"background-color: {c.WIN_COLOR_WIDGET_BG};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Time Selection Widgets ---
        time_layout = QHBoxLayout()

        self.hour_combo = QComboBox()
        self.hour_combo.addItems([f"{h:02d}" for h in range(1, 13)])

        self.minute_combo = QComboBox()
        self.minute_combo.addItems([f"{m:02d}" for m in range(60)])

        self.am_pm_button = QPushButton("AM")
        self.am_pm_button.setCheckable(True)
        self.am_pm_button.clicked.connect(self._toggle_am_pm)

        for combo in [self.hour_combo, self.minute_combo]:
            combo.setStyleSheet(f"""
                QComboBox {{
                    border: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
                    border-radius: {c.WIN_BORDER_RADIUS};
                    padding: 5px;
                }}
            """)

        self.am_pm_button.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
                border-radius: {c.WIN_BORDER_RADIUS};
                padding: 5px 15px;
            }}
            QPushButton:checked {{
                background-color: {c.WIN_COLOR_ACCENT_PRIMARY};
                color: {c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
                border: 1px solid {c.WIN_COLOR_ACCENT_PRIMARY_HOVER};
            }}
        """)

        time_layout.addWidget(self.hour_combo)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.minute_combo)
        time_layout.addSpacing(10)
        time_layout.addWidget(self.am_pm_button)
        time_layout.addStretch()

        main_layout.addLayout(time_layout)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Apply")
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setProperty("primary", True)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box, 0, Qt.AlignmentFlag.AlignRight)

        self._set_initial_time(initial_time)

    def _toggle_am_pm(self):
        if self.am_pm_button.isChecked():
            self.am_pm_button.setText("PM")
        else:
            self.am_pm_button.setText("AM")

    def _set_initial_time(self, time_str):
        """Sets the combo boxes to an initial time value."""
        if not time_str:
            now = QTime.currentTime()
            time_str = now.toString("hh:mm AP")

        try:
            parts = time_str.replace(":", " ").split()
            hour, minute, am_pm = int(parts[0]), int(parts[1]), parts[2]

            self.hour_combo.setCurrentText(f"{hour:02d}")
            self.minute_combo.setCurrentText(f"{minute:02d}")

            if am_pm.upper() == "PM":
                self.am_pm_button.setChecked(True)
            else:
                self.am_pm_button.setChecked(False)
            self._toggle_am_pm()  # Update text
        except (ValueError, IndexError):
            print(f"Warning: Could not parse initial time '{time_str}'")

    def get_selected_time(self):
        """Returns the selected time as a formatted string."""
        hour = self.hour_combo.currentText()
        minute = self.minute_combo.currentText()
        am_pm = self.am_pm_button.text()

        # Convert to 24-hour format for saving, then back to 12-hour for display
        h_24 = int(hour)
        if am_pm == "PM" and h_24 != 12:
            h_24 += 12
        if am_pm == "AM" and h_24 == 12:
            h_24 = 0

        time_obj = QTime(h_24, int(minute))
        return time_obj.toString("hh:mm:ss AP")


