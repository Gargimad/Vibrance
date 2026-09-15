from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QDateEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDate

class VolunteerRegistration(QWidget):
    def __init__(self, on_back_click=None):
        super().__init__()
        self.on_back_click = on_back_click

        # Outer Centered Layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Main Form Container (Card effect)
        card = QFrame()
        card.setObjectName("RegisterCard")
        card.setFixedSize(520, 800)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 40, 35, 40)
        card_layout.setSpacing(15)

        # Header
        title = QLabel("Join as a Volunteer")
        title.setObjectName("FormTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Start making an impact in your local community")
        subtitle.setObjectName("FormSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        # Form Inputs
        self.firstNameInput = QLineEdit()
        self.firstNameInput.setPlaceholderText("First Name")
        self.lastNameInput = QLineEdit()
        self.lastNameInput.setPlaceholderText("Last Name")
        dob_label = QLabel("Date of Birth")
        dob_label.setObjectName("FieldLabel")
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        self.dob_input.setDate(QDate.currentDate().addYears(-13))  # Defaults to 18 years ago

        # Gender Selection Input
        gender_label = QLabel("Gender")
        gender_label.setObjectName("FieldLabel")

        self.gender_input = QComboBox()
        self.gender_input.addItems([
            "Select Gender", 
            "Female", 
            "Male", 
            "Non-binary", 
            "Prefer not to say"
        ])

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email Address")

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.confirmPass_input = QLineEdit()
        self.confirmPass_input.setPlaceholderText("Confirm Password")
        self.confirmPass_input.setEchoMode(QLineEdit.EchoMode.Password)
        
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

        # Buttons
        submit_btn = QPushButton("Create Account")
        submit_btn.setObjectName("PrimaryBtn")

        back_btn = QPushButton("← Back to Home")
        back_btn.setObjectName("SecondaryBtn")
        if self.on_back_click:
            back_btn.clicked.connect(self.on_back_click)

        # Assemble Card
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(5)
        card_layout.addWidget(self.firstNameInput)
        card_layout.addWidget(self.lastNameInput)
        card_layout.addWidget(dob_label)
        card_layout.addWidget(self.dob_input)
        card_layout.addWidget(gender_label)
        card_layout.addWidget(self.gender_input)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.pass_input)
        card_layout.addWidget(self.confirmPass_input)
        card_layout.addWidget(self.country_input)
        card_layout.addWidget(self.zipcode_input)
        card_layout.addSpacing(5)
        card_layout.addWidget(submit_btn)
        card_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        outer_layout.addWidget(card)