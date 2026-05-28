import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktopTransMusic" / "mini_player"))

from PySide6.QtWidgets import QApplication
from ui.mini_bar import MINI_HEIGHT, MINI_WIDTH, MiniBar, VinylRecordWidget


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


class DummySignal:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback


class DummyPlayer:
    def __init__(self):
        self.position_changed = DummySignal()
        self.duration_changed = DummySignal()
        self.track_changed = DummySignal()
        self.cover_changed = DummySignal()
        self.playback_state_changed = DummySignal()
        self.repeat_mode_changed = DummySignal()

    def prev(self):
        pass

    def next(self):
        pass

    def set_volume(self, value):
        pass


class MiniBarVinylIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_mini_bar_keeps_400_by_50(self):
        self.assertEqual(MINI_WIDTH, 400)
        self.assertEqual(MINI_HEIGHT, 50)

    def test_build_ui_creates_record_widget_first(self):
        original_setup_tray = MiniBar._setup_tray
        MiniBar._setup_tray = lambda self: None
        try:
            bar = MiniBar(DummyPlayer())
        finally:
            MiniBar._setup_tray = original_setup_tray

        self.assertIsInstance(bar._vinyl_widget, VinylRecordWidget)
        self.assertIs(bar.layout().itemAt(0).widget(), bar._vinyl_widget)


if __name__ == "__main__":
    unittest.main()
