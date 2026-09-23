from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton


class SearchBar(QWidget):
    """
    Thin bar directly under the nav bar. Lets a guest or logged-in volunteer
    search across organizations, opportunities, and events stored in the
    volunteer database. Emits searchRequested(keyword, category) so the
    parent window (Landing) decides what to do with the results.
    """

    searchRequested = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(10)

        self.categoryCombo = QComboBox()
        self.categoryCombo.setObjectName("SearchCategoryCombo")
        self.categoryCombo.addItems(["All", "Organizations", "Opportunities", "Remote"])
        self.categoryCombo.setFixedWidth(150)

        self.searchInput = QLineEdit()
        self.searchInput.setObjectName("SearchInput")
        self.searchInput.setPlaceholderText("Search organizations, opportunities, or events...")
        self.searchInput.returnPressed.connect(self._emit_search)

        self.searchBtn = QPushButton("🔍 Search")
        self.searchBtn.setObjectName("SearchBtn")
        self.searchBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.searchBtn.clicked.connect(self._emit_search)

        layout.addWidget(self.categoryCombo)
        layout.addWidget(self.searchInput, 1)
        layout.addWidget(self.searchBtn)

    def _emit_search(self):
        keyword = self.searchInput.text().strip()
        if not keyword:
            return
        self.searchRequested.emit(keyword, self.categoryCombo.currentText())