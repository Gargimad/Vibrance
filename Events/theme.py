"""theme.py — Shared object-name constants and asset paths."""
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def asset(filename: str) -> str:
    """Absolute path to a file in assets/. Pass just the filename."""
    return os.path.join(ASSETS_DIR, filename)


def apply_theme(app, is_dark: bool) -> bool:
    filename = "darkMode.qss" if is_dark else "lightMode.qss"
    path = os.path.join(BASE_DIR, "QSS", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        return True
    except FileNotFoundError:
        print(f"[theme] Stylesheet not found: {path}")
        return False


# ── Navigation / chrome ───────────────────────────────────────────────
navBar = "NavBar"
navLogo = "NavLogo"
navDropdown = "NavDropdown"
searchBar = "SearchBar"
searchInput = "SearchInput"
searchBtn = "SearchBtn"
searchCategory = "SearchCategoryCombo"

# ── Home / marketing ──────────────────────────────────────────────────
heroSection = "HeroSection"
heroLogo = "HeroLogo"
HOME_SCROLL = "HomeScrollArea"
HOME_SCROLL_CONTENT = "HomeScrollContent"
SECTION_TITLE = "SectionTitle"
FEATURES_SECTION = "FeaturesSection"
FEATURE_CARD = "FeatureCard"
FEATURE_IMAGE = "FeatureImage"
FEATURE_TITLE = "FeatureTitle"
FEATURE_DESC = "FeatureDesc"
BOTTOM_BAR = "BottomBar"
SLOGAN_TEXT = "SloganText"

HERO_MISSION_TITLE = "HeroMissionTitle"
HERO_MISSION_BODY_LG = "HeroMissionBodyLg"
HERO_MISSION_BODY_MD = "HeroMissionBodyMd"
HERO_MISSION_BODY_SM = "HeroMissionBodySm"
HERO_LEARN_BTN = "HeroLearnBtn"
# Hero — editorial split-panel (new layout)
HERO_LEFT_PANEL = "HeroLeftPanel"
HERO_RIGHT_PANEL = "HeroRightPanel"
HERO_BOTTOM_BAR = "HeroBottomBar"
HERO_WORDMARK = "HeroWordmark"
HERO_HEADLINE = "HeroHeadline"
HERO_SUB = "HeroSub"
HERO_PHOTO = "HeroPhoto"

OPPORTUNITY_ROW = "OpportunityRow"
OPPORTUNITY_ROW_TITLE = "OpportunityRowTitle"
OPPORTUNITY_SCROLL = "OpportunityScroll"
OPPORTUNITY_SCROLL_CONTENT = "OpportunityScrollContent"
OPPORTUNITY_EMPTY = "OpportunityEmpty"

# ── Forms ─────────────────────────────────────────────────────────────
REGISTER_CARD = "RegisterCard"
LOGIN_CARD = "LoginCard"
FORM_TITLE = "FormTitle"
FORM_SUBTITLE = "FormSubtitle"
FIELD_LABEL = "FieldLabel"
PRIMARY_BTN = "PrimaryBtn"
SECONDARY_BTN = "SecondaryBtn"
BACK_BTN = "BackBtn"
CAPTCHA_IMAGE = "CaptchaImage"
CAPTCHA_REFRESH = "CaptchaRefreshBtn"
OTP_INPUT = "OtpInput"
REGISTER_SCROLL = "RegisterScroll"
REGISTER_SCROLL_CONTENT = "RegisterScrollContent"

# ── Event cards ───────────────────────────────────────────────────────
EVENT_CARD = "EventCard"
EVENT_SOURCE_MOXIE = "EventSourceMoxie"
EVENT_SOURCE_EXTERNAL = "EventSourceExternal"
EVENT_DETAILS_BTN = "EventDetailsBtn"
EVENT_THUMB = "EventThumb"
EVENT_TITLE = "EventTitle"
EVENT_TITLE_LIST = "EventTitleList"
EVENT_DESCRIPTION = "EventDescription"
EVENT_ORG = "EventOrg"
EVENT_META_KEY = "EventMetaKey"
EVENT_META_VALUE = "EventMetaValue"
EVENT_CATEGORY_BADGE = "EventCategoryBadge"
EVENT_LOCATION_BADGE = "EventLocationBadge"
EVENT_STATUS_BADGE = "EventStatusBadge"
EVENT_RSVP_BTN = "EventRsvpBtn"
EVENT_LINK_BTN = "EventLinkBtn"

# ── Bookmarks ─────────────────────────────────────────────────────────
EVENT_BOOKMARK_BTN = "EventBookmarkBtn"
EVENT_BOOKMARK_BTN_ON = "EventBookmarkBtnOn"
BOOKMARK_TAB_EMPTY = "BookmarkTabEmpty"

# ── Volunteer Match ───────────────────────────────────────────────────
MATCH_PAGE = "MatchPage"
MATCH_CARD = "MatchCard"
MATCH_STEP_TITLE = "MatchStepTitle"
MATCH_CHIP = "MatchChip"
MATCH_CHIP_CHECKED = "MatchChipChecked"

# ── Career cluster selector ───────────────────────────────────────────
CLUSTER_MULTI = "ClusterMultiSelect"
CLUSTER_CHIP = "ClusterChip"
CLUSTER_CHIP_CHECKED = "ClusterChipChecked"

# ── QR / time-gated event view ────────────────────────────────────────
EVENT_QR_DIALOG = "EventQrDialog"
EVENT_QR_IMAGE = "EventQrImage"
EVENT_QR_STATUS = "EventQrStatus"
EVENT_QR_WINDOW = "EventQrWindow"

# ── Export ────────────────────────────────────────────────────────────
EXPORT_DIALOG = "ExportDialog"
EXPORT_SECTION = "ExportSection"
EXPORT_FORMAT_ROW = "ExportFormatRow"

# ── Nav groups ────────────────────────────────────────────────────────
NAV_GROUP_BTN = "NavGroupBtn"
NAV_GROUP_MENU = "NavGroupMenu"

# ── Filters (Georgia) ─────────────────────────────────────────────────
FILTER_CITY = "FilterCityCombo"
FILTER_SCHOOL = "FilterSchoolCombo"
FILTER_CLUSTER = "FilterClusterCombo"

# ── Event details dialog ──────────────────────────────────────────────
EVENT_DETAILS_DIALOG = "EventDetailsDialog"
DETAILS_SCROLL = "DetailsScroll"
DETAILS_SCROLL_CONTENT = "DetailsScrollContent"
DETAILS_DESCRIPTION = "DetailsDescription"
DETAILS_CLOSE_BTN = "DetailsCloseBtn"

# ── Filter bar ────────────────────────────────────────────────────────
FILTER_BAR = "FilterBar"
FILTER_searchInput = "FilterSearchInput"
FILTER_LOCATION_INPUT = "FilterLocationInput"
FILTER_COMBO = "FilterCombo"
FILTER_DATE = "FilterDate"
FILTER_LABEL = "FilterLabel"
FILTER_MORE_BTN = "FilterMoreBtn"
FILTER_MORE_ROW = "FilterMoreRow"
FILTER_CLEAR_BTN = "FilterClearBtn"
# Sidebar filter
FILTER_SIDEBAR = "FilterSidebar"
FILTER_SIDEBAR_SCROLL = "FilterSidebarScroll"
FILTER_SIDEBAR_CONTENT = "FilterSidebarContent"
FILTER_SIDEBAR_HEADING = "FilterSidebarHeading"
FILTER_SIDEBAR_INPUT = "FilterSidebarInput"
FILTER_SIDEBAR_RADIO = "FilterSidebarRadio"
FILTER_SIDEBAR_CHECK = "FilterSidebarCheck"
FILTER_SIDEBAR_CLEAR = "FilterSidebarClear"

# Card additions
EVENT_CARD_BODY = "EventCardBody"
EVENT_CARD_META_ICON = "EventCardMetaIcon"
EVENT_CARD_ACTIONS = "EventCardActions"
EVENT_CLUSTER_CHIP = "EventClusterChip"
EVENT_MAIN_AREA = "EventMainArea"

# ── Volunteer listing page ────────────────────────────────────────────
VOLUNTEER_DASHBOARD = "VolunteerDashboard"
VOLUNTEER_PAGE = "VolunteerPage"
VOLUNTEER_HEADER = "VolunteerHeader"
VOLUNTEER_TITLE = "VolunteerTitle"
VOLUNTEER_BACK_BTN = "VolunteerBackBtn"
VOLUNTEER_SCROLL = "VolunteerScroll"
VOLUNTEER_GRID_CONTAINER = "VolunteerGridContainer"
VOLUNTEER_LIST_CONTAINER = "VolunteerListContainer"
VOLUNTEER_CONTENT_STACK = "VolunteerContentStack"
VOLUNTEER_EMPTY_WRAP = "VolunteerEmptyWrap"
VOLUNTEER_EMPTY = "VolunteerEmpty"
VOLUNTEER_EMPTY_BTN = "VolunteerEmptyBtn"
VOLUNTEER_RESULTS_COUNT = "VolunteerResultsCount"
VIEW_TOGGLE_BTN = "ViewToggleBtn"

# ── Org dashboard ─────────────────────────────────────────────────────
ORG_DASHBOARD = "OrgDashboard"
ORG_OPP_LIST = "OrgOppList"

# ── FAQ ───────────────────────────────────────────────────────────────
FAQ_PAGE = "FAQPage"
faqItem = "FAQItem"
FAQ_CATEGORY = "FAQCategoryHeading"
FAQ_HEADER = "FAQHeader"
FAQ_QUESTION = "FAQQuestion"
FAQ_ANSWER = "FAQAnswer"
FAQ_TOGGLE_BTN = "FAQToggleBtn"
FAQ_TITLE = "FAQTitle"
FAQ_searchInput = "FAQSearchInput"
FAQ_SCROLL_AREA = "FAQScrollArea"
FAQ_SCROLL_CONTENT = "FAQScrollContent"
FAQ_NO_RESULTS = "FAQNoResults"
FAQ_SUBTITLE = "FAQSubtitle"
FAQ_CAT_PILL = "FAQCatPill"