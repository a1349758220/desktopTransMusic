import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktopTransMusic" / "mini_player"))

from PySide6.QtWidgets import QApplication
from ui.mini_bar import VinylRecordWidget


class VinylRecordWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_set_playing_controls_animation_timer(self):
        widget = VinylRecordWidget()

        widget.set_playing(True)
        self.assertTrue(widget._rotation_timer.isActive())

        widget.set_playing(False)
        self.assertFalse(widget._rotation_timer.isActive())

    def test_set_cover_bytes_none_clears_cover(self):
        widget = VinylRecordWidget()

        widget.set_cover_bytes(None)

        self.assertIsNone(widget._cover_pixmap)

    def test_vinyl_widget_has_expected_fixed_size(self):
        widget = VinylRecordWidget()

        self.assertEqual(widget.width(), 42)
        self.assertEqual(widget.height(), 44)


if __name__ == "__main__":
    unittest.main()
