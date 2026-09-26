from db import Database
db = Database()

n = db.cursor.execute(
    "DELETE FROM opportunities WHERE source_id LIKE 'vc:%'"
).rowcount
print(f"deleted {n}")
db.connection.commit()

import volunteer_connector as vc
print(f"inserted {vc.sync(db, max_pages=3, use_cache=False)}")

for r in db.cursor.execute("""
    SELECT event_date, event_end_date, title
    FROM opportunities WHERE source_id LIKE 'vc:%' LIMIT 8
""").fetchall():
    print(f"  {r['event_date']:12s} -> {r['event_end_date'] or '':12s}  "
          f"{r['title'][:40]}")