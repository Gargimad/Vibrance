import io
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QDateEdit, QComboBox,
    QScrollArea, QMessageBox, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, QByteArray
from captcha.image import ImageCaptcha
from db import Database


def send_otp_email(recipient_email: str, otp_code: str) -> bool:
    """Sends a 6-digit verification OTP to the user's email address.

    Credentials come from environment variables so they never live in source:
        MOXIE_SMTP_USER      (optional, defaults to the sender address below)
        MOXIE_SMTP_PASSWORD  (a Gmail App Password)
    """
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.environ.get("SENDER_EMAIL", "gargimadala17@gmail.com")
    sender_password = os.environ.get("SENDER_PASSWORD", "")

    if not sender_password:
        print("SMTP Error: SENDER_PASSWORD environment variable is not set.")
        return False

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = "Verify Your Email Address"

    body = f"Hello,\n\nYour 6-digit MFA enrollment code is: {otp_code}\n\nEnter this code in the app to complete your account setup."
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False


class VolunteerRegistration(QWidget):
    CARD_WIDTH = 760

    def __init__(self, on_back_click=None):
        super().__init__()
        self.on_back_click = on_back_click
        self.db = Database()
        self.captcha_text = ""
        self.generated_otp = ""
        self.pending_user_data = {}

        # Outer Layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Scroll area setup (kept, but the card is sized so it rarely needs it)
        scroll_area = QScrollArea()
        scroll_area.setObjectName("RegisterScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_content.setObjectName("RegisterScrollContent")  # new
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(24, 32, 24, 32)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Main Card Container
        card = QFrame()
        card.setObjectName("RegisterCard")
        card.setFixedWidth(self.CARD_WIDTH)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(52, 42, 52, 46)

        # Stacked Widget to switch between Registration & Email Verification
        self.stacked_widget = QStackedWidget()
        card_layout.addWidget(self.stacked_widget)

        # Step 1 View: Form Inputs
        self.form_page = QWidget()
        self._build_form_page()
        self.stacked_widget.addWidget(self.form_page)

        # Step 2 View: Email MFA Setup
        self.mfa_page = QWidget()
        self._build_mfa_page()
        self.stacked_widget.addWidget(self.mfa_page)

        # Let the card shrink to whichever page is showing
        self.stacked_widget.currentChanged.connect(self._fit_stack_to_current_page)
        self._fit_stack_to_current_page(0)

        # Assembly
        scroll_layout.addWidget(card)
        scroll_area.setWidget(scroll_content)
        outer_layout.addWidget(scroll_area)

    def _fit_stack_to_current_page(self, index):
        """QStackedWidget sizes itself to its tallest page; ignore hidden pages so the
        short verification page doesn't inherit the form page's height."""
        for i in range(self.stacked_widget.count()):
            page = self.stacked_widget.widget(i)
            policy = QSizePolicy.Policy.Preferred if i == index else QSizePolicy.Policy.Ignored
            page.setSizePolicy(policy, policy)
        self.stacked_widget.updateGeometry()

    def _build_form_page(self):
        layout = QVBoxLayout(self.form_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        title = QLabel("Join as a Volunteer")
        title.setObjectName("FormTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Start making an impact in your local community")
        subtitle.setObjectName("FormSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        def add_labeled_widget(label_text, widget):
            col = QVBoxLayout()
            col.setSpacing(6)
            lbl = QLabel(label_text)
            lbl.setObjectName("FieldLabel")
            col.addWidget(lbl)
            col.addWidget(widget)
            return col

        # Form Controls
        self.firstNameInput = QLineEdit()
        self.lastNameInput = QLineEdit()

        name_row = QHBoxLayout()
        name_row.setSpacing(20)
        name_row.addLayout(add_labeled_widget("First Name", self.firstNameInput))
        name_row.addLayout(add_labeled_widget("Last Name", self.lastNameInput))
        layout.addLayout(name_row)

        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        self.dob_input.setDate(QDate.currentDate().addYears(-18))

        self.gender_input = QComboBox()
        self.gender_input.addItems(["Select Gender", "Female", "Male", "Non-binary", "Prefer not to say"])

        dob_gender_row = QHBoxLayout()
        dob_gender_row.setSpacing(20)
        dob_gender_row.addLayout(add_labeled_widget("Date of Birth", self.dob_input))
        dob_gender_row.addLayout(add_labeled_widget("Gender", self.gender_input))
        layout.addLayout(dob_gender_row)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("name@example.com")
        layout.addLayout(add_labeled_widget("Email Address", self.email_input))

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirmPass_input = QLineEdit()
        self.confirmPass_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.toggle_pwd_action = QAction("👁", self.pass_input)
        self.toggle_pwd_action.setCheckable(True)
        self.toggle_pwd_action.triggered.connect(self._toggle_password_visibility)
        self.pass_input.addAction(self.toggle_pwd_action, QLineEdit.ActionPosition.TrailingPosition)

        pass_row = QHBoxLayout()
        pass_row.setSpacing(20)
        pass_row.addLayout(add_labeled_widget("Password", self.pass_input))
        pass_row.addLayout(add_labeled_widget("Confirm Password", self.confirmPass_input))
        layout.addLayout(pass_row)

        self.country_input = QComboBox()
        self.country_input.addItems(["Select Country", "United States", "Canada", "United Kingdom", "Australia", "Germany", "France", "Japan", "Other"])

        self.zipcode_input = QLineEdit()
        self.zipcode_input.setPlaceholderText("e.g. 90210")

        location_row = QHBoxLayout()
        location_row.setSpacing(20)
        location_row.addLayout(add_labeled_widget("Country", self.country_input), stretch=2)
        location_row.addLayout(add_labeled_widget("Zip Code", self.zipcode_input), stretch=1)
        layout.addLayout(location_row)

        # CAPTCHA Section: image, refresh and answer all sit on one row
        captcha_container = QVBoxLayout()
        captcha_container.setSpacing(6)
        captcha_label = QLabel("Verification")
        captcha_label.setObjectName("FieldLabel")
        captcha_container.addWidget(captcha_label)

        captcha_row = QHBoxLayout()
        captcha_row.setSpacing(10)

        self.captcha_image_label = QLabel()
        self.captcha_image_label.setObjectName("CaptchaImage")
        self.captcha_image_label.setFixedSize(204, 64)
        self.captcha_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.refresh_captcha_btn = QPushButton("🔄")
        self.refresh_captcha_btn.setObjectName("CaptchaRefreshBtn")
        self.refresh_captcha_btn.setFixedSize(46, 64)
        self.refresh_captcha_btn.clicked.connect(self.generate_captcha)

        self.captcha_input = QLineEdit()
        self.captcha_input.setPlaceholderText("Enter the code shown")

        captcha_row.addWidget(self.captcha_image_label)
        captcha_row.addWidget(self.refresh_captcha_btn)
        captcha_row.addWidget(self.captcha_input, 1, Qt.AlignmentFlag.AlignVCenter)
        captcha_container.addLayout(captcha_row)

        layout.addLayout(captcha_container)
        self.generate_captcha()

        layout.addSpacing(6)

        submit_btn = QPushButton("Continue to Email Verification")
        submit_btn.setObjectName("PrimaryBtn")
        submit_btn.clicked.connect(self.initiate_mfa_step)

        back_btn = QPushButton("← Back to Home")
        back_btn.setObjectName("SecondaryBtn")
        if self.on_back_click:
            back_btn.clicked.connect(self.on_back_click)

        layout.addWidget(submit_btn)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _build_mfa_page(self):
        layout = QVBoxLayout(self.mfa_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        otp_title = QLabel("Email Verification")
        otp_title.setObjectName("FormTitle")
        otp_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.otp_info_label = QLabel("A 6-digit code was sent to your email address.")
        self.otp_info_label.setObjectName("FormSubtitle")
        self.otp_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.otp_info_label.setWordWrap(True)

        self.mfa_code_input = QLineEdit()
        self.mfa_code_input.setObjectName("OtpInput")
        self.mfa_code_input.setPlaceholderText("000000")
        self.mfa_code_input.setMaxLength(6)
        self.mfa_code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        verify_btn = QPushButton("Verify Code & Create Account")
        verify_btn.setObjectName("PrimaryBtn")
        verify_btn.clicked.connect(self.complete_registration)

        cancel_btn = QPushButton("Cancel / Edit Details")
        cancel_btn.setObjectName("SecondaryBtn")
        cancel_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        layout.addWidget(otp_title)
        layout.addWidget(self.otp_info_label)
        layout.addSpacing(8)
        layout.addWidget(self.mfa_code_input)
        layout.addSpacing(6)
        layout.addWidget(verify_btn)
        layout.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def generate_captcha(self):
        chars = string.ascii_uppercase + string.digits
        self.captcha_text = ''.join(random.choices(chars, k=5))

        image_gen = ImageCaptcha(width=200, height=60)
        image_data = image_gen.generate(self.captcha_text)

        raw_bytes = image_data.getvalue()
        qbyte_array = QByteArray(bytes(raw_bytes))

        pixmap = QPixmap()
        pixmap.loadFromData(qbyte_array)

        self.captcha_image_label.setPixmap(pixmap)
        self.captcha_input.clear()

    def _toggle_password_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.pass_input.setEchoMode(mode)
        self.confirmPass_input.setEchoMode(mode)

    def initiate_mfa_step(self):
        """Validates fields, generates an OTP, sends the email, and navigates to the verification screen."""
        first_name = self.firstNameInput.text().strip()
        last_name = self.lastNameInput.text().strip()
        email = self.email_input.text().strip()
        password = self.pass_input.text()
        confirm_password = self.confirmPass_input.text()
        user_captcha = self.captcha_input.text().strip()

        if not first_name or not last_name or not email or not password:
            QMessageBox.warning(self, "Input Error", "Please fill in all required fields.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Password Error", "Passwords do not match.")
            return

        if not user_captcha:
            QMessageBox.warning(self, "Verification Required", "Please enter the CAPTCHA code.")
            return

        if user_captcha.upper() != self.captcha_text.upper():
            QMessageBox.warning(self, "CAPTCHA Error", "Incorrect verification code. Please try again.")
            self.generate_captcha()
            return

        gender = self.gender_input.currentText()
        country = self.country_input.currentText()

        # Save temporary record until verification succeeds
        self.pending_user_data = {
            "gender": "Unspecified" if gender == "Select Gender" else gender,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "country": "Unspecified" if country == "Select Country" else country,
            "zipcode": self.zipcode_input.text().strip(),
            "dob": self.dob_input.date().toString("yyyy-MM-dd"),
            "skills": ""
        }

        # Generate 6-digit OTP code
        self.generated_otp = str(random.randint(100000, 999999))

        # Send email OTP
        if send_otp_email(email, self.generated_otp):
            self.otp_info_label.setText(f"Enter the 6-digit code sent to:\n{email}")
            self.mfa_code_input.clear()
            self.stacked_widget.setCurrentIndex(1)  # View Step 2
        else:
            QMessageBox.critical(self, "Email Error", "Could not send verification email. Please check your email address or internet connection.")

    def complete_registration(self):
        """Verifies the OTP code and creates the database entry upon success."""
        user_code = self.mfa_code_input.text().strip()

        if not user_code:
            QMessageBox.warning(self, "MFA Error", "Please enter the 6-digit verification code.")
            return

        if user_code != self.generated_otp:
            QMessageBox.warning(self, "MFA Error", "Incorrect code. Please check your email and try again.")
            return

        # Insert user into SQLite database
        success = self.db.addVolunteer(
            self.pending_user_data["gender"],
            self.pending_user_data["first_name"],
            self.pending_user_data["last_name"],
            self.pending_user_data["email"],
            self.pending_user_data["password"],
            self.pending_user_data["country"],
            self.pending_user_data["zipcode"],
            self.pending_user_data["dob"],
            self.pending_user_data["skills"]
        )

        if success:
            QMessageBox.information(self, "Success", "Account created and email verified successfully!")
            if self.on_back_click:
                self.on_back_click()
        else:
            QMessageBox.critical(self, "Database Error", "Failed to register account. An account with this email may already exist.")
            self.stacked_widget.setCurrentIndex(0)