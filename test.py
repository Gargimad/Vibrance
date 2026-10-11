import csv
from db import Database

# 1. Connect to the database
db = Database()
cursor = db.cursor

# 2. Open the CSV file
with open('georgia_volunteer_events.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        org_name = row['org_name'].strip()
        if not org_name:
            continue

        # 3. Look up the orgID by name
        cursor.execute(
            "SELECT orgID FROM organizations WHERE org_name = ?",
            (org_name,)
        )
        org_row = cursor.fetchone()
        if not org_row:
            print(f"⚠️  Organization not found: {org_name}. Skipping.")
            continue
        orgID = org_row['orgID']

        # 4. Map CSV fields to the opportunities table
        #    (Only columns that exist in the table)
        try:
            cursor.execute("""
                INSERT INTO opportunities (
                    orgID, title, description, category, location, address,
                    is_remote, event_date, event_end_date, start_time, end_time,
                    capacity, status, required_skills, contact_name,
                    contact_email, website_link, city, state, high_school,
                    min_age, max_age, meal_provided,
                    background_check_required, training_required,
                    training_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                          ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                orgID,
                row.get('title', ''),
                row.get('description', ''),
                row.get('category', ''),
                row.get('location', ''),
                row.get('address', ''),
                int(row.get('is_remote', 0) or 0),
                row.get('event_date') or None,
                row.get('event_end_date') or None,
                row.get('start_time') or None,
                row.get('end_time') or None,
                int(row['capacity']) if row.get('capacity') else None,
                row.get('status', 'open'),
                row.get('required_skills') or None,
                row.get('contact_name') or None,
                row.get('contact_email') or None,
                row.get('website_link') or None,
                row.get('city') or None,
                row.get('state', 'GA'),
                row.get('high_school') or None,
                int(row['min_age']) if row.get('min_age') else None,
                int(row['max_age']) if row.get('max_age') else None,
                int(row.get('meal_provided', 0) or 0),
                int(row.get('background_check_required', 0) or 0),
                int(row.get('training_required', 0) or 0),
                row.get('training_description') or None,
            ))
            print(f"✅ Added event: {row['title']} for {org_name}")
        except Exception as e:
            print(f"❌ Failed to add {row.get('title')}: {e}")

# 5. Commit and close
db.connection.commit()
db.close()
print("\nEvent import complete!")