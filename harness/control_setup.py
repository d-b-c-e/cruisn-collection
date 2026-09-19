"""Staged launcher controls UI. Providers are injected; import never opens devices.

The launcher owns one Session and one read-only reader. Saved records become
effective only through the launch adapter; a device preview is not game input.
"""
from collections import deque
from copy import deepcopy
import configparser
import json
import math
from pathlib import Path

import control_preferences as preferences

ROLES = {'steer': 'Steering', 'gas': 'Throttle', 'brake': 'Brake'}
STABLE_SECONDS = .35
STABLE_RANGE = .025
OTHER_MOVEMENT = .15
TIMEOUT = 90.


def record_label(record):
    if not record:
        return 'Not bound'
    identity = record['identity']
    return identity.get('display_name', 'DirectInput device') + ' / ' + record['axis']


def device_label(record):
    # Same-name twins stay distinguishable; this is display only, never matching.
    return '[' + record['identity']['instance_guid'][:8] + '] ' + record.get('name', 'Device')


def preview_text(role, raw, calibration):
    if raw is None:
        return 'Waiting for device'
    if calibration is None:
        return f'Raw {raw:+.2f} / calibration needed'
    value = preferences.normalize(raw, calibration)
    if role == 'steer':
        direction = 'Centre' if abs(value) < .02 else 'Left' if value < 0 else 'Right'
        return f'{direction} {abs(value)*100:.0f}% / raw {raw:+.2f}'
    name = 'Released' if value < .02 else 'Full' if value > .98 else 'Pressed'
    return f'{name} {value*100:.0f}% / raw {raw:+.2f}'


def native_status(binary):
    try:
        import control_launch
        return bool(control_launch.supported(binary))
    except (ImportError, OSError, ValueError):
        return False


def load_ffb(path):
    try:
        import control_launch
        return control_launch.load_ffb_selection(path)
    except ImportError:
        # Read-only presentation until the owner supplies the native launch seam.
        import configparser
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(path, encoding='utf-8-sig')
        section = cp['collection'] if cp.has_section('collection') else {}
        mode = section.get('ffb_device_mode', 'steering')
        if mode not in ('steering', 'explicit'):
            raise ValueError('Saved FFB device mode is invalid; choose a device explicitly.')
        identity = json.loads(section['ffb_device_identity']) if mode == 'explicit' else None
        return dict(mode=mode, identity=preferences.canonical_identity(identity) if identity else None)


def save_ffb(path, mode, identity=None, **kwargs):
    try:
        import control_launch
    except ImportError as error:
        raise ValueError('FFB selection save adapter is pending; previous choice retained.') from error
    return control_launch.save_ffb_selection(path, mode, identity, **kwargs)


def clear_role(path, role, **kwargs):
    try:
        import control_launch
        clear = control_launch.clear_control_selection
    except (ImportError, AttributeError) as error:
        raise ValueError('Clear adapter is pending; previous assignment retained.') from error
    return clear(path, role, **kwargs)


