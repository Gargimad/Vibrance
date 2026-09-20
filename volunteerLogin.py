import os
import random
import smtplib
import ssl
from dotenv import load_dotenv

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox, QStackedWidget
)
from PyQt6.QtCore import Qt
from db import Database

# Load environment variables from .env file
load_dotenv()


class VolunteerLogin(QWidget):
    def __init__(self, on_login_success=None, on_back_click=None):
        super().__init__()
        self.on_login_success = on_login_success
        self.on_back_click = on_back_click
        self.db = Database()
        
        self.active_user_data = None
        self.generated_otp = ""

        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Main Card Container
        card = QFrame()
        card.setObjectName("LoginCard")
        card.setFixedWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 35, 35, 35)

        # Stacked Widget: Page 0 = Credentials, Page 1 = MFA Verification
        self.stacked_widget = QStackedWidget()
        card_layout.addWidget(self.stacked_widget)

        # Page 0: Email & Password
        self.credentials_page = QWidget()
        self._build_credentials_page()
        self.stacked_widget.addWidget(self.credentials_page)

        # Page 1: MFA Verification
        self.otp_page = QWidget()
        self._build_otp_page()
        self.stacked_widget.addWidget(self.otp_page)

        outer_layout.addWidget(card)

    def _build_credentials_page(self):
        layout = QVBoxLayout(self.credentials_page)
        layout.setSpacing(14)

        title = QLabel("Welcome Back")
        title.setObjectName("FormTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Log in to access your volunteer portal")
        subtitle.setObjectName("FormSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Email Input
        email_lbl = QLabel("Email Address")
        email_lbl.setObjectName("FieldLabel")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("example@domain.com")

        layout.addWidget(email_lbl)
        layout.addWidget(self.email_input)

        # Password Input
        pwd_lbl = QLabel("Password")
        pwd_lbl.setObjectName("FieldLabel")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Password visibility toggle
        self.toggle_pwd_action = QAction("👁", self.pass_input)
        self.toggle_pwd_action.setCheckable(True)
        self.toggle_pwd_action.triggered.connect(self._toggle_password_visibility)
        self.pass_input.addAction(self.toggle_pwd_action, QLineEdit.ActionPosition.TrailingPosition)

        layout.addWidget(pwd_lbl)
        layout.addWidget(self.pass_input)

        # Buttons
        login_btn = QPushButton("Log In")
        login_btn.setObjectName("PrimaryBtn")
        login_btn.clicked.connect(self.verify_credentials)

        back_btn = QPushButton("← Back to Home")
        back_btn.setObjectName("SecondaryBtn")
        if self.on_back_click:
            back_btn.clicked.connect(self.on_back_click)

        layout.addWidget(login_btn)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _build_otp_page(self):
        layout = QVBoxLayout(self.otp_page)
        layout.setSpacing(14)

        otp_title = QLabel("Security Verification")
        otp_title.setObjectName("FormTitle")
        otp_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.otp_info_label = QLabel("A 6-digit code was sent to your email.")
        self.otp_info_label.setObjectName("FormSubtitle")
        self.otp_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.otp_info_label.setWordWrap(True)

        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter 6-digit verification code")
        self.otp_input.setMaxLength(6)

        verify_btn = QPushButton("Verify & Log In")
        verify_btn.setObjectName("PrimaryBtn")
        verify_btn.clicked.connect(self.verify_login_otp)

        back_to_login_btn = QPushButton("← Back to Login")
        back_to_login_btn.setObjectName("SecondaryBtn")
        back_to_login_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        layout.addWidget(otp_title)
        layout.addWidget(self.otp_info_label)
        layout.addWidget(self.otp_input)
        layout.addWidget(verify_btn)
        layout.addWidget(back_to_login_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _toggle_password_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.pass_input.setEchoMode(mode)

    
    def _finalize_login(self, first_name):
        QMessageBox.information(self, "Success", f"Welcome back, {first_name}!")
        if self.on_login_success:
            self.on_login_success(self.active_user_data)
    def send_login_otp(self, recipient_email: str, otp_code: str) -> bool:
        """Dispatches a login verification code via SSL SMTP (Port 465)."""
        # Read variables strictly from .env
        sender_email = os.getenv("SENDER_EMAIL")
        password = os.getenv("SENDER_PASSWORD")
        display_name = os.getenv("DISPLAY_NAME", "Moxie")

        if not sender_email or not password:
            print("SMTP Error: SENDER_EMAIL or SENDER_PASSWORD not set in .env file.")
            return False

        message = (
            f"From: {display_name} <{sender_email}>\n"
            f"To: {recipient_email}\n"
            f"Subject: Moxie Login Verification Code\n\n"
            f"Your login verification code is: {otp_code}\n\n"
            f"If you did not attempt to log in, please secure your account."
        )

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, recipient_email, message)
            return True
        except Exception as e:
            print(f"SMTP Error: {e}")
            return False
    def verify_credentials(self):
        email = self.email_input.text().strip()
        password = self.pass_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both email and password.")
            return

        user = self.db.get_user_by_email(email)

        if not user or user[2] != password:
            QMessageBox.critical(self, "Login Failed", "Invalid email or password.")
            return

        volunteerID, first_name, password, mfa_enabled = user

        if mfa_enabled:
            self.active_user_data = {"id": volunteerID, "first_name": first_name, "email": email}
            self.generated_otp = str(random.randint(100000, 999999))

            if self.send_login_otp(email, self.generated_otp):
                self.otp_info_label.setText(f"Enter the 6-digit verification code sent to:\n{email}")
                self.otp_input.clear()
                self.stacked_widget.setCurrentIndex(1)
            else:
                QMessageBox.critical(self, "Email Error", "Failed to send verification email. Please check your environment variables or connection.")
        else:
            self._finalize_login(first_name)

    def verify_login_otp(self):
        entered_code = self.otp_input.text().strip()

        if not entered_code:
            QMessageBox.warning(self, "Input Error", "Please enter the 6-digit code.")
            return

        if entered_code == self.generated_otp:
            first_name = self.active_user_data["first_name"]
            self._finalize_login(first_name)
        else:
            QMessageBox.warning(self, "Verification Failed", "Incorrect OTP code. Please try again.")

