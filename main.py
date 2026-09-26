"""
main.py — Entry point.

Creates the QApplication, applies the initial theme, and shows Landing.
"""

import sys

from PyQt6.QtWidgets import QApplication

from landing import Landing


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Moxie")
    app.setOrganizationName("Moxie")

    window = Landing()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()