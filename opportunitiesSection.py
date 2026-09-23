import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
)
from volunteerPage import EventCard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FALLBACK_IMAGE = os.path.join(BASE_DIR, "noThumbnail.png")


class OpportunityRow(QWidget):
    """A titled, horizontally-scrolling row of EventCards."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("OpportunityRow")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 10, 40, 10)
        outer.setSpacing(12)

        self.titleLabel = QLabel(title)
        self.titleLabel.setObjectName("OpportunityRowTitle")

        self.scrollArea = QScrollArea()
        self.scrollArea.setObjectName("OpportunityScroll")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollArea.setFixedHeight(EventCard.GRID_FIXED_HEIGHT + 20)

        self.cardsContainer = QWidget()
        self.cardsContainer.setObjectName("OpportunityScrollContent")
        self.cardsLayout = QHBoxLayout(self.cardsContainer)
        self.cardsLayout.setContentsMargins(0, 0, 0, 0)
        self.cardsLayout.setSpacing(16)
        self.cardsLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.scrollArea.setWidget(self.cardsContainer)

        outer.addWidget(self.titleLabel)
        outer.addWidget(self.scrollArea)

        self.emptyLabel = QLabel("Nothing to show here yet — check back soon!")
        self.emptyLabel.setObjectName("OpportunityEmpty")
        self.emptyLabel.setVisible(False)
        outer.addWidget(self.emptyLabel)

    def load(self, rows):
        """rows: list of sqlite3.Row from a Database opportunity query."""
        while self.cardsLayout.count():
            item = self.cardsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not rows:
            self.scrollArea.setVisible(False)
            self.emptyLabel.setVisible(True)
            return

        self.scrollArea.setVisible(True)
        self.emptyLabel.setVisible(False)

        for row in rows:
            # No more tuple-padding hack — EventCard reads by field name.
            card = EventCard(row, view_mode="grid")
            self.cardsLayout.addWidget(card)

        self.cardsLayout.addStretch(1)


class OpportunitiesSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OpportunitiesSection")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 40)
        layout.setSpacing(20)

        self.sectionTitle = QLabel("Volunteering Opportunities")
        self.sectionTitle.setObjectName("SectionTitle")
        self.sectionTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.soonestRow = OpportunityRow("Starting Soon")
        self.newestRow = OpportunityRow("Newest Opportunities")
        self.remoteRow = OpportunityRow("Remote Opportunities")

        layout.addWidget(self.sectionTitle)
        layout.addWidget(self.soonestRow)
        layout.addWidget(self.newestRow)
        layout.addWidget(self.remoteRow)

    def load_from_db(self, db, limit=10):
        for name, fn in (
            ("soonest", db.getSoonestOpportunities),
            ("newest", db.getNewestOpportunities),
            ("remote", db.getRemoteOpportunities),
        ):
            row = {"soonest": self.soonestRow,
                   "newest": self.newestRow,
                   "remote": self.remoteRow}[name]
            try:
                row.load(fn(limit=limit))
            except Exception as e:
                print(f"Failed to load {name} opportunities:", e)
                row.load([])