"""Pure control identity/calibration contract. No device, UI or native imports.

See docs/reviews/2026-09-19-control-preferences-contract.md for the persisted
schema, normalized units, caller responsibilities and native golden vectors.
"""
from copy import deepcopy
import configparser
import io
import json
import math
import os
from pathlib import Path
import re
import tempfile
import uuid

VERSION = 1
MIN_SPAN = 0.05
RETURN_TOLERANCE = 0.10
AXES = ('XAXIS', 'YAXIS', 'ZAXIS', 'RXAXIS', 'RYAXIS', 'RZAXIS', 'SLIDER1', 'SLIDER2')
ROOT_SECTION = 'control_preferences'
SECTION_PREFIX = 'control:'


def _guid(value):
    if not isinstance(value, str) or not re.fullmatch(
            r'\{?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}?', value):
        raise ValueError('Expected a canonical DirectInput GUID.')
    if value.startswith('{') != value.endswith('}'):
        raise ValueError('Unmatched GUID braces.')
    result = str(uuid.UUID(value))
    if int(uuid.UUID(result)) == 0:
        raise ValueError('An empty GUID cannot identify a device.')
    return result


def canonical_identity(value):
    """Canonical dinput identity; path/capability are optional metadata, not keys."""
    if not isinstance(value, dict) or value.get('backend') != 'dinput':
        raise ValueError('Only backend-qualified DirectInput identities are supported.')
    result = deepcopy(value)
    result.update(backend='dinput', product_guid=_guid(value.get('product_guid')),
                  instance_guid=_guid(value.get('instance_guid')))
    if 'hid_path' in value:
        path = value['hid_path']
        if not isinstance(path, str) or not path or any(c in path for c in '\r\n\0'):
            raise ValueError('HID path must be a nonempty device path without control characters.')
        if not path.startswith('\\\\?\\'):
            raise ValueError('HID path must be a Windows device-interface path.')
        result['hid_path'] = path.upper()
    if 'ffb_capable' in value and type(value['ffb_capable']) is not bool:
        raise ValueError('FFB capability metadata must be a boolean when supplied.')
    return result


def _identity_key(value):
    value = canonical_identity(value)
    return value['backend'], value['product_guid'], value['instance_guid']


def resolve_device(identity, inventory):
    """Return status resolved/missing/ambiguous/invalid; never use name or index.

    inventory rows contain {identity: {...}, name: str, axes: [fixed slots]}.
    Optional metadata is copied from the current inventory, not the saved record.
    Malformed inventory makes resolution invalid rather than dropping a possible twin.
    """
    try:
        key = _identity_key(identity)
        matches = []
        for row in inventory:
            if not isinstance(row, dict):
                raise ValueError('Invalid inventory row.')
            current = canonical_identity(row.get('identity'))
            if _identity_key(current) == key:
                matched = deepcopy(row)
                matched['identity'] = current
                matches.append(matched)
    except (TypeError, ValueError):
        return {'status': 'invalid', 'device': None}
    if len(matches) != 1:
        return {'status': 'missing' if not matches else 'ambiguous', 'device': None}
    return {'status': 'resolved', 'device': matches[0]}


def output_path(resolution):
    """Current verified bridge material or None; never invent an output selector.

    Caller supplies inventory from its verified DirectInput provider. This does
    not prove SDL presence, constant-force capability or physical-device status.
    """
    if resolution.get('status') != 'resolved' or not resolution.get('device'):
        return None
    identity = canonical_identity(resolution['device']['identity'])
    return None if identity.get('ffb_capable') is False else identity.get('hid_path')


def propose_legacy_identity(name, inventory):
    """Unique whole-name match yields an UNSAVED proposal, never a resolution."""
    if not isinstance(name, str) or not name.strip():
        return {'status': 'missing', 'identity': None}
    candidates = []
    try:
        for row in inventory:
            identity = canonical_identity(row['identity'])
            if not isinstance(row.get('name'), str):
                raise ValueError('Inventory has no friendly name.')
            if row['name'].casefold() == name.casefold():
                candidates.append(identity)
    except (KeyError, TypeError, ValueError):
        return {'status': 'invalid', 'identity': None}
    if len(candidates) != 1:
        return {'status': 'missing' if not candidates else 'ambiguous', 'identity': None}
    return {'status': 'proposal', 'identity': candidates[0]}


