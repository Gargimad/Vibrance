import os
from PyQt6.QtCore import Qt, QByteArray, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QScrollArea, QSizePolicy, QGridLayout, QLineEdit, QComboBox,
    QDateEdit, QStackedWidget, QButtonGroup, QMessageBox, QDialog
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FALLBACK_IMAGE = os.path.join(BASE_DIR, "noThumbnail.png")

# ---------------------------------------------------------------------------
# Thumbnail helpers (with a small cache so filtering/resizing doesn't
# re-decode and re-scale every image each time)
# ---------------------------------------------------------------------------
_PIXMAP_CACHE = {}
_PIXMAP_CACHE_LIMIT = 300


def clear_thumbnail_cache():
    """Call this if thumbnails are edited or replaced in the database."""
    _PIXMAP_CACHE.clear()


def load_thumbnail_pixmap(blob, width, height, key=None):
    cache_key = (key, width, height) if key is not None else None
    if cache_key is not None and cache_key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[cache_key]

    pixmap = QPixmap()
    if isinstance(blob, str):
        pixmap = QPixmap(blob)              # column holds a file path
    elif blob:
        pixmap.loadFromData(QByteArray(blob))   # column holds raw bytes
    if pixmap.isNull() and os.path.exists(FALLBACK_IMAGE):
        pixmap = QPixmap(FALLBACK_IMAGE)
    if pixmap.isNull():
        return None

    scaled = pixmap.scaled(width, height,
                           Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                           Qt.TransformationMode.SmoothTransformation)
    x = (scaled.width() - width) // 2
    y = (scaled.height() - height) // 2
    result = scaled.copy(x, y, width, height)

    if cache_key is not None:
        if len(_PIXMAP_CACHE) >= _PIXMAP_CACHE_LIMIT:
            _PIXMAP_CACHE.pop(next(iter(_PIXMAP_CACHE)))
        _PIXMAP_CACHE[cache_key] = result
    return result


def truncate_text(text, max_len):
    if not text:
        return ""
    text = " ".join(str(text).split())
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"


def build_badges(category, is_remote, location, status):
    """Shared badge builder used by both the card and the details dialog."""
    labels = []
    if category:
        cat = QLabel(category)
        cat.setObjectName("EventCategoryBadge")
        cat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labels.append(cat)

    loc_text = "Remote" if is_remote else (location or "Location TBD")
    loc = QLabel(loc_text)
    loc.setObjectName("EventLocationBadge")
    loc.setAlignment(Qt.AlignmentFlag.AlignCenter)
    labels.append(loc)

    if status and status != "open":
        st = QLabel(status.upper())
        st.setObjectName("EventStatusBadge")
        st.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labels.append(st)
    return labels


def make_meta_row(key, value):
    row = QHBoxLayout()
    row.setSpacing(6)
    row.setContentsMargins(0, 0, 0, 0)
    k = QLabel(f"{key}:")
    k.setObjectName("EventMetaKey")
    v = QLabel(value)
    v.setObjectName("EventMetaValue")
    v.setWordWrap(True)
    row.addWidget(k)
    row.addWidget(v, 1)
    return row


