"""
filterBar.py — Search / type / location row plus a collapsible advanced
row (category + date range).

Emits filtersChanged(dict) whenever any control changes, debounced 250ms
for the text inputs so typing doesn't fire a query per keystroke.

The dict shape (kept stable so volunteerPage._query_db can rely on it):
    {
        "keyword":      str,
        "type":         "All" | "In-person" | "Remote",
        "location":     str,
        "category":     "All Causes" | <category>,
        "date_enabled": bool,
        "date_from":    "YYYY-MM-DD",
        "date_to":      "YYYY-MM-DD",
    }
"""

from PyQt6.QtCore import Qt, QTimer, QDate, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QDateEdit,
)

import theme


class FilterBar(QWidget):
    filtersChanged = pyqtSignal(dict)

    TYPE_OPTIONS = ["All", "In-person", "Remote"]
    DATE_PRESETS = ["Any date", "Next 7 days", "Next 30 days", "Custom range"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.FILTER_BAR)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 10, 20, 10)
        outer.setSpacing(8)

        # ── Row 1: always visible ─────────────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setObjectName(theme.FILTER_SEARCH_INPUT)
        self.search_input.setPlaceholderText("Search by keyword, cause, org...")

        self.type_combo = QComboBox()
        self.type_combo.setObjectName(theme.FILTER_COMBO)
        self.type_combo.addItems(self.TYPE_OPTIONS)

        self.location_input = QLineEdit()
        self.location_input.setObjectName(theme.FILTER_LOCATION_INPUT)
        self.location_input.setPlaceholderText("Location or zipcode...")

        self.more_btn = QPushButton("More filters")
        self.more_btn.setObjectName(theme.FILTER_MORE_BTN)
        self.more_btn.setCheckable(True)
        self.more_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.clear_btn = QPushButton("Clear filters")
        self.clear_btn.setObjectName(theme.FILTER_CLEAR_BTN)
        self.clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_btn.clicked.connect(self.clear_filters)

        row1.addWidget(self.search_input, 3)
        row1.addWidget(self.type_combo, 1)
        row1.addWidget(self.location_input, 2)
        row1.addWidget(self.more_btn)
        row1.addWidget(self.clear_btn)

        # ── Row 2: collapsible ────────────────────────────────────────────
        self.more_row = QWidget()
        self.more_row.setObjectName(theme.FILTER_MORE_ROW)
        row2 = QHBoxLayout(self.more_row)
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(10)

        self.category_combo = QComboBox()
        self.category_combo.setObjectName(theme.FILTER_COMBO)
        self.category_combo.addItem("All Causes")

        self.date_preset = QComboBox()
        self.date_preset.setObjectName(theme.FILTER_COMBO)
        self.date_preset.addItems(self.DATE_PRESETS)

        self.date_from = QDateEdit()
        self.date_from.setObjectName(theme.FILTER_DATE)
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate())
        self.date_from.setDisplayFormat("yyyy-MM-dd")

        self.date_to = QDateEdit()
        self.date_to.setObjectName(theme.FILTER_DATE)
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate().addMonths(6))
        self.date_to.setDisplayFormat("yyyy-MM-dd")

        self.arrow_lbl = QLabel("→")
        self.arrow_lbl.setObjectName(theme.FILTER_LABEL)

        cause_lbl = QLabel("Cause")
        cause_lbl.setObjectName(theme.FILTER_LABEL)
        date_lbl = QLabel("Date")
        date_lbl.setObjectName(theme.FILTER_LABEL)

        row2.addWidget(cause_lbl)
        row2.addWidget(self.category_combo, 2)
        row2.addWidget(date_lbl)
        row2.addWidget(self.date_preset, 1)
        row2.addWidget(self.date_from)
        row2.addWidget(self.arrow_lbl)
        row2.addWidget(self.date_to)
        row2.addStretch(1)

        outer.addLayout(row1)
        outer.addWidget(self.more_row)

        # ── Debounce ──────────────────────────────────────────────────────
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(250)
        self._debounce.timeout.connect(self._emit)

        self.search_input.textChanged.connect(lambda _t: self._debounce.start())
        self.location_input.textChanged.connect(lambda _t: self._debounce.start())
        self.type_combo.currentTextChanged.connect(self._emit)
        self.category_combo.currentTextChanged.connect(self._emit)
        self.date_preset.currentTextChanged.connect(self._on_preset_changed)
        self.date_from.dateChanged.connect(self._emit)
        self.date_to.dateChanged.connect(self._emit)
        self.more_btn.toggled.connect(self._toggle_more)

        self._toggle_more(False)
        self._on_preset_changed("Any date")

    # ── Category population ───────────────────────────────────────────────
    def populate_categories(self, categories):
        current = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("All Causes")
        for c in categories:
            self.category_combo.addItem(c)
        idx = self.category_combo.findText(current)
        self.category_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.category_combo.blockSignals(False)

    # ── Advanced-row toggling ─────────────────────────────────────────────
    def _toggle_more(self, expanded):
        self.more_row.setVisible(expanded)
        self._update_more_label()

    def _on_preset_changed(self, preset):
        custom = (preset == "Custom range")
        self.date_from.setVisible(custom)
        self.date_to.setVisible(custom)
        self.arrow_lbl.setVisible(custom)
        self._emit()

    def _advanced_active(self):
        return (self.category_combo.currentIndex() > 0
                or self.date_preset.currentIndex() > 0)

    def _update_more_label(self):
        arrow = "▾" if self.more_btn.isChecked() else "▸"
        dot = " •" if self._advanced_active() else ""
        self.more_btn.setText(f"More filters{dot} {arrow}")

    # ── Clear ─────────────────────────────────────────────────────────────
    def clear_filters(self):
        widgets = (self.search_input, self.location_input, self.type_combo,
                   self.category_combo, self.date_preset)
        for w in widgets:
            w.blockSignals(True)
        self.search_input.clear()
        self.location_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        self.date_preset.setCurrentIndex(0)
        for w in widgets:
            w.blockSignals(False)
        self._on_preset_changed("Any date")  # also emits once

    # ── Emit ──────────────────────────────────────────────────────────────
    def _date_range(self):
        preset = self.date_preset.currentText()
        today = QDate.currentDate()
        fmt = "yyyy-MM-dd"
        if preset == "Next 7 days":
            return True, today.toString(fmt), today.addDays(7).toString(fmt)
        if preset == "Next 30 days":
            return True, today.toString(fmt), today.addDays(30).toString(fmt)
        if preset == "Custom range":
            return (True,
                    self.date_from.date().toString(fmt),
                    self.date_to.date().toString(fmt))
        return False, "", ""

    def _emit(self, *_args):
        enabled, d_from, d_to = self._date_range()
        filters = {
            "keyword": self.search_input.text().strip(),
            "type": self.type_combo.currentText(),
            "location": self.location_input.text().strip(),
            "category": self.category_combo.currentText(),
            "date_enabled": enabled,
            "date_from": d_from,
            "date_to": d_to,
        }
        self._update_more_label()
        self.filtersChanged.emit(filters)

    # ── External setters (used by landing.handle_search) ──────────────────
    def set_search_text(self, text):
        self.search_input.setText(text)

    def set_type_filter(self, value):
        """Accepts legacy 'Events'/'Organizations' or new 'In-person'/'Remote'."""
        legacy = {"Events": "In-person", "Organizations": "All"}
        value = legacy.get(value, value)
        idx = self.type_combo.findText(value)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)