"""
featuresSection.py — The three-card "what Moxie offers" section on the
guest home page.

Each FeatureCard is an image + title + description tile with a fixed
width and cover-cropped image. Paths resolve through theme.asset() so
moving assets/ around is a one-line change.
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
)

import theme


class FeatureCard(QFrame):
    """A single feature tile: image on top, title + description below."""

    CARD_WIDTH = 280
    IMAGE_HEIGHT = 160

    def __init__(self, image_filename, title, description, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.FEATURE_CARD)
        self.setFixedWidth(self.CARD_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Image (flush with the card edges) ─────────────────────────────
        self.imageLabel = QLabel()
        self.imageLabel.setObjectName(theme.FEATURE_IMAGE)
        self.imageLabel.setFixedSize(self.CARD_WIDTH, self.IMAGE_HEIGHT)
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imageLabel.setStyleSheet("padding: 0; border: none;")

        # ── Text block (padded) ───────────────────────────────────────────
        text_wrap = QVBoxLayout()
        text_wrap.setContentsMargins(24, 16, 24, 24)
        text_wrap.setSpacing(10)

        self.titleLabel = QLabel(title)
        self.titleLabel.setObjectName(theme.FEATURE_TITLE)
        self.titleLabel.setWordWrap(True)

        self.desLabel = QLabel(description)
        self.desLabel.setObjectName(theme.FEATURE_DESC)
        self.desLabel.setWordWrap(True)

        text_wrap.addWidget(self.titleLabel)
        text_wrap.addWidget(self.desLabel)
        text_wrap.addStretch(1)

        layout.addWidget(self.imageLabel)
        layout.addLayout(text_wrap)

        self.set_image(image_filename)

    def set_image(self, image_filename):
        """
        Load an image, cover-crop to exactly (CARD_WIDTH, IMAGE_HEIGHT).
        Falls back to noThumbnail.png, then to a text placeholder.
        """
        if not image_filename:
            self._show_fallback()
            return

        path = (image_filename if os.path.isabs(image_filename)
                else theme.asset(image_filename))
        pixmap = QPixmap(path)

        if pixmap.isNull():
            fallback = QPixmap(theme.asset("noThumbnail.png"))
            if not fallback.isNull():
                pixmap = fallback

        if pixmap.isNull():
            self._show_fallback()
            return

        w, h = self.imageLabel.width(), self.imageLabel.height()
        scaled = pixmap.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (scaled.width() - w) // 2
        y = (scaled.height() - h) // 2
        self.imageLabel.setPixmap(scaled.copy(x, y, w, h))

    def _show_fallback(self):
        self.imageLabel.clear()
        self.imageLabel.setText("[ image ]")


class FeaturesSection(QWidget):
    """
    Three-card row on the guest home page. Swap the images by changing
    the filenames below; they resolve against assets/.
    """

    CARDS = [
        (
            "discoverOpportunitiesImg.jpg",
            "Discover Volunteering Opportunities",
            "Browse volunteering opportunities and events from organizations "
            "near you or fully remote.",
        ),
        (
            "postVolunteerOpportunities.jpg",
            "Post Volunteering Opportunities",
            "Post volunteering opportunities and events for your organization "
            "in minutes.",
        ),
        (
            "trackVolunteers.jpg",
            "Manage Volunteers Seamlessly",
            "Recruit, manage, and communicate with your volunteer team.",
        ),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.FEATURES_SECTION)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 50, 40, 50)
        outer.setSpacing(30)

        section_title = QLabel("What Moxie Offers")
        section_title.setObjectName(theme.SECTION_TITLE)
        section_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(24)
        cards_row.addStretch(1)

        for filename, title, desc in self.CARDS:
            card = FeatureCard(filename, title, desc)
            cards_row.addWidget(card)

        cards_row.addStretch(1)

        outer.addWidget(section_title)
        outer.addLayout(cards_row)