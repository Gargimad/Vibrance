"""
searchBar.py - Thin bar under the nav bar.

Only visible on the guest home page (landing.py handles that). Typing a
keyword and pressing Enter, or clicking Search, emits
searchRequested(keyword, category). The category combo offers All /
Organizations / Opportunities / Remote.

Features:
    - Rounded pill input, combo, and button, styled via QSS.
    - Search icon inside the input (leading).
    - Clear button inside the input (trailing), shown only when
      there's text.
    - Recent searches dropdown, shown on focus.
    - Ctrl+K shortcut focuses the input (wired from landing.py).

landing.handle_search forwards the keyword to the listing page and
maps the category onto the listing page's type filter.
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


# How many recent searches to remember.
MAX_RECENTS = 6


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

        # ── State ─────────────────────────────────────────────────
        self._recent_searches = []

        # ── Layout ────────────────────────────────────────────────
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # ── Category combo ────────────────────────────────────────
        self.categoryCombo = QComboBox()
        self.categoryCombo.setObjectName(theme.SEARCH_CATEGORY)
        self.categoryCombo.addItems(self.CATEGORY_OPTIONS)
        self.categoryCombo.setFixedWidth(150)
        self.categoryCombo.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )

        # ── Search input ──────────────────────────────────────────
        self.searchInput = QLineEdit()
        self.searchInput.setObjectName(theme.SEARCH_INPUT)
        self.searchInput.setPlaceholderText(
            "Search organizations, opportunities, or events..."
        )
        self.searchInput.setClearButtonEnabled(False)  # we do our own
        self.searchInput.returnPressed.connect(self._emit_search)
        self.searchInput.textChanged.connect(self._on_text_changed)

        # Leading search icon (decorative)
        icon_path = theme.asset("search.svg")
        if os.path.exists(icon_path):
            icon_action = QAction(
                QIcon(icon_path), "", self.searchInput
            )
            icon_action.setEnabled(False)
            self.searchInput.addAction(
                icon_action, QLineEdit.ActionPosition.LeadingPosition
            )

        # Trailing clear button (native icon, hidden until text)
        self.clear_action = QAction(
            QApplication.style().standardIcon(
                QStyle.StandardPixmap.SP_LineEditClearButton
            ),
            "Clear", self.searchInput,
        )
        self.clear_action.setVisible(False)
        self.clear_action.triggered.connect(self.searchInput.clear)
        self.searchInput.addAction(
            self.clear_action,
            QLineEdit.ActionPosition.TrailingPosition,
        )

        # ── Search button ─────────────────────────────────────────
        self.searchBtn = QPushButton("Search")
        self.searchBtn.setObjectName(theme.SEARCH_BTN)
        self.searchBtn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        self.searchBtn.clicked.connect(self._emit_search)

        layout.addWidget(self.categoryCombo)
        layout.addWidget(self.searchInput, 1)
        layout.addWidget(self.searchBtn)

        # ── Recent searches popup ─────────────────────────────────
        # A frameless popup window: floats above everything, closes
        # automatically when the user clicks outside.
        self.suggestions = QListWidget()
        self.suggestions.setObjectName("SearchSuggestions")
        self.suggestions.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.suggestions.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.suggestions.setVisible(False)
        self.suggestions.itemClicked.connect(self._pick_suggestion)

        # ── Ctrl+K focuses the input ──────────────────────────────
        QShortcut(
            QKeySequence("Ctrl+K"), self, activated=self.focus_input
        )

    # ── Input events ──────────────────────────────────────────────
    def _on_text_changed(self, text):
        # Clear button visibility
        self.clear_action.setVisible(bool(text))
        # Hide suggestions once the user starts typing fresh text.
        if text:
            self.suggestions.setVisible(False)

    # ── Public API ────────────────────────────────────────────────
    def focus_input(self):
        """Focus the input, select all, and offer recent searches."""
        self.searchInput.setFocus()
        self.searchInput.selectAll()
        self._maybe_show_suggestions()

    def set_keyword(self, text):
        self.searchInput.setText(text)

    def set_category(self, category):
        idx = self.categoryCombo.findText(category)
        if idx >= 0:
            self.categoryCombo.setCurrentIndex(idx)

    # ── Emit ──────────────────────────────────────────────────────
    def _emit_search(self):
        keyword = self.searchInput.text().strip()
        if not keyword:
            return

        # Remember it (most recent first, no duplicates).
        if keyword in self._recent_searches:
            self._recent_searches.remove(keyword)
        self._recent_searches.insert(0, keyword)
        self._recent_searches = self._recent_searches[:MAX_RECENTS]

        self.suggestions.setVisible(False)
        self.searchRequested.emit(
            keyword, self.categoryCombo.currentText()
        )

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
        # Screen coordinates: the popup is a top-level window.
        top_left = self.searchInput.mapToGlobal(
            QPoint(0, self.searchInput.height())
        )
        self.suggestions.move(top_left)
        self.suggestions.setFixedWidth(self.searchInput.width())
        count = self.suggestions.count()
        row_h = self.suggestions.sizeHintForRow(0) if count else 24
        self.suggestions.setFixedHeight(
            min(count * row_h + 8, 220)
        )
        self.suggestions.show()
        self.suggestions.raise_()

    def _pick_suggestion(self, item):
        text = item.data(Qt.ItemDataRole.UserRole) or item.text()
        self.searchInput.setText(text)
        self.suggestions.setVisible(False)
        self._emit_search()

    def hideEvent(self, event):
        # Close the popup if the bar is hidden (leaving the page).
        self.suggestions.setVisible(False)
        super().hideEvent(event)