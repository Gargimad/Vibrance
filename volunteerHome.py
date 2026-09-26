"""
volunteerHome.py — Volunteer dashboard.

Tabs in a QStackedWidget. Tab buttons live in landing.py's top nav bar.
    0. Dashboard       summary of every other tab + statistics
    1. Calendar        month view, color-coded by organization
    2. My Events       signups with check-in / check-out / cancel
    3. Organizations   join / leave organizations
    4. Notifications   list of notifications for this user
    5. Help            AI chatbot (Anthropic API)
    6. Profile         edit profile, notification setting, password
"""

import calendar
import html
import json
import os
import urllib.error
import urllib.request
import zlib
from datetime import date, timedelta

from PyQt6.QtCore import Qt, QPointF, QRectF, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPalette
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QStackedWidget, QScrollArea, QMessageBox,
    QCalendarWidget, QLineEdit, QTextBrowser, QCheckBox, QFormLayout,
    QGridLayout, QProgressBar,
)

import theme


# ── Constants ─────────────────────────────────────────────────────────────
ISO = "yyyy-MM-dd"

ORG_PALETTE = [
    "#2E86DE", "#E67E22", "#27AE60", "#C0392B", "#8E44AD",
    "#16A085", "#D4AC0D", "#E84393", "#5D6D7E", "#00A8CC",
]
INDEPENDENT_COLOR = "#7F8C8D"

CLAUDE_MODEL = "claude-sonnet-5"
CLAUDE_URL = "https://api.anthropic.com/v1/messages"

TAB_DASHBOARD, TAB_CALENDAR, TAB_EVENTS, TAB_ORGS = 0, 1, 2, 3
TAB_NOTIFS, TAB_HELP, TAB_PROFILE = 4, 5, 6

# Cap on how far we'll expand a multi-day event onto the calendar
MAX_RANGE_DAYS = 90


# ── Small helpers ─────────────────────────────────────────────────────────
def rget(row, key, default=None):
    try:
        val = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if val is None else val


def org_color(org_name):
    if not org_name:
        return INDEPENDENT_COLOR
    return ORG_PALETTE[zlib.crc32(org_name.encode("utf-8")) % len(ORG_PALETTE)]


def time_range(row):
    start, end = rget(row, "start_time"), rget(row, "end_time")
    if not start:
        return ""
    return f" · {start}" + (f"–{end}" if end else "")


def date_range(row):
    """
    Human-readable date string for a row, handling multi-day ranges.
    Examples:
        ("2026-09-01", None)                 -> "2026-09-01"
        ("2026-09-01", "2026-09-03")         -> "2026-09-01 → 2026-09-03"
        ("Ongoing", None)                    -> "Ongoing"
    """
    start = str(rget(row, "event_date", "") or "").strip()
    end = str(rget(row, "event_end_date", "") or "").strip()
    if not start:
        return "TBD"
    if end and end != start:
        return f"{start} → {end}"
    return start


def expand_to_days(start_str, end_str):
    """
    Yield ISO date strings for every day in [start, end] inclusive.
    Returns nothing if start can't be parsed as YYYY-MM-DD.
    Ranges longer than MAX_RANGE_DAYS collapse to just the start day.
    """
    if not start_str:
        return
    try:
        start = date.fromisoformat(str(start_str)[:10])
    except ValueError:
        return
    end = start
    if end_str:
        try:
            end = date.fromisoformat(str(end_str)[:10])
        except ValueError:
            end = start
    if (end - start).days > MAX_RANGE_DAYS:
        end = start

    cur = start
    while cur <= end:
        yield cur.isoformat()
        cur += timedelta(days=1)


# ── Calendar widget with colored dots ─────────────────────────────────────
class EventCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.events_by_date = {}
        self.setGridVisible(True)
        self.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.setHorizontalHeaderFormat(
            QCalendarWidget.HorizontalHeaderFormat.ShortDayNames
        )

    def set_events(self, events_by_date):
        self.events_by_date = events_by_date
        self.updateCells()

    def paintCell(self, painter, rect, d):
        super().paintCell(painter, rect, d)
        events = self.events_by_date.get(d.toString(ISO))
        if not events:
            return

        colors = []
        for e in events:
            c = org_color(rget(e, "org_name"))
            if c not in colors:
                colors.append(c)
        colors = colors[:4]

        radius, gap = 4.5, 3.0
        total = len(colors) * radius * 2 + (len(colors) - 1) * gap
        x = rect.center().x() - total / 2 + radius
        y = rect.bottom() - radius - 4

        painter.save()
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        for c in colors:
            painter.setBrush(QColor(c))
            painter.drawEllipse(QPointF(x, y), radius, radius)
            x += radius * 2 + gap
        painter.restore()


# ── Small bar chart ───────────────────────────────────────────────────────
class MonthlyBars(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.setMinimumHeight(160)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = self.palette().color(QPalette.ColorRole.WindowText)

        w, h = self.width(), self.height()
        top, bottom = 18, 22
        n = len(self.data)
        slot = w / n
        bar_w = min(42.0, slot * 0.55)
        max_v = max(v for _, v in self.data) or 1.0

        for i, (label, v) in enumerate(self.data):
            bar_h = (h - top - bottom) * (v / max_v)
            x = slot * i + (slot - bar_w) / 2
            y = h - bottom - bar_h
            if v > 0:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor("#2E86DE"))
                p.drawRoundedRect(QRectF(x, y, bar_w, bar_h), 4, 4)
                p.setPen(text)
                p.drawText(QRectF(slot * i, y - 16, slot, 14),
                           Qt.AlignmentFlag.AlignCenter, f"{v:.1f}")
            p.setPen(text)
            p.drawText(QRectF(slot * i, h - bottom + 3, slot, bottom - 3),
                       Qt.AlignmentFlag.AlignCenter, label)
        p.end()


