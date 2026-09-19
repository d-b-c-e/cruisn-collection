"""Saved control/device preferences and the isolated native launch boundary.

No device access at import time. UI callers adopt edits only after atomic save.
Capability receipts bind opt-in controls to a qualified executable's bytes.
"""
import configparser
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
import xml.etree.ElementTree as ET

from control_preferences import canonical_identity, load_records, output_path, resolve_device

FEATURES = frozenset(('strict-dinput-v1', 'control-calibration-v1', 'ffb-path-v1'))


@lru_cache(maxsize=8)
def _supported(binary, binary_stat, receipt_stat):
    try:
        receipt = json.loads(Path(binary + '.features.json').read_text(encoding='utf-8'))
        if (not isinstance(receipt, dict) or type(receipt.get('version')) is not int
                or receipt['version'] != 1 or not isinstance(receipt.get('features'), list)
                or not all(isinstance(f, str) for f in receipt['features'])
                or not FEATURES.issubset(receipt['features'])):
            return False
        with open(binary, 'rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        return digest == receipt.get('sha256')
    except (OSError, ValueError, TypeError):
        return False


def supported(binary):
    """Cached hash-bound capability check; never enumerates/acquires devices."""
    try:
        path = Path(binary).resolve()
        signature = lambda p: (p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
        return _supported(str(path), signature(path), signature(Path(str(path)+'.features.json')))
    except OSError:
        return False


def _parse(original):
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str
    if original is not None:
        cp.read_string(original.decode('utf-8-sig'))
    return cp


def _key(cp, section, key):
    matches = [k for k in cp._sections.get(section, {}) if k.casefold() == key.casefold()]
    if len(matches) > 1:
        raise ValueError('Ambiguous saved setting: '+key)
    return matches[0] if matches else key


def _get(cp, section, key, default=None):
    return cp._sections.get(section, {}).get(_key(cp, section, key), default)


def _selection(cp):
    mode = _get(cp, 'collection', 'ffb_device_mode', 'steering')
    raw = _get(cp, 'collection', 'ffb_device_identity')
    if mode not in ('steering', 'explicit'):
        raise ValueError('Unsupported saved force-feedback device mode.')
    if mode == 'steering':
        if raw:
            raise ValueError('Follow Steering must not have an explicit device identity.')
        return {'mode': mode, 'identity': None}
    try:
        identity = canonical_identity(json.loads(raw))
    except (TypeError, ValueError) as error:
        raise ValueError('Invalid saved force-feedback device identity.') from error
    return {'mode': mode, 'identity': identity}


def load_ffb_selection(path):
    path = Path(path)
    return _selection(_parse(path.read_bytes() if path.exists() else None))


def _edit(path, expected_original, mutate):
    """Optimistic single-writer edit with exact-byte backup and atomic replace."""
    path = Path(path)
    original = path.read_bytes() if path.exists() else None
    if original != expected_original:
        raise ValueError('Settings changed while editing; reopen before saving.')
    cp = _parse(original)
    result = mutate(cp)
    output = io.StringIO()
    cp.write(output)
    payload = output.getvalue().encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        if original is not None:
            backup = path.with_name(path.name+'.before-controls.'+uuid.uuid4().hex+'.bak')
            with backup.open('xb') as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
        with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, prefix=path.name+'.',
                                         suffix='.tmp', delete=False) as stream:
            name = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if (path.read_bytes() if path.exists() else None) != original:
            raise ValueError('Settings changed before replacement; previous settings retained.')
        os.replace(name, path)
        name = None
    finally:
        if name and os.path.exists(name):
            os.unlink(name)
    return result


def save_ffb_selection(path, mode, identity=None, *, expected_original, inventory):
    """Save output selection independently of force enabled/strength/tune values."""
    if mode not in ('steering', 'explicit') or (mode == 'steering' and identity is not None):
        raise ValueError('Choose Follow Steering or one explicit output device.')
    selected = None
    if mode == 'explicit':
        selected = canonical_identity(identity)
        resolved = resolve_device(selected, list(inventory))
        if not output_path(resolved):
            raise ValueError('The output device is missing, ambiguous or has no verified output path.')
        selected = resolved['device']['identity']

    def mutate(cp):
        if not cp.has_section('collection'):
            cp.add_section('collection')
        cp.set('collection', _key(cp, 'collection', 'ffb_device_mode'), mode)
        key = _key(cp, 'collection', 'ffb_device_identity')
        if selected is None:
            cp.remove_option('collection', key)
        else:
            cp.set('collection', key, json.dumps(selected, ensure_ascii=True, separators=(',', ':')))
        return _selection(cp)
    return _edit(path, expected_original, mutate)


def clear_control_selection(path, role, *, expected_original):
    """Clear both persisted representations; never uncover an old wizard bind."""
    if role not in ('steer', 'gas', 'brake', 'clutch', 'handbrake'):
        raise ValueError('Unsupported control role.')
    def mutate(cp):
        cp.remove_section('control:'+role)
        if cp.has_section('wheelmap'):
            cp.remove_option('wheelmap', _key(cp, 'wheelmap', role))
        # A tombstone overrides inherited controller mappings at launch too.
        if not cp.has_section('control_unbound'):
            cp.add_section('control_unbound')
        cp.set('control_unbound', role, '1')
    return _edit(path, expected_original, mutate)


def resolve_output(path, inventory):
    """Current strict output selector, or None. No name/index fallback."""
    selection = load_ffb_selection(path)
    identity = selection['identity']
    if selection['mode'] == 'steering':
        steering = load_records(path).get('steer')
        identity = steering['identity'] if steering else None
    if identity is None:
        return None
    path = output_path(resolve_device(identity, inventory))
    return 'path:'+path if path else None


def save_legacy_bindings(path, bindings):
    """A deliberate wizard rebind replaces the same role's newer axis record."""
    path = Path(path)
    original = path.read_bytes() if path.exists() else None
    def mutate(cp):
        if not cp.has_section('wheelmap'):
            cp.add_section('wheelmap')
        for role, value in bindings.items():
            if not re.fullmatch(r'[a-z][a-z0-9_]{0,31}', role):
                raise ValueError('Invalid binding role.')
            if value is not None and (not isinstance(value, str) or not value or any(c in value for c in '\r\n\0')):
                raise ValueError('Invalid binding value.')
            cp.remove_section('control:'+role)
            if cp.has_section('control_unbound'):
                cp.remove_option('control_unbound', _key(cp, 'control_unbound', role))
            key = _key(cp, 'wheelmap', role)
            if value is None:
                cp.remove_option('wheelmap', key)
                if role in ('steer', 'gas', 'brake', 'clutch', 'handbrake'):
                    if not cp.has_section('control_unbound'):
                        cp.add_section('control_unbound')
                    cp.set('control_unbound', role, '1')
            else:
                cp.set('wheelmap', key, value)
    return _edit(path, original, mutate)


def apply_controls(tree, config, inventory, tables):
    """Overlay identities on a private controller tree and return profile text.

    tables maps system name to the existing role -> (port types, key) catalog.
    Reuse a unique name's current logical slot to preserve its legacy buttons;
    names are never used to choose physical ownership of a saved identity.
    """
    config = Path(config)
    records = load_records(config)
    cp = _parse(config.read_bytes() if config.exists() else None)
    unbound = {role for role, value in cp._sections.get('control_unbound', {}).items() if value == '1'} - records.keys()
    roles = records.keys() | unbound
    for role in roles:
        if role not in tables['default']:
            raise ValueError('This game build has no mapped control role: '+role)
    if not roles:
        return None
    root = tree.getroot()
    def system_input(name):
        systems = [s for s in root.findall('system') if s.get('name') == name]
        if len(systems) > 1:
            raise ValueError('Ambiguous controller system: '+name)
        system = systems[0] if systems else ET.SubElement(root, 'system', name=name)
        inp = system.find('input')
        return inp if inp is not None else ET.SubElement(system, 'input')
    default = system_input('default')
    slots, tokens, calibrations = {}, {}, {}
    maps = list(default.findall('mapdevice'))
    used = {int(m.get('controller')[8:]) for m in maps
            if re.fullmatch(r'JOYCODE_[1-9][0-9]*', m.get('controller', ''))}
    for role, record in records.items():
        resolution = resolve_device(record['identity'], inventory)
        device = resolution['device']
        if resolution['status'] != 'resolved' or record['axis'] not in device.get('axes', ()):
            raise ValueError(role+': reconnect the saved device and selected axis before launching.')
        identity = canonical_identity(record['identity'])
        selector = 'strict-dinput:'+identity['product_guid']+':'+identity['instance_guid']
        if selector not in slots:
            same_name = [row for row in inventory if row.get('name', '').casefold() == device['name'].casefold()]
            candidates = [m for m in maps if m.get('device') == selector or
                          (len(same_name) == 1 and m.get('device', '').casefold() == device['name'].casefold())]
            if len(candidates) > 1:
                raise ValueError('Ambiguous logical controller slot for '+device['name'])
            if candidates:
                mapping = candidates[0]
                if not re.fullmatch(r'JOYCODE_[1-9][0-9]*', mapping.get('controller', '')):
                    raise ValueError('Invalid logical controller slot.')
                slot = int(mapping.get('controller')[8:])
                if sum(m.get('controller') == mapping.get('controller') for m in maps) != 1:
                    raise ValueError('Two controller mappings claim the same logical slot.')
                mapping.set('device', selector)
            else:
                slot = max(used, default=0)+1
                mapping = ET.SubElement(default, 'mapdevice', device=selector, controller=f'JOYCODE_{slot}')
                maps.append(mapping)
            used.add(slot)
            slots[selector] = slot
        axis = record['axis']
        cal = record['calibration']
        key = (identity['product_guid'], identity['instance_guid'], axis)
        if key in calibrations and calibrations[key] != cal:
            raise ValueError('One physical axis cannot use two different calibrations.')
        calibrations[key] = cal
        token = f'JOYCODE_{slots[selector]}_{axis}'
        # Uncalibrated legacy pedals may intentionally use one half of the axis.
        old = _get(cp, 'wheelmap', role, '')
        if cal is None and role in ('gas', 'brake') and '|axis:' in old:
            sign = old.rsplit(':', 1)[-1]
            if sign in ('pos', 'neg'):
                token += '_'+sign.upper()+'_ABSOLUTE'
        tokens[role] = token
    # Remove conflicting per-game overrides before writing the exact role ports.
    claimed = {port for table in tables.values() for role in roles
               for port in table.get(role, ([], None))[0]}
    for inp in root.iter('input'):
        for port in list(inp.findall('port')):
            if port.get('type') in claimed:
                inp.remove(port)
    for name, table in tables.items():
        inp = system_input(name)
        for role in roles:
            for ptype in table.get(role, ([], None))[0]:
                port = ET.SubElement(inp, 'port', type=ptype)
                ET.SubElement(port, 'newseq', type='standard').text = tokens.get(role, 'NONE')
    lines = ['cruisn-calibration-v1']
    for (product, instance, axis), cal in sorted(calibrations.items()):
        if cal is None:
            continue
        pedal = cal['kind'] == 'pedal'
        fields = [product, instance, axis, cal['kind'],
                  cal['released'] if pedal else cal['left'], 0 if pedal else cal['centre'],
                  cal['full'] if pedal else cal['right'], int(cal['invert']), cal['deadzone']]
        lines.append('|'.join(str(field) for field in fields))
    return '\n'.join(lines)+'\n' if records else None
