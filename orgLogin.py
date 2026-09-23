from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFrame
)
from PyQt6.QtGui import QCursor


class OrgLogin(QWidget):
    """Minimal organization login page — mirrors VolunteerLogin."""

    def __init__(self, db, on_login_success=None, on_back_click=None, parent=None):
        super().__init__(parent)
        self.setObjectName("OrgLoginPage")
        self.db = db
        self.on_login_success = on_login_success
        self.on_back_click = on_back_click

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setSpacing(16)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("RegisterCard")
        card.setFixedWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)

        title = QLabel("Organization Login")
        title.setObjectName("FormTitle")
        subtitle = QLabel("Post and manage your volunteering opportunities.")
        subtitle.setObjectName("FormSubtitle")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_btn = QPushButton("Log in")
        login_btn.setObjectName("PrimaryBtn")
        login_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        login_btn.clicked.connect(self._attempt_login)

        back_btn = QPushButton("← Back to home")
        back_btn.setObjectName("SecondaryBtn")
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if on_back_click:
            back_btn.clicked.connect(on_back_click)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(login_btn)
        card_layout.addWidget(back_btn)

        outer.addWidget(card)

    def _attempt_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if not email or not password:
            QMessageBox.warning(self, "Missing info", "Enter email and password.")
            return
        row = self.db.authenticate_org(email, password)
        if not row:
            QMessageBox.warning(self, "Login failed",
                                "Email or password is incorrect.")
            return
        if self.on_login_success:
            self.on_login_success(dict(row))