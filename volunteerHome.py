from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)


class VolunteerHome(QWidget):
    def __init__(self, on_logout_click=None):
        super().__init__()
        self.on_logout_click = on_logout_click
        self.user_data = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Hero / Dashboard Area ---
        heroWidget = QWidget()
        heroWidget.setObjectName("HeroSection")
        heroLayout = QVBoxLayout(heroWidget)
        heroLayout.setContentsMargins(40, 40, 40, 40)

        # Welcome Card
        card = QFrame()
        card.setObjectName("RegisterCard")  # Reuses existing card styles
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)

        self.welcome_title = QLabel("Welcome Back!")
        self.welcome_title.setObjectName("FormTitle")
        self.welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.user_info_label = QLabel("Loading user details...")
        self.user_info_label.setObjectName("FormSubtitle")
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logout_btn = QPushButton("Log Out")
        logout_btn.setObjectName("PrimaryBtn")
        if self.on_logout_click:
            logout_btn.clicked.connect(self.on_logout_click)

        card_layout.addWidget(self.welcome_title)
        card_layout.addWidget(self.user_info_label)
        card_layout.addSpacing(20)
        card_layout.addWidget(logout_btn)

        # Center card inside hero
        center_container = QHBoxLayout()
        center_container.addStretch(1)
        center_container.addWidget(card, stretch=2)
        center_container.addStretch(1)

        heroLayout.addStretch(1)
        heroLayout.addLayout(center_container)
        heroLayout.addStretch(1)

        # --- Bottom Slogan Bar ---
        bottomBar = QWidget()
        bottomBar.setObjectName("BottomBar")
        bottomLayout = QHBoxLayout(bottomBar)
        bottomLayout.setContentsMargins(20, 30, 20, 30)

        sloganLabel = QLabel("Ready to make a difference in your community today?")
        sloganLabel.setObjectName("SloganText")
        sloganLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottomLayout.addWidget(sloganLabel)

        layout.addWidget(heroWidget, stretch=1)
        layout.addWidget(bottomBar, stretch=0)

    def set_user_data(self, user_data):
        """Pass logged in user data to update UI elements dynamically."""
        self.user_data = user_data
        if user_data:
            first_name = user_data.get("first_name", "Volunteer")
            email = user_data.get("email", "")
            self.welcome_title.setText(f"Welcome, {first_name}!")
            self.user_info_label.setText(f"Logged in as: {email}")