def _number(value, label, low=-1.0, high=1.0):
    if type(value) not in (int, float) or not low <= value <= high or not math.isfinite(value):
        raise ValueError(f'{label} must be finite and in [{low}, {high}].')
    return float(value)


def validate_calibration(value):
    """Validate/clone v1 endpoints in raw [-1,1]; None means exact passthrough."""
    if value is None:
        return None
    if not isinstance(value, dict) or type(value.get('version')) is not int or value['version'] != VERSION:
        raise ValueError('Unsupported calibration version.')
    kind = value.get('kind')
    endpoints = ('left', 'centre', 'right') if kind == 'steering' else ('released', 'full') if kind == 'pedal' else ()
    if not endpoints or set(value) != {'version', 'kind', 'invert', 'deadzone', *endpoints}:
        raise ValueError('Calibration fields do not match the supported kind.')
    if type(value['invert']) is not bool:
        raise ValueError('Invert must be an explicit boolean.')
    result = deepcopy(value)
    for key in endpoints:
        result[key] = _number(value[key], key)
    deadzone = _number(value['deadzone'], 'Deadzone', 0.0, 1.0)
    if deadzone >= 1.0:
        raise ValueError('Deadzone must be less than 1.')
    result['deadzone'] = deadzone
    if kind == 'steering':
        left, centre, right = (result[key] for key in endpoints)
        if not (left < centre < right or right < centre < left):
            raise ValueError('Centre must be strictly between the two ends.')
        if min(abs(left-centre), abs(right-centre)) < MIN_SPAN:
            raise ValueError('Each steering span must be at least 0.05 raw units.')
    elif abs(result['full']-result['released']) < MIN_SPAN:
        raise ValueError('Pedal span must be at least 0.05 raw units.')
    return result


def normalize(raw, calibration=None):
    """Steering -> [-1,1]; pedal -> [0,1]; None -> raw unchanged in [-1,1].

    Endpoints establish direction. Invert reverses that normalized direction;
    for a pedal it swaps released/full interpretation. Deadzone is then applied
    ONCE at zero and the remaining interval is rescaled. Native must not apply
    another deadzone or old half-axis transform to this result.
    """
    raw = _number(raw, 'Raw input')
    cal = validate_calibration(calibration)
    if cal is None:
        return raw
    if cal['kind'] == 'steering':
        orientation = 1.0 if cal['right'] > cal['centre'] else -1.0
        delta = (raw-cal['centre']) * orientation
        span = abs(cal['right']-cal['centre']) if delta >= 0 else abs(cal['left']-cal['centre'])
        value = max(-1.0, min(1.0, delta/span))
        if cal['invert']:
            value = -value
        magnitude = max(0.0, (abs(value)-cal['deadzone'])/(1.0-cal['deadzone']))
        return math.copysign(magnitude, value) if magnitude else 0.0
    value = max(0.0, min(1.0, (raw-cal['released'])/(cal['full']-cal['released'])))
    if cal['invert']:
        value = 1.0-value
    return max(0.0, (value-cal['deadzone'])/(1.0-cal['deadzone']))


def _action(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,31}', value):
        raise ValueError('Action must be a lowercase identifier of at most 32 characters.')
    return value


def _record(value):
    if not isinstance(value, dict) or type(value.get('version')) is not int or value['version'] != VERSION:
        raise ValueError('Unsupported control record version.')
    if value.get('axis') not in AXES or 'calibration' not in value:
        raise ValueError('A fixed DirectInput axis slot and explicit calibration state are required.')
    result = deepcopy(value)
    result['identity'] = canonical_identity(value.get('identity'))
    result['calibration'] = validate_calibration(value['calibration'])
    return result


