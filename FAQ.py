"""
FAQ.py — FAQ page with live search and category filtering.

Contains:
    FAQItem   - one accordion row (question + collapsible answer)
    FAQPage   - header, search, category pills, grouped question list

Questions are grouped under visible category headings. Search and the
category filter combine: typing narrows matches inside the active
category, and category headings disappear when nothing under them is
visible.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame, QPushButton, QButtonGroup,
)

import theme


# ── FAQ content ──────────────────────────────────────────────────────────
CATEGORIES = [
    "Getting Started",
    "For Volunteers",
    "For Organizations",
    "Hours & Impact",
    "Account & Support",
]

FAQ_DATA = [
    # ── Getting Started ────────────────────────────────────────────────
    {
        "category": "Getting Started",
        "question": "What is Moxie?",
        "answer": (
            "Moxie is a platform that connects volunteers with local "
            "organizations, community projects, and nonprofits. Volunteers "
            "can browse opportunities, RSVP to events they care about, "
            "and track the hours they contribute. Organizations get a "
            "dashboard to post opportunities, manage their roster, verify "
            "hours, and communicate with their volunteers — all in one "
            "place."
        ),
    },
    {
        "category": "Getting Started",
        "question": "Do I need an account to browse opportunities?",
        "answer": (
            "No. Anyone can browse the guest home page and search the "
            "listing without signing up. You only need an account when "
            "you want to RSVP to an event, track hours, or contact an "
            "organization. Creating an account is free and takes under "
            "a minute — you just need an email address and a password."
        ),
    },
    {
        "category": "Getting Started",
        "question": "How do I know which events are hosted by Moxie organizations?",
        "answer": (
            "Every opportunity card carries a small label near the top: "
            "'Moxie' if the organization registered directly on the "
            "platform, or 'External' if the listing was imported from an "
            "outside source like the Volunteer Connector. Moxie-hosted "
            "events also show a 'Verified on Moxie' pill on the thumbnail "
            "and use a 'Sign up' button, while imported events use 'RSVP' "
            "and link back to the original posting."
        ),
    },

    # ── For Volunteers ─────────────────────────────────────────────────
    {
        "category": "For Volunteers",
        "question": "How do I sign up as a volunteer?",
        "answer": (
            "Click the Register dropdown in the navigation bar and choose "
            "'Register as a Volunteer'. Fill in your name, email, and a "
            "password of at least eight characters, then verify your "
            "email with the six-digit code we send you. Everything else "
            "— date of birth, country, zip code, and skills — is optional "
            "and can be added later from your profile page."
        ),
    },
    {
        "category": "For Volunteers",
        "question": "Is using Moxie free for volunteers?",
        "answer": (
            "Yes, Moxie is completely free for volunteers. There are no "
            "subscriptions, no hidden fees, and no charges for RSVPing "
            "to events or tracking your hours. The only thing you need "
            "is an email address so we can verify your account and send "
            "you event reminders."
        ),
    },
    {
        "category": "For Volunteers",
        "question": "How do I find opportunities near me?",
        "answer": (
            "Open the Volunteer tab from the nav bar and use the filter "
            "row at the top. You can search by keyword, filter by type "
            "(in-person or remote), type in a location or zip code, and "
            "narrow results further with the 'More filters' button to "
            "pick a specific cause or date range. Your dashboard also "
            "suggests events based on the skills you've listed in your "
            "profile."
        ),
    },
    {
        "category": "For Volunteers",
        "question": "What happens after I RSVP to an event?",
        "answer": (
            "The opportunity immediately appears in your 'My Events' tab "
            "with the date, time, and organization listed. You'll also "
            "receive a reminder notification within 24 hours of the "
            "event start. When you arrive, tap Check In; when you leave, "
            "tap Check Out and Moxie will calculate your hours "
            "automatically. If your plans change, you can cancel from "
            "the same tab at any time."
        ),
    },

    # ── For Organizations ──────────────────────────────────────────────
    {
        "category": "For Organizations",
        "question": "How can my nonprofit post opportunities?",
        "answer": (
            "Register your organization from the Register dropdown on the "
            "home page, verify your email, and log in. Your dashboard "
            "gives you a full set of tools: create, edit, and cancel "
            "opportunities; post announcements to your volunteers; review "
            "signups and check-ins; verify hours; and export reports for "
            "grant applications or board updates."
        ),
    },
    {
        "category": "For Organizations",
        "question": "Are there any fees for organizations?",
        "answer": (
            "Basic posting and organization listings are free. You can "
            "publish as many opportunities as you like, invite volunteers, "
            "track their hours, and export reports at no cost. If we "
            "introduce optional paid features in the future, they'll be "
            "clearly marked and completely optional — the core "
            "volunteer-management tools will always remain free."
        ),
    },
    {
        "category": "For Organizations",
        "question": "Can I import my existing volunteer roster?",
        "answer": (
            "Yes. Open the 'Data migration' tab in your organization "
            "dashboard and choose 'Choose file'. Moxie accepts CSV and "
            "Excel (.xlsx) rosters with columns for email, first name, "
            "last name, and any other profile fields you already track. "
            "Each imported volunteer receives a one-time activation code "
            "by email and chooses their own password the first time they "
            "log in. You can download a starter template from the same "
            "screen."
        ),
    },
    {
        "category": "For Organizations",
        "question": "How do I manage volunteers who have signed up?",
        "answer": (
            "The 'Volunteers' tab lists everyone who has ever signed up "
            "for one of your events, sorted by total hours. Click any row "
            "to see their full history with your organization, leave "
            "private notes or tags, and — if needed — ban them from "
            "future signups. From 'Reports' you can filter by date range, "
            "volunteer, or opportunity, and export the results to CSV."
        ),
    },

    # ── Hours & Impact ─────────────────────────────────────────────────
    {
        "category": "Hours & Impact",
        "question": "How do I track my volunteer hours?",
        "answer": (
            "From your dashboard, open the 'My Events' tab. Each event "
            "you've signed up for has a Check In button while you're on "
            "site and a Check Out button when you leave. Moxie records "
            "the time between them and adds it to your running total, "
            "which you can see any time on your dashboard. If a check-in "
            "or check-out is missed, the organization can adjust your "
            "hours when they verify them."
        ),
    },
    {
        "category": "Hours & Impact",
        "question": "How are my hours verified?",
        "answer": (
            "After you check out, the organization reviews the entry in "
            "their attendance view and marks it as verified. Verified "
            "hours carry a green indicator on your event history and are "
            "the ones counted in the impact record you can export. "
            "Organizations can also mark a signup as a no-show if you "
            "didn't attend, in which case the hours aren't counted."
        ),
    },
    {
        "category": "Hours & Impact",
        "question": "Can I export a record of my volunteer work?",
        "answer": (
            "Yes. On your dashboard, click 'Export verified impact "
            "record'. Moxie produces a CSV listing every verified event "
            "you've completed, with the opportunity title, organization, "
            "date, and hours for each. The file opens in Excel or Google "
            "Sheets and can be attached to scholarship applications, "
            "school service requirements, or résumés."
        ),
    },
    {
        "category": "Hours & Impact",
        "question": "What happens if I can't make it to an event I signed up for?",
        "answer": (
            "Open 'My Events' and click Cancel next to the event. "
            "Cancelling frees your spot for someone else and notifies "
            "the organization, so please do it as early as you can. If "
            "you simply don't show up, the organization may mark you as "
            "a no-show — this doesn't ban you, but it does appear on "
            "their private record for that event."
        ),
    },

    # ── Account & Support ──────────────────────────────────────────────
    {
        "category": "Account & Support",
        "question": "How do I reset my account password?",
        "answer": (
            "Password reset is not automated yet. Email "
            "support@moxiecommunity.org from the address on your account "
            "and tell us you'd like a reset — we'll reply with a link to "
            "set a new password. If you're already logged in, you can "
            "change your password yourself from Profile & Settings "
            "without contacting support."
        ),
    },
    {
        "category": "Account & Support",
        "question": "How do I change my email or profile details?",
        "answer": (
            "Log in and open the 'Profile' tab in the navigation bar. "
            "You can update your first and last name, phone number, "
            "skills, and notification preferences, then click Save "
            "Changes. Changing the email on your account isn't supported "
            "from the app yet — contact support and we'll update it for "
            "you."
        ),
    },
    {
        "category": "Account & Support",
        "question": "What is two-factor authentication and is it required?",
        "answer": (
            "Two-factor authentication (2FA) sends a one-time six-digit "
            "code to your email every time you log in, on top of your "
            "password. It's on by default because it's the single "
            "easiest way to keep an account safe. It is not required — "
            "you can turn it off from Profile & Settings if you'd "
            "rather log in with just a password."
        ),
    },
    {
        "category": "Account & Support",
        "question": "How do I contact support?",
        "answer": (
            "Email support@moxiecommunity.org with a short description "
            "of the issue and, if it's about a specific event or "
            "account, the email address associated with it. We aim to "
            "reply within one business day. For quick questions about "
            "using the app, you can also ask the built-in assistant "
            "from the Help tab in your volunteer dashboard."
        ),
    },
]


# ── One FAQ row ──────────────────────────────────────────────────────────
class FAQItem(QFrame):
    """Accordion-style FAQ row. Click the header to expand or collapse."""

    def __init__(self, question: str, answer: str, parent=None):
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

        self.lbl_question = QLabel(question)
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
        self.btn_toggle.setText("-" if self.is_expanded else "+")


# ── Full FAQ page ────────────────────────────────────────────────────────
class FAQPage(QWidget):
    def __init__(self, on_back_click=None, parent=None):
        super().__init__(parent)
        self.setObjectName(theme.FAQ_PAGE)
        self.on_back_click = on_back_click
        self._active_category = "All"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 24, 40, 24)
        main_layout.setSpacing(16)

        # ── Header ─────────────────────────────────────────────────────
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

        # ── Search ─────────────────────────────────────────────────────
        self.search_input = QLineEdit()
        self.search_input.setObjectName(theme.FAQ_SEARCH_INPUT)
        self.search_input.setPlaceholderText(
            "Search questions, keywords, or answers..."
        )
        self.search_input.textChanged.connect(self._apply_filters)
        main_layout.addWidget(self.search_input)

        # ── Category filter pills ──────────────────────────────────────
        cat_row = QHBoxLayout()
        cat_row.setSpacing(6)
        self._cat_group = QButtonGroup(self)
        self._cat_group.setExclusive(True)

        self._cat_buttons = {}
        for cat in ["All"] + CATEGORIES:
            btn = QPushButton(cat)
            btn.setObjectName(theme.VIEW_TOGGLE_BTN)
            btn.setCheckable(True)
            btn.setChecked(cat == "All")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(
                lambda _checked, c=cat: self._set_category(c)
            )
            self._cat_group.addButton(btn)
            self._cat_buttons[cat] = btn
            cat_row.addWidget(btn)

        cat_row.addStretch(1)
        main_layout.addLayout(cat_row)

        # ── Scrollable, category-grouped list ─────────────────────────
        scroll = QScrollArea()
        scroll.setObjectName(theme.FAQ_SCROLL_AREA)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll = scroll

        scroll_content = QWidget()
        scroll_content.setObjectName(theme.FAQ_SCROLL_CONTENT)
        self.items_layout = QVBoxLayout(scroll_content)
        self.items_layout.setContentsMargins(0, 8, 0, 8)
        self.items_layout.setSpacing(12)

        # Heading + items per category, so a heading always sits above
        # its group and can be hidden cleanly when nothing matches.
        self.category_headings = {}
        self.faq_widgets = []

        for cat in CATEGORIES:
            hheading = QLabel(cat)
            hheading.setObjectName(theme.SEARCH_CATEGORY)
            self.items_layout.addWidget(hheading)
            self.category_headings[cat] = hheading
            for faq in FAQ_DATA:
                if faq["category"] != cat:
                    continue
                item = FAQItem(faq["question"], faq["answer"])
                self.items_layout.addWidget(item)
                self.faq_widgets.append((faq, item))

        self.lbl_no_results = QLabel(
            "No matching FAQ questions found. Try a different keyword "
            "or pick another category."
        )
        self.lbl_no_results.setObjectName(theme.FAQ_NO_RESULTS)
        self.lbl_no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_no_results.setWordWrap(True)
        self.lbl_no_results.setVisible(False)
        self.items_layout.addWidget(self.lbl_no_results)

        self.items_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

    # ── Filtering ──────────────────────────────────────────────────────
    def _set_category(self, category: str):
        self._active_category = category
        self._apply_filters()

    def filter_faqs(self, query: str):
        """Kept for backwards compatibility with any older callers."""
        self._apply_filters()

    def _apply_filters(self):
        query = self.search_input.text().lower().strip()
        active = self._active_category

        # Count how many items are visible under each category so we can
        # hide headings that have nothing left to show.
        visible_per_cat = {c: 0 for c in CATEGORIES}

        for faq, widget in self.faq_widgets:
            matches_query = (
                not query
                or query in faq["question"].lower()
                or query in faq["answer"].lower()
            )
            matches_cat = (active == "All"
                           or faq["category"] == active)
            visible = matches_query and matches_cat
            widget.setVisible(visible)
            if visible:
                visible_per_cat[faq["category"]] += 1

        for cat, heading in self.category_headings.items():
            heading.setVisible(visible_per_cat[cat] > 0)

        total_visible = sum(visible_per_cat.values())
        self.lbl_no_results.setVisible(total_visible == 0)
        self.scroll.setVisible(total_visible > 0)