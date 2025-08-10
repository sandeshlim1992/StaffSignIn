import os
import csv
from functools import partial
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QToolButton,
    QFrame
)
from PySide6.QtGui import QFont, QIcon, QAction

import constants as c
from config_manager import load_admin_mode
# --- MODIFICATION: Import database functions ---
from database_manager import (
    get_all_staff, add_staff_member, update_staff_member, delete_staff_member, get_staff_by_token
)


class MemberDialog(QDialog):
    """A dialog for adding or editing a staff member."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(15, 15, 15, 15)
        self.form_layout.setSpacing(10)

        self.name_input = QLineEdit()
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Enter token number or swipe card")

        self.form_layout.addRow("Full Name:", self.name_input)
        self.form_layout.addRow("Token Number:", self.token_input)

        layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_data(self):
        name = self.name_input.text().strip()
        token_str = self.token_input.text().strip()

        if not name or not token_str:
            QMessageBox.warning(self, "Input Error", "Name and Token Number are required.")
            return None

        try:
            token = int(token_str)
            return {"name": name, "token": token}
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Token Number must be a valid number.")
            return None


class MembersPage(QWidget):
    """The main settings page, featuring the member management section."""
    staff_data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        # self.staff_file = 'staff_data.csv' # No longer needed

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Title Bar ---
        top_bar_layout = QHBoxLayout()
        page_title = QLabel("Manage Members")
        page_title.setFont(QFont(c.WIN_FONT_FAMILY, 18, QFont.Bold))

        self.add_member_button = QPushButton("")
        self.add_member_button.setIcon(QIcon("icons/user_add.svg"))
        self.add_member_button.setIconSize(QSize(50, 50))
        self.add_member_button.setFixedSize(60, 60)
        self.add_member_button.setToolTip("Add New Member")
        self.add_member_button.setCursor(Qt.PointingHandCursor)
        self.add_member_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border-radius: 30px; /* half of FixedSize */
                border: none;
            }}
            QPushButton:hover {{
                background-color: {c.WIN_COLOR_CONTROL_BG_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {c.WIN_COLOR_CONTROL_BG_PRESSED};
            }}
        """)
        self.add_member_button.clicked.connect(self.add_member)

        top_bar_layout.addWidget(page_title)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.add_member_button)
        main_layout.addLayout(top_bar_layout)

        # --- Search and Filter Bar ---
        search_frame = QFrame()
        search_frame.setFixedHeight(40)
        search_frame.setMaximumWidth(600)
        search_frame.setStyleSheet(
            f"background-color: {c.WIN_COLOR_WIDGET_BG}; border-radius: 20px; border: 1px solid {c.WIN_COLOR_BORDER_LIGHT};")

        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(5, 0, 5, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Name or Token...")
        self.search_input.setStyleSheet("border: none; background-color: transparent; padding-left: 10px;")

        search_icon_action = QAction(self.search_input)
        search_icon_action.setIcon(QIcon("icons/search_icon.svg"))
        self.search_input.addAction(search_icon_action, QLineEdit.ActionPosition.LeadingPosition)

        search_button = QPushButton("Search")
        search_button.setCursor(Qt.PointingHandCursor)
        search_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.WIN_COLOR_ACCENT_PRIMARY};
                color: {c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
                border: none;
                font-weight: bold;
                padding: 8px 18px;
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background-color: {c.WIN_COLOR_ACCENT_PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {c.WIN_COLOR_ACCENT_PRIMARY_PRESSED};
            }}
        """)
        search_button.clicked.connect(self.filter_table)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        main_layout.addWidget(search_frame)

        # --- Members Table ---
        self.members_table = QTableWidget()
        self.members_table.setColumnCount(3)
        self.members_table.setHorizontalHeaderLabels(["Staff Name", "Token", "Actions"])
        self.members_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.members_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.members_table.verticalHeader().setVisible(False)
        self.members_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.members_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.members_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.members_table.setSortingEnabled(True)

        self.members_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
                border-radius: 8px;
                gridline-color: transparent;
            }}
            QHeaderView::section {{
                background-color: {c.WIN_COLOR_WIDGET_BG_ALT};
                padding: 10px;
                border: none;
                border-bottom: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
                font-weight: bold;
                color: {c.WIN_COLOR_TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding-left: 10px;
                border-bottom: 1px solid {c.WIN_COLOR_BORDER_LIGHT};
            }}
            QTableWidget::item:selected {{
                background-color: {c.WIN_COLOR_ACCENT_PRIMARY};
                color: {c.WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
            }}
        """)

        main_layout.addWidget(self.members_table)
        self.load_members_data()

    def load_members_data(self):
        """Reads staff data from the database and populates the table."""
        is_admin_mode_unlocked = load_admin_mode()
        self.members_table.setRowCount(0)

        staff_list = get_all_staff()

        for member in staff_list:
            row = self.members_table.rowCount()
            self.members_table.insertRow(row)

            # Columns are now Name, Token
            name_item = QTableWidgetItem(member['name'])
            token_item = QTableWidgetItem(str(member['token']))

            # Store the token in the item for later retrieval
            token_item.setData(Qt.ItemDataRole.UserRole, member['token'])

            self.members_table.setItem(row, 0, name_item)
            self.members_table.setItem(row, 1, token_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            actions_layout.setSpacing(10)

            edit_button = QToolButton()
            edit_button.setIcon(QIcon("icons/edit_icon.svg"))
            edit_button.setToolTip("Edit Member")
            edit_button.setCursor(Qt.PointingHandCursor)
            edit_button.setStyleSheet("QToolButton { border: none; }")
            edit_button.clicked.connect(partial(self.edit_member, row))

            delete_button = QToolButton()
            delete_button.setIcon(QIcon("icons/close_icon.svg"))
            delete_button.setToolTip("Delete Member")
            delete_button.setCursor(Qt.PointingHandCursor)
            delete_button.setStyleSheet("QToolButton { border: none; }")
            delete_button.clicked.connect(partial(self.delete_member, row))

            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            self.members_table.setCellWidget(row, 2, actions_widget)
            actions_widget.setEnabled(is_admin_mode_unlocked)

    def filter_table(self):
        """Hides rows that don't match the search text."""
        search_text = self.search_input.text().lower()
        for row in range(self.members_table.rowCount()):
            name_item = self.members_table.item(row, 0)
            token_item = self.members_table.item(row, 1)

            is_match = (search_text in name_item.text().lower() or
                        search_text in token_item.text().lower())
            self.members_table.setRowHidden(row, not is_match)

    def add_member(self):
        """Opens a dialog to add a new member."""
        dialog = MemberDialog("Add New Member", self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                token = data["token"]
                name = data["name"]

                # Check if token already exists in the database
                if get_staff_by_token(token):
                    QMessageBox.warning(self, "Duplicate Token", "This token number is already registered.")
                    return

                if add_staff_member(token, name):
                    QMessageBox.information(self, "Success", f"Member '{name}' added successfully.")
                    self.load_members_data()
                    self.staff_data_changed.emit()
                else:
                    QMessageBox.critical(self, "Database Error",
                                         "Could not add the new member due to a database error.")

    def edit_member(self, row):
        """Opens a dialog to edit an existing member."""
        name = self.members_table.item(row, 0).text()
        token_item = self.members_table.item(row, 1)
        original_token = token_item.data(Qt.ItemDataRole.UserRole)

        dialog = MemberDialog("Edit Member", self)
        dialog.name_input.setText(name)
        dialog.token_input.setText(str(original_token))

        if dialog.exec():
            data = dialog.get_data()
            if data:
                new_token = data["token"]
                new_name = data["name"]

                # If token is changed, check if the new one is a duplicate
                if new_token != original_token and get_staff_by_token(new_token):
                    QMessageBox.warning(self, "Duplicate Token",
                                        "The new token number is already registered to another member.")
                    return

                if update_staff_member(original_token, new_token, new_name):
                    QMessageBox.information(self, "Success", "Member details updated successfully.")
                    self.load_members_data()
                    self.staff_data_changed.emit()
                else:
                    QMessageBox.critical(self, "Database Error", "Could not update member details.")

    def delete_member(self, row):
        """Deletes a member after confirmation."""
        name = self.members_table.item(row, 0).text()
        token_item = self.members_table.item(row, 1)
        token = token_item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete {name}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if delete_staff_member(token):
                QMessageBox.information(self, "Success", f"Member '{name}' deleted.")
                self.load_members_data()
                self.staff_data_changed.emit()
            else:
                QMessageBox.critical(self, "Database Error", "Could not delete the member.")

    def update_admin_mode_ui(self, is_unlocked):
        """Enables or disables member controls based on admin mode."""
        self.add_member_button.setEnabled(is_unlocked)
        for row in range(self.members_table.rowCount()):
            widget = self.members_table.cellWidget(row, 2)
            if widget:
                widget.setEnabled(is_unlocked)