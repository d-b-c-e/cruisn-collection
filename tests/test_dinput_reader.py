import ctypes
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
import dinput_reader as reader


class ReaderTests(unittest.TestCase):
    def test_fixed_state_layout_and_ranges(self):
        self.assertEqual(ctypes.sizeof(reader.State), 272)
        self.assertEqual(reader.State.buttons.offset, 48)
        fmt, objects, guids = reader.data_format()
        self.assertEqual((fmt.count, fmt.data_size), (140, 272))
        self.assertEqual([objects[i].offset for i in range(8)], list(range(0, 32, 4)))
        self.assertEqual(objects[139].offset, 175)
        self.assertEqual([reader.normalized(v, 0, 65535) for v in (0, 32767.5, 65535)], [-1, 0, 1])
        self.assertEqual(reader.normalized(99999, 0, 65535), 1)
        for lo, hi in ((0, 0), (5, -5), (0, float('nan'))):
            with self.assertRaises(ValueError):
                reader.normalized(0, lo, hi)

    def make_reader(self):
        r = reader.Reader.__new__(reader.Reader)
        r.api, r.device = 10, 20
        r.instance = reader.di.GUID.from_str('00112233-4455-6677-8899-AABBCCDDEEFF')
        r.ranges = {'YAXIS': (1, 0, 1000)}
        return r

    def test_exact_axis_and_high_buttons_without_effect_api(self):
        r = self.make_reader()
        methods = []
        def method(device, slot, *args):
            methods.append((device, slot))
            if slot == 9:
                def read(_device, size, pointer):
                    state = ctypes.cast(pointer, ctypes.POINTER(reader.State)).contents
                    state.axes[1] = 750
                    state.buttons[100] = 0x80
                    return 0
                return read
            return lambda *args: 0
        with patch.object(reader.di, '_method', side_effect=method):
            value = r.sample()
        self.assertEqual(value['axes'], {'YAXIS': .5})
        self.assertEqual([i for i, v in enumerate(value['buttons']) if v], [100])
        self.assertEqual(methods, [(10, 5), (20, 25), (20, 9)])

    def test_disconnect_or_failed_read_clears_reader_and_does_not_reselect(self):
        for failing in ((10, 5), (20, 25), (20, 9)):
            with self.subTest(failing=failing):
                r = self.make_reader()
                methods = []
                def method(device, slot, *args):
                    methods.append((device, slot))
                    return lambda *args: -1 if (device, slot) == failing else 0
                with patch.object(reader.di, '_method', side_effect=method):
                    self.assertIsNone(r.sample())
                    count = len(methods)
                    self.assertIsNone(r.sample())
                    self.assertEqual(len(methods), count)
                self.assertIsNone(r.device)
                self.assertIsNone(r.api)
                self.assertEqual(r.ranges, {})
                self.assertEqual(methods[-3:], [(20, 8), (20, 2), (10, 2)])
                self.assertNotIn((10, 3), methods)  # No replacement CreateDevice.


if __name__ == '__main__':
    unittest.main()
