"""
heroSection.py - Mission-style hero for Moxie's guest home page.

Layout (matches the reference design):
    ┌─────────────────────┐      [Moxie wordmark]
    │  [green rect]       │      is to connect volunteers
    │   ┌────────────┐    │      with local organizations,
    │   │   image    │    │      community projects,
    │   └────────────┘    │      and nonprofits
    │       [orange rect] │      that need them most.
    └─────────────────────┘      [Learn More]

The two columns are wrapped in a centered container so the composition
reads the same on narrow laptops and ultrawide monitors. The brand
wordmark swaps between light and dark assets via set_theme().
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSizePolicy,
)

import Events.theme as theme


# ── Layered image with two offset color blocks ─────────────────────────
class LayeredImage(QWidget):
    GREEN = "#2D1A3E"
    ORANGE = "#2F3B8A"

    # Overall footprint (image + the offset blocks that stick out)
    # Reduced from 620x460 → 500x410 so the right column gets more room.
    BLOCK_W = 500
    BLOCK_H = 410

    # Image — shrunk from 400x280 → 340x230
    IMG_X, IMG_Y, IMG_W, IMG_H = 40, 30, 340, 230

    # Top-left rect (behind image) — smaller corner tab
    GREEN_X, GREEN_Y, GREEN_W, GREEN_H = 0, 0, 210, 200

    # Bottom-right rect (behind image) — moved so it hugs the photo
    ORANGE_X, ORANGE_Y = 120, 210
    ORANGE_W, ORANGE_H = 360, 180

    def __init__(self, image_path: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(self.BLOCK_W, self.BLOCK_H)
        self.setStyleSheet("background: transparent;")

        # Green block (bottom of the stack)
        self.green = QFrame(self)
        self.green.setStyleSheet(
            f"background-color: {self.GREEN}; border: none;"
        )
        self.green.setGeometry(
            self.GREEN_X, self.GREEN_Y, self.GREEN_W, self.GREEN_H
        )

        # Image (middle)
        self.image = QLabel(self)
        self.image.setStyleSheet("border: none; background: transparent;")
        self.image.setGeometry(self.IMG_X, self.IMG_Y,
                               self.IMG_W, self.IMG_H)
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pix = QPixmap(image_path) if image_path else QPixmap()
        if not pix.isNull():
            scaled = pix.scaled(
                self.IMG_W, self.IMG_H,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (scaled.width() - self.IMG_W) // 2
            y = (scaled.height() - self.IMG_H) // 2
            self.image.setPixmap(
                scaled.copy(x, y, self.IMG_W, self.IMG_H)
            )
        else:
            self.image.setText("[ add heroImage.jpg to assets/ ]")
            self.image.setStyleSheet(
                "border: none; color: rgba(127,127,127,180);"
                "background: rgba(127,127,127,20);"
            )

        # Orange block (behind the image, tucked under the photo)
        self.orange = QFrame(self)
        self.orange.setStyleSheet(
            f"background-color: {self.ORANGE}; border: none;"
        )
        self.orange.setGeometry(
            self.ORANGE_X, self.ORANGE_Y,
            self.ORANGE_W, self.ORANGE_H
        )

        # Stack order: green at bottom, image over it, orange under that
        self.green.lower()
        self.image.raise_()
        self.orange.lower()


# ── Full hero ──────────────────────────────────────────────────────────
class HeroSection(QWidget):
    learnMoreRequested = pyqtSignal()

    # Max height for the wordmark; keeps it from dominating on big screens.
    LOGO_MAX_HEIGHT = 200

    def __init__(self, image_filename: str = "heroImage.jpg", parent=None):
        super().__init__(parent)
        self.setObjectName(theme.heroSection)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Preferred)

        # ── Outer wrapper: center the two-column block horizontally ────
        # The outer stretches on both sides keep the inner content
        # balanced on any window width, from a small laptop to an
        # ultrawide monitor.
        outer = QHBoxLayout(self)
        outer.setContentsMargins(40, 60, 40, 60)
        outer.setSpacing(0)
        outer.addStretch(1)

        # The inner container holds the actual two columns.
        inner = QWidget()
        inner.setSizePolicy(QSizePolicy.Policy.Maximum,
                            QSizePolicy.Policy.Preferred)
        inner_layout = QHBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(70)

        # ── Left: layered image ────────────────────────────────────────
        image_path = theme.asset(image_filename)
        if not os.path.exists(image_path):
            # Fall back to any existing feature image so the layout
            # doesn't render an empty box during development.
            for fallback in ("discoverOpportunitiesImg.jpg",
                             "trackVolunteers.jpg",
                             "noThumbnail.png"):
                candidate = theme.asset(fallback)
                if os.path.exists(candidate):
                    image_path = candidate
                    break

        self.image_stack = LayeredImage(image_path, self)

        image_col = QVBoxLayout()
        image_col.addStretch(1)
        image_col.addWidget(self.image_stack)
        image_col.addStretch(1)
        inner_layout.addLayout(image_col, 0)

        # ── Right: logo + mission ──────────────────────────────────────
        # Stretch=2 gives the text column noticeably more width than
        # the image column, which is what we want now.
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.addStretch(1)

        # Brand wordmark (pixmap, not text)
        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignLeft
                               | Qt.AlignmentFlag.AlignVCenter)
        self.logo.setSizePolicy(QSizePolicy.Policy.Preferred,
                                QSizePolicy.Policy.Fixed)
        text_col.addWidget(self.logo)
        text_col.addSpacing(14)

        # Lines with alternating weights/sizes, matching the reference.
        text_col.addWidget(self._line(
            "is to connect volunteers",
            theme.HERO_MISSION_BODY_SM,
        ))
        text_col.addWidget(self._line(
            "with local organizations,",
            theme.HERO_MISSION_BODY_LG,
        ))
        text_col.addWidget(self._line(
            "community projects,",
            theme.HERO_MISSION_BODY_LG,
        ))
        text_col.addWidget(self._line(
            "and nonprofits",
            theme.HERO_MISSION_BODY_LG,
        ))
        text_col.addWidget(self._line(
            "that need them most.",
            theme.HERO_MISSION_BODY_MD,
        ))

        text_col.addSpacing(28)

        learn_btn = QPushButton("Learn More")
        learn_btn.setObjectName(theme.HERO_LEARN_BTN)
        learn_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        learn_btn.setFixedSize(180, 54)
        learn_btn.clicked.connect(self.learnMoreRequested.emit)

        btn_row = QHBoxLayout()
        btn_row.addWidget(learn_btn)
        btn_row.addStretch(1)
        text_col.addLayout(btn_row)

        text_col.addStretch(1)
        inner_layout.addLayout(text_col, 2)

        outer.addWidget(inner)
        outer.addStretch(1)

        # Load the initial wordmark (light mode by default).
        self.set_theme(is_dark=False)

    # ── Theme ─────────────────────────────────────────────────────────
    def set_theme(self, is_dark: bool):
        """Swap the wordmark to match the current theme.

        Called by landing._update_logos() whenever the theme changes,
        and once at construction time to set the initial asset.
        """
        filename = ("logoFullLight.png" if is_dark
                    else "logoFullDark.png")
        path = theme.asset(filename)
        pix = QPixmap(path)

        if pix.isNull():
            # Fallback so the hero doesn't collapse if the asset is
            # missing — a plain text heading in the right theme colour.
            self.logo.setText("Moxie")
            color = "#F5F0EE" if is_dark else "#2D1A3E"
            self.logo.setStyleSheet(
                f"font-size: 72px; font-weight: 900; "
                f"letter-spacing: -2px; color: {color};"
            )
            return

        scaled = pix.scaledToHeight(
            self.LOGO_MAX_HEIGHT,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.logo.setPixmap(scaled)

    # ── Helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _line(text: str, object_name: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName(object_name)
        lbl.setWordWrap(True)
        return lbl