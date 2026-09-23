from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QStackedWidget, QScrollArea, QMessageBox
)


class VolunteerHome(QWidget):
    def __init__(self, on_logout_click=None, db=None, parent=None):
        super().__init__(parent)
        self.on_logout_click = on_logout_click
        self.db = db
        self.user_data = None
        self.volunteerID = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- Header strip with a small tab bar ----
        header = QWidget()
        header.setObjectName("VolunteerHeader")
        h = QHBoxLayout(header)
        h.setContentsMargins(20, 14, 20, 14)

        self.title_lbl = QLabel("My Dashboard")
        self.title_lbl.setObjectName("VolunteerTitle")

        self.tab_overview = QPushButton("Overview")
        self.tab_events = QPushButton("My Events")
        self.tab_notifications = QPushButton("Notifications")
        for b in (self.tab_overview, self.tab_events, self.tab_notifications):
            b.setObjectName("ViewToggleBtn")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)

        self.tab_overview.setChecked(True)
        self.tab_overview.clicked.connect(lambda: self._show_tab(0))
        self.tab_events.clicked.connect(lambda: self._show_tab(1))
        self.tab_notifications.clicked.connect(lambda: self._show_tab(2))

        self.logout_btn = QPushButton("Log Out")
        self.logout_btn.setObjectName("SecondaryBtn")
        if self.on_logout_click:
            self.logout_btn.clicked.connect(self.on_logout_click)

        h.addWidget(self.title_lbl)
        h.addStretch()
        h.addWidget(self.tab_overview)
        h.addWidget(self.tab_events)
        h.addWidget(self.tab_notifications)
        h.addWidget(self.logout_btn)

        # ---- Tab stack ----
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_overview_page())
        self.stack.addWidget(self._build_events_page())
        self.stack.addWidget(self._build_notifications_page())

        outer.addWidget(header, 0)
        outer.addWidget(self.stack, 1)

        # ---- Bottom slogan bar (kept from original) ----
        bottomBar = QWidget()
        bottomBar.setObjectName("BottomBar")
        bottomLayout = QHBoxLayout(bottomBar)
        bottomLayout.setContentsMargins(20, 20, 20, 20)
        sloganLabel = QLabel("Ready to make a difference in your community today?")
        sloganLabel.setObjectName("SloganText")
        sloganLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottomLayout.addWidget(sloganLabel)
        outer.addWidget(bottomBar, 0)

    # ------------------------------------------------------------------
    def _build_overview_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(20)

        card = QFrame()
        card.setObjectName("RegisterCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(10)

        self.welcome_title = QLabel("Welcome Back!")
        self.welcome_title.setObjectName("FormTitle")
        self.welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.user_info_label = QLabel("Loading user details...")
        self.user_info_label.setObjectName("FormSubtitle")
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stats_label = QLabel("")
        self.stats_label.setObjectName("FormSubtitle")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(self.welcome_title)
        card_layout.addWidget(self.user_info_label)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.stats_label)

        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(card, 3)
        center.addStretch(1)
        lay.addLayout(center)
        lay.addStretch(1)
        return page

    def _build_events_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 20, 40, 20)
        lay.setSpacing(10)

        self.events_heading = QLabel("My Registered Events")
        self.events_heading.setObjectName("SectionTitle")

        self.events_scroll = QScrollArea()
        self.events_scroll.setWidgetResizable(True)
        self.events_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.events_scroll.setObjectName("HomeScrollArea")

        self.events_content = QWidget()
        self.events_layout = QVBoxLayout(self.events_content)
        self.events_layout.setContentsMargins(0, 0, 0, 0)
        self.events_layout.setSpacing(10)
        self.events_layout.addStretch(1)
        self.events_scroll.setWidget(self.events_content)

        lay.addWidget(self.events_heading)
        lay.addWidget(self.events_scroll, 1)
        return page

    def _build_notifications_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 20, 40, 20)
        lay.setSpacing(10)

        heading = QLabel("Notifications")
        heading.setObjectName("SectionTitle")

        self.notif_scroll = QScrollArea()
        self.notif_scroll.setWidgetResizable(True)
        self.notif_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.notif_scroll.setObjectName("HomeScrollArea")

        self.notif_content = QWidget()
        self.notif_layout = QVBoxLayout(self.notif_content)
        self.notif_layout.setContentsMargins(0, 0, 0, 0)
        self.notif_layout.setSpacing(8)
        self.notif_layout.addStretch(1)
        self.notif_scroll.setWidget(self.notif_content)

        lay.addWidget(heading)
        lay.addWidget(self.notif_scroll, 1)
        return page

    # ------------------------------------------------------------------
    def _show_tab(self, idx):
        self.stack.setCurrentIndex(idx)
        self.tab_overview.setChecked(idx == 0)
        self.tab_events.setChecked(idx == 1)
        self.tab_notifications.setChecked(idx == 2)
        if idx == 1:
            self._refresh_events()
        elif idx == 2:
            self._refresh_notifications()

    def set_user_data(self, user_data):
        """Accept the dict produced by VolunteerLogin._finalize_login."""
        self.user_data = user_data
        if not user_data:
            return

        # Login stores the ID under "id"; older callers may use "volunteerID".
        self.volunteerID = user_data.get("volunteerID") or user_data.get("id")
        first_name = user_data.get("first_name", "Volunteer")
        email = user_data.get("email", "")

        self.welcome_title.setText(f"Welcome, {first_name}!")
        self.user_info_label.setText(f"Logged in as: {email}")

        self._refresh_stats()

    # ------------------------------------------------------------------
    def _refresh_stats(self):
        if not (self.db and self.volunteerID):
            self.stats_label.setText("")
            return
        try:
            rows = self.db.getSignupsForVolunteer(self.volunteerID)
        except Exception as e:
            print("stats query failed:", e)
            rows = []

        upcoming = sum(1 for r in rows if (r["status"] or "") == "registered"
                       and (r["event_date"] or "") >= "")
        total_hours = sum(r["hours_logged"] or 0 for r in rows)
        self.stats_label.setText(
            f"{len(rows)} signups  •  {upcoming} active  •  "
            f"{total_hours:.1f} hours logged"
        )

    def _clear(self, layout):
        # Keep the trailing stretch
        while layout.count() > 1:
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _refresh_events(self):
        if not (self.db and self.volunteerID):
            return
        self._clear(self.events_layout)
        try:
            rows = self.db.getSignupsForVolunteer(self.volunteerID)
        except Exception as e:
            print("signups query failed:", e)
            rows = []

        if not rows:
            empty = QLabel("You haven't registered for anything yet.")
            empty.setObjectName("VolunteerEmpty")
            self.events_layout.insertWidget(0, empty)
            return

        for r in rows:
            self.events_layout.insertWidget(
                self.events_layout.count() - 1, self._make_signup_card(r))

    def _make_signup_card(self, r):
        card = QFrame()
        card.setObjectName("EventCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(6)

        title = QLabel(r["title"] or "Untitled event")
        title.setObjectName("EventTitleList")

        meta = QLabel(
            f"{r['event_date'] or 'TBD'}  •  "
            f"{(r['start_time'] or '')}"
            f"{'–' + r['end_time'] if r['end_time'] else ''}  •  "
            f"{r['org_name'] or 'Independent'}  •  "
            f"status: {r['status'] or 'registered'}"
        )
        meta.setObjectName("EventMetaValue")

        row = QHBoxLayout()
        row.setSpacing(8)

        # Check-in / check-out buttons driven by the row's timestamps
        if not r["check_in_time"]:
            ci = QPushButton("Check In")
            ci.setObjectName("PrimaryBtn")
            ci.clicked.connect(
                lambda _, oid=r["opportunityID"]: self._do_check_in(oid))
            row.addWidget(ci)
        elif not r["check_out_time"]:
            co = QPushButton("Check Out")
            co.setObjectName("PrimaryBtn")
            co.clicked.connect(
                lambda _, oid=r["opportunityID"]: self._do_check_out(oid))
            row.addWidget(co)
        else:
            done = QLabel(f"✔ Logged {r['hours_logged'] or 0:.2f} hours")
            done.setObjectName("EventMetaValue")
            row.addWidget(done)

        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryBtn")
        cancel.clicked.connect(
            lambda _, oid=r["opportunityID"]: self._do_cancel(oid))
        row.addStretch(1)
        row.addWidget(cancel)

        lay.addWidget(title)
        lay.addWidget(meta)
        lay.addLayout(row)
        return card

    def _do_check_in(self, opportunityID):
        if self.db.checkIn(self.volunteerID, opportunityID):
            self._refresh_events()
            self._refresh_stats()

    def _do_check_out(self, opportunityID):
        if self.db.checkOut(self.volunteerID, opportunityID):
            self._refresh_events()
            self._refresh_stats()

    def _do_cancel(self, opportunityID):
        if QMessageBox.question(
                self, "Cancel RSVP", "Cancel your signup for this event?") \
                != QMessageBox.StandardButton.Yes:
            return
        if self.db.cancelSignup(self.volunteerID, opportunityID):
            self._refresh_events()
            self._refresh_stats()

    def _refresh_notifications(self):
        if not (self.db and self.volunteerID):
            return
        self._clear(self.notif_layout)
        try:
            rows = self.db.getNotifications(self.volunteerID)
        except Exception as e:
            print("notifications query failed:", e)
            rows = []

        if not rows:
            empty = QLabel("No notifications yet.")
            empty.setObjectName("VolunteerEmpty")
            self.notif_layout.insertWidget(0, empty)
            return

        for r in rows:
            lbl = QLabel(
                f"<b>{r['created_at']}</b> — {r['message']}"
            )
            lbl.setObjectName("EventMetaValue")
            lbl.setWordWrap(True)
            self.notif_layout.insertWidget(self.notif_layout.count() - 1, lbl)