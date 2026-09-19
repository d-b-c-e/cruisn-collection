"""Saved output switch, independent of strength and per-game conditioning."""
from settings_view import update_section
from pathlib import Path


def stop_file(path):
    return Path(path).with_name('ffb-user-stopped')


def stopped(path):
    try:
        stop_file(path).stat()
        return True
    except FileNotFoundError:
        return False


def enabled(section, path=None):
    if path is not None and stopped(path):
        return False
    flag = section.get('ffb_enabled')
    if flag is not None:
        return str(flag).strip().lower() in ('1', 'on', 'true', 'yes')
    try:
        return int(section.get('ffb', 50)) > 0
    except (TypeError, ValueError):
        return False


def set_enabled(path, value):
    update_section(path, 'collection', {'ffb_enabled': '1' if value else '0'},
                   '.before-ffb-switch.bak')
    # Only an explicit On can clear the native panic marker. Save first: if
    # persistence fails, the last Off choice must remain effective.
    if value:
        stop_file(path).unlink(missing_ok=True)
