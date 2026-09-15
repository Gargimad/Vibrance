# Change this import line:
from PyQt6.QtGui import QAction

# Remove QWidgetAction from PyQt6.QtWidgets import list
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QDateEdit, QComboBox,
    QScrollArea
)
from PyQt6.QtCore import Qt, QDate

class VolunteerRegistration(QWidget):
    def __init__(self, on_back_click=None):
        super().__init__()
        self.on_back_click = on_back_click

        # Outer Layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Scroll area for smaller screen heights
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Main Form Container
        card = QFrame()
        card.setObjectName("RegisterCard")
        card.setFixedWidth(540)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 35, 35, 35)
        card_layout.setSpacing(14)

        # Header
        title = QLabel("Join as a Volunteer")
        title.setObjectName("FormTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Start making an impact in your local community")
        subtitle.setObjectName("FormSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(6)

        # --- Layout Helpers ---
        def add_labeled_widget(label_text, widget):
            col = QVBoxLayout()
            col.setSpacing(4)
            lbl = QLabel(label_text)
            lbl.setObjectName("FieldLabel")
            col.addWidget(lbl)
            col.addWidget(widget)
            return col

        # First / Last Name Row
        self.firstNameInput = QLineEdit()
        self.firstNameInput.setPlaceholderText("First Name")
        
        self.lastNameInput = QLineEdit()
        self.lastNameInput.setPlaceholderText("Last Name")

        name_row = QHBoxLayout()
        name_row.setSpacing(12)
        name_row.addLayout(add_labeled_widget("First Name", self.firstNameInput))
        name_row.addLayout(add_labeled_widget("Last Name", self.lastNameInput))
        card_layout.addLayout(name_row)

        # DOB / Gender Row
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        self.dob_input.setDate(QDate.currentDate().addYears(-18))

        self.gender_input = QComboBox()
        self.gender_input.addItems([
            "Select Gender", "Female", "Male", "Non-binary", "Prefer not to say"
        ])

        dob_gender_row = QHBoxLayout()
        dob_gender_row.setSpacing(12)
        dob_gender_row.addLayout(add_labeled_widget("Date of Birth", self.dob_input))
        dob_gender_row.addLayout(add_labeled_widget("Gender", self.gender_input))
        card_layout.addLayout(dob_gender_row)

        # Email Input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("name@example.com")
        card_layout.addLayout(add_labeled_widget("Email Address", self.email_input))

        # Password / Confirm Password Row with Toggle Action
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirmPass_input = QLineEdit()
        self.confirmPass_input.setPlaceholderText("Confirm Password")
        self.confirmPass_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Replace QWidgetAction with QAction:
        self.toggle_pwd_action = QAction("👁", self.pass_input)
        self.toggle_pwd_action.setCheckable(True)
        self.toggle_pwd_action.triggered.connect(self._toggle_password_visibility)
        self.pass_input.addAction(self.toggle_pwd_action, QLineEdit.ActionPosition.TrailingPosition)
        pass_row = QHBoxLayout()
        pass_row.setSpacing(12)
        pass_row.addLayout(add_labeled_widget("Password", self.pass_input))
        pass_row.addLayout(add_labeled_widget("Confirm Password", self.confirmPass_input))
        card_layout.addLayout(pass_row)

        # Country / Zip Code Row
        self.country_input = QComboBox()
        self.country_input.addItems([
            "Select Country", "United States", "Canada", "United Kingdom",
            "Australia", "Germany", "France", "Japan", "Other"
        ])

        self.zipcode_input = QLineEdit()
        self.zipcode_input.setPlaceholderText("Zip / Postal")

        location_row = QHBoxLayout()
        location_row.setSpacing(12)
        
        c_layout = add_labeled_widget("Country", self.country_input)
        z_layout = add_labeled_widget("Zip Code", self.zipcode_input)
        
        location_row.addLayout(c_layout, stretch=2)
        location_row.addLayout(z_layout, stretch=1)
        card_layout.addLayout(location_row)

        # Buttons
        card_layout.addSpacing(8)

        submit_btn = QPushButton("Create Account")
        submit_btn.setObjectName("PrimaryBtn")

        back_btn = QPushButton("← Back to Home")
        back_btn.setObjectName("SecondaryBtn")
        if self.on_back_click:
            back_btn.clicked.connect(self.on_back_click)

        card_layout.addWidget(submit_btn)
        card_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Final Assembly
        scroll_layout.addWidget(card)
        scroll_area.setWidget(scroll_content)
        outer_layout.addWidget(scroll_area)

    def _toggle_password_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.pass_input.setEchoMode(mode)
        self.confirmPass_input.setEchoMode(mode)