# ---------------------------------------------------------------------------
# Event Card
# ---------------------------------------------------------------------------
class EventCard(QFrame):
    openLinkRequested = pyqtSignal(str)
    rsvpRequested = pyqtSignal(int)        # opportunityID
    detailsRequested = pyqtSignal(object)  # the card itself

    GRID_WIDTH = 300
    GRID_THUMB_H = 150
    GRID_FIXED_HEIGHT = 465
    LIST_THUMB_W = 220
    LIST_THUMB_H = 160
    LIST_MIN_HEIGHT = 160

    def __init__(self, row, view_mode="grid", parent=None, current_volunteer_id=None):
        """
        row: sqlite3.Row (or dict) from an opportunity query.
        current_volunteer_id: used for the RSVP tooltip; the actual login
        check happens when the button is clicked.
        """
        super().__init__(parent)
        self.setObjectName("EventCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.row = row
        self.view_mode = view_mode
        self.current_volunteer_id = current_volunteer_id

        def g(key, default=""):
            try:
                v = row[key]
            except (KeyError, IndexError, TypeError):
                return default
            return v if v is not None else default

        self.opportunityID = g("opportunityID", 0)
        self.title = g("title", "Untitled event")
        self.description = g("description", "")
        self.category = g("category", "")
        self.location = g("location", "")
        self.is_remote = bool(g("is_remote", 0))
        self.event_date = g("event_date", "")
        self.start_time = g("start_time", "")
        self.end_time = g("end_time", "")
        self.capacity = g("capacity", None)
        self.status = g("status", "open") or "open"
        self.org_name = g("org_name", "Independent")
        self.thumbnail = g("thumbnail", None)
        self.website_link = g("website_link", "")
        try:
            self.registered_count = int(g("registered_count", 0) or 0)
        except (TypeError, ValueError):
            self.registered_count = 0

        # Derive "full" from capacity so it doesn't rely on organizers
        # remembering to flip the status by hand.
        if (self.status == "open" and self.capacity
                and self.registered_count >= self.capacity):
            self.status = "full"

        if view_mode == "list":
            self._build_list_layout()
        else:
            self._build_grid_layout()

    # -------- shared sub-builders --------
    def _make_thumbnail(self, w, h):
        thumb = QLabel()
        thumb.setObjectName("EventThumb")
        thumb.setFixedSize(w, h)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setScaledContents(False)
        pixmap = load_thumbnail_pixmap(self.thumbnail, w, h,
                                       key=self.opportunityID or None)
        if pixmap is not None:
            thumb.setPixmap(pixmap)
        else:
            thumb.setText("No image")
        return thumb

    def _make_badges(self, with_org=False):
        row = QHBoxLayout()
        row.setSpacing(6)
        row.setContentsMargins(0, 0, 0, 0)
        for lbl in build_badges(self.category, self.is_remote,
                                self.location, self.status):
            row.addWidget(lbl)
        if with_org:
            org = QLabel(f"by {self.org_name}")
            org.setObjectName("EventOrg")
            row.addWidget(org)
        row.addStretch(1)
        return row

    def _make_link_button(self):
        btn = QPushButton("Open link" if self.website_link else "No link")
        btn.setObjectName("EventLinkBtn")
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setEnabled(bool(self.website_link))
        btn.clicked.connect(self.open_link)
        return btn

    def _rsvp_label(self):
        if self.status == "open":
            return "RSVP"
        if self.status == "full":
            return "Full"
        return self.status.capitalize()      # e.g. "Closed"

    def _make_rsvp_button(self):
        btn = QPushButton(self._rsvp_label())
        btn.setObjectName("EventRsvpBtn")
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self.status == "open":
            # Stay clickable when logged out: the page shows a login prompt,
            # which is clearer than a greyed-out button.
            btn.setEnabled(True)
            btn.setToolTip("RSVP for this event" if self.current_volunteer_id
                           else "Log in as a volunteer to RSVP")
        else:
            btn.setEnabled(False)
            btn.setToolTip(f"This event is {self.status}")
        btn.clicked.connect(self.request_rsvp)
        return btn

    def _date_text(self):
        text = self.event_date or "TBD"
        if self.start_time and self.end_time:
            text += f"  •  {self.start_time}–{self.end_time}"
        elif self.start_time:
            text += f"  •  {self.start_time}"
        return text

    def _spots_text(self):
        if not self.capacity:
            return ""
        left = max(0, self.capacity - self.registered_count)
        return f"{left} of {self.capacity} left"

    def _make_date_line(self):
        box = QVBoxLayout()
        box.setSpacing(4)
        box.setContentsMargins(0, 0, 0, 0)
        box.addLayout(make_meta_row("Date", self._date_text()))
        spots = self._spots_text()
        if spots:
            box.addLayout(make_meta_row("Spots", spots))
        return box

    def _make_org_line(self):
        lbl = QLabel(f"by {self.org_name}")
        lbl.setObjectName("EventOrg")
        lbl.setWordWrap(True)
        return lbl

    # -------- grid layout --------
    def _build_grid_layout(self):
        self.setFixedWidth(self.GRID_WIDTH)
        self.setFixedHeight(self.GRID_FIXED_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._make_thumbnail(self.GRID_WIDTH, self.GRID_THUMB_H))

        content = QVBoxLayout()
        content.setContentsMargins(16, 14, 16, 14)
        content.setSpacing(10)

        content.addLayout(self._make_badges())

        title_lbl = QLabel(truncate_text(self.title, 60))
        title_lbl.setObjectName("EventTitle")
        title_lbl.setWordWrap(True)
        title_lbl.setMaximumHeight(44)
        title_lbl.setToolTip(self.title)
        content.addWidget(title_lbl)

        content.addWidget(self._make_org_line())

        desc_lbl = QLabel(truncate_text(self.description, 120))
        desc_lbl.setObjectName("EventDescription")
        desc_lbl.setWordWrap(True)
        desc_lbl.setMinimumHeight(50)
        desc_lbl.setMaximumHeight(58)
        content.addWidget(desc_lbl)

        content.addLayout(self._make_date_line())
        content.addStretch(1)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self._make_link_button())
        actions.addWidget(self._make_rsvp_button())
        content.addLayout(actions)

        layout.addLayout(content)

    # -------- list layout --------
    def _build_list_layout(self):
        self.setMinimumHeight(self.LIST_MIN_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._make_thumbnail(self.LIST_THUMB_W, self.LIST_THUMB_H))

        content = QVBoxLayout()
        content.setContentsMargins(20, 16, 20, 16)
        content.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(16)

        title_lbl = QLabel(self.title)
        title_lbl.setObjectName("EventTitleList")
        title_lbl.setWordWrap(True)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self._make_link_button())
        actions.addWidget(self._make_rsvp_button())

        top.addWidget(title_lbl, 1)
        top.addLayout(actions)
        content.addLayout(top)

        content.addLayout(self._make_badges(with_org=True))

        desc_lbl = QLabel(truncate_text(self.description, 260))
        desc_lbl.setObjectName("EventDescription")
        desc_lbl.setWordWrap(True)
        desc_lbl.setMaximumHeight(60)
        content.addWidget(desc_lbl)

        content.addLayout(self._make_date_line())
        content.addStretch(1)
        layout.addLayout(content, 1)

    # -------- events --------
    def open_link(self):
        if self.website_link:
            self.openLinkRequested.emit(self.website_link)

    def request_rsvp(self):
        if self.opportunityID:
            self.rsvpRequested.emit(self.opportunityID)

    def mouseReleaseEvent(self, event):
        # Buttons handle their own clicks; anything else opens the details.
        if (event.button() == Qt.MouseButton.LeftButton
                and self.rect().contains(event.position().toPoint())):
            self.detailsRequested.emit(self)
        super().mouseReleaseEvent(event)


