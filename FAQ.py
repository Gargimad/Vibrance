"""
FAQ.py — FAQ page with live search filter.

Contains:
    FAQItem   — one accordion row (question + collapsible answer)
    FAQPage   — the full page: header, search input, scrollable list

Search filters question, answer, and category text live as the user types.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame, QPushButton,
)

import theme


# ─────────────────────────────────────────────────────────────────────────────
# FAQ content
# ─────────────────────────────────────────────────────────────────────────────
FAQ_DATA = [
    {
        "category": "General",
        "question": "What is Moxie?",
        "answer": (
            "Moxie is a platform that connects volunteers with local "
            "organizations, community projects, and nonprofits. Volunteers "
            "can browse and RSVP to events; organizations can post and "
            "manage their opportunities."
        ),
    },
    {
        "category": "Volunteers",
        "question": "How do I sign up as a volunteer?",
        "answer": (
            "Click the Register dropdown in the navigation bar and choose "
            "'Register as a Volunteer'. Fill in your name, email, and "
            "password, then verify your email with the 6-digit code we send "
            "you. Everything else is optional and can be added later."
        ),
    },
    {
        "category": "Volunteers",
        "question": "Is using Moxie free for volunteers?",
        "answer": (
            "Yes. Moxie is completely free for volunteers."
        ),
    },
    {
        "category": "Volunteers",
        "question": "How do I track my volunteer hours?",
        "answer": (
            "From your dashboard, open the 'My Events' tab and use the "
            "Check In and Check Out buttons on each event. Moxie records "
            "the time between them as hours logged."
        ),
    },
    {
        "category": "Organizations",
        "question": "How can my nonprofit post opportunities?",
        "answer": (
            "Register your organization from the Register dropdown, verify "
            "your email, and log in. Your dashboard will let you create, "
            "edit, and cancel opportunities."
        ),
    },
    {
        "category": "Organizations",
        "question": "Are there any fees for organizations?",
        "answer": (
            "Basic posting and organization listings are free."
        ),
    },
    {
        "category": "Account & Support",
        "question": "How do I reset my account password?",
        "answer": (
            "For now, password reset is not automated — please contact "
            "support@moxiecommunity.org and we'll help you recover access."
        ),
    },
    {
        "category": "Account & Support",
        "question": "How do I contact support?",
        "answer": (
            "Email us at support@moxiecommunity.org or use the contact "
            "form on your dashboard."
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# One FAQ row
# ─────────────────────────────────────────────────────────────────────────────
class FAQItem(QFrame):
    """Accordion-style FAQ row. Click the header to expand or collapse."""

    def __init__(self, category: str, question: str, answer: str, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.FAQ_ITEM)

        self.is_expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QWidget()
        header.setObjectName(theme.FAQ_HEADER)
        header.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_question = QLabel(f"[{category}] {question}")
        self.lbl_question.setObjectName(theme.FAQ_QUESTION)
        self.lbl_question.setWordWrap(True)

        self.btn_toggle = QPushButton("+")
        self.btn_toggle.setObjectName(theme.FAQ_TOGGLE_BTN)
        self.btn_toggle.setFixedWidth(32)
        self.btn_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle.clicked.connect(self.toggle)

        header_layout.addWidget(self.lbl_question, 1)
        header_layout.addWidget(self.btn_toggle, 0)

        self.lbl_answer = QLabel(answer)
        self.lbl_answer.setObjectName(theme.FAQ_ANSWER)
        self.lbl_answer.setWordWrap(True)
        self.lbl_answer.setVisible(False)

        layout.addWidget(header)
        layout.addWidget(self.lbl_answer)

        header.mousePressEvent = lambda e: self.toggle()

    def toggle(self):
        self.is_expanded = not self.is_expanded
        self.lbl_answer.setVisible(self.is_expanded)
        self.btn_toggle.setText("−" if self.is_expanded else "+")


# ─────────────────────────────────────────────────────────────────────────────
# Full FAQ page
# ─────────────────────────────────────────────────────────────────────────────
class FAQPage(QWidget):
    def __init__(self, on_back_click=None, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.FAQ_PAGE)
        self.on_back_click = on_back_click

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 24, 40, 24)
        main_layout.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────────
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Frequently Asked Questions")
        title.setObjectName(theme.FAQ_TITLE)

        back_btn = QPushButton("Back")
        back_btn.setObjectName(theme.SECONDARY_BTN)
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self.on_back_click:
            back_btn.clicked.connect(self.on_back_click)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(back_btn)

        main_layout.addWidget(header_widget)

        # ── Search ────────────────────────────────────────────────────────
        self.search_input = QLineEdit()
        self.search_input.setObjectName(theme.FAQ_SEARCH_INPUT)
        self.search_input.setPlaceholderText(
            "🔍 Search questions, keywords, or categories..."
        )
        self.search_input.textChanged.connect(self.filter_faqs)
        main_layout.addWidget(self.search_input)

        # ── Scrollable list ───────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setObjectName(theme.FAQ_SCROLL_AREA)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_content.setObjectName(theme.FAQ_SCROLL_CONTENT)
        self.items_layout = QVBoxLayout(scroll_content)
        self.items_layout.setContentsMargins(0, 8, 0, 8)
        self.items_layout.setSpacing(12)

        self.faq_widgets = []
        for faq in FAQ_DATA:
            item = FAQItem(faq["category"], faq["question"], faq["answer"])
            self.items_layout.addWidget(item)
            self.faq_widgets.append((faq, item))

        self.lbl_no_results = QLabel("No matching FAQ questions found.")
        self.lbl_no_results.setObjectName(theme.FAQ_NO_RESULTS)
        self.lbl_no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_no_results.setVisible(False)
        self.items_layout.addWidget(self.lbl_no_results)

        self.items_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

    # ── Live filter ───────────────────────────────────────────────────────
    def filter_faqs(self, query: str):
        query = query.lower().strip()
        visible_count = 0

        for faq, widget in self.faq_widgets:
            match = (
                not query
                or query in faq["question"].lower()
                or query in faq["answer"].lower()
                or query in faq["category"].lower()
            )
            widget.setVisible(match)
            if match:
                visible_count += 1

        self.lbl_no_results.setVisible(visible_count == 0)