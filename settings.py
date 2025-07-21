import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont

import constants as c
from config_manager import (
    load_path, save_setting, load_password, PASSWORD_KEY, PATH_KEY,
    load_title, TITLE_KEY
)


class SettingsPage(QWidget):
    """
    A page for application settings, including a customizable save location and Excel password.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Title ---
        title_label = QLabel("Settings")
        title_label.setFont(QFont(c.WIN_FONT_FAMILY, 18, QFont.Bold))
        main_layout.addWidget(title_label)

        # --- General Settings Section ---
        general_frame = QFrame()
        general_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG};
                border-radius: 8px;
                border: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
            }}
        """)
        general_layout = QVBoxLayout(general_frame)
        general_layout.setSpacing(15)

        general_section_label = QLabel("General")
        general_section_label.setFont(QFont(c.WIN_FONT_FAMILY, 12, QFont.Bold))
        general_section_label.setStyleSheet("border: none;")
        general_layout.addWidget(general_section_label)

        title_layout = QHBoxLayout()
        title_field_label = QLabel("Application Title:")
        title_field_label.setStyleSheet("border: none;")
        self.title_input = QLineEdit()
        self.title_input.setText(load_title())
        self.title_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
                padding: 5px;
                border-radius: {c.WIN_BORDER_RADIUS};
            }}
            QLineEdit:focus {{
                border: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
            }}
        """)

        save_title_button = QPushButton("Save Title")
        save_title_button.clicked.connect(self.save_app_title)

        title_layout.addWidget(title_field_label)
        title_layout.addWidget(self.title_input, 1)
        title_layout.addWidget(save_title_button)
        general_layout.addLayout(title_layout)
        main_layout.addWidget(general_frame)

        # --- File Settings Section ---
        settings_frame = QFrame()
        settings_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG};
                border-radius: 8px;
                border: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
            }}
        """)
        frame_layout = QVBoxLayout(settings_frame)
        frame_layout.setSpacing(15)

        section_label = QLabel("File Management")
        section_label.setFont(QFont(c.WIN_FONT_FAMILY, 12, QFont.Bold))
        section_label.setStyleSheet("border: none;")
        frame_layout.addWidget(section_label)

        # --- Directory Path Display and Selection ---
        path_layout = QHBoxLayout()
        path_label = QLabel("Save Directory:")
        path_label.setStyleSheet("border: none;")

        self.path_display = QLineEdit()
        self.path_display.setText(load_path())
        self.path_display.setReadOnly(True)
        self.path_display.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
                background-color: #f8f8f8;
                padding: 5px;
                border-radius: {c.WIN_BORDER_RADIUS};
            }}
            QLineEdit:focus {{
                border: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
            }}
        """)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.select_directory)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_display, 1)
        path_layout.addWidget(browse_button)

        frame_layout.addLayout(path_layout)

        # --- Excel Password Section ---
        password_layout = QHBoxLayout()
        password_label = QLabel("Excel Password:")
        password_label.setStyleSheet("border: none;")

        self.password_input = QLineEdit()
        self.password_input.setText(load_password())
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
                padding: 5px;
                border-radius: {c.WIN_BORDER_RADIUS};
            }}
            QLineEdit:focus {{
                border: 1px solid {c.WIN_COLOR_BORDER_MEDIUM};
            }}
        """)

        save_password_button = QPushButton("Save Password")
        save_password_button.clicked.connect(self.save_excel_password)

        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input, 1)
        password_layout.addWidget(save_password_button)

        frame_layout.addLayout(password_layout)
        main_layout.addWidget(settings_frame)

    def select_directory(self):
        """Opens a dialog to select a new save directory."""
        current_path = self.path_display.text()
        new_dir = QFileDialog.getExistingDirectory(self, "Select Save Directory", current_path)

        if new_dir and new_dir != current_path:
            save_setting(PATH_KEY, new_dir)
            self.path_display.setText(new_dir)
            QMessageBox.information(self, "Path Saved", f"New save directory has been set to:\n{new_dir}")

    def save_excel_password(self):
        """Saves the new Excel password to the config file."""
        new_password = self.password_input.text()
        if not new_password:
            QMessageBox.warning(self, "Input Error", "Password cannot be empty.")
            return

        save_setting(PASSWORD_KEY, new_password)
        QMessageBox.information(self, "Password Saved", "The Excel password has been updated.")

    def save_app_title(self):
        """Saves the new application title to the config file."""
        new_title = self.title_input.text().strip()
        if not new_title:
            QMessageBox.warning(self, "Input Error", "Title cannot be empty.")
            return

        save_setting(TITLE_KEY, new_title)
        QMessageBox.information(self, "Title Saved",
                                "The new application title has been saved.\nPlease restart the application for the change to take effect.")