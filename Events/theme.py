"""
theme.py — Shared object-name constants and asset paths.

Every QSS selector in lightMode.qss / darkMode.qss keys off the objectName
strings defined here. Pages call setObjectName(theme.navBar) rather than
typing "NavBar" inline, so a typo shows up as an import error instead of a
silently unstyled widget.
"""

import os

# Get the current directory (Events)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the root directory (Vibranc)
BASE_DIR = os.path.dirname(CURRENT_DIR) 
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def asset(filename: str) -> str:
    """Absolute path to a file in assets/. Pass just the filename."""
    return os.path.join(ASSETS_DIR, filename)

# ... keep all your object name constants here ...

def apply_theme(app, is_dark: bool) -> bool:
    """
    Load lightMode.qss or darkMode.qss and apply to the QApplication.
    Returns True on success, False if the file is missing.
    """
    filename = "darkMode.qss" if is_dark else "lightMode.qss"
    # The QSS files are in the QSS folder
    path = os.path.join(BASE_DIR, "QSS", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        return True
    except FileNotFoundError:
        print(f"[theme] Stylesheet not found: {path}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Object names — keep in sync with lightMode.qss / darkMode.qss
# ─────────────────────────────────────────────────────────────────────────────

# Navigation / chrome
navBar             = "NavBar"
navLogo            = "NavLogo"
navDropdown        = "NavDropdown"
searchBar          = "SearchBar"
searchInput        = "SearchInput"
searchBtn          = "SearchBtn"
searchCategory     = "SearchCategoryCombo"

# Home / marketing
heroSection        = "HeroSection"
heroLogo           = "HeroLogo"
HOME_SCROLL         = "HomeScrollArea"
HOME_SCROLL_CONTENT = "HomeScrollContent"
SECTION_TITLE       = "SectionTitle"
FEATURES_SECTION    = "FeaturesSection"
FEATURE_CARD        = "FeatureCard"
FEATURE_IMAGE       = "FeatureImage"
FEATURE_TITLE       = "FeatureTitle"
FEATURE_DESC        = "FeatureDesc"
BOTTOM_BAR          = "BottomBar"
SLOGAN_TEXT         = "SloganText"

# Hero mission typography (NEW — used by heroSection.py)
HERO_MISSION_TITLE   = "HeroMissionTitle"
HERO_MISSION_BODY_LG = "HeroMissionBodyLg"
HERO_MISSION_BODY_MD = "HeroMissionBodyMd"
HERO_MISSION_BODY_SM = "HeroMissionBodySm"
HERO_LEARN_BTN       = "HeroLearnBtn"

# Opportunity rows (home page carousels)
OPPORTUNITY_ROW        = "OpportunityRow"
OPPORTUNITY_ROW_TITLE  = "OpportunityRowTitle"
OPPORTUNITY_SCROLL     = "OpportunityScroll"
OPPORTUNITY_SCROLL_CONTENT = "OpportunityScrollContent"
OPPORTUNITY_EMPTY      = "OpportunityEmpty"

# Forms
REGISTER_CARD   = "RegisterCard"
LOGIN_CARD      = "LoginCard"
FORM_TITLE      = "FormTitle"
FORM_SUBTITLE   = "FormSubtitle"
FIELD_LABEL     = "FieldLabel"
PRIMARY_BTN     = "PrimaryBtn"
SECONDARY_BTN   = "SecondaryBtn"
BACK_BTN        = "BackBtn"                # NEW — standardized back button
CAPTCHA_IMAGE   = "CaptchaImage"
CAPTCHA_REFRESH = "CaptchaRefreshBtn"
OTP_INPUT       = "OtpInput"
REGISTER_SCROLL = "RegisterScroll"
REGISTER_SCROLL_CONTENT = "RegisterScrollContent"

# Event cards
EVENT_CARD           = "EventCard"
EVENT_SOURCE_MOXIE = "EventSourceMoxie"
EVENT_SOURCE_EXTERNAL = "EventSourceExternal"
EVENT_DETAILS_BTN = "EventDetailsBtn"
EVENT_THUMB          = "EventThumb"
EVENT_TITLE          = "EventTitle"
EVENT_TITLE_LIST     = "EventTitleList"
EVENT_DESCRIPTION    = "EventDescription"
EVENT_ORG            = "EventOrg"
EVENT_META_KEY       = "EventMetaKey"
EVENT_META_VALUE     = "EventMetaValue"
EVENT_CATEGORY_BADGE = "EventCategoryBadge"
EVENT_LOCATION_BADGE = "EventLocationBadge"
EVENT_STATUS_BADGE   = "EventStatusBadge"
EVENT_RSVP_BTN       = "EventRsvpBtn"
EVENT_LINK_BTN       = "EventLinkBtn"

# Event details dialog
EVENT_DETAILS_DIALOG = "EventDetailsDialog"
DETAILS_SCROLL       = "DetailsScroll"
DETAILS_SCROLL_CONTENT = "DetailsScrollContent"
DETAILS_DESCRIPTION  = "DetailsDescription"
DETAILS_CLOSE_BTN    = "DetailsCloseBtn"

# Filter bar
FILTER_BAR              = "FilterBar"
FILTER_searchInput     = "FilterSearchInput"
FILTER_LOCATION_INPUT   = "FilterLocationInput"
FILTER_COMBO            = "FilterCombo"
FILTER_DATE             = "FilterDate"
FILTER_LABEL            = "FilterLabel"
FILTER_MORE_BTN         = "FilterMoreBtn"
FILTER_MORE_ROW         = "FilterMoreRow"
FILTER_CLEAR_BTN        = "FilterClearBtn"

# Volunteer listing page
VOLUNTEER_DASHBOARD    = "VolunteerDashboard"
VOLUNTEER_PAGE          = "VolunteerPage"
VOLUNTEER_HEADER        = "VolunteerHeader"
VOLUNTEER_TITLE         = "VolunteerTitle"
VOLUNTEER_BACK_BTN      = "VolunteerBackBtn"
VOLUNTEER_SCROLL        = "VolunteerScroll"
VOLUNTEER_GRID_CONTAINER = "VolunteerGridContainer"
VOLUNTEER_LIST_CONTAINER = "VolunteerListContainer"
VOLUNTEER_CONTENT_STACK = "VolunteerContentStack"
VOLUNTEER_EMPTY_WRAP    = "VolunteerEmptyWrap"
VOLUNTEER_EMPTY         = "VolunteerEmpty"
VOLUNTEER_EMPTY_BTN     = "VolunteerEmptyBtn"
VOLUNTEER_RESULTS_COUNT = "VolunteerResultsCount"
VIEW_TOGGLE_BTN         = "ViewToggleBtn"

# Org dashboard
ORG_DASHBOARD   = "OrgDashboard"
ORG_OPP_LIST    = "OrgOppList"

# FAQ
FAQ_PAGE          = "FAQPage"
faqItem          = "FAQItem"
FAQ_CATEGORY      = "FAQCategoryHeading"    # NEW — FAQ category headings
FAQ_HEADER        = "FAQHeader"
FAQ_QUESTION      = "FAQQuestion"
FAQ_ANSWER        = "FAQAnswer"
FAQ_TOGGLE_BTN    = "FAQToggleBtn"
FAQ_TITLE         = "FAQTitle"
FAQ_searchInput  = "FAQSearchInput"
FAQ_SCROLL_AREA   = "FAQScrollArea"
FAQ_SCROLL_CONTENT = "FAQScrollContent"
FAQ_NO_RESULTS    = "FAQNoResults"


# ─────────────────────────────────────────────────────────────────────────────
# Theme helpers
# ─────────────────────────────────────────────────────────────────────────────