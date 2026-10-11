# patch_thumbnails.py
import csv
import shutil
from db import Database

db = Database()
updated = 0

with open("georgia_volunteer_events.csv", newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        url = (row.get("thumbnail") or "").strip()
        if not url:
            continue
        db.cursor.execute(
            "UPDATE opportunities SET thumbnail = ? WHERE title = ?",
            (url, row["title"].strip()),
        )
        updated += db.cursor.rowcount

db.connection.commit()
db.close()
print(f"Updated {updated} rows.")

shutil.rmtree("Events/.thumb_cache", ignore_errors=True)
print("Cleared thumbnail cache.")