import sys
from PyQt6.QtWidgets import QApplication
from landing import Landing

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Instantiate and display the main window
    window = Landing()
    window.show()
    
    sys.exit(app.exec())