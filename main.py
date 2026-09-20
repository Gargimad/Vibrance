import sys
from PyQt6.QtWidgets import QApplication
from landing import Landing
from volunteerRegister import VolunteerRegistration
from db import Database

import sys
from PyQt6.QtWidgets import QApplication
from landing import Landing

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Landing()
    window.show()
    sys.exit(app.exec())