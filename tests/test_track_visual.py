import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktopTransMusic" / "mini_player"))

from core.player import MusicPlayer


class PlayerTrackVisualSignalTests(unittest.TestCase):
    def test_player_exposes_track_visual_changed_signal(self):
        self.assertTrue(hasattr(MusicPlayer, "track_visual_changed"))

    def test_player_no_longer_exposes_cover_changed_signal(self):
        self.assertFalse(hasattr(MusicPlayer, "cover_changed"))


if __name__ == "__main__":
    unittest.main()
