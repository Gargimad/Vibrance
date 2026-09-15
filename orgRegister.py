from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QHBoxLayout, QComboBox
)
from PyQt6.QtCore import Qt

class OrganizationRegistration(QWidget):
    def __init__(self, on_back_click=None):
        super().__init__()
        self.on_back_click = on_back_click

        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("RegisterCard")
        card.setFixedSize(420, 800)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 40, 35, 40)
        card_layout.setSpacing(15)

        title = QLabel("Register Organization")
        title.setObjectName("FormTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Connect your farm or community program with volunteers")
        subtitle.setObjectName("FormSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        self.org_name = QLineEdit()
        self.org_name.setPlaceholderText("Organization Name")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Contact Email")

        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText("Website / Social Link")

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.location_layout = QHBoxLayout()
        self.location_layout.setSpacing(10)

        self.country_input = QComboBox()
        self.country_input.addItems([
            "Select Country",
            "United States",
            "Canada",
            "United Kingdom",
            "Australia",
            "Germany",
            "France",
            "Japan",
            "Other"
        ])

        self.zipcode_input = QLineEdit()
        self.zipcode_input.setPlaceholderText("Zip / Postal Code")

        self.location_layout.addWidget(self.country_input, stretch=2)
        self.location_layout.addWidget(self.zipcode_input, stretch=1)

        submit_btn = QPushButton("Register Organization")
        submit_btn.setObjectName("PrimaryBtn")

        back_btn = QPushButton("← Back to Home")
        back_btn.setObjectName("SecondaryBtn")
        if self.on_back_click:
            back_btn.clicked.connect(self.on_back_click)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(5)
        card_layout.addWidget(self.org_name)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.website_input)
        card_layout.addWidget(self.pass_input)
        card_layout.addWidget(self.country_input)
        card_layout.addWidget(self.zipcode_input)
        card_layout.addSpacing(10)
        card_layout.addWidget(submit_btn)
        card_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        outer_layout.addWidget(card)