class Session:
    """One modal edit with one reader. All writes are explicit and injectable."""
    def __init__(self, path, inventory, reader, window, *, binary='',
                 commit=preferences.commit_proposals, ffb_save=save_ffb,
                 clear=clear_role, ffb_load=load_ffb, supported=native_status):
        self.path = Path(path)
        self.inventory_provider, self.reader_factory = inventory, reader
        self.window, self.binary = window, binary
        self.commit, self.ffb_save, self.clear, self.ffb_load = commit, ffb_save, clear, ffb_load
        self.supported = supported
        self.reader = None
        self.mode = 'closed'
        self.error = self.message = ''
        self.role = None
        self.records = {}
        self.original = None
        self.devices = []
        self.device = None
        self.axis = None
        self.draft = None
        self.proposal = None
        self.selected = 1
        self.now = self.deadline = 0.
        self.samples = deque()
        self.baseline = None
        self.last = None
        self.neutral_frames = 0
        self.ffb = dict(mode='steering', identity=None)
        self.ffb_proposal = None
        self.invert = False
        self.deadzone = 0.
        self._last_frame = -1
        self.release_rest = None
        self.saved = False
        self.ready_native = False

    def _close_reader(self):
        reader, self.reader = self.reader, None
        if reader is not None:
            reader.close()
        self.last = None

    def open(self, role, now):
        if role not in (*ROLES, 'ffb'):
            raise ValueError('Unsupported control role')
        self._close_reader()
        self.role, self.now = role, now
        self.error = self.message = ''
        self.proposal = self.ffb_proposal = self.draft = None
        self.device = self.axis = self.baseline = None
        self.release_rest = None
        self.saved = False
        self.original = None
        self.ready_native = False
        self.selected = 1
        self.samples.clear()
        self.deadline = now + TIMEOUT
        try:
            self.original = self.path.read_bytes() if self.path.exists() else None
            self.records = preferences.load_records(self.path)
            if role == 'ffb':
                try:
                    self.ffb = self.ffb_load(self.path)
                except (ValueError, KeyError) as error:
                    self.ffb = dict(mode='invalid', identity=None)
                    self.error = str(error)+' Choose a replacement explicitly or Cancel.'
            self.ready_native = self.supported(self.binary)
            self.refresh()
            if role == 'ffb':
                self.mode = 'ffb'
            elif role in self.records:
                record = self.records[role]
                result = preferences.resolve_device(record['identity'], self.devices)
                self.mode = 'role'
                if result['device'] is not None:
                    self.device = result['device']
                    self.axis = record['axis']
                    calibration = record.get('calibration')
                    if calibration:
                        self.release_rest = calibration.get('centre', calibration.get('released'))
                    self._read_selected()
                else:
                    self.error = 'Saved device ' + result['status'] + '. Refresh or Bind a replacement.'
            else:
                self.mode = 'devices'
        except (OSError, ValueError, KeyError, configparser.Error) as error:
            self.mode = 'error'
            self.error = str(error)
        self.focus_action()
        return self

    def focus_action(self):
        passive = {'header', 'status', 'device', 'axis', 'preview', 'current', 'choice', 'waiting'}
        self.selected = next((i for i, row in enumerate(self.rows()) if row[0] not in passive), 1)

    def refresh(self):
        self._close_reader()
        self.devices = list(self.inventory_provider())
        # Reject malformed rows rather than display/select a misleading index.
        for device in self.devices:
            preferences.canonical_identity(device['identity'])
            if any(axis not in preferences.AXES for axis in device.get('axes', ())):
                raise ValueError('Device reported an unsupported axis.')
        self.message = 'No devices found. Connect hardware, then Refresh.' if not self.devices else ''

    def _read_selected(self):
        self._close_reader()
        resolved = preferences.resolve_device(self.device['identity'], self.devices)
        if resolved['device'] is None or self.axis not in resolved['device'].get('axes', ()):
            raise ValueError('Selected device or axis is missing or ambiguous. Refresh and select it explicitly.')
        self.device = resolved['device']
        self.reader = self.reader_factory(self.device, self.window)
        self.baseline = None
        self.samples.clear()

    def _save_calibration(self):
        if self.reader is None or self.last is None:
            raise ValueError('Wait for a current device preview, or Cancel and reconnect before saving.')
        if not self._neutral():
            raise ValueError('Return the control to rest and release device buttons before saving.')
        # Inventory and a live reader must never own DirectInput concurrently.
        # Restore this exact reader afterwards for both Retry and release gating.
        baseline = self.baseline
        self._close_reader()
        try:
            current = list(self.inventory_provider())
            self.devices = current
            result = self.commit(self.path, [self.proposal], expected_original=self.original, inventory=current)
            self.records = result['records']
            self.saved = True
        finally:
            try:
                self._read_selected()
                self.baseline = baseline
            except (OSError, ValueError, KeyError):
                # A committed save is still a save if the preview cannot reopen.
                # No fallback device or background reacquisition is attempted.
                self._close_reader()
        self.cancel('Calibration saved for the next launch. Game input still needs verification.')

    def _start_calibration(self):
        self._read_selected()
        self.draft = preferences.CalibrationDraft(self.role, self.device['identity'], self.axis,
            'steering' if self.role == 'steer' else 'pedal', original=self.records.get(self.role))
        old = self.records.get(self.role, {}).get('calibration') or {}
        self.invert, self.deadzone = old.get('invert', False), old.get('deadzone', 0.)
        self.proposal = None
        self.release_rest = None
        self.mode = 'capture'
        self.deadline = self.now + TIMEOUT
        self.error = ''

    def _calibration(self):
        if self.proposal is not None:
            return self.proposal['record']['calibration']
        if self.draft is not None:
            return None
        return self.records.get(self.role, {}).get('calibration')

    def _make_proposal(self):
        self.proposal = self.draft.proposal(invert=self.invert, deadzone=self.deadzone)
        self.proposal['record']['identity']['display_name'] = self.device.get('name', 'Device')

    def _neutral(self):
        if self.last is None:
            return self.reader is None
        if any(self.last['buttons']):
            return False
        for axis, value in self.last['axes'].items():
            if axis == self.axis and self.release_rest is not None:
                if abs(value-self.release_rest) > .10:
                    return False
            elif self.baseline is not None and abs(value-self.baseline[axis]) > .10:
                return False
        return True

    def tick(self, now, *, focused=True, external_held=False, frame=0):
        self.now = now
        if self.mode == 'closed':
            return
        if not focused:
            self.cancel('Focus lost; '+('saved change retained.' if self.saved else 'previous assignment retained.'))
            self._close_reader()
        elif self.mode == 'capture' and now >= self.deadline:
            self.cancel('Calibration timed out; previous assignment retained.')
        if self.reader is not None:
            try:
                sample = self.reader.sample()
                if sample is None:
                    raise ValueError('Device disconnected. Reopen and Refresh.')
                axes = sample['axes']
                if self.axis not in axes or any(not isinstance(v, (int, float)) or not math.isfinite(v) or not -1 <= v <= 1 for v in axes.values()):
                    raise ValueError('Device input is unavailable; previous assignment retained.')
                if self.baseline is None:
                    self.baseline = dict(axes)
                if set(axes) != set(self.baseline):
                    raise ValueError('Device axis layout changed; select the device again.')
                self.last = sample
                self.samples.append((now, dict(axes)))
                while len(self.samples) > 1 and now-self.samples[1][0] >= STABLE_SECONDS:
                    self.samples.popleft()
            except (OSError, ValueError, KeyError) as error:
                self.cancel(str(error)+' '+('Saved change retained.' if self.saved else 'Previous assignment retained.'))
                self._close_reader()
        if self.mode == 'closing':
            if frame == self._last_frame:
                return
            consecutive = frame == self._last_frame+1
            self._last_frame = frame
            neutral = focused and not external_held and self._neutral()
            self.neutral_frames = (self.neutral_frames+1 if consecutive else 1) if neutral else 0
            if self.neutral_frames >= 2:
                self._close_reader()
                self.mode = 'closed'

    def capture(self):
        if self.mode != 'capture' or self.last is None:
            raise ValueError('Wait for a current device sample.')
        if len(self.samples) < 3 or self.now-self.samples[0][0] < STABLE_SECONDS:
            raise ValueError('Hold this position steadily for a moment, then Capture.')
        if any(self.last['buttons']):
            raise ValueError('Release device buttons; move only the requested axis.')
        values = [axes[self.axis] for _, axes in self.samples]
        if max(values)-min(values) > STABLE_RANGE:
            raise ValueError('The axis is still moving. Hold steadily, then Capture.')
        # Do not accept one chosen axis while another also moves away from rest.
        if any(abs(value-self.baseline[axis]) > OTHER_MOVEMENT for axis, value in self.last['axes'].items() if axis != self.axis):
            raise ValueError('More than one control moved. Return other controls to rest and retry.')
        step = self.draft.steps[len(self.draft.samples)]
        self.draft.capture(step, sum(values)/len(values), self.device['identity'])
        if step in ('centre', 'released'):
            self.release_rest = self.draft.samples[step]
        self.samples.clear()
        self.error = ''
        self.deadline = self.now + TIMEOUT
        if self.draft.status == 'ready':
            self._make_proposal()
            self.mode = 'review'

    def cancel(self, message='Cancelled; previous saved assignment retained.'):
        if self.draft is not None:
            self.draft.cancel()
        self.message, self.error = message, ''
        self.mode = 'closing'
        self.neutral_frames = 0
        # Keep the completed calibration only for neutral checking, never save it.
        self._last_frame = -1

    def close(self):
        """Window shutdown: discard proposals and deterministically close COM."""
        self._close_reader()
        self.mode = 'closed'

    def activate(self, action):
        self.error = ''
        previous_mode = self.mode
        try:
            if action in ('cancel', 'back'):
                self.cancel()
            elif action == 'reopen':
                self.open(self.role, self.now)
            elif action == 'refresh':
                self.refresh()
                self.mode = 'ffb' if self.role == 'ffb' else 'devices'
            elif action == 'bind':
                self._close_reader(); self.mode = 'devices'
            elif action.startswith('device:'):
                self.device = deepcopy(self.devices[int(action.split(':')[1])])
                self.mode = 'axes'
            elif action.startswith('axis:'):
                self.axis = action.split(':')[1]
                self._start_calibration()
            elif action == 'calibrate':
                self._start_calibration()
            elif action == 'capture':
                self.capture()
            elif action == 'invert':
                self.invert = not self.invert
                self._make_proposal()
            elif action == 'deadzone' or action.startswith('deadzone:'):
                change = .01 if action == 'deadzone' else float(action.split(':')[1])
                # Preserve a saved value above the normal UI ceiling when + is
                # pressed; reducing a custom value must remain a deliberate -.
                self.deadzone = (max(self.deadzone, min(.99, round(self.deadzone+change, 4))) if change > 0
                                 else max(0., round(self.deadzone+change, 4)))
                self._make_proposal()
            elif action == 'clear':
                self.mode = 'clear'
            elif action == 'save_clear':
                self.clear(self.path, self.role, expected_original=self.original)
                self.saved = True
                self.cancel('Assignment cleared. Other roles and tuning retained.')
            elif action == 'save':
                self._save_calibration()
            elif action == 'follow':
                self.ffb_proposal = dict(mode='steering', identity=None)
                self.mode = 'ffb_review'
            elif action.startswith('ffb:'):
                identity = self.devices[int(action.split(':')[1])]['identity']
                if not preferences.output_path(preferences.resolve_device(identity, self.devices)):
                    raise ValueError('This device has no verified output path; choose another device.')
                self.ffb_proposal = dict(mode='explicit', identity=deepcopy(identity))
                self.mode = 'ffb_review'
            elif action == 'save_ffb':
                current = list(self.inventory_provider())
                self.ffb = self.ffb_save(self.path, **self.ffb_proposal, expected_original=self.original, inventory=current)
                self.saved = True
                self.cancel('FFB device saved for the next launch. FFB On/Off and strength retained.')
            if previous_mode != self.mode:
                self.focus_action()
        except (OSError, ValueError, KeyError, IndexError, configparser.Error) as error:
            self.error = str(error) + ' Previous saved values retained.'
            if action in ('save', 'save_clear', 'save_ffb'):
                self.retry = action
                self.mode = 'save_error'
                self.focus_action()

    def rows(self):
        """Actual renderer rows; safe for CPU-only layout fixtures."""
        title = 'FFB device' if self.role == 'ffb' else ROLES.get(self.role, 'Controls')
        rows = [('header', title, 'Finish or cancel to change view', '')]
        def add(key, label, value='', hint=''):
            rows.append((key, label, value, hint))
        status = 'Native adapter supported' if getattr(self, 'ready_native', False) else 'Native support pending'
        add('status', 'Next launch', status, 'Saved preferences only. Device preview is not verified game input. No force output runs here.')
        if self.mode == 'devices':
            for i, device in enumerate(self.devices):
                add(f'device:{i}', device_label(device), 'Choose', device_label(device)+': select for '+title+'. Other roles remain independent.')
            add('refresh', 'Refresh devices')
        elif self.mode == 'axes':
            for axis in self.device.get('axes', ()):
                add('axis:'+axis, axis, 'Choose', device_label(self.device)+' / choose one axis to calibrate.')
            add('bind', 'Choose another device')
        elif self.mode in ('role', 'capture', 'review'):
            add('device', 'Device', device_label(self.device) if self.device else 'Missing', record_label(self.records.get(self.role)))
            add('axis', 'Axis', self.axis or 'Not available')
            raw = self.last['axes'].get(self.axis) if self.last else None
            add('preview', 'Device preview', preview_text(self.role, raw, self._calibration()), 'Device raw / calibrated input only; native final input remains unverified.')
            if self.mode == 'role':
                add('bind', 'Bind', 'Choose device / axis')
                if self.device is not None: add('calibrate', 'Calibrate')
                add('clear', 'Clear', 'Review before saving')
                add('refresh', 'Refresh devices')
            elif self.mode == 'capture':
                step = self.draft.steps[len(self.draft.samples)]
                instruction = {'centre':'Centre steering and hold', 'left':'Turn fully left and hold', 'right':'Turn fully right and hold',
                               'released':'Release pedal and hold', 'full':'Press fully and hold', 'return':'Return to centre' if self.role == 'steer' else 'Release pedal again'}[step]
                add('capture', instruction, 'Capture', 'Move only this control. Hold steady, then choose Capture. Esc cancels; 90 seconds per step.')
                add('calibrate', 'Restart calibration', 'Discard this draft')
            else:
                add('invert', 'Invert', 'On' if self.invert else 'Off', 'Endpoint direction is automatic. Invert explicitly reverses the normalized result.')
                add('deadzone', 'Deadzone', f'{self.deadzone*100:g}%', 'Left / right changes 1%; Enter increases. Applied once after calibration; other steering tuning is retained.')
                add('save', 'Save calibration', 'Save', 'Saves device, axis and endpoints together; other controls remain unchanged.')
        elif self.mode == 'clear':
            add('save_clear', 'Clear '+title, 'Save clear', 'Removes this role including its legacy fallback. Other roles stay saved.')
        elif self.mode == 'ffb':
            current = 'Invalid saved choice' if self.ffb['mode'] == 'invalid' else 'Use steering wheel'
            if self.ffb['mode'] == 'explicit':
                match = preferences.resolve_device(self.ffb['identity'], self.devices)
                current = (device_label(match['device']) if match['device'] else
                           '['+self.ffb['identity']['instance_guid'][:8]+'] '+match['status'])
            add('current', 'Saved choice', current, current+'. A missing explicit device never falls back to another wheel.')
            steering = self.records.get('steer')
            match = preferences.resolve_device(steering['identity'], self.devices) if steering else {'status':'unbound', 'device':None}
            path = preferences.output_path(match)
            add('follow', 'Use steering wheel', 'Choose', record_label(steering)+(' / output path available; runtime unverified' if path else ' / bind Steering or refresh its output identity'))
            for i, device in enumerate(self.devices):
                if preferences.output_path(preferences.resolve_device(device['identity'], self.devices)):
                    add(f'ffb:{i}', device_label(device), 'Choose', device_label(device)+': explicit output device; runtime force capability remains unverified.')
            add('refresh', 'Refresh devices')
        elif self.mode == 'ffb_review':
            add('choice', 'New choice', 'Use steering wheel' if self.ffb_proposal['mode'] == 'steering' else self.ffb_proposal['identity']['instance_guid'][:8])
            add('save_ffb', 'Save FFB device', 'Save', 'Preserves saved Off, strength, tunes and all input assignments.')
        elif self.mode == 'save_error':
            add(self.retry, 'Retry save', 'Retry', self.error)
        elif self.mode == 'error':
            add('reopen', 'Retry opening setup', 'Retry', self.error)
        elif self.mode == 'closing':
            add('waiting', 'Release controls', 'Waiting', self.message+' Release keys, buttons, pedals and steering to continue.')
        if self.mode not in ('closing', 'closed'):
            add('cancel', 'Cancel', 'Keep saved values')
        return rows
