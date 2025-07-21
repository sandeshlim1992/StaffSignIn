import sys
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Slot, QVariantAnimation, QEvent, QSize, Signal
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel, QListWidget, QListWidgetItem,
    QStackedWidget, QStatusBar, QStyle, QMessageBox
)
from PySide6.QtGui import QIcon, QFont

import constants as c
from dashboard import DashboardPage
from members_page import MembersPage
from settings import SettingsPage
from system_tray import SystemTrayIcon
from config_manager import load_title


class DatabaseSetup:
    def setup_database(self):
        print("Mock database setup complete.")


database_setup = DatabaseSetup()


class NavigationDrawer(QFrame):
    logout_requested = Signal()

    def __init__(self, parent=None, full_width=250, compact_width=60):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG_ALT};
                border-right: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
            }}
        """)

        self.full_width = full_width
        self.compact_width = compact_width
        self._is_open = False
        self._is_pinned = False
        self.setMouseTracking(True)

        self.drawer_layout = QVBoxLayout(self)
        self.drawer_layout.setContentsMargins(5, 5, 5, 10)
        self.drawer_layout.setSpacing(8)

        self.pin_button = QPushButton(c.ICON_MENU_NORMAL)
        self.pin_button.setFixedSize(40, 40)
        self.pin_button.setToolTip("Pin navigation open / Enable hover")
        self.pin_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {c.WIN_COLOR_TEXT_PRIMARY};
                border: none; padding: 0px; font-size: 20px;
                border-radius: {c.WIN_BORDER_RADIUS};
            }}
            QPushButton:hover {{ background-color: {c.WIN_COLOR_CONTROL_BG_HOVER}; }}
        """)
        self.pin_button.clicked.connect(self.toggle_pin)
        self.drawer_layout.addWidget(self.pin_button,
                                     alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.title_label = QLabel(load_title())
        font = QFont(c.WIN_FONT_FAMILY, c.WIN_FONT_SIZE_TITLE, QFont.Bold)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"color: {c.WIN_COLOR_TEXT_PRIMARY};")
        self.drawer_layout.addWidget(self.title_label)

        self.nav_list = QListWidget()
        self.nav_list.setIconSize(QSize(28, 28))
        self.nav_list.setStyleSheet(f"""
            QListWidget {{ 
                border: none; 
                background-color: transparent; 
            }}
            QListWidget::item {{
                padding: 10px 8px; 
                color: {c.WIN_COLOR_TEXT_SECONDARY};
                border-radius: {c.WIN_BORDER_RADIUS};
                outline: none; /* Removes the focus border */
            }}
            QListWidget::item:hover {{
                background-color: {c.WIN_COLOR_CONTROL_BG_HOVER};
                color: {c.WIN_COLOR_TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {c.WIN_COLOR_ACCENT_PRIMARY_HOVER};
                color: {c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
                border-left: 3px solid {c.WIN_COLOR_ACCENT_PRIMARY};
                padding-left: 5px;
            }}
        """)
        self.nav_list.setMouseTracking(True)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.menu_definitions = [
            ("Dashboard", "icons/dashboard_icon.svg"),
            ("Members", "icons/member_icon.svg"),
            ("Settings", "icons/settings_icon.svg")
        ]
        self.original_item_texts = [text for text, icon_path in self.menu_definitions]

        for text, icon_path in self.menu_definitions:
            item_icon = QIcon(icon_path)
            if item_icon.isNull():
                print(f"Warning: Could not load icon for '{text}' from path: {icon_path}")

            list_item = QListWidgetItem(item_icon, text)
            self.nav_list.addItem(list_item)

        self.drawer_layout.addWidget(self.nav_list)
        self.drawer_layout.addStretch()

        # Create and add the separate logout button
        self.logout_button = QPushButton("Logout")
        self.logout_button.setIcon(QIcon("icons/logout_icon.svg"))
        self.logout_button.setIconSize(self.nav_list.iconSize())
        self.logout_button.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 8px; 
                color: {c.WIN_COLOR_TEXT_SECONDARY};
                border-radius: {c.WIN_BORDER_RADIUS};
                border: none;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {c.WIN_COLOR_CONTROL_BG_HOVER};
                color: {c.WIN_COLOR_TEXT_PRIMARY};
            }}
        """)
        self.logout_button.clicked.connect(self.logout_requested.emit)
        self.drawer_layout.addWidget(self.logout_button)

        self.setFixedWidth(self.compact_width)
        self._set_item_texts_visibility(False)

        self.width_anim = QVariantAnimation(self)
        self.width_anim.setDuration(250)
        self.width_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.width_anim.valueChanged.connect(self._set_animated_width)
        self.width_anim.finished.connect(self._animation_finished)

    def toggle_pin(self):
        self._is_pinned = not self._is_pinned
        self.pin_button.setText(c.ICON_MENU_PINNED if self._is_pinned else c.ICON_MENU_NORMAL)
        if self._is_pinned and not self._is_open:
            self.open_drawer(force_open=True)
        elif not self._is_pinned and not self.underMouse():
            self.close_drawer()

    def enterEvent(self, event: QEvent):
        if not self._is_pinned and not self._is_open: self.open_drawer()
        event.accept()

    def leaveEvent(self, event: QEvent):
        if not self._is_pinned and self._is_open: self.close_drawer()
        event.accept()

    def open_drawer(self, force_open=False):
        if self.width_anim.state() == QVariantAnimation.State.Running or (self._is_open and not force_open): return
        self._is_open = True
        self._set_item_texts_visibility(True)
        self.width_anim.setStartValue(self.width())
        self.width_anim.setEndValue(self.full_width)
        self.width_anim.start()

    def close_drawer(self):
        if self.width_anim.state() == QVariantAnimation.State.Running or not self._is_open or self._is_pinned: return
        self._is_open = False
        self.width_anim.setStartValue(self.width())
        self.width_anim.setEndValue(self.compact_width)
        self.width_anim.start()

    def _set_item_texts_visibility(self, show_text):
        self.title_label.setVisible(show_text)
        self.logout_button.setText("Logout" if show_text else "")
        for i in range(self.nav_list.count()):
            item = self.nav_list.item(i)
            if item:
                item.setText(self.original_item_texts[i] if show_text else "")
                align = Qt.AlignmentFlag.AlignLeft if show_text else Qt.AlignmentFlag.AlignCenter
                item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)

    @Slot(object)
    def _set_animated_width(self, width_value):
        self.setFixedWidth(int(width_value))

    @Slot()
    def _animation_finished(self):
        if not self._is_open: self._set_item_texts_visibility(False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign In")
        self.setGeometry(100, 100, 1280, 800)
        self.setStatusBar(QStatusBar())
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.nav_drawer = NavigationDrawer(self.central_widget)
        self.main_layout.addWidget(self.nav_drawer)
        self.content_pane = QWidget()
        self.content_pane_layout = QVBoxLayout(self.content_pane)
        self.content_pane_layout.setContentsMargins(0, 0, 0, 0)
        self.content_pane_layout.setSpacing(0)
        self.stacked_content_area = QStackedWidget(self.content_pane)

        self.dashboard_page = DashboardPage(self)
        self.members_page = MembersPage(self)
        self.settings_page = SettingsPage(self)

        self.pages = {
            "Dashboard": self.dashboard_page,
            "Members": self.members_page,
            "Settings": self.settings_page
        }
        for page_widget in self.pages.values():
            if self.stacked_content_area.indexOf(page_widget) == -1:
                self.stacked_content_area.addWidget(page_widget)

        self.members_page.staff_data_changed.connect(self.dashboard_page.load_staff_data)
        self.nav_drawer.logout_requested.connect(self.confirm_logout)

        self.content_pane_layout.addWidget(self.stacked_content_area, 1)
        self.main_layout.addWidget(self.content_pane, 1)
        self.nav_drawer.nav_list.itemClicked.connect(self.display_page)
        self.display_page(self.nav_drawer.nav_list.item(0))
        self.nav_drawer.nav_list.setCurrentRow(0)

        self.setup_tray_icon()

    def setup_tray_icon(self):
        """Creates the system tray icon and connects its signals."""
        icon_path = "icons/app_icon.ico"
        self.tray_icon = SystemTrayIcon(icon_path, self)
        self.tray_icon.show_action.triggered.connect(self.restore_window)
        self.tray_icon.quit_action.triggered.connect(QApplication.instance().quit)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        """Handles clicks on the tray icon."""
        if reason == SystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_window()

    def restore_window(self):
        """Shows and activates the main window."""
        self.showNormal()
        self.activateWindow()

    @Slot(QListWidgetItem)
    def display_page(self, item: QListWidgetItem):
        row = self.nav_drawer.nav_list.row(item)
        page_name = self.nav_drawer.original_item_texts[row]
        if page_name in self.pages:
            self.stacked_content_area.setCurrentWidget(self.pages[page_name])

    def confirm_logout(self):
        """Shows a confirmation dialog before closing the application."""
        reply = QMessageBox.question(self, "Confirm Logout",
                                     "Are you sure you want to log out and exit?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            QApplication.instance().quit()

    def show_status_message(self, message, timeout=3000):
        self.statusBar().showMessage(message, timeout)


if __name__ == "__main__":
    database_setup.setup_database()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    app.setStyleSheet(c.APP_STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())