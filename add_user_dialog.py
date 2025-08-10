from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QDialogButtonBox
)

from database_manager import get_all_staff

class AddUserDialog(QDialog):
    """A dialog to search for and select a staff member from the database."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add User to Sheet")
        self.setMinimumWidth(350)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for a staff member...")
        self.search_input.textChanged.connect(self.filter_list)
        layout.addWidget(self.search_input)

        # Staff list
        self.staff_list_widget = QListWidget()
        self.staff_list_widget.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.staff_list_widget)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.populate_staff_list()

    def populate_staff_list(self):
        """Fetches all staff from the database and adds them to the list."""
        self.staff_list_widget.clear()
        all_staff = get_all_staff()
        for staff_member in all_staff:
            item = QListWidgetItem(staff_member['name'])
            # Store the full staff data (token and name) in the item
            item.setData(Qt.ItemDataRole.UserRole, staff_member)
            self.staff_list_widget.addItem(item)

    def filter_list(self):
        """Hides or shows items in the list based on the search text."""
        search_text = self.search_input.text().lower()
        for i in range(self.staff_list_widget.count()):
            item = self.staff_list_widget.item(i)
            item.setHidden(search_text not in item.text().lower())

    def get_selected_staff(self):
        """Returns the data dictionary of the selected staff member."""
        selected_item = self.staff_list_widget.currentItem()
        if selected_item:
            return selected_item.data(Qt.ItemDataRole.UserRole)
        return None