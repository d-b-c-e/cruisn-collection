"""Launcher presentation preferences; never materialize runtime defaults here."""
import configparser
import os
from pathlib import Path
import tempfile

VIEWS = ('simple', 'advanced')
CORE = ('setup', 'controls', 'ffb', 'cameras', 'telemetry', 'support')
ADVANCED = {'display', 'graphics', 'impacts'}
PAGES = {'root', 'buttons', *CORE, *ADVANCED}


def view(value):
    return value if value in VIEWS else 'simple'


def page(value, selected_view):
    if value not in PAGES:
        return 'setup'
    if view(selected_view) == 'simple' and value in ADVANCED:
        return 'ffb' if value == 'impacts' else 'setup'
    return value


def load(section):
    selected = view(section.get('settings_view'))
    return dict(settings_view=selected,
                settings_page=page(section.get('settings_page', 'setup'), selected))


def update_section(path, section, values, backup_suffix):
    """Atomic scoped update; None removes one owned key, never another section."""
    path = Path(path)
    cp = configparser.ConfigParser(interpolation=None)
    original = path.read_bytes() if path.exists() else None
    if original is not None:
        cp.read_string(original.decode('utf-8-sig'))
    if not cp.has_section(section):
        cp.add_section(section)
    for key,value in values.items():
        if value is None:cp.remove_option(section,key)
        else:cp[section][key]=str(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(path.name + backup_suffix)
    if original is not None and not backup.exists():
        with backup.open('xb') as stream:
            stream.write(original)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix=path.name + '.', suffix='.tmp', delete=False) as stream:
            name = stream.name
            cp.write(stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def save(path, selected, selected_page):
    """Save only presentation keys; never materialize runtime defaults."""
    selected=view(selected);selected_page=page(selected_page,selected)
    values=dict(settings_view=selected,settings_page=selected_page)
    update_section(path,'collection',values,'.before-settings-view.bak')
    return values


def change(state, path, selected, selected_page, editing=False):
    if editing:
        raise ValueError('Finish or cancel the current edit to change view.')
    saved = save(path, selected, selected_page)
    state.update(saved)  # Failed persistence leaves the active view unchanged.
    return saved['settings_page']


def hit_row(width, height, x, y, selected_row, row_count):
    """Shared layout hit regions; the view header stays fixed while rows scroll."""
    if not width*.16 <= x <= width*.84:
        return None
    if height*.305 <= y <= height*.345:
        return 0
    offset = int((y/height-.40)/.048)
    if y < height*.40 or not 0 <= offset < 8:
        return None
    index = max(0,selected_row-8)+offset+1
    return index if index < row_count else None


def hit_page(width, height, x, y):
    if width*.14 <= x < width*.86 and height*.35 <= y <= height*.39:
        return CORE[int((x/width-.14)/.12)]
    return None


def hit_action(width, height, x, y):
    if height*.78 <= y < height*.83:
        if width*.14 <= x <= width*.34: return 'close'
        if width*.65 <= x <= width*.86: return 'stop_ffb'
    return None


def custom_sections(state, diag=False):
    sections = []
    if (state.get('ffbspring', 0) or state.get('ffbinvert', 0)
            or state.get('ffbprofile', 'cruisn-vunit@2') != 'cruisn-vunit@2'
            or any(state.get('ffbimpacts', {}).values())):
        sections.append(('ffb', 'Custom FFB tuning active'))
    if any(v not in (None, 100) for name in ('steersens', 'steercurve')
           for v in state.get(name, {}).values()):
        sections.append(('controls', 'Custom steering tuning active'))
    if not state.get('crt', True) or state.get('margin') is not None or state.get('scale', 4) != 4:
        sections.append(('display', 'Custom display settings active'))
    if not state.get('crackfill', True) or any(
            bool(v) for values in state.get('graphics', {}).values()
            for key, v in values.items() if key != 'world_lookahead'):
        sections.append(('graphics', 'Rendering experiments active'))
    if diag:
        sections.append(('support', 'FFB diagnostics active'))
    return sections
