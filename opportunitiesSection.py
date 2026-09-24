"""
opportunitiesSection.py — Home-page carousels.

Three horizontally-scrolling rows of EventCards:
    • Starting Soon     — soonest upcoming, excluding cancelled
    • Newest Opportunities — most recently posted
    • Remote Opportunities — is_remote = 1

load_from_db(db) fetches from the Database and populates each row.
Called once at startup and again whenever a new opportunity is posted.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
)

import theme
from eventCard import EventCard


class OpportunityRow(QWidget):
    """A titled, horizontally-scrolling strip of EventCards."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.OPPORTUNITY_ROW)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 10, 40, 10)
        outer.setSpacing(12)

        self.titleLabel = QLabel(title)
        self.titleLabel.setObjectName(theme.OPPORTUNITY_ROW_TITLE)

        self.scrollArea = QScrollArea()
        self.scrollArea.setObjectName(theme.OPPORTUNITY_SCROLL)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scrollArea.setFixedHeight(EventCard.GRID_FIXED_HEIGHT + 20)

        self.cardsContainer = QWidget()
        self.cardsContainer.setObjectName(theme.OPPORTUNITY_SCROLL_CONTENT)
        self.cardsLayout = QHBoxLayout(self.cardsContainer)
        self.cardsLayout.setContentsMargins(0, 0, 0, 0)
        self.cardsLayout.setSpacing(16)
        self.cardsLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.scrollArea.setWidget(self.cardsContainer)

        outer.addWidget(self.titleLabel)
        outer.addWidget(self.scrollArea)

        self.emptyLabel = QLabel(
            "Nothing to show here yet — check back soon!"
        )
        self.emptyLabel.setObjectName(theme.OPPORTUNITY_EMPTY)
        self.emptyLabel.setVisible(False)
        outer.addWidget(self.emptyLabel)

    def load(self, rows, current_volunteer_id=None):
        """rows: list of sqlite3.Row from a Database opportunity query."""
        while self.cardsLayout.count():
            item = self.cardsLayout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not rows:
            self.scrollArea.setVisible(False)
            self.emptyLabel.setVisible(True)
            return

        self.scrollArea.setVisible(True)
        self.emptyLabel.setVisible(False)

        for row in rows:
            card = EventCard(
                row, view_mode="grid",
                current_volunteer_id=current_volunteer_id,
            )
            self.cardsLayout.addWidget(card)

        self.cardsLayout.addStretch(1)


class OpportunitiesSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.OPPORTUNITY_ROW)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 40)
        layout.setSpacing(20)

        section_title = QLabel("Volunteering Opportunities")
        section_title.setObjectName(theme.SECTION_TITLE)
        section_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.soonestRow = OpportunityRow("Starting Soon")
        self.newestRow = OpportunityRow("Newest Opportunities")
        self.remoteRow = OpportunityRow("Remote Opportunities")

        layout.addWidget(section_title)
        layout.addWidget(self.soonestRow)
        layout.addWidget(self.newestRow)
        layout.addWidget(self.remoteRow)

    def load_from_db(self, db, limit=10, current_volunteer_id=None):
        jobs = [
            (self.soonestRow, db.getSoonestOpportunities),
            (self.newestRow, db.getNewestOpportunities),
            (self.remoteRow, db.getRemoteOpportunities),
        ]
        for row_widget, fetch in jobs:
            try:
                rows = fetch(limit=limit)
            except Exception as e:
                print(f"Opportunities query failed: {e}")
                rows = []
            row_widget.load(rows, current_volunteer_id=current_volunteer_id)