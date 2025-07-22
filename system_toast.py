from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect, QApplication
from PySide6.QtGui import QFont, QColor
import constants as c

class SystemToast(QDialog):
    """
    A custom, self-closing dialog that mimics the appearance of the in-app toast notifications.
    """
    def __init__(self, title, message, status='info', parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Main Background and Layout
        self.background = QFrame()
        self.background.setStyleSheet(f"""
            QFrame {{
                background-color: {c.TOAST_BG};
                border: 1px solid {c.TOAST_BORDER};
                border-radius: 6px;
            }}
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.addWidget(self.background)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.background.setGraphicsEffect(shadow)

        # Content Layout
        content_layout = QVBoxLayout(self.background)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("border: none;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # --- MODIFICATION: Set icon color based on status ---
        if status == 'success':
            icon_color = "#21BF73"  # Green
        elif status == 'error':
            icon_color = "#FD5E53"  # Red
        else:
            icon_color = c.WIN_COLOR_ACCENT_PRIMARY # Blue

        icon_label = QLabel()
        icon_label.setFixedSize(QSize(20, 20))
        icon_label.setStyleSheet(f"background-color: {icon_color}; border-radius: 4px;")

        title_label = QLabel(title)
        title_label.setFont(QFont(c.WIN_FONT_FAMILY, 10, QFont.Bold))

        close_button = QPushButton("✕")
        close_button.setFixedSize(QSize(24, 24))
        close_button.setStyleSheet(f"""
            QPushButton {{ font-size: 14pt; color: {c.TOAST_HEADER_FG}; border: none; background-color: transparent; }}
            QPushButton:hover {{ color: {c.WIN_COLOR_TEXT_PRIMARY}; }}
        """)
        close_button.clicked.connect(self.close)

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_button)

        # Body
        body_label = QLabel(message)
        body_label.setFont(QFont(c.WIN_FONT_FAMILY, 10))
        body_label.setWordWrap(True)
        body_label.setStyleSheet(f"color: {c.WIN_COLOR_TEXT_SECONDARY}; padding-top: 5px; border-top: 1px solid {c.WIN_COLOR_BORDER_LIGHT};")

        content_layout.addWidget(header_frame)
        content_layout.addWidget(body_label)

        # Animation
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Timer to self-close
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._fade_out)

    def show_toast(self):
        self.setWindowOpacity(0.0)
        self.show()

        QTimer.singleShot(0, self._position_toast)

        self.animation.setDirection(QPropertyAnimation.Forward)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        self.timer.start(4000)

    def _position_toast(self):
        """Calculates and sets the toast's position in the bottom-right corner."""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen_geometry.right() - self.width() - 20,
            screen_geometry.bottom() - self.height() - 40
        )

    def _fade_out(self):
        self.animation.setDirection(QPropertyAnimation.Backward)
        self.animation.finished.connect(self.close)
        self.animation.start()