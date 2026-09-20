import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QMenu, QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from orgRegister import OrganizationRegistration
from volunteerRegister import VolunteerRegistration
from volunteerLogin import VolunteerLogin


class Landing(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Moxie")
        self.setWindowIcon(QIcon("logoHalfDark.png"))
        self.resize(900, 600)

        self.is_dark_mode = False

        # Main layout container
        mainWid = QWidget()
        self.setCentralWidget(mainWid)
        mainLayout = QVBoxLayout(mainWid)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # Navigation bar
        navWid = QWidget()
        navWid.setObjectName("NavBar")
        navLayout = QHBoxLayout(navWid)
        navLayout.setContentsMargins(20, 10, 20, 10)

        # Store nav_logo as instance variable
        self.nav_logo = QLabel()
        self.nav_logo.setObjectName("NavLogo")
        self.nav_logo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.nav_logo.mousePressEvent = lambda event: self.show_home_page()

        btnAbout = QPushButton("About")
        btnFeatures = QPushButton("Features")
        btnDemo = QPushButton("Demo")
        btnLogin = QPushButton("Login")
        btnLogin.clicked.connect(self.show_login_volunteer_page)

        self.btnConnect = QPushButton("Register ▾ ")
        self.btnConnect.setObjectName("NavDropdown")

        # Dropdown Menu Setup
        connectMenu = QMenu(self)
        connectMenu.setObjectName("NavDropdownMenu")

        actionVolunteer = QAction("Register as a Volunteer", self)
        actionOrg = QAction("Register an Organization", self)

        actionVolunteer.triggered.connect(self.show_volunteer_page)
        actionOrg.triggered.connect(self.show_org_page)

        connectMenu.addAction(actionVolunteer)
        connectMenu.addAction(actionOrg)

        self.btnThemeToggle = QPushButton("🌙")
        self.btnThemeToggle.setToolTip("Toggle Dark/Light Mode")
        self.btnThemeToggle.clicked.connect(self.toggle_theme)

        navLayout.addWidget(self.nav_logo)
        navLayout.addStretch()
        navLayout.addWidget(btnAbout)
        navLayout.addWidget(btnFeatures)
        navLayout.addWidget(btnDemo)
        navLayout.addWidget(self.btnConnect)
        self.btnConnect.setMenu(connectMenu)
        navLayout.addWidget(btnLogin)
        navLayout.addWidget(self.btnThemeToggle)

        # HERO SECTION
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

        # Bottom Slogan Bar
        bottomBar = QWidget()
        bottomBar.setObjectName("BottomBar")
        bottomLayout = QHBoxLayout(bottomBar)
        bottomLayout.setContentsMargins(20, 30, 20, 30)

        sloganLabel = QLabel(
            "Grow food. Grow community. Grow a better future."
        )
        sloganLabel.setObjectName("SloganText")
        sloganLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bottomLayout.addWidget(sloganLabel)

        # Home Page Container
        self.homePage = QWidget()
        homeLayout = QVBoxLayout(self.homePage)
        homeLayout.setContentsMargins(0, 0, 0, 0)
        homeLayout.setSpacing(0)

        homeLayout.addWidget(heroWidget, stretch=1)
        homeLayout.addWidget(bottomBar, stretch=0)

        # Registration Pages
        self.volunteerPage = VolunteerRegistration(
            on_back_click=self.show_home_page
        )
        self.orgPage = OrganizationRegistration(
            on_back_click=self.show_home_page
        )
        self.volunteerLoginPage = VolunteerLogin(
            on_login_success=self.show_home_page
        )

        # Central View Container (Stack)
        self.pageStack = QStackedWidget()
        self.pageStack.addWidget(self.homePage)
        self.pageStack.addWidget(self.volunteerPage)
        self.pageStack.addWidget(self.orgPage)
        self.pageStack.addWidget(self.volunteerLoginPage)
        mainLayout.addWidget(navWid, 0)
        mainLayout.addWidget(self.pageStack, 1)

        # Initialize stylesheet and logos
        self.apply_theme("lightMode.qss")
        self.update_logos()

    # --- Page Switcher Slots ---
    def show_home_page(self):
        self.pageStack.setCurrentWidget(self.homePage)

    def show_login_volunteer_page(self):
        self.pageStack.setCurrentWidget(self.volunteerLoginPage)

    def show_volunteer_page(self):
        self.pageStack.setCurrentWidget(self.volunteerPage)

    def show_org_page(self):
        self.pageStack.setCurrentWidget(self.orgPage)

    def update_logos(self):
        """Updates logo images based on current mode."""
        # Light mode uses dark logo; Dark mode uses light logo
        logo_filename = "logoFullLight.png" if self.is_dark_mode else "logoFullDark.png"
        
        smooth_transform = Qt.TransformationMode.SmoothTransformation

        # Nav Logo (height 32px)
        nav_pixmap = QPixmap(logo_filename).scaledToHeight(32, smooth_transform)
        self.nav_logo.setPixmap(nav_pixmap)

        # Hero Logo (height 300px)
        hero_pixmap = QPixmap(logo_filename).scaledToHeight(500, smooth_transform)
        self.hero_logo.setPixmap(hero_pixmap)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        qss = "darkMode.qss" if self.is_dark_mode else "lightMode.qss"

        self.apply_theme(qss)
        self.btnThemeToggle.setText("☀️" if self.is_dark_mode else "🌙")
        self.update_logos()

    def apply_theme(self, qss_filename):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(script_dir, qss_filename)

        try:
            with open(qss_path, "r") as f:
                stylesheet = f.read()
                app = QApplication.instance()
                if isinstance(app, QApplication):
                    app.setStyleSheet(stylesheet)
        except FileNotFoundError:
            print(f"Error: Stylesheet not found at '{qss_path}'.")