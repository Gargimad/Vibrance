"""
volunteerPage.py — The volunteer-facing opportunity listing page.

Composes:
    • a header (back button, title, grid/list toggle)
    • a FilterBar (delegates to filterBar.py)
    • a results count line
    • an empty state with a "Clear filters" action
    • a QScrollArea with either a QGridLayout (grid view) or a QVBoxLayout
      (list view), populated with EventCards

Filtering runs in SQL via Database.searchOpportunitiesFiltered. The page
only handles presentation and layout.

Signals emitted upward:
    openLinkRequested(str) — the user clicked "Open link" on a card or dialog.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QStackedWidget, QGridLayout, QButtonGroup, QMessageBox,
)

import theme
from eventCard import EventCard
from eventDetailsDialog import EventDetailsDialog
from filterBar import FilterBar


class VolunteerPage(QWidget):
    openLinkRequested = pyqtSignal(str)

    def __init__(self, db, on_back_click=None, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.VOLUNTEER_PAGE)
        self.db = db
        self.on_back_click = on_back_click
        self.current_view = "grid"
        self.current_filters = {}
        self.current_volunteer_id = None
        self._grid_cards = []
        self._grid_cols = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())
        self.filter_bar = FilterBar()
        self.filter_bar.filtersChanged.connect(self.apply_filters)
        outer.addWidget(self.filter_bar)

        outer.addWidget(self._build_results_count())
        outer.addWidget(self._build_empty_state())
        outer.addWidget(self._build_scroll(), 1)

        self._populate_category_filter()
        self.refresh()

    # ── Construction helpers ──────────────────────────────────────────────
    def _build_header(self):
        header = QWidget()
        header.setObjectName(theme.VOLUNTEER_HEADER)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 12, 20, 12)

        back_btn = QPushButton("← Back")
        back_btn.setObjectName(theme.VOLUNTEER_BACK_BTN)
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self.on_back_click:
            back_btn.clicked.connect(self.on_back_click)

        self.title_lbl = QLabel("Explore Opportunities")
        self.title_lbl.setObjectName(theme.VOLUNTEER_TITLE)

        self.grid_btn = QPushButton("Grid")
        self.grid_btn.setObjectName(theme.VIEW_TOGGLE_BTN)
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.grid_btn.clicked.connect(lambda: self.set_view("grid"))

        self.list_btn = QPushButton("List")
        self.list_btn.setObjectName(theme.VIEW_TOGGLE_BTN)
        self.list_btn.setCheckable(True)
        self.list_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.list_btn.clicked.connect(lambda: self.set_view("list"))

        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self.grid_btn)
        group.addButton(self.list_btn)

        layout.addWidget(back_btn)
        layout.addWidget(self.title_lbl)
        layout.addStretch()
        layout.addWidget(self.grid_btn)
        layout.addWidget(self.list_btn)
        return header

    def _build_results_count(self):
        wrap = QWidget()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(20, 2, 20, 2)
        self.results_lbl = QLabel("")
        self.results_lbl.setObjectName(theme.VOLUNTEER_RESULTS_COUNT)
        layout.addWidget(self.results_lbl)
        layout.addStretch()
        return wrap

    def _build_empty_state(self):
        self.empty_wrap = QWidget()
        self.empty_wrap.setObjectName(theme.VOLUNTEER_EMPTY_WRAP)
        layout = QVBoxLayout(self.empty_wrap)
        layout.setContentsMargins(20, 40, 20, 40)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.empty_lbl = QLabel("No results match your filters.")
        self.empty_lbl.setObjectName(theme.VOLUNTEER_EMPTY)
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.empty_btn = QPushButton("Clear filters")
        self.empty_btn.setObjectName(theme.VOLUNTEER_EMPTY_BTN)
        self.empty_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.empty_btn.clicked.connect(self.filter_bar.clear_filters)

        layout.addWidget(self.empty_lbl)
        layout.addWidget(self.empty_btn, 0, Qt.AlignmentFlag.AlignCenter)
        self.empty_wrap.setVisible(False)
        return self.empty_wrap

    def _build_scroll(self):
        self.scroll = QScrollArea()
        self.scroll.setObjectName(theme.VOLUNTEER_SCROLL)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName(theme.VOLUNTEER_CONTENT_STACK)

        # Grid container
        self.grid_container = QWidget()
        self.grid_container.setObjectName(theme.VOLUNTEER_GRID_CONTAINER)
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(20, 10, 20, 30)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        # List container
        self.list_container = QWidget()
        self.list_container.setObjectName(theme.VOLUNTEER_LIST_CONTAINER)
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(20, 10, 20, 30)
        self.list_layout.setSpacing(12)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.content_stack.addWidget(self.grid_container)
        self.content_stack.addWidget(self.list_container)
        self.scroll.setWidget(self.content_stack)
        return self.scroll

    # ── External API ──────────────────────────────────────────────────────
    def set_current_volunteer(self, volunteer_id):
        """Called by landing.py on login/logout so RSVP knows who's asking."""
        self.current_volunteer_id = volunteer_id
        self.refresh()

    def set_search_text(self, text):
        self.filter_bar.set_search_text(text)

    def set_type_filter(self, value):
        self.filter_bar.set_type_filter(value)

    def set_view(self, mode):
        self.current_view = mode
        self.grid_btn.setChecked(mode == "grid")
        self.list_btn.setChecked(mode == "list")
        self.refresh()

    def apply_filters(self, filters):
        self.current_filters = filters
        self.refresh()

    # ── Data fetch ────────────────────────────────────────────────────────
    def _populate_category_filter(self):
        try:
            cats = self.db.getDistinctCategories()
        except Exception as e:
            print("Category query error:", e)
            cats = []
        self.filter_bar.populate_categories(cats)

    def _query_db(self):
        f = self.current_filters or {}
        date_enabled = f.get("date_enabled", False)
        return self.db.searchOpportunitiesFiltered(
            keyword=f.get("keyword", ""),
            type_filter=f.get("type", "All"),
            location=f.get("location", ""),
            category=f.get("category", "All Causes"),
            date_from=f.get("date_from") if date_enabled else None,
            date_to=f.get("date_to") if date_enabled else None,
            upcoming_only=True,
            limit=1000,
        )

    # ── Render ────────────────────────────────────────────────────────────
    def refresh(self):
        try:
            rows = self._query_db()
        except Exception as e:
            print("VolunteerPage query error:", e)
            rows = []

        self._clear_layouts()

        if not rows:
            self.empty_wrap.setVisible(True)
            self.scroll.setVisible(False)
            self.results_lbl.setText("0 results")
            return

        self.empty_wrap.setVisible(False)
        self.scroll.setVisible(True)
        n = len(rows)
        self.results_lbl.setText(f"{n} result{'s' if n != 1 else ''}")

        if self.current_view == "grid":
            self._populate_grid(rows)
            self.content_stack.setCurrentWidget(self.grid_container)
            self._layout_grid(force=True)
        else:
            self._populate_list(rows)
            self.content_stack.setCurrentWidget(self.list_container)

    def _make_card(self, row, view_mode):
        card = EventCard(
            row, view_mode=view_mode,
            current_volunteer_id=self.current_volunteer_id,
        )
        card.openLinkRequested.connect(self.openLinkRequested.emit)
        card.rsvpRequested.connect(self._handle_rsvp)
        card.detailsRequested.connect(self._show_details)
        return card

    def _populate_grid(self, rows):
        self._grid_cards = [self._make_card(row, "grid") for row in rows]
        self._grid_cols = 0  # force next _layout_grid to place them

    def _populate_list(self, rows):
        for row in rows:
            self.list_layout.addWidget(self._make_card(row, "list"))

    def _clear_layouts(self):
        self._grid_cards = []
        self._grid_cols = 0
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    # ── Responsive grid ───────────────────────────────────────────────────
    def _grid_columns(self):
        m = self.grid_layout.contentsMargins()
        spacing = self.grid_layout.spacing()
        avail = self.scroll.viewport().width() - m.left() - m.right()
        return max(1, (avail + spacing) // (EventCard.GRID_WIDTH + spacing))

    def _layout_grid(self, force=False):
        if not self._grid_cards:
            return
        cols = self._grid_columns()
        if cols == self._grid_cols and not force:
            return
        self._grid_cols = cols
        # Detach without deleting, then re-add in the new arrangement.
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)
        for idx, card in enumerate(self._grid_cards):
            self.grid_layout.addWidget(card, idx // cols, idx % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_view == "grid":
            self._layout_grid()

    def showEvent(self, event):
        super().showEvent(event)
        if self.current_view == "grid":
            self._layout_grid()

    # ── Card events ───────────────────────────────────────────────────────
    def _show_details(self, card):
        EventDetailsDialog(card, self).exec()

    def _handle_rsvp(self, opportunity_id):
        if not self.current_volunteer_id:
            QMessageBox.information(
                self, "Login required",
                "Log in as a volunteer to RSVP.",
            )
            return
        result = self.db.registerForOpportunity(
            self.current_volunteer_id, opportunity_id
        )
        if result == "ok":
            QMessageBox.information(
                self, "Registered",
                "You're signed up! See 'My Events' in your dashboard.",
            )
            self.refresh()  # update the spots line on every visible card
        elif result == "duplicate":
            QMessageBox.information(
                self, "Already registered",
                "You've already RSVP'd for this event.",
            )
        elif result == "full":
            QMessageBox.warning(
                self, "Event full",
                "This event has reached capacity.",
            )
        else:
            QMessageBox.warning(
                self, "Error", "Could not complete RSVP."
            )