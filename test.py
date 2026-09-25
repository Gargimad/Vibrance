from db import Database
import volunteer_connector as vc

db = Database()

n = db.cursor.execute(
    "DELETE FROM opportunities WHERE source_id LIKE 'vc:%'"
).rowcount
db.connection.commit()
print(f"deleted {n} old rows")

inserted = vc.sync(db, max_pages=3, use_cache=False)
print(f"inserted {inserted}")