import calendar
from datetime import date

from PySide6.QtCore import Qt, QDate, Signal, QPoint, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout

import constants as c


class DateCell(QWidget):
    """A custom widget to display a single day in the calendar."""
    clicked = Signal(QDate)

    def __init__(self, dt: QDate, is_current_month=True, parent=None):
        super().__init__(parent)
        self.date = dt
        self.is_current_month = is_current_month
        self.is_today = (dt == QDate.currentDate())
        self.is_selected = False
        self.event_dots = []  # List of colors for event dots

        self.setFixedSize(40, 40)
        self.setCursor(Qt.PointingHandCursor)

    def set_selected(self, selected):
        if self.is_selected != selected:
            self.is_selected = selected
            self.update()  # Trigger a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        day_number = str(self.date.day())

        # --- Draw Selection / Today Indicator ---
        if self.is_selected:
            painter.setBrush(QColor(c.CALENDAR_SELECTION_COLOR))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect.center(), 15, 15)
        elif self.is_today:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            pen = QPen(QColor(c.CALENDAR_SELECTION_COLOR))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawEllipse(rect.center(), 15, 15)

        # --- Draw Day Number ---
        font = QFont(c.WIN_FONT_FAMILY, 10)

        if self.is_selected:
            painter.setPen(QColor(c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY))
        elif self.date > QDate.currentDate():
            painter.setPen(QColor("#cccccc"))  # Gray out all future dates
        elif not self.is_current_month:
            painter.setPen(QColor("#cccccc"))  # Ghosted days
        elif self.is_today:
            painter.setPen(QColor(c.CALENDAR_SELECTION_COLOR))
            font.setBold(True)
        elif self.date.dayOfWeek() in [6, 7]:  # Saturday or Sunday
            painter.setPen(QColor(c.WEEKEND_COLOR))
        else:
            painter.setPen(QColor(c.WIN_COLOR_TEXT_PRIMARY))

        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, day_number)

    def mousePressEvent(self, event):
        if self.is_current_month and self.date <= QDate.currentDate():
            self.clicked.emit(self.date)
        super().mousePressEvent(event)


class CustomCalendar(QWidget):
    """A completely custom calendar widget to match the new design."""
    selection_changed = Signal(QDate)
    month_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        self.selected_date = QDate.currentDate()
        self.date_cells = []

        self._init_ui()
        self._populate_calendar()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        # --- Header with Navigation ---
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(5, 0, 5, 0)

        prev_button = QPushButton("")
        prev_button.setIcon(QIcon("icons/left_arrow.svg"))
        prev_button.clicked.connect(self._previous_month)
        self.month_year_label = QLabel()
        self.month_year_label.setFont(QFont(c.WIN_FONT_FAMILY, 11, QFont.Bold))
        next_button = QPushButton("")
        next_button.setIcon(QIcon("icons/right_arrow.svg"))
        next_button.clicked.connect(self._next_month)

        for btn in [prev_button, next_button]:
            btn.setFixedSize(28, 28)
            btn.setIconSize(QSize(20, 20))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {c.WIN_COLOR_CONTROL_BG_HOVER};
                }}
            """)

        header_layout.addWidget(prev_button)
        header_layout.addStretch()
        header_layout.addWidget(self.month_year_label)
        header_layout.addStretch()
        header_layout.addWidget(next_button)

        # --- Weekday Grid ---
        self.weekday_grid = QGridLayout()
        self.weekday_grid.setSpacing(0)
        weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        for i, day in enumerate(weekdays):
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont(c.WIN_FONT_FAMILY, 8, QFont.Bold))
            label.setStyleSheet(f"color: {c.WIN_COLOR_TEXT_SECONDARY};")
            self.weekday_grid.addWidget(label, 0, i)

        # --- Calendar Grid for Dates ---
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(0)
        self.calendar_grid.setContentsMargins(0, 5, 0, 0)

        main_layout.addWidget(header)
        main_layout.addLayout(self.weekday_grid)
        main_layout.addLayout(self.calendar_grid)

    def _populate_calendar(self):
        # Clear previous cells
        for cell in self.date_cells:
            cell.deleteLater()
        self.date_cells = []

        self.month_year_label.setText(self.current_date.toString("MMMM yyyy"))

        month_cal = calendar.monthcalendar(self.current_date.year(), self.current_date.month())

        for week_num, week_data in enumerate(month_cal):
            for day_num, day_of_week in enumerate(week_data):
                if day_of_week == 0:
                    continue

                date_obj = QDate(self.current_date.year(), self.current_date.month(), day_of_week)
                cell = DateCell(date_obj, is_current_month=True)
                cell.set_selected(date_obj == self.selected_date)
                cell.clicked.connect(self._date_clicked)

                self.calendar_grid.addWidget(cell, week_num, day_num)
                self.date_cells.append(cell)

    def _date_clicked(self, q_date: QDate):
        self.selected_date = q_date

        for cell in self.date_cells:
            cell.set_selected(cell.date == self.selected_date)

        self.selection_changed.emit(self.selected_date)

    def _previous_month(self):
        self.current_date = self.current_date.addMonths(-1)
        self._populate_calendar()
        self.month_changed.emit()

    def _next_month(self):
        self.current_date = self.current_date.addMonths(1)
        self._populate_calendar()
        self.month_changed.emit()

    def set_date(self, year, month):
        self.current_date = QDate(year, month, 1)
        self._populate_calendar()

    def selectedDate(self):
        return self.selected_date