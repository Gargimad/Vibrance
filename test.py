from db import Database
db = Database()
for m in ("getOrgStats", "getUpcomingForOrg", "getRecentSignupsForOrg"):
    print(m, hasattr(db, m))