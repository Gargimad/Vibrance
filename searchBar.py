"""searchBar.py - Thin bar under the nav bar.

Only visible on the guest home page. Emits `searchRequested(filters)` with
a dict shaped exactly like VolunteerPage.filter_bar expects:

    {
        "keyword":   str,
        "location":  str,
        "type":      "All" | "In-person" | "Remote",
        "category":  "All Causes" | <category>,
        "date_enabled": bool,
        "date_from": str | "",
        "date_to":   str | "",
    }
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import (
    QCursor, QAction, QIcon, QKeySequence, QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication, QStyle,
    QWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
    QListWidget, QListWidgetItem,
)

import theme

MAX_RECENTS = 6


class SearchBar(QWidget):
    searchRequested = pyqtSignal(dict)

    CATEGORY_OPTIONS = ["All Causes"]        # populated from DB later
    TYPE_OPTIONS = ["All", "In-person", "Remote"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.SEARCH_BAR)
        self._recent_searches = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Category
        self.categoryCombo = QComboBox()
        self.categoryCombo.setObjectName(theme.SEARCH_CATEGORY)
        self.categoryCombo.addItems(self.CATEGORY_OPTIONS)
        self.categoryCombo.setFixedWidth(160)
        self.categoryCombo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Type (in-person / remote)
        self.typeCombo = QComboBox()
        self.typeCombo.setObjectName(theme.SEARCH_CATEGORY)
        self.typeCombo.addItems(self.TYPE_OPTIONS)
        self.typeCombo.setFixedWidth(130)
        self.typeCombo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Keyword
        self.searchInput = QLineEdit()
        self.searchInput.setObjectName(theme.SEARCH_INPUT)
        self.searchInput.setPlaceholderText(
            "Search organizations, opportunities, or events..."
        )
        self.searchInput.setClearButtonEnabled(False)
        self.searchInput.returnPressed.connect(self._emit_search)
        self.searchInput.textChanged.connect(self._on_text_changed)

        icon_path = theme.asset("search.svg")
        if os.path.exists(icon_path):
            icon_action = QAction(QIcon(icon_path), "", self.searchInput)
            icon_action.setEnabled(False)
            self.searchInput.addAction(
                icon_action, QLineEdit.ActionPosition.LeadingPosition
            )

        self.clear_action = QAction(
            QApplication.style().standardIcon(
                QStyle.StandardPixmap.SP_LineEditClearButton
            ),
            "Clear", self.searchInput,
        )
        self.clear_action.setVisible(False)
        self.clear_action.triggered.connect(self.searchInput.clear)
        self.searchInput.addAction(
            self.clear_action, QLineEdit.ActionPosition.TrailingPosition
        )

        # Location
        self.locationInput = QLineEdit()
        self.locationInput.setObjectName(theme.SEARCH_INPUT)
        self.locationInput.setPlaceholderText("Location or zipcode...")
        self.locationInput.setFixedWidth(200)
        self.locationInput.returnPressed.connect(self._emit_search)

        # Button
        self.searchBtn = QPushButton("Search")
        self.searchBtn.setObjectName(theme.SEARCH_BTN)
        self.searchBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.searchBtn.clicked.connect(self._emit_search)

        layout.addWidget(self.categoryCombo)
        layout.addWidget(self.typeCombo)
        layout.addWidget(self.searchInput, 1)
        layout.addWidget(self.locationInput)
        layout.addWidget(self.searchBtn)

        # Recent-searches popup
        self.suggestions = QListWidget()
        self.suggestions.setObjectName("SearchSuggestions")
        self.suggestions.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.suggestions.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.suggestions.setVisible(False)
        self.suggestions.itemClicked.connect(self._pick_suggestion)

        QShortcut(
            QKeySequence("Ctrl+K"), self, activated=self.focus_input
        )

    # ── Public API ────────────────────────────────────────────────
    def focus_input(self):
        self.searchInput.setFocus()
        self.searchInput.selectAll()
        self._maybe_show_suggestions()

    def set_keyword(self, text):
        self.searchInput.setText(text)

    def set_category(self, category):
        idx = self.categoryCombo.findText(category)
        if idx >= 0:
            self.categoryCombo.setCurrentIndex(idx)

    def populate_categories(self, categories):
        current = self.categoryCombo.currentText()
        self.categoryCombo.blockSignals(True)
        self.categoryCombo.clear()
        self.categoryCombo.addItem("All Causes")
        for c in categories:
            self.categoryCombo.addItem(c)
        idx = self.categoryCombo.findText(current)
        self.categoryCombo.setCurrentIndex(idx if idx >= 0 else 0)
        self.categoryCombo.blockSignals(False)

    # ── Input events ──────────────────────────────────────────────
    def _on_text_changed(self, text):
        self.clear_action.setVisible(bool(text))
        if text:
            self.suggestions.setVisible(False)

    # ── Emit ──────────────────────────────────────────────────────
    def _emit_search(self):
        keyword = self.searchInput.text().strip()
        location = self.locationInput.text().strip()
        type_ = self.typeCombo.currentText()
        category = self.categoryCombo.currentText()

        # Nothing meaningful → do nothing (matches old behaviour).
        if not keyword and not location and type_ == "All" and category == "All Causes":
            return

        if keyword:
            if keyword in self._recent_searches:
                self._recent_searches.remove(keyword)
            self._recent_searches.insert(0, keyword)
            self._recent_searches = self._recent_searches[:MAX_RECENTS]

        self.suggestions.setVisible(False)
        self.searchRequested.emit({
            "keyword": keyword,
            "location": location,
            "type": type_,
            "category": category,
            "date_enabled": False,
            "date_from": "",
            "date_to": "",
        })

    # ── Suggestions popup ─────────────────────────────────────────
    def _maybe_show_suggestions(self):
        if not self._recent_searches:
            return
        if self.searchInput.text().strip():
            return
        self._populate_suggestions()
        self._position_suggestions()

    def _populate_suggestions(self):
        self.suggestions.clear()
        for s in self._recent_searches:
            item = QListWidgetItem(s)
            item.setData(Qt.ItemDataRole.UserRole, s)
            self.suggestions.addItem(item)

    def _position_suggestions(self):
        top_left = self.searchInput.mapToGlobal(
            QPoint(0, self.searchInput.height())
        )
        self.suggestions.move(top_left)
        self.suggestions.setFixedWidth(self.searchInput.width())
        count = self.suggestions.count()
        row_h = self.suggestions.sizeHintForRow(0) if count else 24
        self.suggestions.setFixedHeight(min(count * row_h + 8, 220))
        self.suggestions.show()
        self.suggestions.raise_()

    def _pick_suggestion(self, item):
        text = item.data(Qt.ItemDataRole.UserRole) or item.text()
        self.searchInput.setText(text)
        self.suggestions.setVisible(False)
        self._emit_search()

    def hideEvent(self, event):
        self.suggestions.setVisible(False)
        super().hideEvent(event)