from PySide6.QtCore import Qt, QSize, QRect, QPropertyAnimation, QEasingCurve, Signal, Property
from PySide6.QtGui import QPainter, QColor, QFont, QIcon
from PySide6.QtWidgets import QWidget
import constants as c


class AdminSwitch(QWidget):
    """A custom animated toggle switch for Admin Mode."""
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 32)
        self.setCursor(Qt.PointingHandCursor)

        self._unlocked = False
        self._circle_position_x = 16

        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(300)

    def is_unlocked(self):
        return self._unlocked

    def set_unlocked(self, is_unlocked):
        self._unlocked = is_unlocked
        self.animation.setStartValue(self.circle_position_x())
        self.animation.setEndValue(84 if is_unlocked else 16)
        self.animation.start()
        self.update()

    def circle_position_x(self):
        return self._circle_position_x

    def set_circle_position_x(self, pos):
        self._circle_position_x = pos
        self.update()

    circle_position = Property(int, circle_position_x, set_circle_position_x)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Determine background color based on state
        bg_color = QColor("#21BF73") if self._unlocked else QColor("#FD5E53")

        # Draw background pill
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(self.rect(), 16, 16)

        # Draw text on the background
        font = QFont("Segoe UI Variable", 8, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY))

        if self._unlocked:
            # Draw "Unlocked" on the left side
            text_rect = QRect(0, 0, 70, 32)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Unlocked")
        else:
            # Draw "Locked" on the right side
            text_rect = QRect(30, 0, 70, 32)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Locked")

        # Draw sliding part (circle) on top of the text
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(self._circle_position_x - 13, 3, 26, 26)

    def mousePressEvent(self, event):
        self.set_unlocked(not self._unlocked)
        self.toggled.emit(self._unlocked)
        super().mousePressEvent(event)