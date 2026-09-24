"""
eventCard.py — The opportunity card used on the home carousels and the
volunteer listing page.

Reads a sqlite3.Row (or dict) from Database._opportunity_base_query() and
renders it in one of two modes:
    "grid"  — fixed 300×465 tile for the grid view and home carousels
    "list"  — horizontal row for the list view

Metadata shown on every card:
    • date + start–end time
    • spots (registered_count / capacity, when capacity is set)
    • category, location/remote, status badges
    • org name
    • RSVP button (disabled when full/cancelled) and external link button
"""

import os
from PyQt6.QtCore import Qt, QByteArray, pyqtSignal
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)

import theme

# Thumbnail fallback — mirrors the path scheme in theme.asset()
FALLBACK_IMAGE = theme.asset("noThumbnail.png")

# Small in-memory cache so re-filtering doesn't re-decode every image.
_PIXMAP_CACHE = {}
_PIXMAP_CACHE_LIMIT = 300


def clear_thumbnail_cache():
    """Call after an org edits/replaces a thumbnail so the next render
    picks up the new bytes."""
    _PIXMAP_CACHE.clear()


def load_thumbnail_pixmap(blob, width, height, key=None):
    """
    blob: either a path string (column holds a filename) or raw bytes.
    Returns a QPixmap cover-cropped to (width, height), or None on failure.
    """
    cache_key = (key, width, height) if key is not None else None
    if cache_key and cache_key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[cache_key]

    pixmap = QPixmap()
    if isinstance(blob, str) and blob:
        pixmap = QPixmap(blob)
    elif blob:
        pixmap.loadFromData(QByteArray(blob))

    if pixmap.isNull() and os.path.exists(FALLBACK_IMAGE):
        pixmap = QPixmap(FALLBACK_IMAGE)
    if pixmap.isNull():
        return None

    scaled = pixmap.scaled(
        width, height,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    x = (scaled.width() - width) // 2
    y = (scaled.height() - height) // 2
    result = scaled.copy(x, y, width, height)

    if cache_key:
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
    """Reusable badge row — also used by EventDetailsDialog."""
    labels = []
    if category:
        cat = QLabel(category)
        cat.setObjectName(theme.EVENT_CATEGORY_BADGE)
        cat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labels.append(cat)

    loc_text = "Remote" if is_remote else (location or "Location TBD")
    loc = QLabel(loc_text)
    loc.setObjectName(theme.EVENT_LOCATION_BADGE)
    loc.setAlignment(Qt.AlignmentFlag.AlignCenter)
    labels.append(loc)

    if status and status != "open":
        st = QLabel(status.upper())
        st.setObjectName(theme.EVENT_STATUS_BADGE)
        st.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labels.append(st)
    return labels


def make_meta_row(key, value):
    row = QHBoxLayout()
    row.setSpacing(6)
    row.setContentsMargins(0, 0, 0, 0)
    k = QLabel(f"{key}")
    k.setObjectName(theme.EVENT_META_KEY)
    v = QLabel(value)
    v.setObjectName(theme.EVENT_META_VALUE)
    v.setWordWrap(True)
    row.addWidget(k)
    row.addWidget(v, 1)
    return row


class EventCard(QFrame):
    openLinkRequested = pyqtSignal(str)     # external website URL
    rsvpRequested = pyqtSignal(int)         # opportunityID
    detailsRequested = pyqtSignal(object)   # the card itself

    GRID_WIDTH = 300
    GRID_THUMB_H = 150
    GRID_FIXED_HEIGHT = 465
    LIST_THUMB_W = 220
    LIST_THUMB_H = 160
    LIST_MIN_HEIGHT = 160

    def __init__(self, row, view_mode="grid", parent=None,
                 current_volunteer_id=None):
        super().__init__(parent)
        self.setObjectName(theme.EVENT_CARD)
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

        # Derive "full" from capacity so an org doesn't have to flip the
        # status by hand after the last spot goes.
        if (self.status == "open" and self.capacity
                and self.registered_count >= self.capacity):
            self.status = "full"

        if view_mode == "list":
            self._build_list_layout()
        else:
            self._build_grid_layout()

    # ── shared sub-builders ───────────────────────────────────────────────
    def _make_thumbnail(self, w, h):
        thumb = QLabel()
        thumb.setObjectName(theme.EVENT_THUMB)
        thumb.setFixedSize(w, h)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setScaledContents(False)
        pixmap = load_thumbnail_pixmap(
            self.thumbnail, w, h, key=self.opportunityID or None
        )
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
            org.setObjectName(theme.EVENT_ORG)
            row.addWidget(org)
        row.addStretch(1)
        return row

    def _make_link_button(self):
        btn = QPushButton("Open link" if self.website_link else "No link")
        btn.setObjectName(theme.EVENT_LINK_BTN)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setEnabled(bool(self.website_link))
        btn.clicked.connect(self.open_link)
        return btn

    def _rsvp_label(self):
        if self.status == "open":
            return "RSVP"
        if self.status == "full":
            return "Full"
        return self.status.capitalize()

    def _make_rsvp_button(self):
        btn = QPushButton(self._rsvp_label())
        btn.setObjectName(theme.EVENT_RSVP_BTN)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self.status == "open":
            # Stay clickable when logged out so the page can show the
            # login prompt; a greyed-out button gives no feedback.
            btn.setEnabled(True)
            btn.setToolTip(
                "RSVP for this event" if self.current_volunteer_id
                else "Log in as a volunteer to RSVP"
            )
        else:
            btn.setEnabled(False)
            btn.setToolTip(f"This event is {self.status}")
        btn.clicked.connect(self.request_rsvp)
        return btn

    def _date_text(self):
        text = self.event_date or "TBD"
        if self.start_time and self.end_time:
            text += f" · {self.start_time}–{self.end_time}"
        elif self.start_time:
            text += f" · {self.start_time}"
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
        lbl.setObjectName(theme.EVENT_ORG)
        lbl.setWordWrap(True)
        return lbl

    # ── grid layout ───────────────────────────────────────────────────────
    def _build_grid_layout(self):
        self.setFixedWidth(self.GRID_WIDTH)
        self.setFixedHeight(self.GRID_FIXED_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            self._make_thumbnail(self.GRID_WIDTH, self.GRID_THUMB_H)
        )

        content = QVBoxLayout()
        content.setContentsMargins(16, 14, 16, 14)
        content.setSpacing(10)

        content.addLayout(self._make_badges())

        title_lbl = QLabel(truncate_text(self.title, 60))
        title_lbl.setObjectName(theme.EVENT_TITLE)
        title_lbl.setWordWrap(True)
        title_lbl.setMaximumHeight(44)
        title_lbl.setToolTip(self.title)
        content.addWidget(title_lbl)

        content.addWidget(self._make_org_line())

        desc_lbl = QLabel(truncate_text(self.description, 120))
        desc_lbl.setObjectName(theme.EVENT_DESCRIPTION)
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

    # ── list layout ───────────────────────────────────────────────────────
    def _build_list_layout(self):
        self.setMinimumHeight(self.LIST_MIN_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Minimum)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            self._make_thumbnail(self.LIST_THUMB_W, self.LIST_THUMB_H)
        )

        content = QVBoxLayout()
        content.setContentsMargins(20, 16, 20, 16)
        content.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(16)

        title_lbl = QLabel(self.title)
        title_lbl.setObjectName(theme.EVENT_TITLE_LIST)
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
        desc_lbl.setObjectName(theme.EVENT_DESCRIPTION)
        desc_lbl.setWordWrap(True)
        desc_lbl.setMaximumHeight(60)
        content.addWidget(desc_lbl)

        content.addLayout(self._make_date_line())
        content.addStretch(1)

        layout.addLayout(content, 1)

    # ── events ────────────────────────────────────────────────────────────
    def open_link(self):
        if self.website_link:
            self.openLinkRequested.emit(self.website_link)

    def request_rsvp(self):
        if self.opportunityID:
            self.rsvpRequested.emit(self.opportunityID)

    def mouseReleaseEvent(self, event):
        # Buttons consume their own clicks; anything else opens the dialog.
        if (event.button() == Qt.MouseButton.LeftButton
                and self.rect().contains(event.position().toPoint())):
            self.detailsRequested.emit(self)
        super().mouseReleaseEvent(event)