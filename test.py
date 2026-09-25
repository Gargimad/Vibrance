"""
resync.py — One-shot script to migrate the organizations table, clear
old external data, and re-sync from Volunteer Connector.

Safe to re-run. Prints progress at each step.

Run from the folder containing db.py and volunteer_connector.py:
    python resync.py
"""

import sqlite3
import sys

from db import Database
import volunteer_connector as vc


def section(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main():
    # ── 1. Migrate the organizations table ───────────────────────────────
    section("1. Migrate organizations table")
    conn = sqlite3.connect("Volunteer.db")
    try:
        conn.execute("ALTER TABLE organizations ADD COLUMN source_id TEXT")
        print("  added source_id column")
    except sqlite3.OperationalError as e:
        print(f"  source_id already present (or error): {e}")

    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_org_source "
        "ON organizations(source_id) WHERE source_id IS NOT NULL"
    )
    conn.commit()
    conn.close()
    print("  unique index ready")

    # ── 2. Clean old external data ───────────────────────────────────────
    section("2. Clear old external data")
    db = Database()

    n1 = db.cursor.execute(
        "DELETE FROM opportunities WHERE source_id LIKE 'vc:%'"
    ).rowcount
    print(f"  deleted {n1} external opportunities")

    n2 = db.cursor.execute("""
        DELETE FROM organizations
        WHERE userID IS NULL
          AND orgID NOT IN (
            SELECT DISTINCT orgID FROM opportunities WHERE orgID IS NOT NULL
          )
    """).rowcount
    print(f"  deleted {n2} external orgs")

    db.connection.commit()

    # ── 3. Re-sync from the API ──────────────────────────────────────────
    section("3. Sync from Volunteer Connector")
    inserted = vc.sync(db, max_pages=3, use_cache=False)
    print(f"  inserted {inserted} new opportunities")

    # ── 4. Verify opportunities ──────────────────────────────────────────
    section("4. Verify opportunities")
    rows = db.cursor.execute(
        "SELECT opportunityID, title, orgID, source_id, website_link "
        "FROM opportunities WHERE source_id LIKE 'vc:%' LIMIT 5"
    ).fetchall()
    print(f"  {len(rows)} shown of external rows:")
    for r in rows:
        link = (r["website_link"] or "(no link)")[:60]
        print(f"    [{r['opportunityID']}] orgID={r['orgID']}  {link}")
        print(f"          {r['title'][:60]}")

    # ── 5. Verify organizations ──────────────────────────────────────────
    section("5. Verify organizations")
    orgs = db.cursor.execute("""
        SELECT orgID, org_name, source_id
        FROM organizations
        WHERE source_id IS NOT NULL
        ORDER BY orgID
    """).fetchall()
    print(f"  {len(orgs)} external orgs:")
    for o in orgs:
        print(f"    [{o['orgID']}] {o['org_name']}")
        print(f"          {o['source_id']}")

    # ── 6. Cross-check ───────────────────────────────────────────────────
    section("6. Cross-check")
    orphan = db.cursor.execute("""
        SELECT COUNT(*) FROM opportunities o
        WHERE o.source_id LIKE 'vc:%'
          AND (o.orgID IS NULL OR o.orgID NOT IN (
            SELECT orgID FROM organizations
          ))
    """).fetchone()[0]
    print(f"  opportunities pointing at a missing org: {orphan}")
    if orphan:
        print("  Something is wrong — orgs were not created.")
    else:
        print("  Every external opportunity points at a real org.")

    section("Done")
    print("Restart the app (python main.py) to see the changes.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)