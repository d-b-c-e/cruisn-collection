"""Launch boundary tests use synthetic identities/files only; no devices/game."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
import control_launch as L
import control_preferences as C

IDENTITY = dict(backend='dinput', product_guid='0006346e-0000-0000-0000-504944564944',
                instance_guid='11111111-2222-3333-4444-555555555555', hid_path=r'\\?\HID#FIXTURE', ffb_capable=True)
DEVICE = dict(identity=IDENTITY, name='Wheel', axes=['XAXIS', 'ZAXIS'])
CAL = dict(version=1, kind='steering', left=-.8, centre=.1, right=.9, invert=False, deadzone=.05)
TABLES = {'default': {'steer': (['P1_PADDLE'], None), 'gas': (['P1_PEDAL'], None)},
          'crusnexo': {'steer': (['P1_AD_STICK_X'], None), 'gas': (['P1_AD_STICK_Y'], None)}}


def tree():
    return ET.ElementTree(ET.fromstring('''<mameconfig><system name="default"><input>
      <mapdevice device="Wheel" controller="JOYCODE_1"/>
      <mapdevice device="Shifter" controller="JOYCODE_2"/>
      <port type="START1"><newseq type="standard">JOYCODE_1_BUTTON1 OR KEYCODE_1</newseq></port>
      <port type="P1_PADDLE"><newseq type="standard">JOYCODE_2_XAXIS</newseq></port>
      </input></system><system name="crusnusa"><input><port type="P1_PADDLE"><newseq>OLD</newseq></port>
      </input></system></mameconfig>'''))


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'collection.ini'
        self.original = b'[collection]\nffb_enabled = 0\nffb = 63\nffb_profile = owner@2\nUnknownCase = Stay\n[wheelmap]\nsteer = Wheel|axis:0:0\nstart = Wheel|btn:0\n'
        self.path.write_bytes(self.original)

    def save_control(self, role='steer', cal=CAL, axis='XAXIS'):
        C.commit_proposals(self.path, [C.make_proposal(role, IDENTITY, axis, cal)],
                           expected_original=self.path.read_bytes(), inventory=[DEVICE])

    def test_ffb_save_preserves_off_tunes_unknown_and_rejects_stale_edit(self):
        selected = L.save_ffb_selection(self.path, 'explicit', IDENTITY,
                                       expected_original=self.original, inventory=[DEVICE])
        self.assertEqual(selected, L.load_ffb_selection(self.path))
        self.assertEqual(L.resolve_output(self.path, [DEVICE]), 'path:'+IDENTITY['hid_path'])
        text = self.path.read_text(encoding='utf-8')
        for value in ('ffb_enabled = 0', 'ffb = 63', 'ffb_profile = owner@2', 'UnknownCase = Stay'):
            self.assertIn(value, text)
        self.assertEqual(next(self.path.parent.glob('*.bak')).read_bytes(), self.original)
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            L.save_ffb_selection(self.path, 'steering', expected_original=self.original, inventory=[])
        self.assertEqual(self.path.read_bytes(), before)
        L.save_ffb_selection(self.path, 'steering', expected_original=before, inventory=[])
        self.assertEqual(L.load_ffb_selection(self.path), dict(mode='steering', identity=None))
        self.assertNotIn('ffb_device_identity', self.path.read_text(encoding='utf-8'))

    def test_unresolved_output_and_failed_replace_never_adopt(self):
        for inventory in ([], [DEVICE, DEVICE], [{**DEVICE, 'identity': {**IDENTITY, 'ffb_capable': False}}]):
            with self.assertRaises(ValueError):
                L.save_ffb_selection(self.path, 'explicit', IDENTITY,
                                     expected_original=self.original, inventory=inventory)
            self.assertEqual(self.path.read_bytes(), self.original)
        with mock.patch('control_launch.os.replace', side_effect=OSError('fixture disk failure')):
            with self.assertRaises(OSError):
                L.save_ffb_selection(self.path, 'explicit', IDENTITY,
                                     expected_original=self.original, inventory=[DEVICE])
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertFalse(list(self.path.parent.glob('*.tmp')))

    def test_clear_disables_inherited_axis_then_new_and_legacy_binds_supersede(self):
        self.save_control()
        L.clear_control_selection(self.path, 'steer', expected_original=self.path.read_bytes())
        self.assertEqual(C.load_records(self.path), {})
        data = tree()
        self.assertIsNone(L.apply_controls(data, self.path, [], TABLES))
        self.assertEqual(data.find("system[@name='default']/input/port[@type='P1_PADDLE']/newseq").text, 'NONE')
        self.assertIsNone(data.find("system[@name='crusnusa']/input/port[@type='P1_PADDLE']"))
        self.save_control()
        data = tree()
        L.apply_controls(data, self.path, [DEVICE], TABLES)
        self.assertEqual(data.find("system[@name='default']/input/port[@type='P1_PADDLE']/newseq").text, 'JOYCODE_1_XAXIS')
        L.save_legacy_bindings(self.path, {'steer': 'KEYBOARD|key:KEYCODE_LEFT'})
        self.assertEqual(C.load_records(self.path), {})
        self.assertNotIn('steer = 1', self.path.read_text(encoding='utf-8'))
        self.assertIn('start = Wheel|btn:0', self.path.read_text(encoding='utf-8'))

    def test_native_overlay_retains_button_slot_and_has_no_double_axis_transform(self):
        self.save_control()
        pedal = dict(version=1, kind='pedal', released=.2, full=1., invert=False, deadzone=.1)
        self.save_control('gas', pedal, 'ZAXIS')
        data = tree()
        profile = L.apply_controls(data, self.path, [DEVICE], TABLES)
        self.assertEqual(len(profile.splitlines()), 3)
        self.assertIn('|XAXIS|steering|-0.8|0.1|0.9|0|0.05', profile)
        inp = data.find("system[@name='default']/input")
        self.assertTrue(inp.find('mapdevice').get('device').startswith('strict-dinput:'))
        self.assertEqual(inp.find("port[@type='START1']/newseq").text, 'JOYCODE_1_BUTTON1 OR KEYCODE_1')
        self.assertEqual(inp.find("port[@type='P1_PEDAL']/newseq").text, 'JOYCODE_1_ZAXIS')
        self.assertEqual(data.find("system[@name='crusnexo']/input/port[@type='P1_AD_STICK_Y']/newseq").text, 'JOYCODE_1_ZAXIS')
        self.assertEqual(L.resolve_output(self.path, [DEVICE]), 'path:'+IDENTITY['hid_path'])
        self.assertIsNone(L.resolve_output(self.path, []))

    def test_missing_twins_axis_conflicts_fail_before_launch(self):
        self.save_control()
        for inventory in ([], [DEVICE, DEVICE], [{**DEVICE, 'axes': []}]):
            with self.assertRaises(ValueError):
                L.apply_controls(tree(), self.path, inventory, TABLES)
        pedal = dict(version=1, kind='pedal', released=-1., full=1., invert=False, deadzone=0.)
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'two different calibrations'):
            self.save_control('gas', pedal, 'XAXIS')
        self.assertEqual(self.path.read_bytes(), before)
        # Independently reject a conflicting file written outside the editor.
        cp = L._parse(before)
        cp.add_section('control:gas')
        cp.set('control:gas', 'record', json.dumps(C.make_proposal('gas', IDENTITY, 'XAXIS', pedal)['record']))
        with self.path.open('w', encoding='utf-8') as stream:
            cp.write(stream)
        with self.assertRaisesRegex(ValueError, 'two different calibrations'):
            L.apply_controls(tree(), self.path, [DEVICE], TABLES)

    def test_capability_receipt_is_bound_to_binary_bytes(self):
        binary = self.path.parent/'vunit.exe'
        binary.write_bytes(b'fixture native bytes')
        self.assertFalse(L.supported(binary))
        receipt = Path(str(binary)+'.features.json')
        receipt.write_text(json.dumps(dict(version=1, features=sorted(L.FEATURES),
                  sha256=hashlib.sha256(binary.read_bytes()).hexdigest())), encoding='utf-8')
        self.assertTrue(L.supported(binary))
        binary.write_bytes(b'other native bytes!!')
        self.assertFalse(L.supported(binary))
        receipt.write_text('{}', encoding='utf-8')
        self.assertFalse(L.supported(binary))


if __name__ == '__main__':
    unittest.main()
