import os
from PyQt6.QtGui import QPixmap, QIcon, QAction
from PyQt6.QtCore import Qt, QUrl, QRectF
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QMainWindow,
    QGraphicsView, QGraphicsScene, QMenu
)
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem

from volunteerRegister import VolunteerRegistration
from orgRegister import OrganizationRegistration


class Landing(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vibrance")
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

        logo = QLabel()
        logo.setObjectName("NavLogo")
        logoImg = QPixmap("logoFullLight.png").scaledToHeight(32, Qt.TransformationMode.SmoothTransformation)
        logo.setPixmap(logoImg)

        btnAbout = QPushButton("About")
        btnFeatures = QPushButton("Features")
        btnDemo = QPushButton("Demo")
        btnLogin = QPushButton("Login")

        # Home button logic on logo click
        logo.setCursor(Qt.CursorShape.PointingHandCursor)
        logo.mousePressEvent = lambda event: self.show_home_page()

        self.btnConnect = QPushButton("Register ▾ ")
        self.btnConnect.setObjectName("NavDropdown")

        # Dropdown Menu Setup
        connectMenu = QMenu(self)
        connectMenu.setObjectName("NavDropdownMenu")

        actionVolunteer = QAction("Register as a Volunteer", self)
        actionOrg = QAction("Register an Organization", self)

        # Trigger navigation on click
        actionVolunteer.triggered.connect(self.show_volunteer_page)
        actionOrg.triggered.connect(self.show_org_page)

        connectMenu.addAction(actionVolunteer)
        connectMenu.addAction(actionOrg)

        self.btnThemeToggle = QPushButton("🌙")
        self.btnThemeToggle.setToolTip("Toggle Dark/Light Mode")
        self.btnThemeToggle.clicked.connect(self.toggle_theme)

        navLayout.addWidget(logo)
        navLayout.addStretch()
        navLayout.addWidget(btnAbout)
        navLayout.addWidget(btnFeatures)
        navLayout.addWidget(btnDemo)
        navLayout.addWidget(self.btnConnect)
        self.btnConnect.setMenu(connectMenu)
        navLayout.addWidget(btnLogin)
        navLayout.addWidget(self.btnThemeToggle)

        # -------------------------------------------------------------
        # HERO SECTION
        # -------------------------------------------------------------
        overlay_widget = QWidget()
        overlay_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        overlay_widget.setStyleSheet("background: transparent;")

        overlay_layout = QVBoxLayout(overlay_widget)

        overlay_logo = QLabel()
        overlay_pixmap = QPixmap("logoFullLight.png").scaledToHeight(150, Qt.TransformationMode.SmoothTransformation)
        overlay_logo.setPixmap(overlay_pixmap)
        overlay_logo.setStyleSheet("background: transparent;")

        overlay_layout.addStretch()
        overlay_layout.addWidget(overlay_logo, alignment=Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addStretch()

        self.hero_view = QGraphicsView()
        self.hero_view.setStyleSheet("background: transparent; border: none;")
        self.hero_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.hero_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.hero_view.setFrameShape(QGraphicsView.Shape.NoFrame)

        self.hero_scene = QGraphicsScene(self.hero_view)
        self.hero_view.setScene(self.hero_scene)

        self.video_item = QGraphicsVideoItem()
        self.video_item.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)
        self.video_item.setZValue(0)
        self.hero_scene.addItem(self.video_item)

        self.overlay_proxy = self.hero_scene.addWidget(overlay_widget)
        self.overlay_proxy.setZValue(1)

        self._update_hero_geometry()

        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video_item)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        video_path = os.path.join(script_dir, "vidMainBg.mp4")
        self.player.setSource(QUrl.fromLocalFile(video_path))
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.player.play()

        # Bottom Slogan Bar
        bottomBar = QWidget()
        bottomBar.setObjectName("BottomBar")
        bottomLayout = QHBoxLayout(bottomBar)
        bottomLayout.setContentsMargins(20, 30, 20, 30)

        sloganLabel = QLabel("Grow food. Grow community. Grow a better future.")
        sloganLabel.setObjectName("SloganText")
        sloganLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bottomLayout.addWidget(sloganLabel)

        # Home Page Container
        self.homePage = QWidget()
        homeLayout = QVBoxLayout(self.homePage)
        homeLayout.setContentsMargins(0, 0, 0, 0)
        homeLayout.setSpacing(0)

        homeLayout.addWidget(self.hero_view, stretch=1)
        homeLayout.addWidget(bottomBar, stretch=0)

        # Registration Pages
        self.volunteerPage = VolunteerRegistration(on_back_click=self.show_home_page)
        self.orgPage = OrganizationRegistration(on_back_click=self.show_home_page)

        # Central View Container (Stack)
        self.pageStack = QStackedWidget()
        self.pageStack.addWidget(self.homePage)        # Index 0
        self.pageStack.addWidget(self.volunteerPage)   # Index 1
        self.pageStack.addWidget(self.orgPage)         # Index 2

        mainLayout.addWidget(navWid, 0)
        mainLayout.addWidget(self.pageStack, 1)

        self.apply_theme("lightMode.qss")

    # --- Page Switcher Slots ---
    def show_home_page(self):
        self.pageStack.setCurrentWidget(self.homePage)

    def show_volunteer_page(self):
        self.pageStack.setCurrentWidget(self.volunteerPage)

    def show_org_page(self):
        self.pageStack.setCurrentWidget(self.orgPage)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_hero_geometry()

    def _update_hero_geometry(self):
        rect = QRectF(0, 0, self.hero_view.width(), self.hero_view.height())
        self.hero_scene.setSceneRect(rect)
        self.video_item.setSize(rect.size())
        self.overlay_proxy.setPos(0, 0)
        self.overlay_proxy.resize(self.hero_view.width(), self.hero_view.height())

    def toggle_theme(self):
        if self.is_dark_mode:
            self.apply_theme("lightMode.qss")
            self.btnThemeToggle.setText("🌙")
            self.is_dark_mode = False
        else:
            self.apply_theme("darkMode.qss")
            self.btnThemeToggle.setText("☀️")
            self.is_dark_mode = True

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