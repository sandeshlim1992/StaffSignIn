from PySide6.QtCore import Signal
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction


class SystemTrayIcon(QSystemTrayIcon):
    """
    A class for managing the application's system tray icon.
    It emits a signal when a notification is requested.
    """
    notification_requested = Signal(str, str) # title, message

    def __init__(self, icon_path, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(icon_path))
        self.setVisible(True)

        # Create a context menu for the tray icon
        self.menu = QMenu(parent)
        self.show_action = QAction("Show", self)
        self.quit_action = QAction("Exit", self)

        self.menu.addAction(self.show_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.setContextMenu(self.menu)

    def show_notification(self, title, message):
        """Emits a signal requesting a notification to be shown."""
        self.notification_requested.emit(title, message)