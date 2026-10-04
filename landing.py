"""
landing.py - Main window and navigation for Moxie.

Owns the QStackedWidget of pages (guest home, register, login, volunteer
home, FAQ, volunteer listing, org dashboard) plus the session-aware nav
bar, the guest search bar, and the global mic button.

The guest home hero scales with the window (see HeroLogo + _sync_hero_height).
The three feature cards emit their own signals so they can route to
different pages.
"""

import webbrowser

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QIcon, QPixmap, QCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMenu, QStackedWidget, QScrollArea, QMessageBox,
)

import theme
from db import Database
from searchBar import SearchBar
from featuresSection import FeaturesSection
from heroLogo import HeroLogo
from opportunitiesSection import OpportunitiesSection
from volunteerRegister import VolunteerRegistration
from orgRegister import OrganizationRegistration
from login import Login
from volunteerHome import VolunteerHome, TAB_PROFILE
from FAQ import FAQPage
from volunteerPage import VolunteerPage
from orgDashboard import OrgDashboard
from globalMic import GlobalMicButton


# Stack page indices
PAGE_HOME = 0
PAGE_VOL_REG = 1
PAGE_ORG_REG = 2
PAGE_LOGIN = 3
PAGE_VOL_HOME = 4
PAGE_FAQ = 5
PAGE_VOL_LIST = 6
PAGE_ORG_DASH = 7

# Nav modes
NAV_GUEST, NAV_VOLUNTEER, NAV_ORG = "guest", "volunteer", "org"

# In volunteer mode, the public "Volunteer" listing tab is inserted
# right after this VolunteerHome tab index (2 == "My Events").
LISTING_AFTER_HOME_TAB = 2


