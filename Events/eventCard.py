"""eventCard.py — the opportunity card used in grid + list views."""
import hashlib
import os
import urllib.request
import urllib.error

from PyQt6.QtCore import Qt, QByteArray, pyqtSignal, QRectF
from PyQt6.QtGui import QPixmap, QCursor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QWidget,
)

from Events.dateFormat import format_event_when
import Events.theme as theme

FALLBACK_IMAGE = theme.asset("noThumbnail.png")
THUMB_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".thumb_cache"
)

_PIXMAP_CACHE = {}
_PIXMAP_CACHE_LIMIT = 300
USER_AGENT = "Moxie/1.0"
THUMB_RADIUS = 12


def clear_thumbnail_cache():
    _PIXMAP_CACHE.clear()


def _cache_path_for(url: str) -> str:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    ext = os.path.splitext(url.split("?")[0])[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"):
        ext = ".img"
    return os.path.join(THUMB_CACHE_DIR, h + ext)


def _fetch_remote_bytes(url: str, timeout: int = 8) -> bytes:
    os.makedirs(THUMB_CACHE_DIR, exist_ok=True)
    cache_path = _cache_path_for(url)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                return f.read()
        except OSError:
            pass
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"[thumb] fetch failed for {url[:60]}: {e}")
        return b""
    try:
        with open(cache_path, "wb") as f:
            f.write(data)
    except OSError:
        pass
    return data


def _fit_centered(pixmap, width, height, radius=None):
    scaled = pixmap.scaled(
        width, height,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    canvas = QPixmap(width, height)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    if radius:
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, width, height), radius, radius)
        painter.setClipPath(path)
    x = (scaled.width() - width) // 2
    y = (scaled.height() - height) // 2
    painter.drawPixmap(0, 0, scaled, x, y, width, height)
    painter.end()
    return canvas


def load_thumbnail_pixmap(blob, width, height, key=None, radius=None):
    cache_key = (key, width, height, radius) if key is not None else None
    if cache_key and cache_key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[cache_key]

    pixmap = QPixmap()
    if isinstance(blob, str) and blob:
        if blob.startswith("http://") or blob.startswith("https://"):
            data = _fetch_remote_bytes(blob)
            if data:
                pixmap.loadFromData(QByteArray(data))
        elif blob.startswith("/"):
            data = _fetch_remote_bytes("https:" + blob)
            if data:
                pixmap.loadFromData(QByteArray(data))
        else:
            pixmap = QPixmap(blob)
    elif isinstance(blob, (bytes, bytearray)) and blob:
        pixmap.loadFromData(QByteArray(bytes(blob)))

    if pixmap.isNull() and os.path.exists(FALLBACK_IMAGE):
        pixmap = QPixmap(FALLBACK_IMAGE)
    if pixmap.isNull():
        return None

    result = _fit_centered(pixmap, width, height, radius=radius)
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
    return cut + "..."


