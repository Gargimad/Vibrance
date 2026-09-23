import sqlite3
import os
from datetime import datetime

try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False
    import hashlib


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Volunteer.db")


def hash_password(plain: str) -> str:
    """Hash a password. Uses bcrypt if available, else a salted PBKDF2 fallback."""
    if _HAS_BCRYPT:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, 200_000)
    return f"pbkdf2${salt.hex()}${dk.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("$2"):  # bcrypt
        if not _HAS_BCRYPT:
            return False
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
        except ValueError:
            return False
    if stored.startswith("pbkdf2$"):
        _, salt_hex, dk_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(dk_hex)
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, 200_000)
        return dk == expected
    # Legacy plaintext — compare directly (migration path only)
    return plain == stored


class Database:
    def __init__(self, db_path: str = DB_PATH):
        # check_same_thread=False is needed once Streamlit touches the DB.
        # WAL keeps PyQt and Streamlit from fighting over a single write lock.
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute("PRAGMA journal_mode = WAL")
        self.createTable()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def createTable(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS volunteers (
                volunteerID   INTEGER PRIMARY KEY AUTOINCREMENT,
                gender        TEXT,
                first_name    TEXT,
                last_name     TEXT,
                email         TEXT UNIQUE,
                password      TEXT,
                country       TEXT,
                zipcode       TEXT,
                dob           TEXT,
                skills        TEXT,
                mfa_enabled   INTEGER DEFAULT 1
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                orgID         INTEGER PRIMARY KEY AUTOINCREMENT,
                org_name      TEXT NOT NULL,
                description   TEXT,
                email         TEXT UNIQUE,
                password      TEXT,
                website_link  TEXT,
                city          TEXT,
                country       TEXT,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP
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
                FOREIGN KEY(orgID) REFERENCES organizations(orgID) ON DELETE CASCADE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_signups (
                signupID       INTEGER PRIMARY KEY AUTOINCREMENT,
                volunteerID    INTEGER NOT NULL,
                opportunityID  INTEGER NOT NULL,
                status         TEXT DEFAULT 'registered',
                signup_time    TEXT DEFAULT CURRENT_TIMESTAMP,
                check_in_time  TEXT,
                check_out_time TEXT,
                hours_logged   REAL,
                UNIQUE(volunteerID, opportunityID),
                FOREIGN KEY(volunteerID)   REFERENCES volunteers(volunteerID) ON DELETE CASCADE,
                FOREIGN KEY(opportunityID) REFERENCES opportunities(opportunityID) ON DELETE CASCADE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notificationID        INTEGER PRIMARY KEY AUTOINCREMENT,
                volunteerID           INTEGER NOT NULL,
                message               TEXT NOT NULL,
                type                  TEXT,
                related_opportunityID INTEGER,
                created_at            TEXT DEFAULT CURRENT_TIMESTAMP,
                read_at               TEXT,
                FOREIGN KEY(volunteerID) REFERENCES volunteers(volunteerID) ON DELETE CASCADE
            );
        """)

        self.connection.commit()

    # ------------------------------------------------------------------
    # Volunteers
    # ------------------------------------------------------------------
    def addVolunteer(self, gender, first_name, last_name, email, password,
                     country, zipcode, dob, skills="", mfa_enabled=1):
        try:
            self.cursor.execute("""
                INSERT INTO volunteers
                    (gender, first_name, last_name, email, password,
                     country, zipcode, dob, skills, mfa_enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (gender, first_name, last_name, email, hash_password(password),
                  country, zipcode, dob, skills, 1 if mfa_enabled else 0))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user_by_email(self, email):
        self.cursor.execute("""
            SELECT volunteerID, first_name, last_name, email, password,
                   country, zipcode, dob, skills, mfa_enabled
            FROM volunteers WHERE email = ?
        """, (email,))
        return self.cursor.fetchone()

    def authenticate_volunteer(self, email, password):
        row = self.get_user_by_email(email)
        if not row:
            return None
        if verify_password(password, row["password"]):
            return row
        return None

    # ------------------------------------------------------------------
    # Organizations
    # ------------------------------------------------------------------
    def addOrganization(self, org_name, description, email, password,
                        website_link="", city="", country=""):
        try:
            self.cursor.execute("""
                INSERT INTO organizations
                    (org_name, description, email, password, website_link, city, country)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (org_name, description, email, hash_password(password),
                  website_link, city, country))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_org_by_email(self, email):
        self.cursor.execute(
            "SELECT orgID, org_name, email, password, website_link, city, country "
            "FROM organizations WHERE email = ?", (email,))
        return self.cursor.fetchone()

    def authenticate_org(self, email, password):
        row = self.get_org_by_email(email)
        if not row:
            return None
        if verify_password(password, row["password"]):
            return row
        return None

    # ------------------------------------------------------------------
    # Opportunities
    # ------------------------------------------------------------------
    def addOpportunity(self, orgID, title, description, category, location,
                       is_remote, event_date, thumbnail=None,
                       start_time=None, end_time=None, capacity=None,
                       status="open", required_skills=None,
                       contact_name=None, contact_email=None, address=None):
        try:
            self.cursor.execute("""
                INSERT INTO opportunities
                    (orgID, title, description, category, location, address,
                     is_remote, event_date, start_time, end_time, capacity,
                     status, required_skills, contact_name, contact_email,
                     thumbnail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (orgID, title, description, category, location, address,
                  1 if is_remote else 0, event_date, start_time, end_time,
                  capacity, status, required_skills, contact_name,
                  contact_email, thumbnail))
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print("Create opportunity error:", e)
            return False

    def updateOpportunity(self, opportunityID, **fields):
        allowed = {"title", "description", "category", "location", "address",
                   "is_remote", "event_date", "start_time", "end_time",
                   "capacity", "status", "required_skills", "contact_name",
                   "contact_email", "thumbnail"}
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
                f"UPDATE opportunities SET {', '.join(sets)} WHERE opportunityID = ?",
                params)
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print("Update opportunity error:", e)
            return False

    def _opportunity_base_query(self):
        return """
            SELECT o.opportunityID, o.title, o.description, o.category,
                   o.location, o.address, o.is_remote, o.event_date,
                   o.start_time, o.end_time, o.capacity, o.status,
                   o.required_skills, o.contact_name, o.contact_email,
                   o.created_at, o.updated_at, o.thumbnail,
                   org.org_name, org.website_link, org.orgID
            FROM opportunities o
            LEFT JOIN organizations org ON o.orgID = org.orgID
        """

    def getAllOpportunitiesWithLinks(self, limit=500):
        q = self._opportunity_base_query() + " ORDER BY o.event_date ASC LIMIT ?"
        self.cursor.execute(q, (limit,))
        return self.cursor.fetchall()

    def getSoonestOpportunities(self, limit=10):
        today = datetime.now().strftime("%Y-%m-%d")
        q = self._opportunity_base_query() + """
            WHERE o.event_date IS NOT NULL AND o.event_date >= ?
              AND COALESCE(o.status, 'open') != 'cancelled'
            ORDER BY o.event_date ASC LIMIT ?
        """
        self.cursor.execute(q, (today, limit))
        return self.cursor.fetchall()

    def getNewestOpportunities(self, limit=10):
        q = self._opportunity_base_query() + """
            WHERE COALESCE(o.status, 'open') != 'cancelled'
            ORDER BY o.created_at DESC LIMIT ?
        """
        self.cursor.execute(q, (limit,))
        return self.cursor.fetchall()

    def getRemoteOpportunities(self, limit=10):
        q = self._opportunity_base_query() + """
            WHERE o.is_remote = 1
              AND COALESCE(o.status, 'open') != 'cancelled'
            ORDER BY o.event_date ASC LIMIT ?
        """
        self.cursor.execute(q, (limit,))
        return self.cursor.fetchall()

    def getOpportunitiesByOrg(self, orgID):
        q = self._opportunity_base_query() + " WHERE o.orgID = ? ORDER BY o.event_date ASC"
        self.cursor.execute(q, (orgID,))
        return self.cursor.fetchall()

    def getDistinctCategories(self):
        self.cursor.execute("""
            SELECT DISTINCT category FROM opportunities
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category ASC
        """)
        return [r["category"] for r in self.cursor.fetchall()]

    def searchOpportunities(self, keyword, category="All", limit=25):
        like = f"%{keyword}%"
        q = self._opportunity_base_query() + """
            WHERE (o.title LIKE ? OR o.description LIKE ?
                   OR o.location LIKE ? OR org.org_name LIKE ?)
        """
        params = [like, like, like, like]

        if category == "Remote":
            q += " AND o.is_remote = 1"
        elif category == "Organizations":
            q += " AND org.org_name LIKE ?"
            params.append(like)

        q += " ORDER BY o.event_date ASC LIMIT ?"
        params.append(limit)
        self.cursor.execute(q, params)
        return self.cursor.fetchall()

    # ------------------------------------------------------------------
    # Signups
    # ------------------------------------------------------------------
    def registerForOpportunity(self, volunteerID, opportunityID):
        try:
            # Capacity check
            self.cursor.execute(
                "SELECT capacity FROM opportunities WHERE opportunityID = ?",
                (opportunityID,))
            row = self.cursor.fetchone()
            if row and row["capacity"] is not None:
                self.cursor.execute(
                    "SELECT COUNT(*) AS c FROM event_signups "
                    "WHERE opportunityID = ? AND status = 'registered'",
                    (opportunityID,))
                if self.cursor.fetchone()["c"] >= row["capacity"]:
                    return "full"

            self.cursor.execute("""
                INSERT INTO event_signups (volunteerID, opportunityID, status)
                VALUES (?, ?, 'registered')
            """, (volunteerID, opportunityID))
            self.connection.commit()
            return "ok"
        except sqlite3.IntegrityError:
            return "duplicate"
        except sqlite3.Error as e:
            print("registerForOpportunity error:", e)
            return "error"

    def cancelSignup(self, volunteerID, opportunityID):
        self.cursor.execute("""
            UPDATE event_signups SET status = 'cancelled'
            WHERE volunteerID = ? AND opportunityID = ?
        """, (volunteerID, opportunityID))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def checkIn(self, volunteerID, opportunityID):
        now = datetime.now().isoformat(timespec="seconds")
        self.cursor.execute("""
            UPDATE event_signups
            SET check_in_time = ?
            WHERE volunteerID = ? AND opportunityID = ? AND check_in_time IS NULL
        """, (now, volunteerID, opportunityID))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def checkOut(self, volunteerID, opportunityID):
        now = datetime.now().isoformat(timespec="seconds")
        self.cursor.execute("""
            UPDATE event_signups
            SET check_out_time = ?,
                hours_logged = ROUND(
                    (julianday(?) - julianday(check_in_time)) * 24.0, 2)
            WHERE volunteerID = ? AND opportunityID = ?
              AND check_in_time IS NOT NULL AND check_out_time IS NULL
        """, (now, now, volunteerID, opportunityID))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def getSignupsForVolunteer(self, volunteerID):
        self.cursor.execute("""
            SELECT s.*, o.title, o.event_date, o.start_time, o.end_time,
                   o.location, o.is_remote, org.org_name
            FROM event_signups s
            JOIN opportunities o ON s.opportunityID = o.opportunityID
            LEFT JOIN organizations org ON o.orgID = org.orgID
            WHERE s.volunteerID = ?
            ORDER BY o.event_date DESC
        """, (volunteerID,))
        return self.cursor.fetchall()

    def getSignup(self, volunteerID, opportunityID):
        self.cursor.execute("""
            SELECT * FROM event_signups
            WHERE volunteerID = ? AND opportunityID = ?
        """, (volunteerID, opportunityID))
        return self.cursor.fetchone()

    def getSignupsForOpportunity(self, opportunityID):
        self.cursor.execute("""
            SELECT s.*, v.first_name, v.last_name, v.email
            FROM event_signups s
            JOIN volunteers v ON s.volunteerID = v.volunteerID
            WHERE s.opportunityID = ?
            ORDER BY s.signup_time ASC
        """, (opportunityID,))
        return self.cursor.fetchall()

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    def addNotification(self, volunteerID, message, type_=None,
                        related_opportunityID=None):
        self.cursor.execute("""
            INSERT INTO notifications (volunteerID, message, type, related_opportunityID)
            VALUES (?, ?, ?, ?)
        """, (volunteerID, message, type_, related_opportunityID))
        self.connection.commit()

    def getNotifications(self, volunteerID, limit=50):
        self.cursor.execute("""
            SELECT * FROM notifications
            WHERE volunteerID = ?
            ORDER BY created_at DESC LIMIT ?
        """, (volunteerID, limit))
        return self.cursor.fetchall()

    def markNotificationRead(self, notificationID):
        self.cursor.execute(
            "UPDATE notifications SET read_at = CURRENT_TIMESTAMP "
            "WHERE notificationID = ?", (notificationID,))
        self.connection.commit()

    # ------------------------------------------------------------------
    def close(self):
        try:
            self.cursor.close()
        finally:
            self.connection.close()