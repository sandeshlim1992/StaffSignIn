import sys
import os
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Slot, QVariantAnimation, QEvent, QSize, Signal
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel, QListWidget, QListWidgetItem,
    QStackedWidget, QStatusBar, QStyle, QMessageBox
)
from PySide6.QtGui import QIcon, QFont, QScreen, QPixmap

import constants as c
from dashboard import DashboardPage
from members_page import MembersPage
from settings import SettingsPage
from system_tray import SystemTrayIcon
from config_manager import load_title, load_admin_mode, load_nav_slider_enabled, load_logo_path
from system_toast import SystemToast


class DatabaseSetup:
    def setup_database(self):
        print("Mock database complete.")


database_setup = DatabaseSetup()


class NavigationDrawer(QFrame):
    logout_requested = Signal()

    def __init__(self, parent=None, full_width=250, compact_width=60):
        super().__init__(parent)
        self._hover_enabled = True
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.WIN_COLOR_WIDGET_BG_ALT};
            }}
        """)

        self.full_width = full_width
        self.compact_width = compact_width
        self._is_open = False
        self.setMouseTracking(True)

        self.drawer_layout = QVBoxLayout(self)
        self.drawer_layout.setContentsMargins(5, 5, 5, 10)
        self.drawer_layout.setSpacing(8)

        # --- Logo and Title Handling ---
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drawer_layout.addWidget(self.logo_label, 0, Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(load_title())
        font = QFont(c.WIN_FONT_FAMILY, c.WIN_FONT_SIZE_TITLE, QFont.Bold)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"color: {c.WIN_COLOR_TEXT_PRIMARY};")
        self.drawer_layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignCenter)

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
                background-color: #E6F0F8; /* A very light blue for hover */
                color: {c.WIN_COLOR_TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: #DDEBF8; /* A slightly darker light blue for selected background */
                color: {c.WIN_COLOR_TEXT_PRIMARY}; /* Change text color to primary text for better contrast on light blue */
                border-left: 3px solid {c.WIN_COLOR_ACCENT_PRIMARY};
                padding-left: 5px;
            }}
            /* Add a specific style for selected item text when hovered if needed */
            QListWidget::item:selected:hover {{
                background-color: #CDE3F4; /* Even lighter blue when selected AND hovered */
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

        self.logout_button = QPushButton("Logout")
        self.logout_button.setIcon(QIcon("icons/logout_icon.svg"))
        self.logout_button.setIconSize(self.nav_list.iconSize())
        self.logout_button.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 8px;
                color: {c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
                background-color: #FD5E53;
                border-radius: {c.WIN_BORDER_RADIUS};
                border: none;
                text-align: left;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #E04B40;
            }}
        """)
        self.logout_button.clicked.connect(self.logout_requested.emit)
        self.drawer_layout.addWidget(self.logout_button)

        self.setFixedWidth(self.compact_width)
        self._set_item_texts_visibility(False)

        self.width_anim = QVariantAnimation(self)
        self.width_anim.setEasingCurve(QEasingCurve.Type.InOutCubic) # Corrected line
        self.width_anim.setDuration(250)
        self.width_anim.valueChanged.connect(self._set_animated_width)
        self.width_anim.finished.connect(self._animation_finished)

    @Slot(str)
    def set_logo(self, path):
        """Sets the logo in the navigation drawer."""
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            logo_size = int(self.full_width * 0.5)
            self.logo_label.setFixedSize(logo_size, logo_size)
            self.logo_label.setPixmap(pixmap.scaled(
                logo_size, logo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            self.logo_label.clear()
            self.logo_label.setFixedSize(0, 0)

        self._set_item_texts_visibility(self._is_open)

    def set_hover_enabled(self, enabled):
        self._hover_enabled = enabled

    def enterEvent(self, event: QEvent):
        if self._hover_enabled:
            if not self._is_open: self.open_drawer()
        event.accept()

    def leaveEvent(self, event: QEvent):
        if self._hover_enabled:
            if not self._is_open: self.close_drawer()
        event.accept()

    def open_drawer(self, force_open=False):
        if self.width_anim.state() == QVariantAnimation.State.Running or (self._is_open and not force_open): return
        self._is_open = True
        self._set_item_texts_visibility(True)
        self.width_anim.setStartValue(self.width())
        self.width_anim.setEndValue(self.full_width)
        self.width_anim.start()

    def close_drawer(self):
        if self.width_anim.state() == QVariantAnimation.State.Running or not self._is_open: return
        self._is_open = False
        self.width_anim.setStartValue(self.width())
        self.width_anim.setEndValue(self.compact_width)
        self.width_anim.start()

    def _set_item_texts_visibility(self, show_text):
        pixmap = self.logo_label.pixmap()
        has_logo = pixmap is not None and not pixmap.isNull()
        self.logo_label.setVisible(has_logo and show_text)
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
        if not self._is_open:
            self._set_item_texts_visibility(False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.active_toasts = []
        self.setWindowTitle("Staff Entry/Exit Log")
        self.resize(1000, 700)
        center_point = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
        self.setStatusBar(QStatusBar())
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.nav_drawer = NavigationDrawer(self.central_widget, full_width=250, compact_width=60)
        self.main_layout.addWidget(self.nav_drawer)
        self.content_pane = QWidget()
        self.content_pane_layout = QVBoxLayout(self.content_pane)
        self.content_pane_layout.setContentsMargins(0, 0, 0, 0)
        self.content_pane_layout.setSpacing(0)
        self.stacked_content_area = QStackedWidget(self.content_pane)

        self.dashboard_page = DashboardPage(self)
        self.members_page = MembersPage(self)
        self.settings_page = SettingsPage(self)
        self.settings_page.admin_mode_changed.connect(self._set_admin_mode)

        self.settings_page.nav_slider_changed.connect(self.nav_drawer.set_hover_enabled)
        self.settings_page.nav_slider_changed.connect(self.on_drawer_toggled)

        self.settings_page.logo_changed.connect(self.nav_drawer.set_logo)

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

        self._set_admin_mode(load_admin_mode())
        self.nav_drawer.set_hover_enabled(load_nav_slider_enabled())
        self.nav_drawer.set_logo(load_logo_path())
        self.tray_icon.show_notification("Application Started", "The sign-in system is now running.")

    def setup_tray_icon(self):
        icon_path = "icons/app_icon.ico"
        self.tray_icon = SystemTrayIcon(icon_path, self)
        self.tray_icon.show_action.triggered.connect(self.restore_window)
        self.tray_icon.quit_action.triggered.connect(self.close)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.notification_requested.connect(self.show_system_toast)

    def on_tray_icon_activated(self, reason):
        if reason == QApplication.DoubleClick:
            self.restore_window()

    def restore_window(self):
        self.showNormal()
        self.activateWindow()

    @Slot(QListWidgetItem)
    def display_page(self, item: QListWidgetItem):
        row = self.nav_drawer.nav_list.row(item)
        page_name = self.nav_drawer.original_item_texts[row]
        if page_name in self.pages:
            self.stacked_content_area.setCurrentWidget(self.pages[page_name])

    @Slot(bool)
    def on_drawer_toggled(self, is_on):
        """Opens or closes the navigation drawer."""
        if is_on:
            self.nav_drawer.open_drawer(force_open=True)
        else:
            self.nav_drawer.close_drawer()

    def confirm_logout(self):
        self.close()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Confirm Exit",
                                     "Are you sure you want to exit the application?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def _set_admin_mode(self, is_unlocked):
        self.settings_page.update_admin_mode_ui(is_unlocked)
        self.members_page.update_admin_mode_ui(is_unlocked)

    @Slot(str, str)
    def show_system_toast(self, title, message):
        """Creates and shows a system toast notification."""
        toast = SystemToast(title, message)
        self.active_toasts.append(toast)
        toast.finished.connect(lambda: self.active_toasts.remove(toast))
        toast.show_toast()

    def show_status_message(self, message, timeout=3000):
        self.statusBar().showMessage(message, timeout)


if __name__ == "__main__":
    if sys.platform == 'win32':
        import ctypes

        myappid = 'mycompany.signinapp.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    database_setup.setup_database()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Set the application icon for the title bar
    app.setWindowIcon(QIcon("icons/app_icon.png"))

    app.setStyleSheet(c.APP_STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())