def _action_record(action, value):
    result = _record(value)
    expected = 'steering' if action == 'steer' else 'pedal' if action in ('gas', 'brake', 'clutch', 'handbrake') else None
    if result['calibration'] is not None and expected and result['calibration']['kind'] != expected:
        raise ValueError(f'{action} requires {expected} calibration.')
    return result


def make_proposal(action, identity, axis, calibration=None, *, legacy_binding=None):
    """Create an unsaved axis-binding/calibration proposal; no active state changes."""
    action = _action(action)
    proposal = {'action': action, 'record': _action_record(action, dict(version=VERSION,
                identity=identity, axis=axis, calibration=calibration))}
    if legacy_binding is not None:
        if not isinstance(legacy_binding, str) or not legacy_binding or any(c in legacy_binding for c in '\r\n\0'):
            raise ValueError('Legacy binding must be one nonempty value.')
        proposal['legacy_binding'] = legacy_binding
    return proposal


class CalibrationDraft:
    """Ordered pure capture; cancellation/disconnect never replace original.

    Caller supplies stable representative samples and current inventory before
    preview/save. This class does not poll devices or decide capture stability.
    """
    def __init__(self, action, identity, axis, kind, *, original=None, legacy_binding=None):
        if kind not in ('steering', 'pedal'):
            raise ValueError('Unsupported calibration kind.')
        self._original = _record(original) if original is not None else None
        self._base = make_proposal(action, identity, axis, legacy_binding=legacy_binding)
        self.kind = kind
        self.steps = ('centre', 'left', 'right', 'return') if kind == 'steering' else ('released', 'full', 'return')
        self.samples = {}
        self.status = 'capturing'

    @property
    def original(self):
        return deepcopy(self._original)

    def cancel(self):
        self.samples.clear()
        self.status = 'cancelled'
        return self.original

    def observe_inventory(self, inventory):
        resolution = resolve_device(self._base['record']['identity'], inventory)
        device = resolution['device']
        available = device is not None and self._base['record']['axis'] in device.get('axes', ())
        if self.status in ('capturing', 'ready') and (resolution['status'] != 'resolved' or not available):
            self.samples.clear()
            self.status = 'disconnected'
        return self.status

    def capture(self, step, raw, identity):
        if self.status != 'capturing':
            raise ValueError('This draft is no longer capturing.')
        try:
            same = _identity_key(identity) == _identity_key(self._base['record']['identity'])
        except ValueError:
            same = False
        if not same:
            self.samples.clear()
            self.status = 'disconnected'
            raise ValueError('Device identity changed; previous calibration retained.')
        if step != self.steps[len(self.samples)]:
            raise ValueError('Capture steps must be completed in order.')
        value = _number(raw, step)
        if step == 'return':
            provisional = dict(version=VERSION, kind=self.kind, invert=False, deadzone=0.0,
                               **self.samples)
            if abs(normalize(value, provisional)) > RETURN_TOLERANCE:
                raise ValueError('Return the control to its recorded resting position.')
        self.samples[step] = value
        if len(self.samples) == len(self.steps):
            self.status = 'ready'

    def proposal(self, *, invert=False, deadzone=0.0):
        if self.status != 'ready':
            raise ValueError('Finish calibration before saving a proposal.')
        calibration = dict(version=VERSION, kind=self.kind, invert=invert, deadzone=deadzone)
        calibration.update({key: value for key, value in self.samples.items() if key != 'return'})
        result = deepcopy(self._base)
        result['record']['calibration'] = validate_calibration(calibration)
        result['record'] = _action_record(result['action'], result['record'])
        return result


def _parse(data):
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str
    if data is not None:
        cp.read_string(data.decode('utf-8-sig'))
    return cp


