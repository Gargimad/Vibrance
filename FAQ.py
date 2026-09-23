from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, 
    QScrollArea, QFrame, QPushButton
)


class FAQItem(QFrame):
    """An accordion-style FAQ component with a collapsible answer."""
    def __init__(self, category: str, question: str, answer: str, parent=None):
        super().__init__(parent)
        self.setObjectName("FAQItem")

        self.category = category
        self.question = question
        self.answer = answer
        self.is_expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header bar containing question & toggle button
        header = QWidget()
        header.setObjectName("FAQHeader")
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_question = QLabel(f"[{category}]  {question}")
        self.lbl_question.setObjectName("FAQQuestion")
        self.lbl_question.setWordWrap(True)

        self.btn_toggle = QPushButton("+")
        self.btn_toggle.setObjectName("FAQToggleBtn")
        self.btn_toggle.setFixedWidth(32)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle)

        header_layout.addWidget(self.lbl_question, 1)
        header_layout.addWidget(self.btn_toggle, 0)

        # Answer body (hidden by default)
        self.lbl_answer = QLabel(answer)
        self.lbl_answer.setObjectName("FAQAnswer")
        self.lbl_answer.setWordWrap(True)
        self.lbl_answer.setVisible(False)

        layout.addWidget(header)
        layout.addWidget(self.lbl_answer)

        # Allow clicking anywhere on the header to expand/collapse
        header.mousePressEvent = lambda e: self.toggle()

    def toggle(self):
        self.is_expanded = not self.is_expanded
        self.lbl_answer.setVisible(self.is_expanded)
        self.btn_toggle.setText("−" if self.is_expanded else "+")


class FAQPage(QWidget):
    """Complete FAQ Page with real-time live search filter."""
    def __init__(self, on_back_click=None, parent=None):
        super().__init__(parent)
        self.setObjectName("FAQPage")
        self.on_back_click = on_back_click

        self.faq_data = [
            {
                "category": "General",
                "question": "What is Moxie?",
                "answer": "Moxie is a platform designed to seamlessly connect passionate volunteers with local organizations, community projects, and non-profits."
            },
            {
                "category": "Volunteers",
                "question": "How do I sign up as a volunteer?",
                "answer": "Click on the 'Register' dropdown menu in the navigation bar and select 'Register as a Volunteer'. Fill out your details and profile preferences to get started."
            },
            {
                "category": "Volunteers",
                "question": "Is using Moxie free for volunteers?",
                "answer": "Yes! Moxie is completely free for all volunteers looking to make an impact in their community."
            },
            {
                "category": "Organizations",
                "question": "How can my non-profit or organization post opportunities?",
                "answer": "Register your organization via the 'Register' dropdown by selecting 'Register an Organization'. Once verified, you will be able to manage postings directly from your dashboard."
            },
            {
                "category": "Organizations",
                "question": "Are there any fees for organizations?",
                "answer": "Basic posting and organization listings are free. Premium tools for large-scale volunteer coordination and advanced reporting are available for partner organizations."
            },
            {
                "category": "Account & Support",
                "question": "How do I reset my account password?",
                "answer": "Navigate to the Login page and click on 'Forgot Password?'. Instructions to reset your password will be sent to your registered email address."
            },
            {
                "category": "Account & Support",
                "question": "How do I contact support if I have trouble?",
                "answer": "You can reach out directly to our support team at support@moxiecommunity.org or through the contact portal on your dashboard."
            }
        ]

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 24, 40, 24)
        main_layout.setSpacing(16)

        # Title / Header Section
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        lbl_title = QLabel("Frequently Asked Questions")
        lbl_title.setObjectName("FAQTitle")

        btn_back = QPushButton("← Back")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.on_back_click:
            btn_back.clicked.connect(self.on_back_click)

        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(btn_back)

        main_layout.addWidget(header_widget)

        # FAQ Search Bar
        self.search_input = QLineEdit()
        self.search_input.setObjectName("FAQSearchInput")
        self.search_input.setPlaceholderText("🔍 Search questions, keywords, or categories...")
        self.search_input.textChanged.connect(self.filter_faqs)
        main_layout.addWidget(self.search_input)

        # Scrollable Area for FAQ items
        scroll = QScrollArea()
        scroll.setObjectName("FAQScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_content.setObjectName("FAQScrollContent")
        self.items_layout = QVBoxLayout(scroll_content)
        self.items_layout.setContentsMargins(0, 8, 0, 8)
        self.items_layout.setSpacing(12)

        # Populate FAQ Items
        self.faq_widgets = []
        for faq in self.faq_data:
            item_widget = FAQItem(faq["category"], faq["question"], faq["answer"])
            self.items_layout.addWidget(item_widget)
            self.faq_widgets.append((faq, item_widget))

        # Empty search state label
        self.lbl_no_results = QLabel("No matching FAQ questions found.")
        self.lbl_no_results.setObjectName("FAQNoResults")
        self.lbl_no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_no_results.setVisible(False)
        self.items_layout.addWidget(self.lbl_no_results)

        self.items_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def filter_faqs(self, query: str):
        query = query.lower().strip()
        visible_count = 0

        for faq, widget in self.faq_widgets:
            match = (
                query in faq["question"].lower()
                or query in faq["answer"].lower()
                or query in faq["category"].lower()
            )
            widget.setVisible(match)
            if match:
                visible_count += 1

        self.lbl_no_results.setVisible(visible_count == 0)