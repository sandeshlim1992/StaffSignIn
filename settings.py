import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont

import constants as c
from config_manager import (
    load_path, save_setting, load_password, PASSWORD_KEY, PATH_KEY,
    load_title, TITLE_KEY, load_admin_mode, ADMIN_MODE_KEY,
    load_nav_slider_enabled, NAV_SLIDER_KEY
)
from admin_switch import AdminSwitch
from feature_switch import FeatureSwitch


class SettingsPage(QWidget):
    """
    A page for application settings, including a customizable save location and Excel password.
    """
    admin_mode_changed = Signal(bool)
    nav_slider_changed = Signal(bool)

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
        general_layout.setContentsMargins(20, 20, 20, 20)
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

        self.save_title_button = QPushButton("Save Title")
        self.save_title_button.clicked.connect(self.save_app_title)

        title_layout.addWidget(title_field_label)
        title_layout.addWidget(self.title_input, 1)
        title_layout.addWidget(self.save_title_button)
        general_layout.addLayout(title_layout)
        main_layout.addWidget(general_frame)

        # --- Interface Section ---
        interface_frame = QFrame()
        interface_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG};
                border-radius: 8px;
                border: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
            }}
        """)
        interface_layout = QVBoxLayout(interface_frame)
        interface_layout.setContentsMargins(20, 20, 20, 20)
        interface_layout.setSpacing(15)

        interface_section_label = QLabel("Interface")
        interface_section_label.setFont(QFont(c.WIN_FONT_FAMILY, 12, QFont.Bold))
        interface_section_label.setStyleSheet("border: none;")
        interface_layout.addWidget(interface_section_label)

        slider_layout = QHBoxLayout()
        slider_label = QLabel("Navigation drawer Slider:")
        slider_label.setStyleSheet("border: none;")

        self.slider_switch = FeatureSwitch()
        self.slider_switch.set_on(load_nav_slider_enabled())
        self.slider_switch.toggled.connect(self._on_nav_slider_toggled)

        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.slider_switch)
        slider_layout.addStretch()
        interface_layout.addLayout(slider_layout)

        main_layout.addWidget(interface_frame)

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
        frame_layout.setContentsMargins(20, 20, 20, 20)
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

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.select_directory)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_display, 1)
        path_layout.addWidget(self.browse_button)

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

        self.save_password_button = QPushButton("Save Password")
        self.save_password_button.clicked.connect(self.save_excel_password)

        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input, 1)
        password_layout.addWidget(self.save_password_button)

        frame_layout.addLayout(password_layout)
        main_layout.addWidget(settings_frame)

        # --- Security Section ---
        security_frame = QFrame()
        security_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG};
                border-radius: 8px;
                border: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
            }}
        """)
        security_layout = QVBoxLayout(security_frame)
        security_layout.setContentsMargins(20, 20, 20, 20)
        security_layout.setSpacing(15)

        security_section_label = QLabel("Security")
        security_section_label.setFont(QFont(c.WIN_FONT_FAMILY, 12, QFont.Bold))
        security_section_label.setStyleSheet("border: none;")
        security_layout.addWidget(security_section_label)

        admin_mode_layout = QHBoxLayout()
        admin_mode_label = QLabel("Admin Mode:")
        admin_mode_label.setStyleSheet("border: none;")

        self.admin_switch = AdminSwitch()
        self.admin_switch.set_unlocked(load_admin_mode())
        self.admin_switch.toggled.connect(self._on_admin_mode_changed)

        admin_mode_layout.addWidget(admin_mode_label)
        admin_mode_layout.addWidget(self.admin_switch)
        admin_mode_layout.addStretch()
        security_layout.addLayout(admin_mode_layout)
        main_layout.addWidget(security_frame)

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

    def _on_nav_slider_toggled(self, is_on):
        """Saves and emits the nav slider state."""
        save_setting(NAV_SLIDER_KEY, str(is_on))
        self.nav_slider_changed.emit(is_on)

    def _on_admin_mode_changed(self, is_unlocked):
        """Saves and emits the admin mode state when the switch is toggled."""
        save_setting(ADMIN_MODE_KEY, str(is_unlocked))
        self.admin_mode_changed.emit(is_unlocked)

    def update_admin_mode_ui(self, is_unlocked):
        """Enables or disables settings controls based on admin mode."""
        self.save_title_button.setEnabled(is_unlocked)
        self.browse_button.setEnabled(is_unlocked)
        self.save_password_button.setEnabled(is_unlocked)