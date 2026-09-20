#
import sqlite3

class Database:
    def __init__(self):
        #Connection to Volunteer.db database for login and signup
        self.connection = sqlite3.connect("Volunteer.db")
        self.cursor = self.connection.cursor()
        self.createTable()
        

    def createTable(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS volunteers (
                "volunteerID"	INTEGER,
                "gender"	TEXT,
                "first_name"	TEXT,
                "last_name"	TEXT,
                "email"	TEXT,
                "password"	TEXT,
                "country"	TEXT,
                "zipcode"	INTEGER,
                "dob"	TEXT,
                "skills"	TEXT,
                "mfa_enabled"	INTEGER DEFAULT 1,
                PRIMARY KEY("volunteerID" AUTOINCREMENT)
            );
        """)
    
#Login+Signup---------------------------------------------------------------------------------
    def addVolunteer(self, gender, first_name, last_name, email, password, country, zipcode, dob, skills="", mfa_enabled=1):
        try:
            self.cursor.execute("INSERT INTO volunteers (gender, first_name, last_name, email, password, country, zipcode, dob, skills, mfa_enabled) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                                (gender, first_name, last_name, email, password, country, zipcode, dob, skills, 1 if mfa_enabled else 0))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    def get_user_by_email(self, email):
        """Retrieves user record for login authentication."""
        self.cursor.execute('''
            SELECT volunteerID, first_name, password, mfa_enabled 
            FROM volunteers 
            WHERE email = ?
        ''', (email,))
        return self.cursor.fetchone()

#Validating if user exists or not--------------------------------------------------------------
    def userExists(self, email, password):
        self.cursor.execute("SELECT * FROM users WHERE email=? AND password=?", 
                            (email, password))
        return self.cursor.fetchone() is not None

    def createBusiness(self, name, description, sub_id, website_link="", city_id=None):
        try:
            self.cursor.execute("""
                INSERT INTO businesses 
                (biz_name, description, sub_id, rating, review_count, website_link, city_id)
                VALUES (?, ?, ?, 0.0, 0, ?, ?)
            """, (name, description, sub_id, website_link, city_id))

            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print("Create business error:", e)
            return False

    def close(self):
        self.connection.close()
        self.cursor.close()