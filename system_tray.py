from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction


class SystemTrayIcon(QSystemTrayIcon):
    """
    A class for managing the application's system tray icon and notifications.
    """

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

    def show_notification(self, title, message, icon=QSystemTrayIcon.MessageIcon.Information):
        """
        Displays a native system tray balloon message.

        Args:
            title (str): The title of the notification.
            message (str): The main body of the notification.
            icon (QSystemTrayIcon.MessageIcon): The icon to display (Information, Warning, Critical).
        """
        self.showMessage(title, message, icon, 3000)  # Show for 3 seconds
