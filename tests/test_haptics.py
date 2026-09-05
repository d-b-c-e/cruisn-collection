import ctypes
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from haptics import stop_all


class HapticsTests(unittest.TestCase):
    def fake(self):
        return SimpleNamespace(SDL_Init=Mock(return_value=0),
            SDL_NumHaptics=Mock(return_value=2),
            SDL_HapticOpen=Mock(side_effect=[0x123456789ABC, None]),
            SDL_HapticStopAll=Mock(return_value=0),
            SDL_HapticClose=Mock(), SDL_Quit=Mock())

    def test_x64_handle_preserved_and_success_acknowledged(self):
        sdl = self.fake()
        self.assertEqual(stop_all("unused", loader=lambda _: sdl), 1)
        self.assertIs(sdl.SDL_HapticOpen.restype, ctypes.c_void_p)
        self.assertEqual(sdl.SDL_HapticStopAll.argtypes, [ctypes.c_void_p])
        sdl.SDL_HapticStopAll.assert_called_once_with(0x123456789ABC)
        sdl.SDL_HapticClose.assert_called_once_with(0x123456789ABC)
        sdl.SDL_Quit.assert_called_once()

    def test_stop_failure_does_not_report_success_and_still_closes(self):
        sdl = self.fake()
        sdl.SDL_HapticStopAll.return_value = -1
        self.assertEqual(stop_all("unused", loader=lambda _: sdl), 0)
        sdl.SDL_HapticClose.assert_called_once()
        sdl.SDL_Quit.assert_called_once()

    def test_partial_init_failure_unwinds(self):
        sdl = self.fake()
        sdl.SDL_Init.return_value = -1
        self.assertEqual(stop_all("unused", loader=lambda _: sdl), 0)
        sdl.SDL_HapticOpen.assert_not_called()
        sdl.SDL_Quit.assert_called_once()
