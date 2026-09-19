"""DirectInput identity-property bridge, using fake COM calls only."""
import ctypes
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
import dinput_axes as d


class IdentityTests(unittest.TestCase):
    def test_guid_byte_order_and_identity_properties(self):
        guid = '00112233-4455-6677-8899-AABBCCDDEEFF'
        self.assertEqual(d.GUID.from_str(guid).text(), guid)
        calls = []
        def method(device, slot, restype, *types):
            calls.append(slot)
            if slot == 5:
                def read(_device, property_id, header):
                    self.assertEqual(property_id.value, 12)
                    value = ctypes.cast(header, ctypes.POINTER(d.DIPROPGUIDANDPATH)).contents
                    self.assertEqual(value.diph.dwSize, ctypes.sizeof(d.DIPROPGUIDANDPATH))
                    self.assertEqual(value.diph.dwHeaderSize, ctypes.sizeof(d.DIPROPHEADER))
                    value.wszPath = '\\\\?\\hid#mixed'
                    return 0
                return read
            self.assertEqual(slot, 3)  # Capabilities, never an effect/acquire method.
            def caps(_device, pointer):
                ctypes.cast(pointer, ctypes.POINTER(d.DIDEVCAPS)).contents.dwFlags = 0x100
                return 0
            return caps
        with patch.object(d, '_method', side_effect=method):
            self.assertEqual(d.device_metadata(123), dict(hid_path='\\\\?\\HID#MIXED', ffb_capable=True))
        self.assertEqual(calls, [5, 3])

    def test_missing_properties_are_not_name_or_capability_proof(self):
        with patch.object(d, '_method', return_value=lambda *args: -1):
            self.assertEqual(d.device_metadata(123), dict(hid_path=None, ffb_capable=None))

    def test_legacy_layout_remains_separate_from_instance_inventory(self):
        records = [dict(name='Twin', instance_guid='one', axes=['YAXIS']),
                   dict(name='Twin', instance_guid='two', axes=['ZAXIS'])]
        with patch.object(d, 'inventory', return_value=records):
            self.assertEqual(d.layout(), {'Twin': ['YAXIS']})
        self.assertEqual(len(records), 2)  # New consumers receive both instances.


if __name__ == '__main__':
    unittest.main()
