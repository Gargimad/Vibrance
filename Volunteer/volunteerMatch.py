"""
volunteerMatch.py — Multi-step "find your volunteering match" wizard.
Step 1: Georgia city + (optional) high school
Step 2: pick exactly 3 career clusters
Step 3: ranked results (cluster overlap + city + school scoring)
"""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QComboBox, QButtonGroup, QMessageBox, QStackedWidget,
)

import Events.theme as theme
from Events.careerClusters import CAREER_CLUSTERS
from Events.gaLocations import GA_CITIES, ALL_CITIES, ALL_SCHOOLS, schools_for_city
from Events.dateFormat import format_event_when


class VolunteerMatch(QWidget):
    """Standalone page — landing.py pushes this onto the stack."""

    browseAllRequested = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.MATCH_PAGE)
        self.db = db
        self.userID = None
        self._selected_clusters = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 24, 40, 24)
        outer.setSpacing(14)

        title = QLabel("Find your volunteering match")
        title.setObjectName(theme.SECTION_TITLE)
        outer.addWidget(title)

        sub = QLabel(
            "Answer two quick questions. We'll rank opportunities and "
            "organizations in the career clusters you care about, near "
            "the Georgia city you choose."
        )
        sub.setObjectName(theme.EVENT_META_VALUE)
        sub.setWordWrap(True)
        outer.addWidget(sub)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_step_location())
        self.stack.addWidget(self._build_step_clusters())
        self.stack.addWidget(self._build_step_results())
        outer.addWidget(self.stack, 1)

    # ── Step 1 ────────────────────────────────────────────────────────
    def _build_step_location(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(12)

        h = QLabel("Where are you based?")
        h.setObjectName(theme.MATCH_STEP_TITLE)
        v.addWidget(h)

        card = QFrame()
        card.setObjectName(theme.MATCH_CARD)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 18, 22, 18)
        cl.setSpacing(10)

        cl.addWidget(QLabel("Georgia city"))
        self.city_combo = QComboBox()
        self.city_combo.addItem(ALL_CITIES)
        for c in GA_CITIES:
            self.city_combo.addItem(c)
        self.city_combo.currentTextChanged.connect(self._on_city_changed)
        cl.addWidget(self.city_combo)

        cl.addWidget(QLabel("High school (optional)"))
        self.school_combo = QComboBox()
        self.school_combo.addItem(ALL_SCHOOLS)
        cl.addWidget(self.school_combo)

        v.addWidget(card)
        v.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)
        next_btn = QPushButton("Next")
        next_btn.setObjectName(theme.PRIMARY_BTN)
        next_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        next_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        row.addWidget(next_btn)
        v.addLayout(row)
        return page

    def _on_city_changed(self, city):
        self.school_combo.clear()
        self.school_combo.addItem(ALL_SCHOOLS)
        for s in schools_for_city(city):
            self.school_combo.addItem(s)

    # ── Step 2 ────────────────────────────────────────────────────────
    def _build_step_clusters(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(12)

        h = QLabel("Pick exactly 3 career clusters")
        h.setObjectName(theme.MATCH_STEP_TITLE)
        v.addWidget(h)

        hint = QLabel("Choose the three clusters you're most curious about.")
        hint.setObjectName(theme.EVENT_META_VALUE)
        v.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        grid = QVBoxLayout(content)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)

        self._cluster_btns = {}
        self._cluster_group = QButtonGroup(self)
        self._cluster_group.setExclusive(False)
        for name in CAREER_CLUSTERS:
            btn = QPushButton(name)
            btn.setObjectName(theme.MATCH_CHIP)
            btn.setCheckable(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(
                lambda _c, b=btn, n=name: self._toggle_cluster(b, n)
            )
            grid.addWidget(btn)
            self._cluster_btns[name] = btn
            self._cluster_group.addButton(btn)

        grid.addStretch(1)
        scroll.setWidget(content)
        v.addWidget(scroll, 1)

        row = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.setObjectName(theme.SECONDARY_BTN)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        row.addWidget(back_btn)
        row.addStretch(1)
        self.next_btn_2 = QPushButton("Show my matches")
        self.next_btn_2.setObjectName(theme.PRIMARY_BTN)
        self.next_btn_2.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.next_btn_2.clicked.connect(self._run_match)
        row.addWidget(self.next_btn_2)
        v.addLayout(row)
        return page

    def _toggle_cluster(self, btn, name):
        if btn.isChecked():
            if len(self._selected_clusters) >= 3:
                btn.setChecked(False)
                QMessageBox.information(
                    self, "Three clusters",
                    "Pick exactly three clusters. Uncheck one to swap.",
                )
                return
            self._selected_clusters.append(name)
        else:
            if name in self._selected_clusters:
                self._selected_clusters.remove(name)
        self.next_btn_2.setEnabled(len(self._selected_clusters) == 3)

    # ── Step 3 ────────────────────────────────────────────────────────
    def _build_step_results(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 10, 0, 0)
        v.setSpacing(10)

        self.results_title = QLabel("Your matches")
        self.results_title.setObjectName(theme.MATCH_STEP_TITLE)
        v.addWidget(self.results_title)

        self.results_sub = QLabel("")
        self.results_sub.setObjectName(theme.EVENT_META_VALUE)
        self.results_sub.setWordWrap(True)
        v.addWidget(self.results_sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setObjectName(theme.HOME_SCROLL)
        content = QWidget()
        self.results_layout = QVBoxLayout(content)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(8)
        self.results_layout.addStretch(1)
        scroll.setWidget(content)
        v.addWidget(scroll, 1)

        row = QHBoxLayout()
        back_btn = QPushButton("Adjust answers")
        back_btn.setObjectName(theme.SECONDARY_BTN)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        row.addWidget(back_btn)
        row.addStretch(1)
        browse = QPushButton("Browse all events")
        browse.setObjectName(theme.SECONDARY_BTN)
        browse.clicked.connect(self.browseAllRequested.emit)
        row.addWidget(browse)
        v.addLayout(row)
        return page

    # ── Matching ──────────────────────────────────────────────────────
    def set_volunteer(self, userID):
        self.userID = userID

    def _run_match(self):
        if self.userID is None:
            QMessageBox.information(
                self, "Log in required",
                "Log in as a volunteer to save your match preferences.",
            )
            return
        if len(self._selected_clusters) != 3:
            return

        city = self.city_combo.currentText()
        school = self.school_combo.currentText()

        self.db.saveVolunteerMatch(
            self.userID,
            location=city if city != ALL_CITIES else "",
            city=city if city != ALL_CITIES else "",
            high_school=school if school != ALL_SCHOOLS else "",
            clusters=self._selected_clusters,
        )

        scored = self._score_opportunities(
            city if city != ALL_CITIES else None,
            school if school != ALL_SCHOOLS else None,
            self._selected_clusters,
        )

        self._render_results(scored, city, school)
        self.stack.setCurrentIndex(2)

    def _score_opportunities(self, city, school, clusters):
        cluster_set = set(clusters)
        rows = self.db.getAllOpportunities(limit=1000) or []
        scored = []

        for r in rows:
            opp_clusters = set(
                self.db.getOpportunityClusters(r["opportunityID"]) or []
            )
            overlap = len(cluster_set & opp_clusters)
            if overlap == 0:
                continue

            score = overlap * 100
            location = (r["location"] or "")
            if city and city.lower() in location.lower():
                score += 25
            if school and school.lower() in (
                (r["location"] or "") + " " + (r["description"] or "")
            ).lower():
                score += 15

            scored.append((score, r))

        scored.sort(key=lambda t: -t[0])
        return scored[:25]

    def _render_results(self, scored, city, school):
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        where = city if city != ALL_CITIES else "Georgia"
        self.results_sub.setText(
            f"Top matches for {', '.join(self._selected_clusters)} "
            f"near {where}."
        )

        if not scored:
            empty = QLabel(
                "No events match yet. Try different clusters or browse "
                "everything in the Volunteer tab."
            )
            empty.setObjectName(theme.VOLUNTEER_EMPTY)
            empty.setWordWrap(True)
            self.results_layout.insertWidget(0, empty)
            return

        for score, r in scored:
            card = QFrame()
            card.setObjectName(theme.EVENT_CARD)
            lay = QVBoxLayout(card)
            lay.setContentsMargins(16, 12, 16, 12)
            lay.setSpacing(4)

            title = QLabel(r["title"] or "Untitled event")
            title.setObjectName(theme.EVENT_TITLE_LIST)
            lay.addWidget(title)

            org = QLabel(
                f"by {r['org_name'] or 'Independent'}"
            )
            org.setObjectName(theme.EVENT_ORG)
            lay.addWidget(org)

            meta = QLabel(
                f"{format_event_when(r)} · match {score}%"
            )
            meta.setObjectName(theme.EVENT_META_VALUE)
            meta.setWordWrap(True)
            lay.addWidget(meta)

            opp_clusters = self.db.getOpportunityClusters(
                r["opportunityID"]
            ) or []
            if opp_clusters:
                c = QLabel(" · ".join(opp_clusters))
                c.setObjectName(theme.EVENT_META_VALUE)
                c.setWordWrap(True)
                lay.addWidget(c)

            self.results_layout.insertWidget(
                self.results_layout.count() - 1, card
            )