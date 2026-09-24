"""
searchBar.py — Thin bar under the nav bar.

Only visible on the guest home page (landing.py handles that). Typing a
keyword and pressing Enter, or clicking Search, emits
searchRequested(keyword, category). The category combo offers All /
Organizations / Opportunities / Remote.

landing.handle_search forwards the keyword to the listing page and maps
the category onto the listing page's type filter.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
)

import theme


class SearchBar(QWidget):
    searchRequested = pyqtSignal(str, str)  # (keyword, category)

    CATEGORY_OPTIONS = [
        "All",
        "Organizations",
        "Opportunities",
        "Remote",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.SEARCH_BAR)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(10)

        self.categoryCombo = QComboBox()
        self.categoryCombo.setObjectName(theme.SEARCH_CATEGORY)
        self.categoryCombo.addItems(self.CATEGORY_OPTIONS)
        self.categoryCombo.setFixedWidth(150)

        self.searchInput = QLineEdit()
        self.searchInput.setObjectName(theme.SEARCH_INPUT)
        self.searchInput.setPlaceholderText(
            "Search organizations, opportunities, or events..."
        )
        self.searchInput.returnPressed.connect(self._emit_search)

        self.searchBtn = QPushButton("🔍 Search")
        self.searchBtn.setObjectName(theme.SEARCH_BTN)
        self.searchBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.searchBtn.clicked.connect(self._emit_search)

        layout.addWidget(self.categoryCombo)
        layout.addWidget(self.searchInput, 1)
        layout.addWidget(self.searchBtn)

    def _emit_search(self):
        keyword = self.searchInput.text().strip()
        if not keyword:
            return
        self.searchRequested.emit(
            keyword, self.categoryCombo.currentText()
        )

    # ── Optional setter for external use ──────────────────────────────────
    def set_keyword(self, text):
        self.searchInput.setText(text)