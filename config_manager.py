import configparser
import os

CONFIG_FILE = 'config.ini'
DEFAULT_SECTION = 'Settings'
PATH_KEY = 'SaveDirectory'
PASSWORD_KEY = 'ExcelPassword'
TITLE_KEY = 'AppTitle'
LOGO_PATH_KEY = 'LogoPath'
ADMIN_MODE_KEY = 'AdminMode'
NAV_SLIDER_KEY = 'NavigationSlider'
THEME_KEY = 'Theme'


def get_default_save_directory():
    """Returns the default 'SignInSheet' directory on the Desktop."""
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    return os.path.join(desktop_path, 'SignInSheet')


def save_setting(key, value):
    """Saves a specific key-value pair to the config file."""
    config = configparser.ConfigParser()
    # Read existing config to not overwrite other settings
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    if not config.has_section(DEFAULT_SECTION):
        config.add_section(DEFAULT_SECTION)

    config.set(DEFAULT_SECTION, key, value)

    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def load_path():
    """Loads the saved path from the config file, or returns the default."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.get(DEFAULT_SECTION, PATH_KEY, fallback=get_default_save_directory())
    return get_default_save_directory()


def load_password():
    """Loads the saved Excel password, or returns the default 'lsst1234'."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.get(DEFAULT_SECTION, PASSWORD_KEY, fallback='lsst1234')
    return 'lsst1234'


def load_title():
    """Loads the saved app title, or returns the default 'LSST'."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.get(DEFAULT_SECTION, TITLE_KEY, fallback='LSST')
    return 'LSST'

def load_logo_path():
    """Loads the saved logo path from the config file, or returns an empty string."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.get(DEFAULT_SECTION, LOGO_PATH_KEY, fallback='')
    return ''

def load_admin_mode():
    """Loads the saved admin mode state, or returns False (locked)."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.getboolean(DEFAULT_SECTION, ADMIN_MODE_KEY, fallback=False)
    return False

def load_nav_slider_enabled():
    """Loads the saved nav slider state, or returns True (enabled)."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.getboolean(DEFAULT_SECTION, NAV_SLIDER_KEY, fallback=True)
    return True

def load_theme():
    """Loads the saved theme from the config file, or returns 'light'."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.get(DEFAULT_SECTION, THEME_KEY, fallback='light')
    return 'light'
