from PySide6.QtWidgets import QInputDialog, QLineEdit


def ask_for_name(parent, token):
    """
    Shows a native PySide6 input dialog to ask for the user's name.

    Args:
        parent: The parent widget for this dialog.
        token: The token number to display in the prompt.

    Returns:
        The user's name as a string if they click OK, otherwise None.
    """
    text, ok = QInputDialog.getText(
        parent,
        "New Card Detected",
        f"Please enter the name for new token: {token}",
        QLineEdit.EchoMode.Normal,  # Standard text input
        ""  # Initial text in the input box
    )

    if ok and text:
        return text
    else:
        return None
