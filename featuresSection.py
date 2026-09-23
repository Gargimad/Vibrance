import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame

# Resolve asset paths against this file's location, not the cwd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Optional: a grey placeholder image reused when a card has no artwork.
# Leave it as "" if you don't have one yet — the "[ image ]" text fallback still works.
FALLBACK_IMAGE = os.path.join(BASE_DIR, "noThumbnail.png")


class FeatureCard(QFrame):
    """A single feature tile: image + title + description."""

    # Fixed dimensions so the image can be cover-cropped to an exact box.
    CARD_WIDTH = 280
    IMAGE_HEIGHT = 160

    def __init__(self, image_path, title, description, parent=None):
        super().__init__(parent)
        self.setObjectName("FeatureCard")
        self.setFixedWidth(self.CARD_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)   # image sits flush with card edges
        layout.setSpacing(0)

        # --- Image (full bleed at the top of the card) ---
        self.imageLabel = QLabel()
        self.imageLabel.setObjectName("FeatureImage")
        self.imageLabel.setFixedSize(self.CARD_WIDTH, self.IMAGE_HEIGHT)
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imageLabel.setStyleSheet("padding: 0; border: none;")

        # --- Text block (padded) ---
        text_wrap = QVBoxLayout()
        text_wrap.setContentsMargins(24, 16, 24, 24)
        text_wrap.setSpacing(10)

        self.titleLabel = QLabel(title)
        self.titleLabel.setObjectName("FeatureTitle")
        self.titleLabel.setWordWrap(True)

        self.descLabel = QLabel(description)
        self.descLabel.setObjectName("FeatureDesc")
        self.descLabel.setWordWrap(True)

        text_wrap.addWidget(self.titleLabel)
        text_wrap.addWidget(self.descLabel)
        text_wrap.addStretch(1)

        layout.addWidget(self.imageLabel)
        layout.addLayout(text_wrap)

        self.set_image(image_path)

    def set_image(self, image_path):
        """Load an image and cover-crop it to fill the image label exactly."""
        pixmap = QPixmap()

        if image_path:
            # Resolve relative paths against this file's folder
            resolved = image_path if os.path.isabs(image_path) \
                       else os.path.join(BASE_DIR, image_path)
            pixmap = QPixmap(resolved)

        # Fallback to the shared placeholder if the requested image failed
        if pixmap.isNull() and FALLBACK_IMAGE:
            pixmap = QPixmap(FALLBACK_IMAGE)

        # Last resort: text placeholder
        if pixmap.isNull():
            self.imageLabel.setText("[ image ]")
            return

        w, h = self.imageLabel.width(), self.imageLabel.height()

        # 1. Scale so the image COVERS the box (may overflow one axis)
        scaled = pixmap.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        # 2. Crop the overflow, centered
        x = (scaled.width() - w) // 2
        y = (scaled.height() - h) // 2
        self.imageLabel.setPixmap(scaled.copy(x, y, w, h))


class FeaturesSection(QWidget):
    """
    The three-card "what Moxie offers" section between the hero and the
    opportunities listing. Swap in real images by passing paths to FeatureCard
    or by calling card.set_image("assets/foo.png") later.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FeaturesSection")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 50, 40, 50)
        outer.setSpacing(30)

        self.sectionTitle = QLabel("What Moxie Offers")
        self.sectionTitle.setObjectName("SectionTitle")
        self.sectionTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cardsRow = QHBoxLayout()
        cardsRow.setSpacing(24)

        self.card1 = FeatureCard(
            "discoverOpportunitiesImg.jpg",
            "Discover Volunteering Opportunities",
            "Browse volunteering opportunities and events from organizations near you or fully remote."
        )
        self.card2 = FeatureCard(
            "postVolunteerOpportunities.jpg",
            "Post Volunteering Opportunities",
            "Post volunteering opportunities and events for your organization."
        )
        self.card3 = FeatureCard(
            "trackVolunteers.jpg",
            "Manage Volunteers Seamlessly",
            "Recruit, manage, and communicate with your volunteer team."
        )

        cardsRow.addWidget(self.card1)
        cardsRow.addWidget(self.card2)
        cardsRow.addWidget(self.card3)

        outer.addWidget(self.sectionTitle)
        outer.addLayout(cardsRow)