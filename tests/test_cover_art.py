import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktopTransMusic" / "mini_player"))

from core.player import _read_cover_art


MUSIC_DIR = Path(r"C:\Users\Suen ZtaYrua\Desktop\music")


class CoverArtTests(unittest.TestCase):
    def test_read_cover_art_returns_bytes_for_embedded_cover(self):
        cover_file = MUSIC_DIR / "一万个舍不得 - 庄心妍&祁隆.mp3"

        cover = _read_cover_art(str(cover_file))

        self.assertIsInstance(cover, bytes)
        self.assertGreater(len(cover), 100)

    def test_read_cover_art_returns_none_without_embedded_cover(self):
        no_cover_file = MUSIC_DIR / "追梦赤子心-GALA.mp3"

        cover = _read_cover_art(str(no_cover_file))

        self.assertIsNone(cover)


if __name__ == "__main__":
    unittest.main()