def _records(cp):
    sections = [section for section in cp.sections() if section.startswith(SECTION_PREFIX)]
    if cp.has_section(ROOT_SECTION):
        # DEFAULT values must never supply a missing schema declaration.
        if cp._sections[ROOT_SECTION].get('version') != str(VERSION):
            raise ValueError('Unsupported control preferences version; settings retained.')
    elif sections:
        raise ValueError('Control records have no version declaration.')
    result = {}
    for section in sections:
        action = _action(section[len(SECTION_PREFIX):])
        try:
            result[action] = _action_record(action, json.loads(cp._sections[section]['record']))
        except (KeyError, configparser.Error, json.JSONDecodeError) as error:
            raise ValueError(f'Invalid saved control record for {action}.') from error
    return result


def load_records(path):
    """Load saved v1 records without migrating legacy wheelmap or querying devices."""
    path = Path(path)
    return _records(_parse(path.read_bytes() if path.exists() else None))


def commit_proposals(path, proposals, *, expected_original, inventory):
    """Atomic explicit save of several action records and optional legacy values.

    expected_original is exact bytes from opening the edit, or None for a file
    that must remain absent. No caller-owned proposal/original object is mutated.
    Return only after replacement succeeds; caller then adopts returned records.
    """
    path = Path(path)
    original = path.read_bytes() if path.exists() else None
    if original != expected_original:
        raise ValueError('Settings changed while editing; reopen before saving.')
    cp = _parse(original)
    saved = _records(cp)
    inventory = list(inventory)
    pending = {}
    for proposal in proposals:
        action = _action(proposal['action'])
        if action in pending:
            raise ValueError('An action appears more than once in this transaction.')
        record = _action_record(action, proposal['record'])
        resolved = resolve_device(record['identity'], inventory)
        if resolved['status'] != 'resolved' or record['axis'] not in resolved['device'].get('axes', ()):
            raise ValueError(f'{action}: saved device is missing, ambiguous or has no selected axis.')
        legacy = proposal.get('legacy_binding')
        checked = make_proposal(action, record['identity'], record['axis'], record['calibration'], legacy_binding=legacy)
        merged = deepcopy(saved.get(action, {}))
        merged.update(record)
        pending[action] = merged
        section = SECTION_PREFIX+action
        if not cp.has_section(section): cp.add_section(section)
        cp.set(section, 'record', json.dumps(merged, ensure_ascii=True, separators=(',', ':'), allow_nan=False))
        if 'legacy_binding' in checked:
            if not cp.has_section('wheelmap'): cp.add_section('wheelmap')
            keys = [key for key in cp['wheelmap'] if key.casefold() == action]
            if len(keys) > 1: raise ValueError('Ambiguous legacy action key; settings retained.')
            cp.set('wheelmap', keys[0] if keys else action, checked['legacy_binding'])
    if not pending:
        raise ValueError('There are no proposals to save.')
    # The native adapter normalizes a physical axis once, before role mapping.
    # Preflight the whole resulting configuration rather than saving a proposal
    # that cannot launch because another role gives that axis different endpoints.
    axes = {}
    for action, record in {**saved, **pending}.items():
        key = (*_identity_key(record['identity']), record['axis'])
        if key in axes and axes[key] != record['calibration']:
            raise ValueError('One physical axis cannot use two different calibrations.')
        axes[key] = record['calibration']
    if not cp.has_section(ROOT_SECTION): cp.add_section(ROOT_SECTION)
    cp.set(ROOT_SECTION, 'version', str(VERSION))
    output = io.StringIO()
    cp.write(output)
    payload = output.getvalue().encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    name = None
    try:
        if original is not None:
            backup = path.with_name(path.name+'.before-controls.'+uuid.uuid4().hex+'.bak')
            with backup.open('xb') as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
        with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, prefix=path.name+'.', suffix='.tmp', delete=False) as stream:
            name = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        current = path.read_bytes() if path.exists() else None
        if current != original:
            raise ValueError('Settings changed before replacement; previous settings retained.')
        os.replace(name, path)
        name = None
    finally:
        if name and os.path.exists(name): os.unlink(name)
    return {'records': {**saved, **pending}, 'backup': backup}
