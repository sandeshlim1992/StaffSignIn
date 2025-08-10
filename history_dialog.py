# history_dialog.py
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QFrame
from PySide6.QtGui import QFont, QColor, QIcon

import constants as c

class StaffHistoryDialog(QDialog):
    def __init__(self, staff_name, tap_times, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"History for {staff_name}")
        self.setFixedSize(400, 500)
        self.setModal(True)
        self.setStyleSheet(f"background-color: {c.WIN_COLOR_WIDGET_BG}; border-radius: 8px;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel(f"Activity for {staff_name}")
        title_label.setFont(QFont(c.WIN_FONT_FAMILY, 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {c.WIN_COLOR_TEXT_PRIMARY};")
        main_layout.addWidget(title_label)

        # List of tap times
        self.history_list_widget = QListWidget()
        self.history_list_widget.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
                border-radius: {c.WIN_BORDER_RADIUS};
                background-color: {c.WIN_COLOR_WIDGET_BG_ALT};
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
            }}
            QListWidget::item:last {{
                border-bottom: none;
            }}
        """)
        self.history_list_widget.setFont(QFont(c.WIN_FONT_FAMILY, 10))

        if tap_times:
            # Sort tap times chronologically if they are strings that can be compared
            # For robustness, you might want to convert them to datetime objects for sorting
            # Example: sorted_times = sorted(tap_times, key=lambda x: datetime.strptime(x.split(' ')[0], '%I:%M:%S'))
            for time_entry in tap_times:
                list_item = QListWidgetItem(time_entry)
                self.history_list_widget.addItem(list_item)
        else:
            list_item = QListWidgetItem("No tap events recorded for this staff member today.")
            self.history_list_widget.addItem(list_item)
            list_item.setForeground(QColor(c.WIN_COLOR_TEXT_SECONDARY)) # Make it greyed out

        main_layout.addWidget(self.history_list_widget)

        # Close button
        close_button = QPushButton("Close")
        close_button.setFont(QFont(c.WIN_FONT_FAMILY, 10, QFont.Bold))
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.WIN_COLOR_SECONDARY_BUTTON_BG};
                color: {c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
                border: none;
                border-radius: {c.WIN_BORDER_RADIUS};
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {c.WIN_COLOR_SECONDARY_BUTTON_HOVER};
            }}
        """)
        close_button.clicked.connect(self.accept) # Close the dialog on click

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

    def sizeHint(self):
        return QSize(400, 500) # Ensure dialog has a consistent size hint