# ---------------------------------------------------------------------------
# Event Details Dialog
# ---------------------------------------------------------------------------
class EventDetailsDialog(QDialog):
    def __init__(self, card, parent=None):
        super().__init__(parent)
        self.setObjectName("EventDetailsDialog")
        self.setWindowTitle(card.title)
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setMinimumHeight(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        badges = QHBoxLayout()
        badges.setSpacing(6)
        for lbl in build_badges(card.category, card.is_remote,
                                card.location, card.status):
            badges.addWidget(lbl)
        badges.addStretch(1)
        layout.addLayout(badges)

        title = QLabel(card.title)
        title.setObjectName("EventTitleList")
        title.setWordWrap(True)
        layout.addWidget(title)

        org = QLabel(f"by {card.org_name}")
        org.setObjectName("EventOrg")
        layout.addWidget(org)

        layout.addLayout(make_meta_row("Date", card._date_text()))
        where = "Remote" if card.is_remote else (card.location or "Location TBD")
        layout.addLayout(make_meta_row("Where", where))
        spots = card._spots_text()
        if spots:
            layout.addLayout(make_meta_row("Spots", spots))

        scroll = QScrollArea()
        scroll.setObjectName("DetailsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("DetailsScrollContent")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 6, 0, 0)
        desc = QLabel(card.description or "No description provided.")
        desc.setObjectName("DetailsDescription")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        desc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        cl.addWidget(desc)
        cl.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("DetailsCloseBtn")
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.reject)

        link_btn = card._make_link_button()
        rsvp_btn = card._make_rsvp_button()
        rsvp_btn.clicked.connect(self.accept)   # close after the RSVP result

        buttons.addWidget(close_btn)
        buttons.addStretch(1)
        buttons.addWidget(link_btn)
        buttons.addWidget(rsvp_btn)
        layout.addLayout(buttons)


# ---------------------------------------------------------------------------
# Filter Bar
# ---------------------------------------------------------------------------
class FilterBar(QWidget):
    filtersChanged = pyqtSignal(dict)

    TYPE_OPTIONS = ["All", "In-person", "Remote"]
    DATE_PRESETS = ["Any date", "Next 7 days", "Next 30 days", "Custom range"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FilterBar")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 10, 20, 10)
        outer.setSpacing(8)

        # ---- Row 1: always visible ----
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("FilterSearchInput")
        self.search_input.setPlaceholderText("Search by keyword, cause, org...")

        self.type_combo = QComboBox()
        self.type_combo.setObjectName("FilterCombo")
        self.type_combo.addItems(self.TYPE_OPTIONS)

        self.location_input = QLineEdit()
        self.location_input.setObjectName("FilterLocationInput")
        self.location_input.setPlaceholderText("Location or zipcode...")

        self.more_btn = QPushButton("More filters ▾")
        self.more_btn.setObjectName("FilterMoreBtn")
        self.more_btn.setCheckable(True)
        self.more_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.clear_btn = QPushButton("Clear filters")
        self.clear_btn.setObjectName("FilterClearBtn")
        self.clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_btn.clicked.connect(self.clear_filters)

        row1.addWidget(self.search_input, 3)
        row1.addWidget(self.type_combo, 1)
        row1.addWidget(self.location_input, 2)
        row1.addWidget(self.more_btn)
        row1.addWidget(self.clear_btn)

        # ---- Row 2: collapsible ----
        self.more_row = QWidget()
        self.more_row.setObjectName("FilterMoreRow")
        row2 = QHBoxLayout(self.more_row)
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(10)

        self.category_combo = QComboBox()
        self.category_combo.setObjectName("FilterCombo")
        self.category_combo.addItem("All Causes")   # populated later from DB

        self.date_preset = QComboBox()
        self.date_preset.setObjectName("FilterCombo")
        self.date_preset.addItems(self.DATE_PRESETS)

        self.date_from = QDateEdit()
        self.date_from.setObjectName("FilterDate")
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate())
        self.date_from.setDisplayFormat("yyyy-MM-dd")

        self.date_to = QDateEdit()
        self.date_to.setObjectName("FilterDate")
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate().addMonths(6))
        self.date_to.setDisplayFormat("yyyy-MM-dd")

        self.arrow_lbl = QLabel("→")
        self.arrow_lbl.setObjectName("FilterLabel")

        cause_lbl = QLabel("Cause")
        cause_lbl.setObjectName("FilterLabel")
        date_lbl = QLabel("Date")
        date_lbl.setObjectName("FilterLabel")

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

        # ---- Debounce ----
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

    # ------------------------------------------------------------------
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
        arrow = "▴" if self.more_btn.isChecked() else "▾"
        dot = "  •" if self._advanced_active() else ""
        self.more_btn.setText(f"More filters{dot} {arrow}")

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
        self._on_preset_changed("Any date")   # also emits once

    def _date_range(self):
        preset = self.date_preset.currentText()
        today = QDate.currentDate()
        fmt = "yyyy-MM-dd"
        if preset == "Next 7 days":
            return True, today.toString(fmt), today.addDays(7).toString(fmt)
        if preset == "Next 30 days":
            return True, today.toString(fmt), today.addDays(30).toString(fmt)
        if preset == "Custom range":
            return (True, self.date_from.date().toString(fmt),
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

    def set_search_text(self, text):
        self.search_input.setText(text)


# ---------------------------------------------------------------------------
# Volunteer Page
# ---------------------------------------------------------------------------
class VolunteerPage(QWidget):
    openLinkRequested = pyqtSignal(str)

    def __init__(self, db, on_back_click=None, parent=None):
        super().__init__(parent)
        self.setObjectName("VolunteerPage")
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

        header = QWidget()
        header.setObjectName("VolunteerHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 12, 20, 12)

        back_btn = QPushButton("← Back")
        back_btn.setObjectName("VolunteerBackBtn")
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if on_back_click:
            back_btn.clicked.connect(on_back_click)

        self.title_lbl = QLabel("Explore Opportunities")
        self.title_lbl.setObjectName("VolunteerTitle")

        self.grid_btn = QPushButton("Grid")
        self.grid_btn.setObjectName("ViewToggleBtn")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.grid_btn.clicked.connect(lambda: self.set_view("grid"))

        self.list_btn = QPushButton("List")
        self.list_btn.setObjectName("ViewToggleBtn")
        self.list_btn.setCheckable(True)
        self.list_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.list_btn.clicked.connect(lambda: self.set_view("list"))

        view_group = QButtonGroup(self)
        view_group.setExclusive(True)
        view_group.addButton(self.grid_btn)
        view_group.addButton(self.list_btn)

        header_layout.addWidget(back_btn)
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.grid_btn)
        header_layout.addWidget(self.list_btn)

        self.filter_bar = FilterBar()
        self.filter_bar.filtersChanged.connect(self.apply_filters)

        self.results_lbl = QLabel("")
        self.results_lbl.setObjectName("VolunteerResultsCount")
        count_wrap = QWidget()
        count_layout = QHBoxLayout(count_wrap)
        count_layout.setContentsMargins(20, 2, 20, 2)
        count_layout.addWidget(self.results_lbl)
        count_layout.addStretch()

        self.scroll = QScrollArea()
        self.scroll.setObjectName("VolunteerScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("VolunteerContentStack")

        self.grid_container = QWidget()
        self.grid_container.setObjectName("VolunteerGridContainer")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(20, 10, 20, 30)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.list_container = QWidget()
        self.list_container.setObjectName("VolunteerListContainer")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(20, 10, 20, 30)
        self.list_layout.setSpacing(12)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Empty state: message + an action
        self.empty_wrap = QWidget()
        self.empty_wrap.setObjectName("VolunteerEmptyWrap")
        empty_layout = QVBoxLayout(self.empty_wrap)
        empty_layout.setContentsMargins(20, 40, 20, 40)
        empty_layout.setSpacing(14)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl = QLabel("No results match your filters.")
        self.empty_lbl.setObjectName("VolunteerEmpty")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_btn = QPushButton("Clear filters")
        self.empty_btn.setObjectName("VolunteerEmptyBtn")
        self.empty_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.empty_btn.clicked.connect(self.filter_bar.clear_filters)
        empty_layout.addWidget(self.empty_lbl)
        empty_layout.addWidget(self.empty_btn, 0, Qt.AlignmentFlag.AlignCenter)
        self.empty_wrap.setVisible(False)

        self.content_stack.addWidget(self.grid_container)
        self.content_stack.addWidget(self.list_container)
        self.scroll.setWidget(self.content_stack)

        outer.addWidget(header)
        outer.addWidget(self.filter_bar)
        outer.addWidget(count_wrap)
        outer.addWidget(self.empty_wrap)
        outer.addWidget(self.scroll, 1)

        self._populate_category_filter()
        self.refresh()

    # ------------------------------------------------------------------
    def set_current_volunteer(self, volunteer_id):
        self.current_volunteer_id = volunteer_id
        self.refresh()

    def _populate_category_filter(self):
        try:
            cats = self.db.getDistinctCategories()
        except Exception as e:
            print("Category query error:", e)
            cats = []
        self.filter_bar.populate_categories(cats)

    def set_view(self, mode):
        self.current_view = mode
        self.grid_btn.setChecked(mode == "grid")
        self.list_btn.setChecked(mode == "list")
        self.refresh()

    def set_search_text(self, text):
        self.filter_bar.set_search_text(text)

    def set_type_filter(self, value):
        # Backwards compatibility with the old "Events"/"Organizations" values
        legacy = {"Events": "In-person", "Organizations": "All"}
        value = legacy.get(value, value)
        idx = self.filter_bar.type_combo.findText(value)
        if idx >= 0:
            self.filter_bar.type_combo.setCurrentIndex(idx)

    def apply_filters(self, filters):
        self.current_filters = filters
        self.refresh()

    # ------------------------------------------------------------------
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
        self.results_lbl.setText(f"{len(rows)} result{'s' if len(rows) != 1 else ''}")

        if self.current_view == "grid":
            self._populate_grid(rows)
            self.content_stack.setCurrentWidget(self.grid_container)
            self._layout_grid(force=True)
        else:
            self._populate_list(rows)
            self.content_stack.setCurrentWidget(self.list_container)

    # ------------------------------------------------------------------
    def _query_db(self):
        """Filtering happens in SQL (Database.searchOpportunitiesFiltered)."""
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

    # ------------------------------------------------------------------
    def _make_card(self, row, view_mode):
        card = EventCard(row, view_mode=view_mode,
                         current_volunteer_id=self.current_volunteer_id)
        card.openLinkRequested.connect(self.openLinkRequested.emit)
        card.rsvpRequested.connect(self._handle_rsvp)
        card.detailsRequested.connect(self._show_details)
        return card

    def _show_details(self, card):
        EventDetailsDialog(card, self).exec()

    def _handle_rsvp(self, opportunity_id):
        if not self.current_volunteer_id:
            QMessageBox.information(self, "Login required",
                                    "Log in as a volunteer to RSVP.")
            return
        result = self.db.registerForOpportunity(self.current_volunteer_id,
                                                opportunity_id)
        if result == "ok":
            QMessageBox.information(self, "Registered",
                                    "You're signed up! See 'My Events' in your dashboard.")
        elif result == "duplicate":
            QMessageBox.information(self, "Already registered",
                                    "You've already RSVP'd for this event.")
        elif result == "full":
            QMessageBox.warning(self, "Event full",
                                "This event has reached capacity.")
        else:
            QMessageBox.warning(self, "Error", "Could not complete RSVP.")

    # ------------------------------------------------------------------
    # Grid (responsive) / list population
    # ------------------------------------------------------------------
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
        # Detach without deleting, then re-add in the new arrangement
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

    def _populate_grid(self, rows):
        self._grid_cards = [self._make_card(row, "grid") for row in rows]
        self._grid_cols = 0   # force the next _layout_grid to place them

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