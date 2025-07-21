# --- Theme Constants (Windows 11 Light Theme Inspired) ---

# --- Colors: Window & Backgrounds ---
WIN_COLOR_WINDOW_BG = "#EFF6FC"
WIN_COLOR_WIDGET_BG = "#FFFFFF"
WIN_COLOR_WIDGET_BG_ALT = "#F0F6FC"
WIN_COLOR_CONTROL_BG_HOVER = "#E1EAF2"
WIN_COLOR_CONTROL_BG_PRESSED = "#D1DAE2"

# --- Colors: Borders ---
WIN_COLOR_BORDER_LIGHT = "#DCE8F2"
WIN_COLOR_BORDER_MEDIUM = "#C5D3E0"
WIN_COLOR_BORDER_FOCUSED = "#0078D4"

# --- Colors: Text ---
WIN_COLOR_TEXT_PRIMARY = "#1A1A1A"
WIN_COLOR_TEXT_SECONDARY = "#5A5A5A"
WIN_COLOR_ACCENT_TEXT_ON_PRIMARY = "#FFFFFF"

# --- Colors: Accent & Buttons (New Blue Theme) ---
WIN_COLOR_ACCENT_PRIMARY = "#0078D4"
WIN_COLOR_ACCENT_PRIMARY_HOVER = "#005A9E"
WIN_COLOR_ACCENT_PRIMARY_PRESSED = "#004578"
WIN_COLOR_SECONDARY_BUTTON_BG = "#6c757d"
WIN_COLOR_SECONDARY_BUTTON_HOVER = "#5a6268"

# --- Colors: Calendar Specific ---
CALENDAR_SELECTION_COLOR = WIN_COLOR_ACCENT_PRIMARY
WEEKEND_COLOR = "#D32F2F"
OK_BUTTON_COLOR = "#0078D4"

# --- Colors: Toast Notification Colors ---
TOAST_BG = "#FFFFFF"
TOAST_BORDER = "#DEE2E6"
TOAST_HEADER_FG = "#6C757D"
TOAST_SUCCESS_BORDER = "#4CAF50"
TOAST_INFO_BORDER = "#0078D4"
TOAST_WARNING_BORDER = "#FFC107"

# --- Fonts ---
WIN_FONT_FAMILY = "Segoe UI Variable"
WIN_FONT_FAMILY_FALLBACK = "Segoe UI"
WIN_FONT_SIZE_TITLE = 14

# --- Styles ---
WIN_BORDER_RADIUS = "4px"

# --- Icons ---
ICON_MENU_NORMAL = "☰"
ICON_MENU_PINNED = "📌"

# --- Global Stylesheet ---
APP_STYLESHEET = f"""
    * {{
        outline: none;
    }}
    QWidget {{
        font-family: "{WIN_FONT_FAMILY}", "{WIN_FONT_FAMILY_FALLBACK}";
    }}
    QLabel {{
        border: none;
        background-color: transparent;
    }}
    QMainWindow {{
        background-color: {WIN_COLOR_WINDOW_BG};
    }}
    QPushButton {{
        padding: 8px 16px;
        border: 1px solid {WIN_COLOR_BORDER_MEDIUM};
        border-radius: {WIN_BORDER_RADIUS};
        background-color: {WIN_COLOR_WIDGET_BG};
    }}
    QPushButton:hover {{
        background-color: {WIN_COLOR_CONTROL_BG_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {WIN_COLOR_CONTROL_BG_PRESSED};
    }}
    /* Style for primary action buttons */
    QPushButton[primary="true"] {{
        background-color: {WIN_COLOR_ACCENT_PRIMARY};
        color: {WIN_COLOR_ACCENT_TEXT_ON_PRIMARY};
        border: none;
        font-weight: bold;
    }}
    QPushButton[primary="true"]:hover {{
        background-color: {WIN_COLOR_ACCENT_PRIMARY_HOVER};
    }}
    QPushButton[primary="true"]:pressed {{
        background-color: {WIN_COLOR_ACCENT_PRIMARY_PRESSED};
    }}
    QPushButton[primary="true"]:disabled {{
        background-color: transparent;
        color: transparent;
        border: none;
    }}
"""