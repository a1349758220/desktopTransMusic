"""
Mini Player — 400×50 frameless semi-transparent music bar.
Always on top, Windows only.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.mini_bar import MiniBar


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = MiniBar()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
