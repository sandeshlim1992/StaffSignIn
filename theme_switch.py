from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, Signal, Property
from PySide6.QtGui import QPainter, QColor, QFont, QIcon
from PySide6.QtWidgets import QWidget


class ThemeSwitch(QWidget):
    """A custom animated toggle switch for light/dark mode."""
    toggled = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 40)
        self.setCursor(Qt.PointingHandCursor)

        self._is_dark_mode = False
        self._circle_position_x = 20

        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(300)

        self.sun_icon = QIcon("icons/sun.svg")
        self.moon_icon = QIcon("icons/moon.svg")

    def is_dark_mode(self):
        return self._is_dark_mode

    def set_dark_mode(self, is_dark, animate=False):
        self._is_dark_mode = is_dark

        if animate:
            self.animation.setStartValue(self.circle_position_x())
            self.animation.setEndValue(140 if is_dark else 20)
            self.animation.start()
        else:
            self.set_circle_position_x(140 if is_dark else 20)

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

        bg_color = QColor("#343A40") if self._is_dark_mode else QColor("#E9ECEF")
        circle_color = QColor("#FFFFFF")
        text_color = QColor("#FFFFFF") if self._is_dark_mode else QColor("#495057")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(self.rect(), 20, 20)

        painter.setPen(text_color)
        font = QFont("Segoe UI Variable", 10, QFont.Bold)
        painter.setFont(font)

        if self._is_dark_mode:
            painter.drawText(QRect(40, 0, 80, 40), Qt.AlignmentFlag.AlignCenter, "DARK")
            self.moon_icon.paint(painter, QRect(15, 10, 20, 20))
        else:
            painter.drawText(QRect(0, 0, 120, 40), Qt.AlignmentFlag.AlignCenter, "LIGHT")
            self.sun_icon.paint(painter, QRect(125, 10, 20, 20))

        painter.setBrush(circle_color)
        painter.drawEllipse(self._circle_position_x - 16, 4, 32, 32)

    def mousePressEvent(self, event):
        self.set_dark_mode(not self._is_dark_mode, animate=True)
        self.toggled.emit("dark" if self._is_dark_mode else "light")
        super().mousePressEvent(event)