class Landing(QMainWindow):
    # Fraction of the window height the guest-home hero should occupy.
    # Bump toward 0.85 for a bigger wordmark; drop toward 0.60 to leave
    # more content visible below the fold.
    HERO_HEIGHT_FRACTION = 0.72

    def __init__(self, settings: QSettings | None = None):
        super().__init__()
        self.settings = settings or QSettings()

        self.setWindowTitle("Moxie")
        self.setWindowIcon(QIcon(theme.asset("logoHalfDark.png")))
        self.resize(1000, 700)

        self.is_dark_mode = (
            self.settings.value("theme", "light", type=str) == "dark"
        )

        self.current_user = None
        self.current_org = None

        self.nav_mode = NAV_GUEST
        self._nav_buttons = {}

        self.db = Database()

        self._build_ui()
        self.global_mic = GlobalMicButton(self)
        self.global_mic.reposition()
        self._wire_signals()
        self._set_nav_mode(NAV_GUEST)

        theme.apply_theme(self._app(), self.is_dark_mode)
        self._update_logos()
        self._sync_search_bar_visibility()

        # Make the hero fill the window height from the very first frame.
        self._sync_hero_height()

        self._refresh_home_carousels()

    # ── UI construction ───────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_nav(), 0)

        self.searchBar = SearchBar()
        try:
            self.searchBar.populate_categories(
                self.db.getDistinctCategories()
            )
        except Exception as e:
            print("Could not load categories:", e)
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
        self.nav_logo.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        self.nav_logo.mousePressEvent = lambda e: self.show_home_page()

        self.navTabs = QWidget()
        self.navTabsLayout = QHBoxLayout(self.navTabs)
        self.navTabsLayout.setContentsMargins(0, 0, 0, 0)
        self.navTabsLayout.setSpacing(8)

        self.btnConnect = QPushButton("Register ▾")
        self.btnConnect.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )

        register_menu = QMenu(self)
        action_vol = QAction("Register as a Volunteer", self)
        action_org = QAction("Register an Organization", self)
        action_vol.triggered.connect(self.show_volunteer_register_page)
        action_org.triggered.connect(self.show_org_register_page)
        register_menu.addAction(action_vol)
        register_menu.addAction(action_org)
        self.btnConnect.setMenu(register_menu)

        self.btnLogin = QPushButton("Login")
        self.btnLogin.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        self.btnLogin.clicked.connect(self.handle_login_nav_click)

        self.btnThemeToggle = QPushButton(
            "🌙" if not self.is_dark_mode else "☀"
        )
        self.btnThemeToggle.setToolTip("Toggle dark / light mode")
        self.btnThemeToggle.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        self.btnThemeToggle.clicked.connect(self.toggle_theme)

        h.addWidget(self.nav_logo)
        h.addStretch()
        h.addWidget(self.navTabs)
        h.addWidget(self.btnConnect)
        h.addWidget(self.btnLogin)
        h.addWidget(self.btnThemeToggle)
        return nav

    def _populate_page_stack(self):
        # 0 - Guest home
        self.guestHomePage = self._build_guest_home()
        self.pageStack.addWidget(self.guestHomePage)

        # 1 - Volunteer register
        self.volunteerRegisterPage = VolunteerRegistration(
            db=self.db,
            on_success=self._handle_registration_success,
            on_back_click=self.show_home_page,
        )
        self.pageStack.addWidget(self.volunteerRegisterPage)

        # 2 - Org register
        self.orgRegisterPage = OrganizationRegistration(
            db=self.db,
            on_success=self._handle_registration_success,
            on_back_click=self.show_home_page,
        )
        self.pageStack.addWidget(self.orgRegisterPage)

        # 3 - Login
        self.loginPage = Login(
            db=self.db,
            on_login_success=self._handle_login_success,
            on_back_click=self.show_home_page,
        )
        self.pageStack.addWidget(self.loginPage)

        # 4 - Volunteer home
        self.volunteerHomePage = VolunteerHome(db=self.db)
        self.volunteerHomePage.tabChanged.connect(
            lambda _i: self._sync_nav_highlight()
        )
        self.volunteerHomePage.browseOpportunitiesRequested.connect(
            self.show_volunteer_listing_page
        )
        self.volunteerHomePage.goToProfileRequested.connect(
            lambda: self.show_volunteer_tab(TAB_PROFILE)
        )
        self.pageStack.addWidget(self.volunteerHomePage)

        # 5 - FAQ
        self.faqPage = FAQPage(on_back_click=self.show_home_page)
        self.pageStack.addWidget(self.faqPage)

        # 6 - Volunteer listing
        self.volunteerListingPage = VolunteerPage(
            db=self.db, on_back_click=self.show_home_page
        )
        self.volunteerListingPage.openLinkRequested.connect(
            self.open_external_link
        )
        self.volunteerListingPage.rsvpSucceeded.connect(
            self._handle_rsvp_success
        )
        self.pageStack.addWidget(self.volunteerListingPage)

        # 7 - Org dashboard
        self.orgDashboard = OrgDashboard(
            db=self.db,
            on_logout_click=self.handle_org_logout,
            on_back_click=self.show_home_page,
        )
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

        # Hero (kept as an attribute so resizeEvent can resize it).
        self.hero_widget = self._build_hero()
        layout.addWidget(self.hero_widget, 0)

        self.featuresSection = FeaturesSection()
        # Each card routes to a real page instead of doing nothing.
        self.featuresSection.discoverRequested.connect(
            lambda: self.show_volunteer_listing_page()
        )
        self.featuresSection.postRequested.connect(
            self.show_org_register_page
        )
        self.featuresSection.manageRequested.connect(
            self.show_org_register_page
        )
        layout.addWidget(self.featuresSection)

        self.opportunitiesSection = OpportunitiesSection()
        self.opportunitiesSection = OpportunitiesSection()
        self.opportunitiesSection.detailsRequested.connect(self._open_event_details)
        self.opportunitiesSection.openLinkRequested.connect(self.open_external_link)
        self.opportunitiesSection.rsvpRequested.connect(self._handle_home_rsvp)
        layout.addWidget(self.opportunitiesSection)
        layout.addWidget(self.opportunitiesSection)
        layout.addStretch(1)

        self.homeScrollArea.setWidget(content)
        outer.addWidget(self.homeScrollArea)
        return page

    def _build_hero(self):
        """Full-bleed hero. Height is driven by _sync_hero_height so it
        grows with the window instead of sitting at a fixed 420px."""
        hero = QWidget()
        hero.setObjectName(theme.HERO_SECTION)
        hero.setMinimumHeight(420)
        hero.setSizePolicy(
            hero.sizePolicy().horizontalPolicy(),
            hero.sizePolicy().verticalPolicy(),
        )

        layout = QVBoxLayout(hero)
        # Small side margins so the wordmark can be nearly full-width on
        # wide screens but never touches the very edge. Set side margins
        # to 0 if you want it truly edge-to-edge.
        layout.setContentsMargins(20, 30, 20, 30)

        self.hero_logo = HeroLogo()
        self.hero_logo.setObjectName(theme.HERO_LOGO)
        layout.addWidget(self.hero_logo, 1)

        return hero

    # ── Session-aware nav bar ─────────────────────────────────────────
    def _nav_spec(self, mode):
        if mode == NAV_VOLUNTEER:
            specs = []
            for i, label in enumerate(VolunteerHome.TAB_LABELS):
                specs.append(
                    (("vol_home", i), label,
                     lambda i=i: self.show_volunteer_tab(i))
                )
                if i == LISTING_AFTER_HOME_TAB:
                    specs.append(
                        (("listing", None), "Volunteer",
                         lambda: self.show_volunteer_listing_page())
                    )
            return specs

        if mode == NAV_ORG:
            labels = getattr(self.orgDashboard, "TAB_LABELS", None) \
                or ["Dashboard"]
            specs = [
                (("org", i), label,
                 lambda i=i: self._show_org_nav_tab(i))
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
        self.nav_mode = mode

        while self.navTabsLayout.count():
            item = self.navTabsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._nav_buttons = {}

        logged_in = mode != NAV_GUEST

        # Every nav tab is a plain text button - no toggle styling,
        # no pill, no highlight. Matches the guest nav bar exactly.
        for key, label, callback in self._nav_spec(mode):
            btn = QPushButton(label)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(
                lambda _checked=False, cb=callback: cb()
            )
            self.navTabsLayout.addWidget(btn)

        self.btnConnect.setVisible(not logged_in)
        self.btnLogin.setText("Log Out" if logged_in else "Login")

    def _active_nav_key(self):
        return None

    def _sync_nav_highlight(self):
        return

    # ── Signals ───────────────────────────────────────────────────────
    def _wire_signals(self):
        self.searchBar.searchRequested.connect(self.handle_search)

    # ── Navigation helpers ────────────────────────────────────────────
    def _goto(self, page_widget):
        self.pageStack.setCurrentWidget(page_widget)
        self._sync_search_bar_visibility()
        self._sync_nav_highlight()

    def _sync_search_bar_visibility(self):
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
        """Show a stack page directly on the org dashboard."""
        self._goto(self.orgDashboard)
        show = getattr(self.orgDashboard, "show_tab", None)
        if callable(show):
            show(idx)

    def _show_org_nav_tab(self, nav_idx):
        """Called by the org nav buttons. nav_idx is a position in
        OrgDashboard.TAB_LABELS, translated to a stack index by the
        dashboard itself (the form page has no nav button)."""
        self._goto(self.orgDashboard)
        fn = getattr(self.orgDashboard, "show_nav_tab", None)
        if callable(fn):
            fn(nav_idx)
        else:
            show = getattr(self.orgDashboard, "show_tab", None)
            if callable(show):
                show(nav_idx)

    def show_volunteer_listing_page(self, keyword=None, filters=None):
        if keyword:
            self.volunteerListingPage.set_search_text(keyword)
        if filters:
            self.volunteerListingPage.apply_external_filters(filters)
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

    def handle_login_nav_click(self):
        if self.current_user:
            self.handle_logout()
        elif self.current_org:
            self.handle_org_logout()
        else:
            self.show_login_page()

    # ── Registration callback ─────────────────────────────────────────
    def _handle_registration_success(self, userID):
        self.show_login_page()

    # ── Login callback ────────────────────────────────────────────────
    def _handle_login_success(self, user):
        if user["role"] == "volunteer":
            self.current_user = user
            self.current_org = None
            self._set_nav_mode(NAV_VOLUNTEER)
            self.volunteerHomePage.set_user_data(user)
            self.volunteerListingPage.set_current_volunteer(user["userID"])
            self._refresh_home_carousels()
            self._goto(self.volunteerHomePage)
        else:
            self.current_org = user
            self.current_user = None
            self._set_nav_mode(NAV_ORG)
            self.orgDashboard.set_org_data(user)
            self._goto(self.orgDashboard)

    # ── Logout callbacks ──────────────────────────────────────────────
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

    # ── RSVP callback ─────────────────────────────────────────────────
    def _handle_rsvp_success(self, opportunity_id):
        if not self.current_user:
            return
        self._goto(self.volunteerHomePage)
        self.volunteerHomePage.show_my_events()

    # ── Home carousels ────────────────────────────────────────────────
    def _refresh_home_carousels(self):
        if not hasattr(self, "opportunitiesSection"):
            return
        volunteer_id = (self.current_user["userID"]
                        if self.current_user else None)
        try:
            self.opportunitiesSection.load_from_db(
                self.db, current_volunteer_id=volunteer_id
            )
        except Exception as e:
            print("Failed to refresh home carousels:", e)

    # ── Search ────────────────────────────────────────────────────────
    def handle_search(self, filters: dict):
        """SearchBar emits a full filter dict; forward it to the
        listing page's FilterBar so its widgets reflect the query."""
        if not filters:
            return
        self.show_volunteer_listing_page(filters=filters)

    def open_external_link(self, url):
        if url:
            webbrowser.open(url)
    def _open_event_details(self, card):
        """Open the same EventDetailsDialog the listing page uses."""
        from eventDetailsDialog import EventDetailsDialog
        EventDetailsDialog(card, self).exec()

    def _handle_home_rsvp(self, opportunity_id):
        """RSVP from the guest-home carousels. The guest home is only shown
        when no user is logged in, so this almost always lands on the login
        prompt — but the logged-in branch is here for completeness."""
        if not self.current_user:
            QMessageBox.information(
                self, "Login required",
                "Log in as a volunteer to sign up for events.",
            )
            return

        result = self.db.registerForOpportunity(
            self.current_user["userID"], opportunity_id
        )
        if result == "ok":
            try:
                row = self.db.getOpportunityByID(opportunity_id)
                title = row["title"] if row else "an event"
                self.db.addNotification(
                    self.current_user["userID"],
                    f"You signed up for {title}.",
                    "rsvp", opportunity_id,
                )
            except Exception as e:
                print("addNotification failed:", e)
            QMessageBox.information(
                self, "Registered",
                "You're signed up! Taking you to My Events.",
            )
            self._handle_rsvp_success(opportunity_id)
        elif result == "duplicate":
            QMessageBox.information(
                self, "Already registered",
                "You've already RSVP'd for this event.",
            )
        elif result == "full":
            QMessageBox.warning(
                self, "Event full",
                "This event has reached capacity.",
            )
        else:
            QMessageBox.warning(self, "Error", "Could not complete RSVP.")

    # ── Theme ─────────────────────────────────────────────────────────
    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.settings.setValue(
            "theme", "dark" if self.is_dark_mode else "light"
        )
        theme.apply_theme(self._app(), self.is_dark_mode)
        self.btnThemeToggle.setText("☀" if self.is_dark_mode else "🌙")
        self._update_logos()

    def _update_logos(self):
        filename = ("logoFullLight.png" if self.is_dark_mode
                    else "logoFullDark.png")
        path = theme.asset(filename)

        smooth = Qt.TransformationMode.SmoothTransformation

        # Nav logo stays a small fixed height - that's fine.
        nav_pixmap = QPixmap(path).scaledToHeight(32, smooth)
        self.nav_logo.setPixmap(nav_pixmap)

        # Hero: hand the full-res pixmap to HeroLogo. It will fit itself
        # to whatever box the layout gives it, on every resize.
        if hasattr(self, "hero_logo"):
            self.hero_logo.set_source(QPixmap(path))

    # ── Hero sizing ───────────────────────────────────────────────────
    def _sync_hero_height(self):
        """Make the hero resize with the window. Called from resizeEvent
        and once at startup from __init__."""
        if not hasattr(self, "hero_widget"):
            return
        vh = self.height()
        target = int(vh * self.HERO_HEIGHT_FRACTION)
        # Never smaller than 420, never taller than the window minus a
        # small allowance for the nav bar and search bar.
        target = max(420, min(target, vh - 120))
        # Pin both min and max so the layout can't disagree with us.
        if self.hero_widget.minimumHeight() != target:
            self.hero_widget.setMinimumHeight(target)
            self.hero_widget.setMaximumHeight(target)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "global_mic"):
            self.global_mic.reposition()
            self.global_mic.raise_()
        self._sync_hero_height()
        self._update_logos()

    # ── Utilities ─────────────────────────────────────────────────────
    def _app(self):
        return QApplication.instance()

    def closeEvent(self, event):
        try:
            self.db.close()
        except Exception:
            pass
        super().closeEvent(event)