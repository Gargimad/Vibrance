"""
db.py — Unified database layer for Moxie.

Schema:
  users               userID, email UNIQUE, password, role, email_verified,
                      mfa_enabled, created_at
  volunteer_profiles  userID PK -> users, first_name, last_name, country,
                      zipcode, dob, gender, skills, phone
  organizations       orgID PK, userID (nullable for external imports),
                      org_name, description, website_link, city, country,
                      source_id (external key, e.g. Volunteer Connector URL)
  org_members         memberID PK, userID -> users, orgID -> organizations
  opportunities       opportunityID PK, orgID -> organizations, ...
  event_signups       signupID PK, userID -> users, opportunityID -> ...
  notifications       notificationID PK, userID -> users, ...
"""

import os
import sqlite3
import hashlib
from datetime import datetime

try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Volunteer.db")


# ─────────────────────────────────────────────────────────────────────────────
# Password hashing (bcrypt if available, PBKDF2-SHA256 fallback)
# ─────────────────────────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    if _HAS_BCRYPT:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, 200_000)
    return f"pbkdf2${salt.hex()}${dk.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("$2") and _HAS_BCRYPT:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
        except ValueError:
            return False
    if stored.startswith("pbkdf2$"):
        try:
            _, salt_hex, dk_hex = stored.split("$")
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(dk_hex)
            dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, 200_000)
            return dk == expected
        except (ValueError, AttributeError):
            return False
    return plain == stored


# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────
class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute("PRAGMA journal_mode = WAL")
        self.createTable()

    # ── Schema ────────────────────────────────────────────────────────────
    def createTable(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            userID        INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT UNIQUE NOT NULL,
            password      TEXT NOT NULL,
            role          TEXT NOT NULL CHECK(role IN ('volunteer', 'org')),
            email_verified INTEGER DEFAULT 0,
            mfa_enabled   INTEGER DEFAULT 1,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS volunteer_profiles (
            userID     INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name  TEXT,
            country    TEXT,
            zipcode    TEXT,
            dob        TEXT,
            gender     TEXT,
            skills     TEXT,
            phone      TEXT,
            FOREIGN KEY(userID) REFERENCES users(userID) ON DELETE CASCADE
        );
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            orgID        INTEGER PRIMARY KEY AUTOINCREMENT,
            userID       INTEGER,
            org_name     TEXT NOT NULL,
            description  TEXT,
            website_link TEXT,
            city         TEXT,
            country      TEXT,
            source_id    TEXT,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(userID) REFERENCES users(userID) ON DELETE CASCADE
        );
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_members (
            memberID    INTEGER PRIMARY KEY AUTOINCREMENT,
            userID      INTEGER NOT NULL,
            orgID       INTEGER NOT NULL,
            member_role TEXT DEFAULT 'member',
            UNIQUE(userID, orgID),
            FOREIGN KEY(userID) REFERENCES users(userID) ON DELETE CASCADE,
            FOREIGN KEY(orgID) REFERENCES organizations(orgID) ON DELETE CASCADE
        );
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            opportunityID   INTEGER PRIMARY KEY AUTOINCREMENT,
            orgID           INTEGER,
            title           TEXT NOT NULL,
            description     TEXT,
            category        TEXT,
            location        TEXT,
            address         TEXT,
            is_remote       INTEGER DEFAULT 0,
            event_date      TEXT,
            start_time      TEXT,
            end_time        TEXT,
            capacity        INTEGER,
            status          TEXT DEFAULT 'open',
            required_skills TEXT,
            contact_name    TEXT,
            contact_email   TEXT,
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at      TEXT DEFAULT CURRENT_TIMESTAMP,
            thumbnail       TEXT,
            website_link    TEXT,
            source_id       TEXT,
            FOREIGN KEY(orgID) REFERENCES organizations(orgID) ON DELETE CASCADE
        );
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_signups (
            signupID      INTEGER PRIMARY KEY AUTOINCREMENT,
            userID        INTEGER NOT NULL,
            opportunityID INTEGER NOT NULL,
            status        TEXT DEFAULT 'registered',
            signup_time   TEXT DEFAULT CURRENT_TIMESTAMP,
            check_in_time TEXT,
            check_out_time TEXT,
            hours_logged  REAL,
            UNIQUE(userID, opportunityID),
            FOREIGN KEY(userID) REFERENCES users(userID) ON DELETE CASCADE,
            FOREIGN KEY(opportunityID) REFERENCES opportunities(opportunityID) ON DELETE CASCADE
        );
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            notificationID        INTEGER PRIMARY KEY AUTOINCREMENT,
            userID                INTEGER NOT NULL,
            message               TEXT NOT NULL,
            type                  TEXT,
            related_opportunityID INTEGER,
            created_at            TEXT DEFAULT CURRENT_TIMESTAMP,
            read_at               TEXT,
            FOREIGN KEY(userID) REFERENCES users(userID) ON DELETE CASCADE
        );
        """)

        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_opp_org ON opportunities(orgID)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_signup_user ON event_signups(userID)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_signup_opp ON event_signups(opportunityID)"
        )
        self.cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_org_source "
            "ON organizations(source_id) WHERE source_id IS NOT NULL"
        )
        self.connection.commit()

    # ── Users / auth ──────────────────────────────────────────────────────
    def register_user(self, email, password, role, **profile):
        if role not in ("volunteer", "org"):
            return None
        try:
            self.cursor.execute(
                "INSERT INTO users (email, password, role, email_verified) "
                "VALUES (?, ?, ?, 1)",
                (email.strip().lower(), hash_password(password), role),
            )
            userID = self.cursor.lastrowid

            if role == "volunteer":
                self.cursor.execute("""
                    INSERT INTO volunteer_profiles
                    (userID, first_name, last_name, country, zipcode,
                     dob, gender, skills, phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    userID,
                    profile.get("first_name", ""),
                    profile.get("last_name", ""),
                    profile.get("country", ""),
                    profile.get("zipcode", ""),
                    profile.get("dob", ""),
                    profile.get("gender", ""),
                    profile.get("skills", ""),
                    profile.get("phone", ""),
                ))
            else:
                self.cursor.execute("""
                    INSERT INTO organizations
                    (userID, org_name, description, website_link, city, country)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    userID,
                    profile.get("org_name", ""),
                    profile.get("description", ""),
                    profile.get("website_link", ""),
                    profile.get("city", ""),
                    profile.get("country", ""),
                ))
            self.connection.commit()
            return userID
        except sqlite3.IntegrityError:
            self.connection.rollback()
            return None

    def email_exists(self, email):
        self.cursor.execute(
            "SELECT 1 FROM users WHERE email = ?", (email.strip().lower(),)
        )
        return self.cursor.fetchone() is not None

    def authenticate(self, email, password):
        self.cursor.execute(
            "SELECT userID, email, password, role, email_verified, mfa_enabled "
            "FROM users WHERE email = ?",
            (email.strip().lower(),),
        )
        row = self.cursor.fetchone()
        if not row or not verify_password(password, row["password"]):
            return None
        return self.get_user_profile(row["userID"])

    def get_user_profile(self, userID):
        self.cursor.execute(
            "SELECT userID, email, role, email_verified, mfa_enabled, created_at "
            "FROM users WHERE userID = ?", (userID,),
        )
        user = self.cursor.fetchone()
        if not user:
            return None
        result = dict(user)

        if user["role"] == "volunteer":
            self.cursor.execute(
                "SELECT first_name, last_name, country, zipcode, "
                "dob, gender, skills, phone "
                "FROM volunteer_profiles WHERE userID = ?", (userID,),
            )
            prof = self.cursor.fetchone()
            if prof:
                result.update(dict(prof))
        elif user["role"] == "org":
            self.cursor.execute(
                "SELECT orgID, org_name, description, website_link, "
                "city, country FROM organizations WHERE userID = ?",
                (userID,),
            )
            org = self.cursor.fetchone()
            if org:
                result.update(dict(org))

        return result

    def getUserProfile(self, userID):
        """Alias for get_user_profile. Used by volunteerHome._db()."""
        return self.get_user_profile(userID)

    def updateUserProfile(self, userID, fields):
        """Update a volunteer profile from a dict. Returns bool."""
        return self.update_volunteer_profile(userID, **fields)

    def changePassword(self, userID, old, new):
        self.cursor.execute(
            "SELECT password FROM users WHERE userID = ?", (userID,),
        )
        row = self.cursor.fetchone()
        if not row or not verify_password(old, row["password"]):
            return False
        self.cursor.execute(
            "UPDATE users SET password = ? WHERE userID = ?",
            (hash_password(new), userID),
        )
        self.connection.commit()
        return True

    def set_mfa_enabled(self, userID, enabled: bool):
        self.cursor.execute(
            "UPDATE users SET mfa_enabled = ? WHERE userID = ?",
            (1 if enabled else 0, userID),
        )
        self.connection.commit()

    def update_volunteer_profile(self, userID, **fields):
        allowed = {"first_name", "last_name", "country", "zipcode",
                   "dob", "gender", "skills", "phone"}
        sets, params = [], []
        for k, v in fields.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                params.append(v)
        if not sets:
            return False
        params.append(userID)
        self.cursor.execute(
            f"UPDATE volunteer_profiles SET {', '.join(sets)} WHERE userID = ?",
            params,
        )
        self.connection.commit()
        return True

    # ── Organizations helpers ─────────────────────────────────────────────
    def get_or_create_organization(self, org_name, source_id=None,
                                   description=None, website_link=None,
                                   city=None, country=None):
        """
        Look up an organization by external source_id (preferred) or by
        name (fallback). Create it if it doesn't exist. Returns orgID or None.

        Matching rules:
          1. If source_id is provided and a row with that source_id exists,
             reuse it.
          2. Else if org_name matches an existing row with source_id IS NULL
             (a Moxie-native org or a legacy row), reuse it.
          3. Else create a new row.
        """
        if source_id:
            self.cursor.execute(
                "SELECT orgID FROM organizations WHERE source_id = ?",
                (source_id,),
            )
            row = self.cursor.fetchone()
            if row:
                return row["orgID"]

        if org_name:
            self.cursor.execute(
                "SELECT orgID FROM organizations "
                "WHERE org_name = ? AND source_id IS NULL",
                (org_name,),
            )
            row = self.cursor.fetchone()
            if row:
                return row["orgID"]

        if not org_name and not source_id:
            return None

        try:
            self.cursor.execute(
                "INSERT INTO organizations "
                "(userID, org_name, source_id, description, website_link, "
                " city, country) "
                "VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                (org_name or "Unknown organization", source_id,
                 description, website_link, city, country),
            )
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print("get_or_create_organization error:", e)
            return None

    def get_or_create_external_org(self, org_name: str) -> int:
        """Kept for backward compatibility. Now a thin alias."""
        return self.get_or_create_organization(
            org_name, description="Imported via Volunteer Connector API"
        )

    def getOrganizations(self, userID):
        """
        Every organization with an is_member flag for the given user.
        Joined orgs first, then alphabetical.
        """
        self.cursor.execute("""
            SELECT o.orgID AS organizationID, o.org_name AS name,
                   o.description, o.website_link, o.city, o.country,
                   o.source_id,
                   CASE WHEN m.memberID IS NULL THEN 0 ELSE 1 END AS is_member
            FROM organizations o
            LEFT JOIN org_members m
              ON m.orgID = o.orgID AND m.userID = ?
            ORDER BY is_member DESC, o.org_name ASC
        """, (userID,))
        return self.cursor.fetchall()

    def joinOrganization(self, userID, orgID):
        try:
            self.cursor.execute(
                "INSERT INTO org_members (userID, orgID) VALUES (?, ?)",
                (userID, orgID),
            )
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return True
        except sqlite3.Error as e:
            print("joinOrganization error:", e)
            return False

    def leaveOrganization(self, userID, orgID):
        self.cursor.execute(
            "DELETE FROM org_members WHERE userID = ? AND orgID = ?",
            (userID, orgID),
        )
        self.connection.commit()
        return self.cursor.rowcount > 0

    # ── Opportunities ─────────────────────────────────────────────────────
    def _opportunity_base_query(self):
        return """
        SELECT o.opportunityID, o.title, o.description, o.category,
               o.location, o.address, o.is_remote, o.event_date,
               o.start_time, o.end_time, o.capacity, o.status,
               o.required_skills, o.contact_name, o.contact_email,
               o.created_at, o.updated_at, o.thumbnail, o.source_id,
               COALESCE(o.website_link, org.website_link) AS website_link,
               org.org_name, org.orgID,
               (SELECT COUNT(*) FROM event_signups s
                WHERE s.opportunityID = o.opportunityID
                  AND s.status = 'registered') AS registered_count
        FROM opportunities o
        LEFT JOIN organizations org ON o.orgID = org.orgID
        """

    def getAllOpportunitiesWithLinks(self, limit=500):
        self.cursor.execute(
            self._opportunity_base_query() +
            " ORDER BY o.event_date ASC LIMIT ?", (limit,),
        )
        return self.cursor.fetchall()

    def getAllOpportunities(self):
        self.cursor.execute(
            self._opportunity_base_query() +
            " WHERE COALESCE(o.status, 'open') != 'cancelled'"
        )
        return self.cursor.fetchall()

    def getSoonestOpportunities(self, limit=10):
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute(
            self._opportunity_base_query() + """
            WHERE o.event_date IS NOT NULL AND o.event_date >= ?
              AND COALESCE(o.status, 'open') != 'cancelled'
            ORDER BY o.event_date ASC LIMIT ?
            """, (today, limit),
        )
        return self.cursor.fetchall()

    def getNewestOpportunities(self, limit=10):
        self.cursor.execute(
            self._opportunity_base_query() + """
            WHERE COALESCE(o.status, 'open') != 'cancelled'
            ORDER BY o.created_at DESC LIMIT ?
            """, (limit,),
        )
        return self.cursor.fetchall()

    def getRemoteOpportunities(self, limit=10):
        self.cursor.execute(
            self._opportunity_base_query() + """
            WHERE o.is_remote = 1
              AND COALESCE(o.status, 'open') != 'cancelled'
            ORDER BY o.event_date ASC LIMIT ?
            """, (limit,),
        )
        return self.cursor.fetchall()

    def getOpportunitiesByOrg(self, orgID):
        self.cursor.execute(
            self._opportunity_base_query() +
            " WHERE o.orgID = ? ORDER BY o.event_date ASC", (orgID,),
        )
        return self.cursor.fetchall()

    def getOpportunityByID(self, opportunityID):
        self.cursor.execute(
            self._opportunity_base_query() + " WHERE o.opportunityID = ?",
            (opportunityID,),
        )
        return self.cursor.fetchone()

    def getDistinctCategories(self):
        self.cursor.execute("""
            SELECT DISTINCT category FROM opportunities
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category ASC
        """)
        return [r["category"] for r in self.cursor.fetchall()]

    def searchOpportunitiesFiltered(self, keyword="", type_filter="All",
                                    location="", category="All Causes",
                                    date_from=None, date_to=None,
                                    upcoming_only=True, limit=1000):
        conditions, params = [], []

        if keyword:
            like = f"%{keyword}%"
            conditions.append(
                "(o.title LIKE ? OR o.description LIKE ? OR o.location LIKE ? "
                " OR org.org_name LIKE ? OR o.category LIKE ?)"
            )
            params.extend([like] * 5)

        if type_filter == "Remote":
            conditions.append("o.is_remote = 1")
        elif type_filter == "In-person":
            conditions.append("o.is_remote = 0")

        if location:
            like = f"%{location}%"
            conditions.append("(o.location LIKE ? OR o.address LIKE ?)")
            params.extend([like, like])

        if category and category != "All Causes":
            conditions.append("o.category = ?")
            params.append(category)

        if date_from:
            conditions.append("o.event_date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("o.event_date <= ?")
            params.append(date_to)

        if upcoming_only:
            today = datetime.now().strftime("%Y-%m-%d")
            conditions.append("(o.event_date IS NULL OR o.event_date >= ?)")
            params.append(today)

        conditions.append("COALESCE(o.status, 'open') != 'cancelled'")

        q = self._opportunity_base_query()
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " ORDER BY o.event_date ASC LIMIT ?"
        params.append(limit)

        self.cursor.execute(q, params)
        return self.cursor.fetchall()

    def searchOpportunities(self, keyword, category="All", limit=25):
        return self.searchOpportunitiesFiltered(
            keyword=keyword, type_filter=category, limit=limit
        )

    def addOpportunity(self, orgID, title, description, category, location,
                       is_remote, event_date, thumbnail=None,
                       start_time=None, end_time=None, capacity=None,
                       status="open", required_skills=None,
                       contact_name=None, contact_email=None, address=None,
                       website_link=None):
        try:
            self.cursor.execute("""
                INSERT INTO opportunities
                (orgID, title, description, category, location, address,
                 is_remote, event_date, start_time, end_time, capacity,
                 status, required_skills, contact_name, contact_email,
                 thumbnail, website_link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                orgID, title, description, category, location, address,
                1 if is_remote else 0, event_date, start_time, end_time,
                capacity, status, required_skills, contact_name,
                contact_email, thumbnail, website_link,
            ))
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print("addOpportunity error:", e)
            return None

    def updateOpportunity(self, opportunityID, **fields):
        allowed = {"title", "description", "category", "location", "address",
                   "is_remote", "event_date", "start_time", "end_time",
                   "capacity", "status", "required_skills", "contact_name",
                   "contact_email", "thumbnail", "website_link"}
        sets, params = [], []
        for k, v in fields.items():
            if k not in allowed:
                continue
            if k == "is_remote":
                v = 1 if v else 0
            sets.append(f"{k} = ?")
            params.append(v)
        if not sets:
            return False
        sets.append("updated_at = CURRENT_TIMESTAMP")
        params.append(opportunityID)
        try:
            self.cursor.execute(
                f"UPDATE opportunities SET {', '.join(sets)} "
                f"WHERE opportunityID = ?", params,
            )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print("updateOpportunity error:", e)
            return False

    # ── Signups ───────────────────────────────────────────────────────────
    def registerForOpportunity(self, userID, opportunityID):
        try:
            self.cursor.execute(
                "SELECT capacity, COALESCE(status, 'open') AS status "
                "FROM opportunities WHERE opportunityID = ?", (opportunityID,),
            )
            row = self.cursor.fetchone()
            if not row:
                return "error"
            if row["status"] != "open":
                return "full"

            if row["capacity"] is not None:
                self.cursor.execute(
                    "SELECT COUNT(*) AS c FROM event_signups "
                    "WHERE opportunityID = ? AND status = 'registered'",
                    (opportunityID,),
                )
                if self.cursor.fetchone()["c"] >= row["capacity"]:
                    return "full"

            self.cursor.execute("""
                INSERT INTO event_signups (userID, opportunityID, status)
                VALUES (?, ?, 'registered')
            """, (userID, opportunityID))
            self.connection.commit()
            return "ok"
        except sqlite3.IntegrityError:
            return "duplicate"
        except sqlite3.Error as e:
            print("registerForOpportunity error:", e)
            return "error"

    def cancelSignup(self, userID, opportunityID):
        self.cursor.execute("""
            UPDATE event_signups SET status = 'cancelled'
            WHERE userID = ? AND opportunityID = ?
        """, (userID, opportunityID))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def checkIn(self, userID, opportunityID):
        now = datetime.now().isoformat(timespec="seconds")
        self.cursor.execute("""
            UPDATE event_signups SET check_in_time = ?
            WHERE userID = ? AND opportunityID = ? AND check_in_time IS NULL
        """, (now, userID, opportunityID))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def checkOut(self, userID, opportunityID):
        now = datetime.now().isoformat(timespec="seconds")
        self.cursor.execute("""
            UPDATE event_signups
            SET check_out_time = ?,
                hours_logged = ROUND(
                    (julianday(?) - julianday(check_in_time)) * 24.0, 2)
            WHERE userID = ? AND opportunityID = ?
              AND check_in_time IS NOT NULL AND check_out_time IS NULL
        """, (now, now, userID, opportunityID))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def getSignupsForVolunteer(self, userID):
        self.cursor.execute("""
            SELECT s.*, o.title, o.event_date, o.start_time, o.end_time,
                   o.location, o.is_remote, o.category,
                   o.required_skills, org.org_name
            FROM event_signups s
            JOIN opportunities o ON s.opportunityID = o.opportunityID
            LEFT JOIN organizations org ON o.orgID = org.orgID
            WHERE s.userID = ?
            ORDER BY o.event_date DESC
        """, (userID,))
        return self.cursor.fetchall()

    def getSignup(self, userID, opportunityID):
        self.cursor.execute("""
            SELECT * FROM event_signups
            WHERE userID = ? AND opportunityID = ?
        """, (userID, opportunityID))
        return self.cursor.fetchone()

    def getSignupsForOpportunity(self, opportunityID):
        self.cursor.execute("""
            SELECT s.*, u.email, vp.first_name, vp.last_name
            FROM event_signups s
            JOIN users u ON s.userID = u.userID
            LEFT JOIN volunteer_profiles vp ON u.userID = vp.userID
            WHERE s.opportunityID = ?
            ORDER BY s.signup_time ASC
        """, (opportunityID,))
        return self.cursor.fetchall()

    # ── Notifications ─────────────────────────────────────────────────────
    def addNotification(self, userID, message, type_=None,
                        related_opportunityID=None):
        self.cursor.execute("""
            INSERT INTO notifications
            (userID, message, type, related_opportunityID)
            VALUES (?, ?, ?, ?)
        """, (userID, message, type_, related_opportunityID))
        self.connection.commit()

    def getNotifications(self, userID, limit=50):
        self.cursor.execute("""
            SELECT * FROM notifications WHERE userID = ?
            ORDER BY created_at DESC LIMIT ?
        """, (userID, limit))
        return self.cursor.fetchall()

    def markNotificationRead(self, notificationID):
        self.cursor.execute("""
            UPDATE notifications SET read_at = CURRENT_TIMESTAMP
            WHERE notificationID = ?
        """, (notificationID,))
        self.connection.commit()

    # ── Shutdown ──────────────────────────────────────────────────────────
    def close(self):
        try:
            self.cursor.close()
        finally:
            self.connection.close()