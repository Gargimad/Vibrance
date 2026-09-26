"""
landing.py — Main window for Moxie.

Owns the nav bar, search bar, page stack, and session state.

Pages in the stack (index):
    0  guest home          hero + features + opportunity carousels
    1  volunteer register  VolunteerRegistration
    2  org register        OrganizationRegistration
    3  login               unified Login (volunteer/org toggle + MFA)
    4  volunteer home      VolunteerHome (dashboard)
    5  FAQ                 FAQPage
    6  volunteer listing   VolunteerPage
    7  org dashboard       OrgDashboard

Routing on login:
    user['role'] == 'volunteer'  → show volunteer home
    user['role'] == 'org'        → show org dashboard

The top nav bar has three modes, switched by _set_nav_mode():
    guest      Volunteer · Organize · FAQ · Register ▾ · Login
    volunteer  tabs from VolunteerHome.TAB_LABELS, with the public
               "Volunteer" listing slotted in after "My Events" · Log Out
    org        tabs from OrgDashboard.TAB_LABELS (if it defines them),
               plus FAQ · Log Out

Theme is applied via theme.apply_theme(app, is_dark). Toggle persists
through QSettings('theme').
"""

import os
import webbrowser

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QIcon, QPixmap, QCursor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu,
    QPushButton, QScrollArea, QStackedWidget,
)

import theme
from db import Database

from searchBar import SearchBar
from featuresSection import FeaturesSection
from opportunitiesSection import OpportunitiesSection
from FAQ import FAQPage

from login import Login
from volunteerRegister import VolunteerRegistration
from orgRegister import OrganizationRegistration
from volunteerHome import VolunteerHome
from orgDashboard import OrgDashboard
from volunteerPage import VolunteerPage


# Page-stack indices — keep in sync with the construction order below
PAGE_HOME       = 0
PAGE_VOL_REG    = 1
PAGE_ORG_REG    = 2
PAGE_LOGIN      = 3
PAGE_VOL_HOME   = 4
PAGE_FAQ        = 5
PAGE_VOL_LIST   = 6
PAGE_ORG_DASH   = 7

# Nav modes
NAV_GUEST, NAV_VOLUNTEER, NAV_ORG = "guest", "volunteer", "org"

# In volunteer mode, the public "Volunteer" listing tab is inserted right
# after this VolunteerHome tab index (2 == "My Events").
LISTING_AFTER_HOME_TAB = 2