def build_badges(category, is_remote, location, status):
    """Legacy helper — kept for eventDetailsDialog compatibility."""
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
    """Legacy helper — kept for eventDetailsDialog compatibility."""
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
    openLinkRequested = pyqtSignal(str)
    rsvpRequested = pyqtSignal(int)
    detailsRequested = pyqtSignal(object)

    GRID_WIDTH = 300
    GRID_THUMB_H = 160
    GRID_FIXED_HEIGHT = 500
    LIST_THUMB_W = 240
    LIST_THUMB_H = 160
    LIST_MIN_HEIGHT = 190

    def __init__(self, row, view_mode="grid", parent=None,
                 current_volunteer_id=None, bookmarked_ids=None):
        super().__init__(parent)

        self.row = row
        self.view_mode = view_mode
        self.current_volunteer_id = current_volunteer_id
        self._bookmarked_ids = set(bookmarked_ids or set())
        self._bookmark_cb = None

        def g(key, default=""):
            try:
                v = row[key]
            except (KeyError, IndexError, TypeError):
                return default
            return v if v is not None else default

        try:
            self.is_moxie_org = bool(int(g("is_moxie_org", 0) or 0))
        except (TypeError, ValueError):
            self.is_moxie_org = False

        self.setObjectName(
            "EventCardMoxie" if self.is_moxie_org else theme.EVENT_CARD
        )
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.opportunityID = g("opportunityID", 0)
        self.title = g("title", "Untitled event")
        self.description = g("description", "")
        self.category = g("category", "")
        self.location = g("location", "")
        self.city = g("city", "")
        self.state = g("state", "GA")
        self.is_remote = bool(g("is_remote", 0))
        self.event_date = g("event_date", "")
        self.event_end_date = g("event_end_date", "")
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

        if (self.status == "open" and self.capacity
                and self.registered_count >= self.capacity):
            self.status = "full"

        if view_mode == "list":
            self._build_list_layout()
        else:
            self._build_grid_layout()

    # ── Bookmark ──────────────────────────────────────────────────────
    def _is_bookmarked(self):
        if not self.current_volunteer_id or not self._bookmarked_ids:
            return False
        return self.opportunityID in self._bookmarked_ids

    def set_bookmark_callback(self, fn):
        self._bookmark_cb = fn

    def _make_bookmark_button(self):
        on = self._is_bookmarked()
        btn = QPushButton("★" if on else "☆")
        btn.setObjectName(
            theme.EVENT_BOOKMARK_BTN_ON if on else theme.EVENT_BOOKMARK_BTN
        )
        btn.setFixedSize(34, 34)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setToolTip("Remove bookmark" if on else "Bookmark this event")
        btn.setEnabled(bool(self.current_volunteer_id))
        if not self.current_volunteer_id:
            btn.setToolTip("Log in as a volunteer to bookmark events")
        btn.clicked.connect(self._toggle_bookmark)
        return btn

    def _toggle_bookmark(self):
        if not self.current_volunteer_id:
            return
        emit_add = self.opportunityID not in self._bookmarked_ids
        if emit_add:
            self._bookmarked_ids.add(self.opportunityID)
        else:
            self._bookmarked_ids.discard(self.opportunityID)
        on = self._is_bookmarked()
        self._refresh_bookmark_button()
        if self._bookmark_cb:
            self._bookmark_cb(self.opportunityID, on)

    def _refresh_bookmark_button(self):
        for b in self.findChildren(QPushButton):
            if b.objectName() in (
                theme.EVENT_BOOKMARK_BTN,
                theme.EVENT_BOOKMARK_BTN_ON,
            ):
                on = self._is_bookmarked()
                b.setText("★" if on else "☆")
                b.setObjectName(
                    theme.EVENT_BOOKMARK_BTN_ON if on
                    else theme.EVENT_BOOKMARK_BTN
                )
                b.style().unpolish(b)
                b.style().polish(b)
                return

    # ── Thumbnail ─────────────────────────────────────────────────────
    def _make_thumbnail(self, w, h, with_bookmark=False):
        wrap = QWidget()
        wrap.setFixedSize(w, h)
        wrap.setObjectName(theme.EVENT_THUMB)

        thumb = QLabel(wrap)
        thumb.setObjectName(theme.EVENT_THUMB)
        thumb.setGeometry(0, 0, w, h)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setScaledContents(False)

        pixmap = load_thumbnail_pixmap(
            self.thumbnail, w, h,
            key=self.opportunityID or None,
            radius=THUMB_RADIUS,
        )
        if pixmap is not None:
            thumb.setPixmap(pixmap)
        else:
            thumb.setText("No image")

        # Source pill (top-left)
        source = QLabel("Moxie" if self.is_moxie_org else "External", wrap)
        source.setObjectName(
            theme.EVENT_SOURCE_MOXIE if self.is_moxie_org
            else theme.EVENT_SOURCE_EXTERNAL
        )
        source.adjustSize()
        source.move(12, 12)
        source.raise_()

        # Bookmark overlay (top-right) — grid view only
        if with_bookmark:
            bm = self._make_bookmark_button()
            bm.setParent(wrap)
            bm.setFixedSize(34, 34)
            bm.move(w - bm.width() - 12, 12)
            bm.raise_()

        return wrap

    # ── Chips / meta ──────────────────────────────────────────────────
    def _make_cluster_chip(self):
        label = self.category or "General"
        chip = QLabel(label)
        chip.setObjectName(theme.EVENT_CLUSTER_CHIP)
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return chip

    def _date_text(self):
        return format_event_when(self.row)

    def _location_text(self):
        if self.is_remote:
            return "Remote"
        if self.city and self.state:
            return f"{self.city}, {self.state}"
        return self.location or "Location TBD"

    def _spots_text(self):
        if not self.capacity:
            return ""
        left = max(0, self.capacity - self.registered_count)
        if left == 0:
            return "Full"
        if left == 1:
            return "1 spot left"
        return f"{left} of {self.capacity} spots"

    def _make_meta_columns(self):
        """Two-column meta grid: Date | Where, and Spots below."""
        wrap = QWidget()
        wrap.setObjectName(theme.EVENT_CARD_BODY)
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setSpacing(20)
        row1.addLayout(self._meta_block("DATE", self._date_text()), 1)
        row1.addLayout(
            self._meta_block("WHERE", self._location_text()), 1
        )
        v.addLayout(row1)

        spots = self._spots_text()
        if spots:
            v.addLayout(self._meta_block("SPOTS", spots))
        return wrap
    def _make_meta_line(self):
        """Compact single-line meta for the list view."""
        parts = []
        date_txt = self._date_text() or "TBD"
        parts.append(f"Date: {date_txt}")

        where = self._location_text()
        if where:
            parts.append(f"Where: {where}")

        spots = self._spots_text()
        if spots:
            parts.append(f"Spots: {spots}")

        label = QLabel("   ·   ".join(parts))
        label.setObjectName(theme.EVENT_META_VALUE)
        label.setWordWrap(True)
        return label
    @staticmethod
    def _meta_block(label_text, value_text):
        block = QVBoxLayout()
        block.setSpacing(2)
        block.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label_text)
        lbl.setObjectName(theme.EVENT_CARD_META_ICON)
        val = QLabel(value_text)
        val.setObjectName(theme.EVENT_META_VALUE)
        val.setWordWrap(True)
        block.addWidget(lbl)
        block.addWidget(val)
        return block

    # ── RSVP / link / details ─────────────────────────────────────────
    def _rsvp_label(self):
        if self.status == "open":
            action = "Sign up" if self.is_moxie_org else "RSVP"
            if not self.current_volunteer_id:
                return f"Log in to {action}"
            return action
        if self.status == "full":
            return "Full"
        return self.status.capitalize()

    def _make_rsvp_button(self):
        btn = QPushButton(self._rsvp_label())
        btn.setObjectName(theme.EVENT_RSVP_BTN)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setMinimumHeight(36)
        if self.status == "open":
            btn.setEnabled(True)
        else:
            btn.setEnabled(False)
        btn.clicked.connect(self.request_rsvp)
        return btn

    def _make_details_button(self):
        btn = QPushButton("Open Details")
        btn.setObjectName(theme.EVENT_DETAILS_BTN)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setMinimumHeight(28)   # was 36
        btn.clicked.connect(self.request_details)
        return btn

    def _make_link_button(self):
        btn = QPushButton("Link" if self.website_link else "No link")
        btn.setObjectName(theme.EVENT_LINK_BTN)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setMinimumHeight(36)
        btn.setEnabled(bool(self.website_link))
        btn.clicked.connect(self.open_link)
        return btn

    # ── Grid layout ───────────────────────────────────────────────────
    def _build_grid_layout(self):
        self.setFixedWidth(self.GRID_WIDTH)
        self.setFixedHeight(self.GRID_FIXED_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed,
                           QSizePolicy.Policy.Fixed)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Image with a bookmark overlay in the top-right corner
        outer.addWidget(
            self._make_thumbnail(
                self.GRID_WIDTH, self.GRID_THUMB_H,
                with_bookmark=True,
            )
        )

        body = QWidget()
        body.setObjectName(theme.EVENT_CARD_BODY)
        v = QVBoxLayout(body)
        v.setContentsMargins(18, 14, 18, 16)
        v.setSpacing(10)

        v.addWidget(self._make_cluster_chip())

        title = QLabel(truncate_text(self.title, 68))
        title.setObjectName(theme.EVENT_TITLE)
        title.setWordWrap(True)
        title.setMinimumHeight(40)
        title.setToolTip(self.title)
        v.addWidget(title)

        org = QLabel(f"by {self.org_name}")
        org.setObjectName(theme.EVENT_ORG)
        org.setWordWrap(True)
        v.addWidget(org)

        desc = QLabel(truncate_text(self.description, 110))
        desc.setObjectName(theme.EVENT_DESCRIPTION)
        desc.setWordWrap(True)
        desc.setMinimumHeight(36)
        desc.setMaximumHeight(56)
        v.addWidget(desc)

        v.addWidget(self._make_meta_columns())
        v.addStretch(1)

        # Action row: RSVP + Link, equal width
        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self._make_rsvp_button(), 1)
        actions.addWidget(self._make_link_button(), 1)
        v.addLayout(actions)

        # Open Details on its own row so nothing gets truncated
        v.addWidget(self._make_details_button())

        outer.addWidget(body, 1)
    # ── List layout ───────────────────────────────────────────────────
    def _build_list_layout(self):
        self.setMinimumHeight(self.LIST_MIN_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Minimum)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(18)

        outer.addWidget(
            self._make_thumbnail(self.LIST_THUMB_W, self.LIST_THUMB_H),
            0, Qt.AlignmentFlag.AlignTop,
        )

        body = QWidget()
        body.setObjectName(theme.EVENT_CARD_BODY)
        v = QVBoxLayout(body)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        # Title + bookmark
        top = QHBoxLayout()
        top.setSpacing(12)
        title = QLabel(self.title)
        title.setObjectName(theme.EVENT_TITLE_LIST)
        title.setWordWrap(True)
        top.addWidget(title, 1)
        top.addWidget(self._make_bookmark_button())
        v.addLayout(top)

        org = QLabel(f"by {self.org_name}")
        org.setObjectName(theme.EVENT_ORG)
        org.setWordWrap(True)
        v.addWidget(org)

        # Chip row
        chips = QHBoxLayout()
        chips.setSpacing(6)
        chips.addWidget(self._make_cluster_chip())
        chips.addStretch(1)
        v.addLayout(chips)

        # One-line description
        desc = QLabel(truncate_text(self.description, 240))
        desc.setObjectName(theme.EVENT_DESCRIPTION)
        desc.setWordWrap(True)
        v.addWidget(desc)

        # Single compact meta line
        v.addWidget(self._make_meta_line())

        v.addStretch(1)

        # Actions right-aligned, minimum width so they never
        # get squeezed into truncated labels
        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch(1)
        link = self._make_link_button()
        rsvp = self._make_rsvp_button()
        details = self._make_details_button()
        for btn in (link, rsvp, details):
            btn.setMinimumWidth(140)
        actions.addWidget(link)
        actions.addWidget(rsvp)
        actions.addWidget(details)
        v.addLayout(actions)

        outer.addWidget(body, 1)
    # ── Events ────────────────────────────────────────────────────────
    def open_link(self):
        if self.website_link:
            self.openLinkRequested.emit(self.website_link)

    def request_rsvp(self):
        if self.opportunityID:
            self.rsvpRequested.emit(self.opportunityID)

    def request_details(self):
        self.detailsRequested.emit(self)

    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and self.rect().contains(event.position().toPoint())):
            self.detailsRequested.emit(self)
        super().mouseReleaseEvent(event)