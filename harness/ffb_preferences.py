"""Saved output switch, independent of strength and per-game conditioning."""
from settings_view import update_section


def enabled(section):
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
