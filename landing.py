"""
Gargi Madala
Congressional App Challenge 2026
Moxie- A Volunteering Management System
23 September 2026
Landing.py
"""
#This file contains the landing page of the application, which includes the navigation bar, search bar, and various sections for volunteers and organizations.
#It greets new users and provides options for registration, login, and exploring volunteering opportunities.


#My imports
import os
import webbrowser
#The PyQt6 imports:
#They are used to create the graphical user interface (GUI) elements of the application, such as windows, buttons, labels, and layouts.
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QIcon, QPixmap, QCursor
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QMenu, QPushButton,
    QScrollArea, QStackedWidget, QVBoxLayout, QWidget
)

#These are imports of classes from other files in the project, which are used to create different pages and functionalities within the application.
#THe registration pages for volunteers and organizations:
from orgRegister import OrganizationRegistration
from volunteerRegister import VolunteerRegistration

#The login pages for for volunteers and organizations
from volunteerLogin import VolunteerLogin
from volunteerHome import VolunteerHome
from orgLogin import OrgLogin
from orgDashboard import OrgDashboard
from searchBar import SearchBar
from featuresSection import FeaturesSection
from opportunitiesSection import OpportunitiesSection
from volunteerPage import VolunteerPage
from db import Database
from FAQ import FAQPage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Landing(QMainWindow):

    def __init__(self, settings: QSettings | None = None):
        super().__init__()
        self.settings = settings or QSettings()

        self.setWindowTitle("Moxie")
        self.setWindowIcon(QIcon(os.path.join(BASE_DIR, "logoHalfDark.png")))
        self.resize(900, 600)

        # Theme persistence — QSettings stores this across launches
        self.is_dark_mode = self.settings.value("theme", "light", type=str) == "dark"
        self.current_user = None
        self.current_org = None

        self.db = Database()

        # ---- Nav bar ----
        mainWid = QWidget()
        self.setCentralWidget(mainWid)
        mainLayout = QVBoxLayout(mainWid)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        navWid = QWidget()
        navWid.setObjectName("NavBar")
        navLayout = QHBoxLayout(navWid)
        navLayout.setContentsMargins(20, 10, 20, 10)

        self.nav_logo = QLabel()
        self.nav_logo.setObjectName("NavLogo")
        self.nav_logo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.nav_logo.mousePressEvent = lambda event: self.show_home_page()

        self.btnVolunteer = QPushButton("Volunteer")
        self.btnVolunteer.clicked.connect(self.show_volunteer_listing_page)

        self.btnOrganize = QPushButton("Organize")
        self.btnOrganize.clicked.connect(self.handle_organize_click)

        self.btnFAQ = QPushButton("FAQ")
        self.btnFAQ.clicked.connect(self.show_faq_page)

        self.btnLogin = QPushButton("Login")
        self.btnLogin.clicked.connect(self.handle_login_nav_click)

        self.btnConnect = QPushButton("Register ▾ ")
        self.btnConnect.setObjectName("NavDropdown")

        connectMenu = QMenu(self)
        connectMenu.setObjectName("NavDropdownMenu")
        self.actionVolunteer = QAction("Register as a Volunteer", self)
        self.actionOrg = QAction("Register an Organization", self)
        self.actionVolunteer.triggered.connect(self.show_volunteer_page)
        self.actionOrg.triggered.connect(self.show_org_page)
        connectMenu.addAction(self.actionVolunteer)
        connectMenu.addAction(self.actionOrg)

        self.btnThemeToggle = QPushButton("☀️" if self.is_dark_mode else "🌙")
        self.btnThemeToggle.setToolTip("Toggle Dark/Light Mode")
        self.btnThemeToggle.clicked.connect(self.toggle_theme)

        navLayout.addWidget(self.nav_logo)
        navLayout.addStretch()
        navLayout.addWidget(self.btnVolunteer)
        navLayout.addWidget(self.btnOrganize)
        navLayout.addWidget(self.btnFAQ)
        navLayout.addWidget(self.btnConnect)
        self.btnConnect.setMenu(connectMenu)
        navLayout.addWidget(self.btnLogin)
        navLayout.addWidget(self.btnThemeToggle)

        for btn in navWid.findChildren(QPushButton):
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # ---- Search bar ----
        self.searchBar = SearchBar()
        self.searchBar.searchRequested.connect(self.handle_search)

        # ---- Guest home: hero + features + opportunities ----
        heroWidget = QWidget()
        heroWidget.setObjectName("HeroSection")
        heroLayout = QVBoxLayout(heroWidget)
        heroLayout.setContentsMargins(0, 0, 0, 0)

        centerContainer = QHBoxLayout()
        self.hero_logo = QLabel()
        self.hero_logo.setObjectName("HeroLogo")
        self.hero_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        centerContainer.addStretch(1)
        centerContainer.addWidget(self.hero_logo)
        centerContainer.addStretch(1)

        heroLayout.addStretch(1)
        heroLayout.addLayout(centerContainer)
        heroLayout.addStretch(1)

        self.featuresSection = FeaturesSection()
        self.opportunitiesSection = OpportunitiesSection()

        self.guestHomePage = QWidget()
        homeOuterLayout = QVBoxLayout(self.guestHomePage)
        homeOuterLayout.setContentsMargins(0, 0, 0, 0)
        homeOuterLayout.setSpacing(0)

        self.homeScrollArea = QScrollArea()
        self.homeScrollArea.setObjectName("HomeScrollArea")
        self.homeScrollArea.setWidgetResizable(True)
        self.homeScrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.homeScrollArea.setFrameShape(QScrollArea.Shape.NoFrame)

        homeScrollContent = QWidget()
        homeScrollContent.setObjectName("HomeScrollContent")
        homeLayout = QVBoxLayout(homeScrollContent)
        homeLayout.setContentsMargins(0, 0, 0, 0)
        homeLayout.setSpacing(0)

        heroWidget.setFixedHeight(420)
        homeLayout.addWidget(heroWidget)
        homeLayout.addWidget(self.featuresSection)
        homeLayout.addWidget(self.opportunitiesSection)
        homeLayout.addStretch(1)

        self.homeScrollArea.setWidget(homeScrollContent)
        homeOuterLayout.addWidget(self.homeScrollArea)

        self.opportunitiesSection.load_from_db(self.db)

        # ---- Register / login pages ----
        self.volunteerPage = VolunteerRegistration(
            on_back_click=self.show_home_page)
        self.orgPage = OrganizationRegistration(
            on_back_click=self.show_home_page)
        self.volunteerLoginPage = VolunteerLogin(
            on_login_success=self.handle_login_success,
            on_back_click=self.show_home_page)

        self.volunteerHomePage = VolunteerHome(
            on_logout_click=self.handle_logout,
            db=self.db)

        # Org login + dashboard (NEW)
        self.orgLoginPage = OrgLogin(
            db=self.db,
            on_login_success=self.handle_org_login_success,
            on_back_click=self.show_home_page)
        self.orgDashboard = OrgDashboard(
            db=self.db,
            on_logout_click=self.handle_org_logout,
            on_back_click=self.show_home_page)

        self.faqPage = FAQPage(on_back_click=self.show_home_page)

        self.volunteerListingPage = VolunteerPage(
            db=self.db, on_back_click=self.show_home_page)
        self.volunteerListingPage.openLinkRequested.connect(self.open_external_link)
        # Tell the listing page who's logged in so it can show RSVP
        self.volunteerListingPage.set_current_volunteer(None)

        # ---- Stack ----
        self.pageStack = QStackedWidget()
        self.pageStack.addWidget(self.guestHomePage)         # 0
        self.pageStack.addWidget(self.volunteerPage)         # 1
        self.pageStack.addWidget(self.orgPage)               # 2
        self.pageStack.addWidget(self.volunteerLoginPage)    # 3
        self.pageStack.addWidget(self.volunteerHomePage)     # 4
        self.pageStack.addWidget(self.faqPage)               # 5
        self.pageStack.addWidget(self.volunteerListingPage)  # 6
        self.pageStack.addWidget(self.orgLoginPage)          # 7
        self.pageStack.addWidget(self.orgDashboard)          # 8

        mainLayout.addWidget(navWid, 0)
        mainLayout.addWidget(self.searchBar, 0)
        mainLayout.addWidget(self.pageStack, 1)

        self.apply_theme("darkMode.qss" if self.is_dark_mode else "lightMode.qss")
        self.update_logos()
        self._sync_search_bar_visibility()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _goto(self, widget):
        self.pageStack.setCurrentWidget(widget)
        self._sync_search_bar_visibility()

    def _sync_search_bar_visibility(self):
        current = self.pageStack.currentWidget()
        self.searchBar.setVisible(current is self.guestHomePage)

    # --- Volunteer session ---
    def handle_login_success(self, user_data):
        self.current_user = user_data
        self.volunteerHomePage.set_user_data(user_data)
        self.volunteerListingPage.set_current_volunteer(
            user_data["volunteerID"] if user_data else None)
        self.btnLogin.setText("Dashboard")
        self.btnConnect.setVisible(False)
        self._goto(self.volunteerHomePage)

    def handle_logout(self):
        self.current_user = None
        self.volunteerListingPage.set_current_volunteer(None)
        self.btnLogin.setText("Login")
        self.btnConnect.setVisible(True)
        self._goto(self.guestHomePage)

    def handle_login_nav_click(self):
        if self.current_user:
            self._goto(self.volunteerHomePage)
        elif self.current_org:
            self._goto(self.orgDashboard)
        else:
            self._goto(self.volunteerLoginPage)

    # --- Org session ---
    def handle_organize_click(self):
        if self.current_org:
            self._goto(self.orgDashboard)
        else:
            self._goto(self.orgLoginPage)

    def handle_org_login_success(self, org_data):
        self.current_org = org_data
        self.orgDashboard.set_org_data(org_data)
        self._goto(self.orgDashboard)

    def handle_org_logout(self):
        self.current_org = None
        self._goto(self.guestHomePage)

    # --- Page shortcuts ---
    def show_home_page(self):
        if self.current_user:
            self._goto(self.volunteerHomePage)
        elif self.current_org:
            self._goto(self.orgDashboard)
        else:
            self._goto(self.guestHomePage)

    def show_volunteer_page(self):
        self._goto(self.volunteerPage)

    def show_org_page(self):
        self._goto(self.orgPage)

    def show_faq_page(self):
        self._goto(self.faqPage)

    def show_volunteer_listing_page(self, keyword=None):
        if keyword:
            self.volunteerListingPage.set_search_text(keyword)
        self._goto(self.volunteerListingPage)

    # ------------------------------------------------------------------
    def handle_search(self, keyword, category):
        if not keyword:
            return
        self.show_volunteer_listing_page(keyword=keyword)
        if category and category != "All":
            set_type = getattr(self.volunteerListingPage, "set_type_filter", None)
            if callable(set_type):
                set_type(category)

    def open_external_link(self, url):
        if url:
            webbrowser.open(url)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def update_logos(self):
        logo_filename = os.path.join(
            BASE_DIR,
            "logoFullLight.png" if self.is_dark_mode else "logoFullDark.png")
        smooth = Qt.TransformationMode.SmoothTransformation

        nav_pixmap = QPixmap(logo_filename).scaledToHeight(32, smooth)
        self.nav_logo.setPixmap(nav_pixmap)

        hero_pixmap = QPixmap(logo_filename).scaledToHeight(500, smooth)
        self.hero_logo.setPixmap(hero_pixmap)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.settings.setValue("theme", "dark" if self.is_dark_mode else "light")
        qss = "darkMode.qss" if self.is_dark_mode else "lightMode.qss"

        self.apply_theme(qss)
        self.btnThemeToggle.setText("☀️" if self.is_dark_mode else "🌙")
        self.update_logos()

    def apply_theme(self, qss_filename):
        qss_path = os.path.join(BASE_DIR, qss_filename)

        was_fullscreen = self.isFullScreen()
        was_maximized = self.isMaximized()

        try:
            with open(qss_path, "r") as f:
                stylesheet = f.read()
                app = QApplication.instance()
                if isinstance(app, QApplication):
                    app.setStyleSheet(stylesheet)

            if was_fullscreen:
                self.showFullScreen()
            elif was_maximized:
                self.showMaximized()

        except FileNotFoundError:
            print(f"Error: Stylesheet not found at '{qss_path}'.")

    def closeEvent(self, event):
        try:
            self.db.close()
        except Exception:
            pass
        super().closeEvent(event)