# ── Background worker for the chatbot ─────────────────────────────────────
class ChatWorker(QThread):
    reply = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, messages, system, parent=None):
        super().__init__(parent)
        self.messages = messages
        self.system = system

    def run(self):
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            self.failed.emit(
                "The chatbot isn't configured yet (missing ANTHROPIC_API_KEY)."
            )
            return

        body = json.dumps({
            "model": CLAUDE_MODEL,
            "max_tokens": 800,
            "system": self.system,
            "messages": self.messages,
        }).encode("utf-8")
        req = urllib.request.Request(
            CLAUDE_URL,
            data=body,
            headers={
                "content-type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            text = "".join(
                b.get("text", "")
                for b in data.get("content", [])
                if b.get("type") == "text"
            ).strip()
            self.reply.emit(text or "(No response)")
        except urllib.error.HTTPError as e:
            self.failed.emit(f"The assistant returned an error ({e.code}).")
        except Exception as e:
            self.failed.emit(f"Couldn't reach the assistant: {e}")


# ── Main widget ───────────────────────────────────────────────────────────
class VolunteerHome(QWidget):
    TAB_LABELS = [
        "Dashboard", "Calendar", "My Events", "Organizations",
        "Notifications", "Help", "Profile",
    ]

    tabChanged = pyqtSignal(int)

    def __init__(self, on_logout_click=None, db=None, parent=None):
        super().__init__(parent)
        self.on_logout_click = on_logout_click
        self.db = db
        self.user_data = None
        self.userID = None

        self._chat_history = []
        self._chat_worker = None
        self._signup_rows = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_overview_page())
        self.stack.addWidget(self._build_calendar_page())
        self.stack.addWidget(self._build_events_page())
        self.stack.addWidget(self._build_orgs_page())
        self.stack.addWidget(self._build_notifications_page())
        self.stack.addWidget(self._build_help_page())
        self.stack.addWidget(self._build_profile_page())
        outer.addWidget(self.stack, 1)

        outer.addWidget(self._build_slogan_bar(), 0)

    # ── DB access ─────────────────────────────────────────────────────────
    def _db(self, method, *args, default=None):
        fn = getattr(self.db, method, None) if self.db else None
        if fn is None:
            print(f"Database.{method}() is not implemented yet")
            return default
        try:
            return fn(*args)
        except Exception as e:
            print(f"Database.{method}() failed:", e)
            return default

    def _db_action(self, method, *args):
        fn = getattr(self.db, method, None) if self.db else None
        if fn is None:
            QMessageBox.information(
                self, "Not available",
                f"This feature needs Database.{method}() to be implemented."
            )
            return False
        try:
            ok = fn(*args)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return False
        return bool(ok)

    def _build_slogan_bar(self):
        bar = QWidget()
        bar.setObjectName(theme.BOTTOM_BAR)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 20, 20, 20)
        slogan = QLabel("Ready to make a difference in your community today?")
        slogan.setObjectName(theme.SLOGAN_TEXT)
        slogan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(slogan)
        return bar

    # ── Reusable page scaffolding ─────────────────────────────────────────
    def _scroll_page(self, heading_text, spacing=10):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 20, 40, 20)
        lay.setSpacing(10)

        heading = QLabel(heading_text)
        heading.setObjectName(theme.SECTION_TITLE)
        lay.addWidget(heading)

        top = QVBoxLayout()
        top.setSpacing(8)
        lay.addLayout(top)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setObjectName(theme.HOME_SCROLL)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(spacing)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        lay.addWidget(scroll, 1)
        return page, content_layout, top

    def _clear(self, layout):
        while layout.count() > 1:
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

    def _add(self, layout, widget):
        layout.insertWidget(layout.count() - 1, widget)

    def _empty(self, layout, text):
        lbl = QLabel(text)
        lbl.setObjectName(theme.VOLUNTEER_EMPTY)
        layout.insertWidget(0, lbl)

    @staticmethod
    def _swatch(color, size=12):
        s = QLabel()
        s.setFixedSize(size, size)
        s.setStyleSheet(
            f"background-color: {color}; border-radius: {size // 2}px;"
        )
        return s

    # ── 0. Dashboard ──────────────────────────────────────────────────────
    def _dash_card(self, title, link_text=None, tab=None):
        card = QFrame()
        card.setObjectName(theme.EVENT_CARD)
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(8)

        head = QHBoxLayout()
        t = QLabel(title)
        t.setObjectName(theme.EVENT_TITLE_LIST)
        head.addWidget(t)
        head.addStretch(1)
        if tab is not None:
            b = QPushButton(f"{link_text} →")
            b.setFlat(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton { border: none; color: #2E86DE; }"
                "QPushButton:hover { text-decoration: underline; }"
            )
            b.clicked.connect(lambda _, i=tab: self.show_tab(i))
            head.addWidget(b)
        v.addLayout(head)

        body = QVBoxLayout()
        body.setSpacing(6)
        v.addLayout(body)
        return card, body

    def _build_overview_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setObjectName(theme.HOME_SCROLL)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(40, 20, 40, 20)
        lay.setSpacing(16)

        self.welcome_title = QLabel("Welcome Back!")
        self.welcome_title.setObjectName(theme.FORM_TITLE)
        self.user_info_label = QLabel("")
        self.user_info_label.setObjectName(theme.FORM_SUBTITLE)
        lay.addWidget(self.welcome_title)
        lay.addWidget(self.user_info_label)

        tiles = QHBoxLayout()
        tiles.setSpacing(10)
        self.tile_values = {}
        for key, caption in [
            ("hours", "Hours logged"),
            ("completed", "Events completed"),
            ("upcoming", "Upcoming events"),
            ("signups", "Total signups"),
            ("orgs", "Organizations"),
            ("rate", "Completion rate"),
        ]:
            tile = QFrame()
            tile.setObjectName(theme.EVENT_CARD)
            tl = QVBoxLayout(tile)
            tl.setContentsMargins(14, 12, 14, 12)
            tl.setSpacing(2)
            val = QLabel("–")
            val.setStyleSheet("font-size: 26px; font-weight: bold;")
            cap = QLabel(caption)
            cap.setObjectName(theme.EVENT_META_VALUE)
            cap.setWordWrap(True)
            tl.addWidget(val)
            tl.addWidget(cap)
            self.tile_values[key] = val
            tiles.addWidget(tile, 1)
        lay.addLayout(tiles)

        rec_card, self.dash_recommended = self._dash_card(
            "Recommended for you", "Browse all", TAB_DASHBOARD
        )
        rec_wrap = QGridLayout()
        rec_wrap.addWidget(rec_card, 0, 0)
        lay.addLayout(rec_wrap)

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        card, self.dash_upcoming = self._dash_card(
            "Upcoming events", "View calendar", TAB_CALENDAR)
        grid.addWidget(card, 0, 0)

        card, body = self._dash_card("Hours by month")
        self.dash_chart = MonthlyBars()
        body.addWidget(self.dash_chart)
        grid.addWidget(card, 0, 1)

        card, self.dash_org_hours = self._dash_card(
            "Hours by organization", "My events", TAB_EVENTS)
        grid.addWidget(card, 1, 0)

        card, self.dash_orgs = self._dash_card(
            "My organizations", "Manage", TAB_ORGS)
        grid.addWidget(card, 1, 1)
        lay.addLayout(grid)

        card, self.dash_notifs = self._dash_card(
            "Recent notifications", "View all", TAB_NOTIFS)
        lay.addWidget(card)

        help_card = QFrame()
        help_card.setObjectName(theme.EVENT_CARD)
        hl = QHBoxLayout(help_card)
        hl.setContentsMargins(16, 12, 16, 12)
        q = QLabel("Questions about check-ins, hours, or finding events?")
        q.setObjectName(theme.EVENT_META_VALUE)
        ask = QPushButton("Ask the assistant")
        ask.setObjectName(theme.PRIMARY_BTN)
        ask.setCursor(Qt.CursorShape.PointingHandCursor)
        ask.clicked.connect(lambda: self.show_tab(TAB_HELP))
        hl.addWidget(q, 1)
        hl.addWidget(ask)
        lay.addWidget(help_card)

        lay.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return page

    # ── 1. Calendar ───────────────────────────────────────────────────────
    def _build_calendar_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 20, 40, 20)
        lay.setSpacing(10)

        heading = QLabel("My Calendar")
        heading.setObjectName(theme.SECTION_TITLE)
        lay.addWidget(heading)

        body = QHBoxLayout()
        body.setSpacing(20)

        left = QVBoxLayout()
        self.calendar = EventCalendar()
        self.calendar.selectionChanged.connect(self._refresh_day_list)
        left.addWidget(self.calendar, 1)

        self.legend_layout = QHBoxLayout()
        self.legend_layout.setSpacing(14)
        left.addLayout(self.legend_layout)

        right = QVBoxLayout()
        self.day_heading = QLabel("")
        self.day_heading.setObjectName(theme.SECTION_TITLE)
        right.addWidget(self.day_heading)

        self.day_scroll = QScrollArea()
        self.day_scroll.setWidgetResizable(True)
        self.day_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.day_scroll.setObjectName(theme.HOME_SCROLL)
        day_content = QWidget()
        self.day_layout = QVBoxLayout(day_content)
        self.day_layout.setContentsMargins(0, 0, 0, 0)
        self.day_layout.setSpacing(8)
        self.day_layout.addStretch(1)
        self.day_scroll.setWidget(day_content)
        right.addWidget(self.day_scroll, 1)

        body.addLayout(left, 3)
        body.addLayout(right, 2)
        lay.addLayout(body, 1)
        return page

    def _refresh_calendar(self):
        """
        Fetch every signup, expand each into the days it spans, and bucket
        by ISO date. A Sept 1 → Sept 15 event lands in all fifteen buckets,
        so the calendar draws a dot on every day of the range.
        """
        rows = self._db("getSignupsForVolunteer", self.userID, default=[]) \
            if self.userID else []
        rows = [r for r in rows if (rget(r, "status", "") or "") != "cancelled"]
        self._signup_rows = rows

        by_date = {}
        orgs = {}
        for r in rows:
            start = str(rget(r, "event_date", "") or "")
            end = str(rget(r, "event_end_date", "") or "") or start
            for iso in expand_to_days(start, end):
                by_date.setdefault(iso, []).append(r)
            name = rget(r, "org_name") or "Independent"
            orgs[name] = org_color(rget(r, "org_name"))
        self.calendar.set_events(by_date)

        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for name in sorted(orgs):
            wrap = QWidget()
            wl = QHBoxLayout(wrap)
            wl.setContentsMargins(0, 0, 0, 0)
            wl.setSpacing(5)
            wl.addWidget(self._swatch(orgs[name]))
            wl.addWidget(QLabel(name))
            self.legend_layout.addWidget(wrap)
        self.legend_layout.addStretch(1)

        self._refresh_day_list()

    def _refresh_day_list(self):
        d = self.calendar.selectedDate()
        self.day_heading.setText(d.toString("dddd, MMMM d"))
        self._clear(self.day_layout)
        events = self.calendar.events_by_date.get(d.toString(ISO), [])
        if not events:
            self._empty(self.day_layout, "No events on this day.")
            return
        for r in events:
            self._add(self.day_layout, self._make_day_card(r))

    def _make_day_card(self, r):
        color = org_color(rget(r, "org_name"))
        card = QFrame()
        card.setObjectName(theme.EVENT_CARD)
        card.setStyleSheet(
            f"QFrame#{theme.EVENT_CARD} {{ border-left: 6px solid {color}; }}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)

        title = QLabel(rget(r, "title", "Untitled event"))
        title.setObjectName(theme.EVENT_TITLE_LIST)
        meta = QLabel(
            f"{date_range(r)} · {rget(r, 'org_name', 'Independent')}"
            f"{time_range(r)}"
        )
        meta.setObjectName(theme.EVENT_META_VALUE)
        meta.setWordWrap(True)
        lay.addWidget(title)
        lay.addWidget(meta)
        return card

    # ── 2. My Events ──────────────────────────────────────────────────────
    def _build_events_page(self):
        page, self.events_layout, _ = self._scroll_page("My Registered Events")
        return page

    def _refresh_events(self):
        if not (self.db and self.userID):
            return
        self._clear(self.events_layout)
        rows = self._db("getSignupsForVolunteer", self.userID, default=[])

        if not rows:
            self._empty(self.events_layout,
                        "You haven't registered for anything yet.")
            return
        for r in rows:
            self._add(self.events_layout, self._make_signup_card(r))

    def _make_signup_card(self, r):
        color = org_color(rget(r, "org_name"))
        card = QFrame()
        card.setObjectName(theme.EVENT_CARD)
        card.setStyleSheet(
            f"QFrame#{theme.EVENT_CARD} {{ border-left: 6px solid {color}; }}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(6)

        title = QLabel(r["title"] or "Untitled event")
        title.setObjectName(theme.EVENT_TITLE_LIST)

        meta = QLabel(
            f"{date_range(r)}{time_range(r)}\n"
            f"{r['org_name'] or 'Independent'} · "
            f"status: {r['status'] or 'registered'}"
        )
        meta.setObjectName(theme.EVENT_META_VALUE)
        meta.setWordWrap(True)

        row = QHBoxLayout()
        row.setSpacing(8)

        if not r["check_in_time"]:
            ci = QPushButton("Check In")
            ci.setObjectName(theme.PRIMARY_BTN)
            ci.setCursor(Qt.CursorShape.PointingHandCursor)
            ci.clicked.connect(
                lambda _, oid=r["opportunityID"]: self._do_check_in(oid)
            )
            row.addWidget(ci)
        elif not r["check_out_time"]:
            co = QPushButton("Check Out")
            co.setObjectName(theme.PRIMARY_BTN)
            co.setCursor(Qt.CursorShape.PointingHandCursor)
            co.clicked.connect(
                lambda _, oid=r["opportunityID"]: self._do_check_out(oid)
            )
            row.addWidget(co)
        else:
            done = QLabel(f"✓ Logged {r['hours_logged'] or 0:.2f} hours")
            done.setObjectName(theme.EVENT_META_VALUE)
            row.addWidget(done)

        cancel = QPushButton("Cancel")
        cancel.setObjectName(theme.SECONDARY_BTN)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(
            lambda _, oid=r["opportunityID"]: self._do_cancel(oid)
        )
        row.addStretch(1)
        row.addWidget(cancel)

        lay.addWidget(title)
        lay.addWidget(meta)
        lay.addLayout(row)
        return card

    def _do_check_in(self, opportunityID):
        if self.db.checkIn(self.userID, opportunityID):
            self._after_signup_change()

    def _do_check_out(self, opportunityID):
        if self.db.checkOut(self.userID, opportunityID):
            self._after_signup_change()

    def _do_cancel(self, opportunityID):
        if QMessageBox.question(
            self, "Cancel RSVP", "Cancel your signup for this event?"
        ) != QMessageBox.StandardButton.Yes:
            return
        if self.db.cancelSignup(self.userID, opportunityID):
            self._after_signup_change()

    def _after_signup_change(self):
        self._refresh_events()
        self._refresh_dashboard()

    # ── 3. Organizations ──────────────────────────────────────────────────
    def _build_orgs_page(self):
        page, self.orgs_layout, top = self._scroll_page("Organizations")
        self.orgs_search = QLineEdit()
        self.orgs_search.setPlaceholderText("Search organizations…")
        self.orgs_search.setClearButtonEnabled(True)
        self.orgs_search.textChanged.connect(self._render_orgs)
        top.addWidget(self.orgs_search)
        self._org_rows = []
        return page

    def _refresh_orgs(self):
        if not (self.db and self.userID):
            return
        self._org_rows = self._db(
            "getOrganizations", self.userID, default=[]
        ) or []
        self._render_orgs()

    def _render_orgs(self):
        self._clear(self.orgs_layout)
        q = self.orgs_search.text().strip().lower()
        rows = [
            r for r in self._org_rows
            if not q or q in (
                f"{rget(r, 'name', '')} {rget(r, 'description', '')}".lower()
            )
        ]
        if not rows:
            self._empty(
                self.orgs_layout,
                "No matching organizations." if q
                else "No organizations available yet."
            )
            return
        rows.sort(key=lambda r: (not rget(r, "is_member", 0),
                                 str(rget(r, "name", "")).lower()))
        for r in rows:
            self._add(self.orgs_layout, self._make_org_card(r))

    def _make_org_card(self, r):
        name = rget(r, "name", "Unnamed organization")
        member = bool(rget(r, "is_member", 0))
        oid = r["organizationID"]

        card = QFrame()
        card.setObjectName(theme.EVENT_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(6)

        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(self._swatch(org_color(name), 14))
        title = QLabel(name)
        title.setObjectName(theme.EVENT_TITLE_LIST)
        head.addWidget(title)
        head.addStretch(1)
        lay.addLayout(head)

        desc = rget(r, "description")
        if desc:
            d = QLabel(desc)
            d.setObjectName(theme.EVENT_META_VALUE)
            d.setWordWrap(True)
            lay.addWidget(d)

        row = QHBoxLayout()
        if member:
            joined = QLabel("✓ Member")
            joined.setObjectName(theme.EVENT_META_VALUE)
            row.addWidget(joined)
            row.addStretch(1)
            leave = QPushButton("Leave")
            leave.setObjectName(theme.SECONDARY_BTN)
            leave.setCursor(Qt.CursorShape.PointingHandCursor)
            leave.clicked.connect(lambda _, o=oid, n=name: self._do_leave(o, n))
            row.addWidget(leave)
        else:
            row.addStretch(1)
            join = QPushButton("Join")
            join.setObjectName(theme.PRIMARY_BTN)
            join.setCursor(Qt.CursorShape.PointingHandCursor)
            join.clicked.connect(lambda _, o=oid: self._do_join(o))
            row.addWidget(join)
        lay.addLayout(row)
        return card

    def _do_join(self, orgID):
        if self._db_action("joinOrganization", self.userID, orgID):
            self._refresh_orgs()

    def _do_leave(self, orgID, name):
        if QMessageBox.question(
            self, "Leave organization", f"Leave {name}?"
        ) != QMessageBox.StandardButton.Yes:
            return
        if self._db_action("leaveOrganization", self.userID, orgID):
            self._refresh_orgs()

    # ── 4. Notifications ──────────────────────────────────────────────────
    def _build_notifications_page(self):
        page, self.notif_layout, _ = self._scroll_page(
            "Notifications", spacing=8
        )
        return page

    def _refresh_notifications(self):
        if not (self.db and self.userID):
            return
        self._clear(self.notif_layout)
        rows = self._db("getNotifications", self.userID, default=[])

        if not rows:
            self._empty(self.notif_layout, "No notifications yet.")
            return
        for r in rows:
            lbl = QLabel(
                f"<b>{html.escape(str(r['created_at']))}</b> — "
                f"{html.escape(str(r['message']))}"
            )
            lbl.setObjectName(theme.EVENT_META_VALUE)
            lbl.setWordWrap(True)
            self._add(self.notif_layout, lbl)

    # ── 5. Help ───────────────────────────────────────────────────────────
    def _build_help_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 20, 40, 20)
        lay.setSpacing(10)

        heading = QLabel("Help")
        heading.setObjectName(theme.SECTION_TITLE)
        sub = QLabel(
            "Ask anything about volunteering, checking in, hours, "
            "or how to use this app."
        )
        sub.setObjectName(theme.EVENT_META_VALUE)
        sub.setWordWrap(True)

        self.chat_view = QTextBrowser()
        self.chat_view.setOpenExternalLinks(True)
        self._chat_reset_view()

        row = QHBoxLayout()
        row.setSpacing(8)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your question…")
        self.chat_input.returnPressed.connect(self._send_chat)
        self.chat_send = QPushButton("Send")
        self.chat_send.setObjectName(theme.PRIMARY_BTN)
        self.chat_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_send.clicked.connect(self._send_chat)
        clear = QPushButton("New chat")
        clear.setObjectName(theme.SECONDARY_BTN)
        clear.setCursor(Qt.CursorShape.PointingHandCursor)
        clear.clicked.connect(self._chat_new)
        row.addWidget(self.chat_input, 1)
        row.addWidget(self.chat_send)
        row.addWidget(clear)

        lay.addWidget(heading)
        lay.addWidget(sub)
        lay.addWidget(self.chat_view, 1)
        lay.addLayout(row)
        return page

    def _chat_reset_view(self):
        self.chat_view.setHtml("")
        self._chat_append(
            "Assistant",
            "Hi! I'm your volunteer assistant. How can I help today?"
        )

    def _chat_new(self):
        if self._chat_worker and self._chat_worker.isRunning():
            return
        self._chat_history = []
        self._chat_reset_view()

    def _chat_append(self, who, text):
        safe = html.escape(text).replace("\n", "<br>")
        self.chat_view.append(f"<p><b>{who}:</b><br>{safe}</p>")
        sb = self.chat_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _chat_system_prompt(self):
        name = (self.user_data or {}).get("first_name") or "the volunteer"
        upcoming = []
        today = date.today().isoformat()
        for r in self._signup_rows:
            d = str(rget(r, "event_date", ""))[:10]
            if d >= today:
                upcoming.append(
                    f"- {rget(r, 'title', 'Untitled')} on {date_range(r)}"
                    f"{time_range(r)} ({rget(r, 'org_name', 'Independent')})"
                )
        upcoming_txt = "\n".join(upcoming[:10]) or "none"
        return (
            "You are the in-app help assistant for a volunteer management "
            "app. You are talking to " + name + ". Be friendly, concise, "
            "and practical. App features: Dashboard, Calendar (color-coded by "
            "organization), My Events (check in, check out, cancel), "
            "Volunteer (browse and sign up for events), Organizations "
            "(join or leave), Notifications, Help, and Profile (edit "
            "details, notification setting, change password). Hours are "
            "logged from check-in to check-out. If you don't know "
            "something specific to a particular organization or event, say "
            "so and suggest contacting the organization. Their upcoming "
            "events:\n" + upcoming_txt
        )

    def _send_chat(self):
        text = self.chat_input.text().strip()
        if not text or (self._chat_worker and self._chat_worker.isRunning()):
            return
        self.chat_input.clear()
        self._chat_append("You", text)
        self._chat_history.append({"role": "user", "content": text})
        self._chat_history = self._chat_history[-20:]
        while self._chat_history and self._chat_history[0]["role"] != "user":
            self._chat_history.pop(0)

        self._set_chat_busy(True)
        self._chat_worker = ChatWorker(
            list(self._chat_history), self._chat_system_prompt(), self
        )
        self._chat_worker.reply.connect(self._on_chat_reply)
        self._chat_worker.failed.connect(self._on_chat_failed)
        self._chat_worker.start()

    def _on_chat_reply(self, text):
        self._chat_history.append({"role": "assistant", "content": text})
        self._chat_append("Assistant", text)
        self._set_chat_busy(False)

    def _on_chat_failed(self, msg):
        if self._chat_history and self._chat_history[-1]["role"] == "user":
            self._chat_history.pop()
        self._chat_append("Assistant", msg)
        self._set_chat_busy(False)

    def _set_chat_busy(self, busy):
        self.chat_input.setEnabled(not busy)
        self.chat_send.setEnabled(not busy)
        self.chat_send.setText("…" if busy else "Send")
        if not busy:
            self.chat_input.setFocus()

    # ── 6. Profile ────────────────────────────────────────────────────────
    def _build_profile_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(40, 20, 40, 20)
        outer.setSpacing(10)

        heading = QLabel("Profile & Settings")
        heading.setObjectName(theme.SECTION_TITLE)
        outer.addWidget(heading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setObjectName(theme.HOME_SCROLL)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, 0, 0)
        inner_lay.setSpacing(16)

        details = QFrame()
        details.setObjectName(theme.EVENT_CARD)
        dl = QVBoxLayout(details)
        dl.setContentsMargins(20, 16, 20, 16)
        dt = QLabel("Your details")
        dt.setObjectName(theme.EVENT_TITLE_LIST)
        dl.addWidget(dt)

        form = QFormLayout()
        form.setSpacing(8)
        self.pf_first = QLineEdit()
        self.pf_last = QLineEdit()
        self.pf_email = QLineEdit()
        self.pf_phone = QLineEdit()
        form.addRow("First name", self.pf_first)
        form.addRow("Last name", self.pf_last)
        form.addRow("Email", self.pf_email)
        form.addRow("Phone", self.pf_phone)
        dl.addLayout(form)

        self.pf_notify = QCheckBox("Email me about event updates and reminders")
        dl.addWidget(self.pf_notify)

        save_row = QHBoxLayout()
        self.pf_status = QLabel("")
        self.pf_status.setObjectName(theme.EVENT_META_VALUE)
        save = QPushButton("Save Changes")
        save.setObjectName(theme.PRIMARY_BTN)
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._save_profile)
        save_row.addWidget(self.pf_status)
        save_row.addStretch(1)
        save_row.addWidget(save)
        dl.addLayout(save_row)
        inner_lay.addWidget(details)

        pw = QFrame()
        pw.setObjectName(theme.EVENT_CARD)
        pl = QVBoxLayout(pw)
        pl.setContentsMargins(20, 16, 20, 16)
        pt = QLabel("Change password")
        pt.setObjectName(theme.EVENT_TITLE_LIST)
        pl.addWidget(pt)

        pform = QFormLayout()
        pform.setSpacing(8)
        self.pw_old = QLineEdit()
        self.pw_new = QLineEdit()
        self.pw_confirm = QLineEdit()
        for f in (self.pw_old, self.pw_new, self.pw_confirm):
            f.setEchoMode(QLineEdit.EchoMode.Password)
        pform.addRow("Current password", self.pw_old)
        pform.addRow("New password", self.pw_new)
        pform.addRow("Confirm new", self.pw_confirm)
        pl.addLayout(pform)

        pw_row = QHBoxLayout()
        pw_row.addStretch(1)
        pw_btn = QPushButton("Update Password")
        pw_btn.setObjectName(theme.SECONDARY_BTN)
        pw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pw_btn.clicked.connect(self._change_password)
        pw_row.addWidget(pw_btn)
        pl.addLayout(pw_row)
        inner_lay.addWidget(pw)

        inner_lay.addStretch(1)
        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)
        return page

    def _refresh_profile(self):
        profile = None
        if self.userID:
            profile = self._db("getUserProfile", self.userID)
        src = profile or self.user_data or {}
        self.pf_first.setText(str(rget(src, "first_name", "")))
        self.pf_last.setText(str(rget(src, "last_name", "")))
        self.pf_email.setText(str(rget(src, "email", "")))
        self.pf_phone.setText(str(rget(src, "phone", "")))
        self.pf_notify.setChecked(bool(rget(src, "notify_email", 1)))
        self.pf_status.setText("")

    def _save_profile(self):
        first = self.pf_first.text().strip()
        email = self.pf_email.text().strip()
        if not first:
            QMessageBox.warning(self, "Profile", "First name is required.")
            return
        if "@" not in email or "." not in email.split("@")[-1]:
            QMessageBox.warning(self, "Profile", "Enter a valid email address.")
            return

        fields = {
            "first_name": first,
            "last_name": self.pf_last.text().strip(),
            "email": email,
            "phone": self.pf_phone.text().strip(),
            "notify_email": 1 if self.pf_notify.isChecked() else 0,
        }
        if self._db_action("updateUserProfile", self.userID, fields):
            if self.user_data is not None:
                self.user_data.update(fields)
            self.welcome_title.setText(f"Welcome, {first}!")
            self.user_info_label.setText(f"Logged in as: {email}")
            self.pf_status.setText("✓ Saved")
        else:
            self.pf_status.setText("Couldn't save changes.")

    def _change_password(self):
        old, new, conf = (self.pw_old.text(), self.pw_new.text(),
                          self.pw_confirm.text())
        if not (old and new and conf):
            QMessageBox.warning(self, "Password", "Fill in all three fields.")
            return
        if new != conf:
            QMessageBox.warning(self, "Password", "New passwords don't match.")
            return
        if len(new) < 8:
            QMessageBox.warning(
                self, "Password", "Use at least 8 characters."
            )
            return
        if self._db_action("changePassword", self.userID, old, new):
            for f in (self.pw_old, self.pw_new, self.pw_confirm):
                f.clear()
            QMessageBox.information(self, "Password", "Password updated.")
        else:
            QMessageBox.warning(
                self, "Password",
                "Couldn't update password. Check your current password."
            )

    # ── Tab switching ─────────────────────────────────────────────────────
    def current_tab(self):
        return self.stack.currentIndex()

    def show_tab(self, idx):
        self.stack.setCurrentIndex(idx)

        refresh = {
            TAB_DASHBOARD: self._refresh_dashboard,
            TAB_CALENDAR: self._refresh_calendar,
            TAB_EVENTS: self._refresh_events,
            TAB_ORGS: self._refresh_orgs,
            TAB_NOTIFS: self._refresh_notifications,
            TAB_PROFILE: self._refresh_profile,
        }.get(idx)
        if refresh:
            refresh()
        self.tabChanged.emit(idx)

    # ── User data ─────────────────────────────────────────────────────────
    def set_user_data(self, user_data):
        self.user_data = user_data
        if not user_data:
            return

        self.userID = user_data.get("userID") or user_data.get("id")
        first_name = user_data.get("first_name") or "Volunteer"
        email = user_data.get("email", "")

        self.welcome_title.setText(f"Welcome, {first_name}!")
        self.user_info_label.setText(f"Logged in as: {email}")

        self._chat_history = []
        self._chat_reset_view()
        self._signup_rows = []

        self.show_tab(TAB_DASHBOARD)

    # ── Dashboard data ────────────────────────────────────────────────────
    def _clear_all(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

    def _dash_text(self, text):
        lbl = QLabel(text)
        lbl.setObjectName(theme.VOLUNTEER_EMPTY)
        lbl.setWordWrap(True)
        return lbl

    def _dash_row(self, color, main, sub=""):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        h.addWidget(self._swatch(color))
        col = QVBoxLayout()
        col.setSpacing(0)
        m = QLabel(main)
        m.setWordWrap(True)
        col.addWidget(m)
        if sub:
            sl = QLabel(sub)
            sl.setObjectName(theme.EVENT_META_VALUE)
            sl.setWordWrap(True)
            col.addWidget(sl)
        h.addLayout(col, 1)
        return w

    def _refresh_dashboard(self):
        for lay in (self.dash_upcoming, self.dash_org_hours,
                    self.dash_orgs, self.dash_notifs):
            self._clear_all(lay)
        if not (self.db and self.userID):
            return

        rows = self._db("getSignupsForVolunteer", self.userID, default=[]) or []
        active = [r for r in rows if (rget(r, "status", "") or "") != "cancelled"]
        self._signup_rows = active

        today = date.today()
        today_s = today.isoformat()

        def day(r):
            return str(rget(r, "event_date", ""))[:10]

        def end_day(r):
            e = str(rget(r, "event_end_date", "") or "")[:10]
            return e or day(r)

        def hrs(r):
            return float(rget(r, "hours_logged", 0) or 0)

        completed = [r for r in active if rget(r, "check_out_time")]
        upcoming = sorted(
            (r for r in active
             if end_day(r) >= today_s and not rget(r, "check_out_time")),
            key=lambda r: (day(r), str(rget(r, "start_time", ""))),
        )
        past = [r for r in active if end_day(r) and end_day(r) < today_s]
        past_done = [r for r in past if rget(r, "check_out_time")]
        total_hours = sum(hrs(r) for r in active)

        org_rows = self._db("getOrganizations", self.userID, default=None)
        if org_rows is not None:
            joined = sorted(
                str(rget(r, "name", "")) for r in org_rows
                if rget(r, "is_member", 0)
            )
        else:
            joined = sorted({rget(r, "org_name") for r in active
                             if rget(r, "org_name")})

        self.tile_values["hours"].setText(f"{total_hours:.1f}")
        self.tile_values["completed"].setText(str(len(completed)))
        self.tile_values["upcoming"].setText(str(len(upcoming)))
        self.tile_values["signups"].setText(str(len(active)))
        self.tile_values["orgs"].setText(str(len(joined)))
        self.tile_values["rate"].setText(
            f"{round(100 * len(past_done) / len(past))}%" if past else "—"
        )

        self._refresh_recommendations(active)

        if not upcoming:
            self.dash_upcoming.addWidget(self._dash_text(
                "Nothing coming up — find events in the Volunteer tab."))
        for r in upcoming[:4]:
            self.dash_upcoming.addWidget(self._dash_row(
                org_color(rget(r, "org_name")),
                str(rget(r, "title", "Untitled event")),
                f"{date_range(r)}{time_range(r)} · "
                f"{rget(r, 'org_name', 'Independent')}",
            ))
        if len(upcoming) > 4:
            self.dash_upcoming.addWidget(
                self._dash_text(f"+ {len(upcoming) - 4} more"))

        totals = {}
        for r in active:
            totals[day(r)[:7]] = totals.get(day(r)[:7], 0.0) + hrs(r)
        data = []
        for back in range(5, -1, -1):
            yy, mm = today.year, today.month - back
            while mm <= 0:
                mm += 12
                yy -= 1
            data.append((calendar.month_abbr[mm],
                         totals.get(f"{yy:04d}-{mm:02d}", 0.0)))
        self.dash_chart.set_data(data)

        by_org = {}
        for r in active:
            name = rget(r, "org_name") or "Independent"
            by_org[name] = by_org.get(name, 0.0) + hrs(r)
        ranked = sorted(((n, v) for n, v in by_org.items() if v > 0),
                        key=lambda t: -t[1])[:5]
        if not ranked:
            self.dash_org_hours.addWidget(
                self._dash_text("No hours logged yet — check in at an event!"))
        top_val = ranked[0][1] if ranked else 1.0
        for name, v in ranked:
            color = org_color(None if name == "Independent" else name)
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(8)
            h.addWidget(self._swatch(color))
            lbl = QLabel(name)
            lbl.setFixedWidth(120)
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setValue(int(v / top_val * 1000))
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            bar.setStyleSheet(
                "QProgressBar { border: none; border-radius: 5px;"
                " background: rgba(127,127,127,50); }"
                f"QProgressBar::chunk {{ background-color: {color};"
                " border-radius: 5px; }"
            )
            hv = QLabel(f"{v:.1f} h")
            h.addWidget(lbl)
            h.addWidget(bar, 1)
            h.addWidget(hv)
            self.dash_org_hours.addWidget(row)

        if not joined:
            self.dash_orgs.addWidget(self._dash_text(
                "You haven't joined any organizations yet."))
        for name in joined[:6]:
            self.dash_orgs.addWidget(self._dash_row(org_color(name), name))
        if len(joined) > 6:
            self.dash_orgs.addWidget(
                self._dash_text(f"+ {len(joined) - 6} more"))

        notifs = self._db("getNotifications", self.userID, default=[]) or []
        notifs = sorted(notifs, key=lambda r: str(rget(r, "created_at", "")),
                        reverse=True)[:3]
        if not notifs:
            self.dash_notifs.addWidget(self._dash_text("No notifications yet."))
        for r in notifs:
            lbl = QLabel(
                f"<b>{html.escape(str(rget(r, 'created_at', '')))}</b> — "
                f"{html.escape(str(rget(r, 'message', '')))}"
            )
            lbl.setObjectName(theme.EVENT_META_VALUE)
            lbl.setWordWrap(True)
            self.dash_notifs.addWidget(lbl)

        for lay in (self.dash_upcoming, self.dash_org_hours,
                    self.dash_orgs, self.dash_notifs):
            lay.addStretch(1)

    # ── Recommendations ───────────────────────────────────────────────────
    def _refresh_recommendations(self, active_signups):
        self._clear_all(self.dash_recommended)

        try:
            from ml_recommender import rank_opportunities
        except ImportError:
            self.dash_recommended.addWidget(self._dash_text(
                "Recommendations need scikit-learn. "
                "Run: pip install scikit-learn"
            ))
            return

        all_opps = self._db("getAllOpportunities", default=None)
        if all_opps is None:
            self.dash_recommended.addWidget(self._dash_text(
                "Add Database.getAllOpportunities() to enable recommendations."
            ))
            return

        user_profile = self._db("getUserProfile", self.userID) or self.user_data
        joined_orgs = self._db("getOrganizations", self.userID, default=[]) or []

        recs, scores = rank_opportunities(
            user_profile, active_signups, joined_orgs,
            list(all_opps), top_n=5,
        )

        if not recs:
            self.dash_recommended.addWidget(self._dash_text(
                "No new recommendations right now. "
                "Browse the Volunteer tab to find events."
            ))
            return

        for r, s in zip(recs, scores):
            sub = (
                f"{date_range(r)}{time_range(r)} · "
                f"{rget(r, 'org_name', 'Independent')}"
            )
            if s > 0:
                sub += f" · match {int(round(s * 100))}%"
            self.dash_recommended.addWidget(self._dash_row(
                org_color(rget(r, "org_name")),
                str(rget(r, "title", "Untitled event")),
                sub,
            ))