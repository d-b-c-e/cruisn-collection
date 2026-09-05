import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from verification import compare_arrays, frame_numbers, image_signature, validate_snapshots


class AcceptanceTests(unittest.TestCase):
    def test_one_wrong_pixel_fails_and_channels_count_once(self):
        ref = np.zeros((2, 3, 3), np.uint8)
        actual = ref.copy()
        actual[1, 2] = (255, 3, 9)
        report = compare_arrays(actual, ref)
        self.assertFalse(report["passed"])
        self.assertEqual(report["differing_pixels"], 1)
        self.assertEqual(report["max_error"], 255)

    def test_unsigned_difference_does_not_wrap(self):
        self.assertEqual(compare_arrays(np.array([[0]], np.uint8),
                                        np.array([[255]], np.uint8))["max_error"], 255)

    def test_explicit_tolerance_and_budget(self):
        ref = np.zeros((1, 3), np.uint32)
        actual = np.array([[0, 1, 10]], np.uint32)
        self.assertFalse(compare_arrays(actual, ref, tolerance=1)["passed"])
        self.assertTrue(compare_arrays(actual, ref, tolerance=1, max_mismatches=1)["passed"])

    def test_bad_dimensions_and_frames_rejected(self):
        for values in ("", "1,1", "2,1", "0,1", "1,no", "-1,2"):
            with self.assertRaises(ValueError):
                frame_numbers(values)
        with self.assertRaises(ValueError):
            compare_arrays(np.zeros((1, 2)), np.zeros((2, 1)))
        self.assertEqual(frame_numbers("1, 20, 300"), [1, 20, 300])

    def test_matching_partial_runs_are_not_successful(self):
        with tempfile.TemporaryDirectory() as td:
            Image.new("RGB", (2, 2)).save(Path(td) / "frame_00000010.png")
            with self.assertRaisesRegex(ValueError, "receipts"):
                validate_snapshots(td, [10, 20], 0, [10])
            with self.assertRaisesRegex(ValueError, "manifest"):
                validate_snapshots(td, [10, 20], 0, [10, 20])
            with self.assertRaisesRegex(ValueError, "exit code"):
                validate_snapshots(td, [10], 1, [10])
            self.assertEqual(list(validate_snapshots(td, [10], 0, [10])), ["10"])

    def test_same_pixel_bytes_different_dimensions_are_different(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a.png", Path(td) / "b.png"
            Image.new("RGB", (1, 4)).save(a)
            Image.new("RGB", (2, 2)).save(b)
            self.assertNotEqual(image_signature(a), image_signature(b))


if __name__ == "__main__":
    unittest.main()