class Landing(QMainWindow):
    def __init__(self, settings: QSettings | None = None):
        super().__init__()
        self.settings = settings or QSettings()

        self.setWindowTitle("Moxie")
        self.setWindowIcon(QIcon(theme.asset("logoHalfDark.png")))
        self.resize(1000, 700)

        self.is_dark_mode = (
            self.settings.value("theme", "light", type=str) == "dark"
        )

        # Session state — exactly one of these is set at a time
        self.current_user = None   # volunteer dict from db.authenticate()
        self.current_org = None    # org dict from db.authenticate()

        self.nav_mode = NAV_GUEST
        self._nav_buttons = {}     # nav key -> checkable tab button

        self.db = Database()

        self._build_ui()
        self._wire_signals()
        self._set_nav_mode(NAV_GUEST)

        theme.apply_theme(self._app(), self.is_dark_mode)
        self._update_logos()
        self._sync_search_bar_visibility()

        # Initial population of the home-page carousels
        self._refresh_home_carousels()

    # ── UI construction ───────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_nav(), 0)

        self.searchBar = SearchBar()
        layout.addWidget(self.searchBar, 0)

        self.pageStack = QStackedWidget()
        self._populate_page_stack()
        layout.addWidget(self.pageStack, 1)

    def _build_nav(self):
        nav = QWidget()
        nav.setObjectName(theme.NAV_BAR)
        h = QHBoxLayout(nav)
        h.setContentsMargins(20, 10, 20, 10)
        h.setSpacing(8)

        self.nav_logo = QLabel()
        self.nav_logo.setObjectName(theme.NAV_LOGO)
        self.nav_logo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nav_logo.mousePressEvent = lambda e: self.show_home_page()

        # Container whose buttons are rebuilt by _set_nav_mode()
        self.navTabs = QWidget()
        self.navTabsLayout = QHBoxLayout(self.navTabs)
        self.navTabsLayout.setContentsMargins(0, 0, 0, 0)
        self.navTabsLayout.setSpacing(8)

        # Register dropdown (guests only)
        self.btnConnect = QPushButton("Register ▾")
        self.btnConnect.setObjectName(theme.NAV_DROPDOWN)

        register_menu = QMenu(self)
        action_vol = QAction("Register as a Volunteer", self)
        action_org = QAction("Register an Organization", self)
        action_vol.triggered.connect(self.show_volunteer_register_page)
        action_org.triggered.connect(self.show_org_register_page)
        register_menu.addAction(action_vol)
        register_menu.addAction(action_org)
        self.btnConnect.setMenu(register_menu)

        # "Login" for guests, "Log Out" once signed in
        self.btnLogin = QPushButton("Login")
        self.btnLogin.clicked.connect(self.handle_login_nav_click)

        self.btnThemeToggle = QPushButton(
            "🌙" if not self.is_dark_mode else "☀"
        )
        self.btnThemeToggle.setToolTip("Toggle dark / light mode")
        self.btnThemeToggle.clicked.connect(self.toggle_theme)

        h.addWidget(self.nav_logo)
        h.addStretch()
        h.addWidget(self.navTabs)
        h.addWidget(self.btnConnect)
        h.addWidget(self.btnLogin)
        h.addWidget(self.btnThemeToggle)

        for btn in (self.btnConnect, self.btnLogin, self.btnThemeToggle):
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        return nav

    def _populate_page_stack(self):
        # 0 — Guest home
        self.guestHomePage = self._build_guest_home()
        self.pageStack.addWidget(self.guestHomePage)

        # 1 — Volunteer register
        self.volunteerRegisterPage = VolunteerRegistration(
            db=self.db,
            on_success=self._handle_registration_success,
            on_back_click=self.show_home_page,
        )
        self.pageStack.addWidget(self.volunteerRegisterPage)

        # 2 — Org register
        self.orgRegisterPage = OrganizationRegistration(
            db=self.db,
            on_success=self._handle_registration_success,
            on_back_click=self.show_home_page,
        )
        self.pageStack.addWidget(self.orgRegisterPage)

        # 3 — Login
        self.loginPage = Login(
            db=self.db,
            on_login_success=self._handle_login_success,
            on_back_click=self.show_home_page,
        )
        self.pageStack.addWidget(self.loginPage)

        # 4 — Volunteer home (tabs are driven by the nav bar; logout lives
        # in the nav bar too)
        self.volunteerHomePage = VolunteerHome(db=self.db)
        self.volunteerHomePage.tabChanged.connect(
            lambda _i: self._sync_nav_highlight()
        )
        self.pageStack.addWidget(self.volunteerHomePage)

        # 5 — FAQ
        self.faqPage = FAQPage(on_back_click=self.show_home_page)
        self.pageStack.addWidget(self.faqPage)

        # 6 — Volunteer listing
        self.volunteerListingPage = VolunteerPage(
            db=self.db, on_back_click=self.show_home_page
        )
        self.volunteerListingPage.openLinkRequested.connect(
            self.open_external_link
        )
        self.pageStack.addWidget(self.volunteerListingPage)

        # 7 — Org dashboard
        self.orgDashboard = OrgDashboard(
            db=self.db,
            on_logout_click=self.handle_org_logout,
            on_back_click=self.show_home_page,
        )
        # Optional: if OrgDashboard defines a tabChanged signal, keep the
        # nav highlight in sync with it.
        if hasattr(self.orgDashboard, "tabChanged"):
            self.orgDashboard.tabChanged.connect(
                lambda _i: self._sync_nav_highlight()
            )
        self.pageStack.addWidget(self.orgDashboard)

    def _build_guest_home(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.homeScrollArea = QScrollArea()
        self.homeScrollArea.setObjectName(theme.HOME_SCROLL)
        self.homeScrollArea.setWidgetResizable(True)
        self.homeScrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.homeScrollArea.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content.setObjectName(theme.HOME_SCROLL_CONTENT)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_hero())
        self.featuresSection = FeaturesSection()
        layout.addWidget(self.featuresSection)
        self.opportunitiesSection = OpportunitiesSection()
        layout.addWidget(self.opportunitiesSection)
        layout.addStretch(1)

        self.homeScrollArea.setWidget(content)
        outer.addWidget(self.homeScrollArea)
        return page

    def _build_hero(self):
        hero = QWidget()
        hero.setObjectName(theme.HERO_SECTION)
        hero.setFixedHeight(420)
        layout = QVBoxLayout(hero)
        layout.setContentsMargins(0, 0, 0, 0)

        self.hero_logo = QLabel()
        self.hero_logo.setObjectName(theme.HERO_LOGO)
        self.hero_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(self.hero_logo)
        center.addStretch(1)

        layout.addStretch(1)
        layout.addLayout(center)
        layout.addStretch(1)
        return hero

    # ── Session-aware nav bar ─────────────────────────────────────────────
    def _nav_spec(self, mode):
        """Return [(key, label, callback), ...] for the given nav mode.

        `key` identifies the destination so _sync_nav_highlight() can work
        out which button matches the page currently on screen.
        """
        if mode == NAV_VOLUNTEER:
            specs = []
            for i, label in enumerate(VolunteerHome.TAB_LABELS):
                specs.append((
                    ("vol_home", i), label,
                    lambda i=i: self.show_volunteer_tab(i),
                ))
                if i == LISTING_AFTER_HOME_TAB:
                    specs.append((
                        ("listing", None), "Volunteer",
                        lambda: self.show_volunteer_listing_page(),
                    ))
            return specs

        if mode == NAV_ORG:
            labels = getattr(self.orgDashboard, "TAB_LABELS", None) \
                or ["Dashboard"]
            specs = [
                (("org", i), label, lambda i=i: self.show_org_tab(i))
                for i, label in enumerate(labels)
            ]
            specs.append((("faq", None), "FAQ", self.show_faq_page))
            return specs

        # Guest
        return [
            (("listing", None), "Volunteer",
             lambda: self.show_volunteer_listing_page()),
            (("faq", None), "FAQ", self.show_faq_page),
        ]

    def _set_nav_mode(self, mode):
        """Rebuild the tab buttons for guest / volunteer / org."""
        self.nav_mode = mode

        # Clear old tab buttons
        while self.navTabsLayout.count():
            item = self.navTabsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._nav_buttons = {}

        logged_in = mode != NAV_GUEST
        for key, label, callback in self._nav_spec(mode):
            btn = QPushButton(label)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if logged_in:
                # Same look as the dashboard's old tab toggles
                btn.setObjectName(theme.VIEW_TOGGLE_BTN)
                btn.setCheckable(True)
            btn.clicked.connect(lambda _checked=False, cb=callback: cb())
            self.navTabsLayout.addWidget(btn)
            if logged_in:
                self._nav_buttons[key] = btn

        self.btnConnect.setVisible(not logged_in)
        self.btnLogin.setText("Log Out" if logged_in else "Login")
        self._sync_nav_highlight()

    def _active_nav_key(self):
        page = self.pageStack.currentWidget()
        if self.nav_mode == NAV_VOLUNTEER:
            if page is self.volunteerHomePage:
                return ("vol_home", self.volunteerHomePage.current_tab())
            if page is self.volunteerListingPage:
                return ("listing", None)
        elif self.nav_mode == NAV_ORG:
            if page is self.orgDashboard:
                current = getattr(self.orgDashboard, "current_tab", None)
                return ("org", current() if callable(current) else 0)
            if page is self.faqPage:
                return ("faq", None)
        return None

    def _sync_nav_highlight(self):
        if not self._nav_buttons:
            return
        active = self._active_nav_key()
        for key, btn in self._nav_buttons.items():
            btn.setChecked(key == active)

    # ── Signals ───────────────────────────────────────────────────────────
    def _wire_signals(self):
        self.searchBar.searchRequested.connect(self.handle_search)

    # ── Navigation helpers ────────────────────────────────────────────────
    def _goto(self, page_widget):
        self.pageStack.setCurrentWidget(page_widget)
        self._sync_search_bar_visibility()
        self._sync_nav_highlight()

    def _sync_search_bar_visibility(self):
        # Search only makes sense on the guest home page
        self.searchBar.setVisible(
            self.pageStack.currentWidget() is self.guestHomePage
        )

    def show_home_page(self):
        if self.current_user:
            self._goto(self.volunteerHomePage)
        elif self.current_org:
            self._goto(self.orgDashboard)
        else:
            self._goto(self.guestHomePage)

    def show_volunteer_tab(self, idx):
        self._goto(self.volunteerHomePage)
        self.volunteerHomePage.show_tab(idx)

    def show_org_tab(self, idx):
        self._goto(self.orgDashboard)
        show = getattr(self.orgDashboard, "show_tab", None)
        if callable(show):
            show(idx)

    def show_volunteer_listing_page(self, keyword=None):
        if keyword:
            self.volunteerListingPage.set_search_text(keyword)
        self._goto(self.volunteerListingPage)

    def show_volunteer_register_page(self):
        self._goto(self.volunteerRegisterPage)

    def show_org_register_page(self):
        self._goto(self.orgRegisterPage)

    def show_faq_page(self):
        self._goto(self.faqPage)

    def show_login_page(self):
        self.loginPage.clear_inputs()
        self._goto(self.loginPage)
    """
    def handle_organize_click(self):
        if self.current_org:
            self._goto(self.orgDashboard)
        else:
            self.show_login_page()
    """
    def handle_login_nav_click(self):
        """Doubles as Login (guest) and Log Out (signed in)."""
        if self.current_user:
            self.handle_logout()
        elif self.current_org:
            self.handle_org_logout()
        else:
            self.show_login_page()

    # ── Registration callback ─────────────────────────────────────────────
    def _handle_registration_success(self, userID):
        # Don't auto-login after registration — the user still has to
        # authenticate (and pass MFA). Send them to the login page with
        # a fresh form.
        self.show_login_page()

    # ── Login callback ────────────────────────────────────────────────────
    def _handle_login_success(self, user):
        if user["role"] == "volunteer":
            self.current_user = user
            self.current_org = None
            self._set_nav_mode(NAV_VOLUNTEER)
            self.volunteerHomePage.set_user_data(user)
            self.volunteerListingPage.set_current_volunteer(user["userID"])
            self._refresh_home_carousels()
            self._goto(self.volunteerHomePage)
        else:  # org
            self.current_org = user
            self.current_user = None
            self._set_nav_mode(NAV_ORG)
            self.orgDashboard.set_org_data(user)
            self._goto(self.orgDashboard)

    # ── Logout callbacks ──────────────────────────────────────────────────
    def handle_logout(self):
        self.current_user = None
        self.volunteerListingPage.set_current_volunteer(None)
        self._set_nav_mode(NAV_GUEST)
        self._refresh_home_carousels()
        self._goto(self.guestHomePage)

    def handle_org_logout(self):
        self.current_org = None
        self._set_nav_mode(NAV_GUEST)
        self._goto(self.guestHomePage)

    # ── Home carousels ────────────────────────────────────────────────────
    def _refresh_home_carousels(self):
        """
        Rebuild the three home-page carousels with the current session in
        mind. Called at startup, on volunteer login, and on logout so the
        RSVP tooltips and enabled state reflect who's logged in.
        """
        if not hasattr(self, "opportunitiesSection"):
            return
        volunteer_id = self.current_user["userID"] if self.current_user else None
        try:
            self.opportunitiesSection.load_from_db(
                self.db, current_volunteer_id=volunteer_id
            )
        except Exception as e:
            print("Failed to refresh home carousels:", e)

    # ── Search ────────────────────────────────────────────────────────────
    def handle_search(self, keyword, category):
        if not keyword:
            return
        self.show_volunteer_listing_page(keyword=keyword)
        if category and category != "All":
            # The listing page's FilterBar knows how to map legacy values
            self.volunteerListingPage.set_type_filter(category)

    def open_external_link(self, url):
        if url:
            webbrowser.open(url)

    # ── Theme ─────────────────────────────────────────────────────────────
    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.settings.setValue(
            "theme", "dark" if self.is_dark_mode else "light"
        )
        theme.apply_theme(self._app(), self.is_dark_mode)
        self.btnThemeToggle.setText("☀" if self.is_dark_mode else "🌙")
        self._update_logos()

    def _update_logos(self):
        # Logo asset names are counterintuitive:
        #   logoFullLight.png  — light-coloured text, used on dark bg
        #   logoFullDark.png   — dark-coloured text, used on light bg
        filename = ("logoFullLight.png" if self.is_dark_mode
                    else "logoFullDark.png")
        path = theme.asset(filename)

        smooth = Qt.TransformationMode.SmoothTransformation
        nav_pixmap = QPixmap(path).scaledToHeight(32, smooth)
        self.nav_logo.setPixmap(nav_pixmap)

        hero_pixmap = QPixmap(path).scaledToHeight(500, smooth)
        self.hero_logo.setPixmap(hero_pixmap)

    # ── Utilities ─────────────────────────────────────────────────────────
    def _app(self):
        from PyQt6.QtWidgets import QApplication
        return QApplication.instance()

    def closeEvent(self, event):
        try:
            self.db.close()
        except Exception:
            pass
        super().closeEvent(event)