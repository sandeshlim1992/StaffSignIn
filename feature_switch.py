from PySide6.QtCore import Qt, QSize, QRect, QPropertyAnimation, QEasingCurve, Signal, Property
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget


class FeatureSwitch(QWidget):  # Renamed from ThemeSwitch
    """A custom animated toggle switch for On/Off states."""
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 32)
        self.setCursor(Qt.PointingHandCursor)

        self._is_on = False
        self._circle_position_x = 16

        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(300)

    def is_on(self):
        return self._is_on

    def set_on(self, is_on):
        self._is_on = is_on
        self.animation.setStartValue(self.circle_position_x())
        self.animation.setEndValue(84 if is_on else 16)
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

        bg_color = QColor("#21BF73") if self._is_on else QColor("#FD5E53")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(self.rect(), 16, 16)

        font = QFont("Segoe UI Variable", 8, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))

        if self._is_on:
            text_rect = QRect(0, 0, 70, 32)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "On")
        else:
            text_rect = QRect(30, 0, 70, 32)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Off")

        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(self._circle_position_x - 13, 3, 26, 26)

    def mousePressEvent(self, event):
        self.set_on(not self._is_on)
        self.toggled.emit(self._is_on)
        super().mousePressEvent(event)