import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from check_centered_display_capture import inspect


class CenteredDisplayCaptureTests(unittest.TestCase):
    def test_exact_center_and_black_bars(self):
        with tempfile.TemporaryDirectory() as directory:
            narrow = Path(directory) / 'n.bmp'
            wide = Path(directory) / 'w.bmp'
            Image.new('RGB', (4, 2), (10, 20, 30)).save(narrow)
            image = Image.new('RGB', (8, 2))
            image.paste(Image.open(narrow), (2, 0))
            image.save(wide)
            result = inspect(narrow, wide)
            self.assertTrue(result['passed'])
            self.assertEqual(result['side_bar_width'], 2)

    def test_rejects_changed_content_or_side_bar(self):
        with tempfile.TemporaryDirectory() as directory:
            narrow = Path(directory) / 'n.bmp'
            wide = Path(directory) / 'w.bmp'
            Image.new('RGB', (4, 2), (10, 20, 30)).save(narrow)
            image = Image.new('RGB', (8, 2))
            image.paste(Image.open(narrow), (2, 0))
            image.putpixel((2, 0), (1, 2, 3))
            image.putpixel((0, 0), (1, 2, 3))
            image.save(wide)
            result = inspect(narrow, wide)
            self.assertFalse(result['passed'])
            self.assertFalse(result['center_exact'])
            self.assertFalse(result['left_bar_black'])
            self.assertTrue(result['right_bar_black'])


if __name__ == '__main__':
    unittest.main()
