import sys
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Slot, QVariantAnimation, QStringListModel, QEvent, QSize
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel, QListWidget, QListWidgetItem,
    QStackedWidget, QStatusBar, QLineEdit, QCompleter, QMessageBox
)
from PySide6.QtGui import QIcon, QFont


# --- Placeholder for custom pages and database setup ---
# In a real application, these would be in separate files.
class DashboardPage(QWidget):
    def __init__(self, parent_main_window=None):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Dashboard Page"), alignment=Qt.AlignCenter)


class DatabaseSetup:
    def setup_database(self):
        print("Mock database setup complete.")

    def get_search_suggestions(self, text):
        return [f"Suggestion for {text} 1", f"Suggestion for {text} 2"]

    def get_book_details_for_dashboard(self, identifier):
        print(f"Searching for book with identifier: {identifier}")
        return None


db_operations = DatabaseSetup()
database_setup = db_operations
# --- End of Placeholders ---


# --- Theme Constants (Windows 11 Light Theme Inspired) ---
WIN_COLOR_WINDOW_BG = "#F9F9F9"
WIN_COLOR_WIDGET_BG = "#FFFFFF"
WIN_COLOR_WIDGET_BG_ALT = "#F0F0F0"
WIN_COLOR_BORDER_LIGHT = "#EAEAEA"
WIN_COLOR_BORDER_MEDIUM = "#D8D8D8"
WIN_COLOR_BORDER_INPUT_HOVER = "#B0B0B0"
WIN_COLOR_BORDER_FOCUSED = "#0078D4"

WIN_COLOR_TEXT_PRIMARY = "#000000"
WIN_COLOR_TEXT_SECONDARY = "#4A4A4A"
WIN_COLOR_TEXT_PLACEHOLDER = "#7A7A7A"
WIN_COLOR_TEXT_DISABLED = "#A0A0A0"
WIN_COLOR_TEXT_ICON_NORMAL = "#707070"

WIN_COLOR_ACCENT_PRIMARY = "#0078D4"
WIN_COLOR_ACCENT_PRIMARY_HOVER = "#005A9E"
WIN_COLOR_ACCENT_PRIMARY_PRESSED = "#004578"
WIN_COLOR_ACCENT_TEXT_ON_PRIMARY = "#FFFFFF"

WIN_COLOR_CONTROL_BG = "#F0F0F0"
WIN_COLOR_CONTROL_BG_HOVER = "#E0E0E0"
WIN_COLOR_CONTROL_BG_PRESSED = "#C8C8C8"
WIN_COLOR_CONTROL_BORDER = "#D8D8D8"
WIN_COLOR_CONTROL_TEXT = "#000000"

WIN_FONT_FAMILY = "Segoe UI Variable"
WIN_FONT_FAMILY_FALLBACK = "Segoe UI"
WIN_FONT_SIZE_BODY = 9
WIN_FONT_SIZE_SUBTITLE = 11
WIN_FONT_SIZE_TITLE = 14

WIN_BORDER_RADIUS = "4px"
WIN_BORDER_RADIUS_DIALOG = "8px"

# --- Icons ---
ICON_SEARCH = "🔍"
ICON_MENU_NORMAL = "☰"
ICON_MENU_PINNED = "📌"


class NavigationDrawer(QFrame):
    def __init__(self, parent=None, full_width=250, compact_width=60):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {WIN_COLOR_WIDGET_BG_ALT};
                border-right: 1px solid {WIN_COLOR_BORDER_LIGHT};
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

        self.pin_button = QPushButton(ICON_MENU_NORMAL)
        self.pin_button.setFixedSize(40, 40)
        self.pin_button.setToolTip("Pin navigation open / Enable hover")
        self.pin_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {WIN_COLOR_CONTROL_TEXT};
                border: none;
                padding: 0px;
                font-size: 20px;
                border-radius: {WIN_BORDER_RADIUS};
            }}
            QPushButton:hover {{ background-color: {WIN_COLOR_CONTROL_BG_HOVER}; }}
            QPushButton:pressed {{ background-color: {WIN_COLOR_CONTROL_BG_PRESSED}; }}
        """)
        self.pin_button.clicked.connect(self.toggle_pin)
        self.drawer_layout.addWidget(self.pin_button,
                                     alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.title_label = QLabel("LSST")
        font = QFont(WIN_FONT_FAMILY, WIN_FONT_SIZE_TITLE)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"color: {WIN_COLOR_TEXT_PRIMARY};")
        self.drawer_layout.addWidget(self.title_label)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: transparent;
            }}
            QListWidget::item {{
                padding: 10px 8px;
                color: {WIN_COLOR_TEXT_ICON_NORMAL};
            }}
            QListWidget::item:hover {{
                background-color: {WIN_COLOR_CONTROL_BG_HOVER};
                color: {WIN_COLOR_TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {WIN_COLOR_ACCENT_PRIMARY_HOVER};
                color: {WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
                border-left: 3px solid {WIN_COLOR_ACCENT_PRIMARY};
                padding-left: 5px;
            }}
        """)
        self.nav_list.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.nav_list.setMouseTracking(True)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.menu_definitions = [
            ("Dashboard", "icons/dashboard_icon.svg"),
            ("Settings", "icons/settings_icon.svg"),
            ("Help", "icons/help_icon.svg")
        ]

        self.original_item_texts = []
        for text, icon_path in self.menu_definitions:
            # Note: Icon loading will fail unless you create an 'icons' folder
            item_icon = QIcon(icon_path)
            list_item = QListWidgetItem(text)
            if not item_icon.isNull():
                list_item.setIcon(item_icon)
            self.nav_list.addItem(list_item)
            self.original_item_texts.append(text)

        self.drawer_layout.addWidget(self.nav_list)
        self.drawer_layout.addStretch()

        self.setFixedWidth(self.compact_width)
        self._set_item_texts_visibility(False)

        self.width_anim = QVariantAnimation(self)
        self.width_anim.setDuration(250)
        self.width_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.width_anim.valueChanged.connect(self._set_animated_width)
        self.width_anim.finished.connect(self._animation_finished)

    def toggle_pin(self):
        self._is_pinned = not self._is_pinned
        if self._is_pinned:
            self.pin_button.setText(ICON_MENU_PINNED)
            if not self._is_open:
                self.open_drawer(force_open=True)
        else:
            self.pin_button.setText(ICON_MENU_NORMAL)
            if not self.underMouse():
                self.close_drawer()

    def enterEvent(self, event: QEvent):
        if not self._is_pinned:
            if not self._is_open and self.width_anim.state() != QVariantAnimation.State.Running:
                self.open_drawer()
        event.accept()

    def leaveEvent(self, event: QEvent):
        if not self._is_pinned:
            if self._is_open and self.width_anim.state() != QVariantAnimation.State.Running:
                self.close_drawer()
        event.accept()

    def open_drawer(self, force_open=False):
        if self.width_anim.state() == QVariantAnimation.State.Running: return
        if self._is_open and not force_open: return
        self._is_open = True
        self._set_item_texts_visibility(True)
        self.width_anim.setStartValue(self.width())
        self.width_anim.setEndValue(self.full_width)
        self.width_anim.start()

    def close_drawer(self):
        if self.width_anim.state() == QVariantAnimation.State.Running or not self._is_open: return
        if self._is_pinned: return
        self._is_open = False
        self.width_anim.setStartValue(self.width())
        self.width_anim.setEndValue(self.compact_width)
        self.width_anim.start()

    def _set_item_texts_visibility(self, show_text):
        self.title_label.setVisible(show_text)
        for i in range(self.nav_list.count()):
            item = self.nav_list.item(i)
            if item:
                if show_text:
                    if i < len(self.original_item_texts):
                        item.setText(self.original_item_texts[i])
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setText("")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

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
        self.setWindowTitle("Sign In")
        self.setGeometry(100, 100, 1280, 800)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

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

        # The top bar is no longer needed as the search bar is removed.
        # You can add a simple header here if you wish.
        # For now, we connect the content area directly.

        self.stacked_content_area = QStackedWidget(self.content_pane)
        self.stacked_content_area.setStyleSheet(f"background-color: {WIN_COLOR_WINDOW_BG}; padding: 10px;")

        self.pages = {
            "Dashboard": DashboardPage(self),
            "Settings": QLabel("Settings Page", alignment=Qt.AlignCenter),
            "Help": QLabel("Help Page", alignment=Qt.AlignCenter)
        }
        for page_widget in self.pages.values():
            self.stacked_content_area.addWidget(page_widget)

        self.content_pane_layout.addWidget(self.stacked_content_area, 1)
        self.main_layout.addWidget(self.content_pane, 1)

        self.nav_drawer.nav_list.itemClicked.connect(self.display_page)
        self.display_page(self.nav_drawer.nav_list.item(0))  # Show Dashboard on start
        self.nav_drawer.nav_list.setCurrentRow(0)

    @Slot(QListWidgetItem)
    def display_page(self, item: QListWidgetItem):
        # We need to get the text from original_item_texts because it might be hidden
        row = self.nav_drawer.nav_list.row(item)
        if row < len(self.nav_drawer.original_item_texts):
            page_name = self.nav_drawer.original_item_texts[row]
        else:
            page_name = item.text()  # Fallback

        if page_name in self.pages:
            self.stacked_content_area.setCurrentWidget(self.pages[page_name])
            self.show_status_message(f"Navigated to {page_name}.", 2000)
        else:
            self.show_status_message(f"Error: Page '{page_name}' not found.", 5000)

    def show_status_message(self, message, timeout=3000):
        self.status_bar.showMessage(message, timeout)


if __name__ == "__main__":
    database_setup.setup_database()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
