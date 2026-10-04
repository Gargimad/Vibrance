## How Moxie Addresses the Topic

Nonprofit organizations need to recruit, organize, and manage
volunteers. Moxie gives them:

### Recruit
- Post opportunities with category, location, capacity, and thumbnail.
- Volunteers browse and RSVP from a filterable listing.

### Organize
- Per-event attendance view with check-in / check-out times.
- Roster of every volunteer who has ever signed up, deduplicated.
- Notes and tags per volunteer (org-private).

### Maintain Records
- Verified hours: the org reviews and approves each volunteer's hours.
- No-show tracking.
- Editable hours for corrections.

### Monitor Participation
- Reports tab: hours by volunteer, hours by opportunity, custom date
  range, CSV export.
- Leaderboard of top volunteers.
- "Needs attention" card surfaces unverified hours and under-filled
  events.

### Migrate an Organization Roster
- Organization admins can open **Data migration** to update organization
  details and import a roster from CSV or Excel `.xlsx` files. Excel imports
  use the first worksheet.
- The first row must contain an `email` column. Optional volunteer columns
  are `first_name`, `last_name`, `country`, `zipcode`, `dob`, `gender`,
  `skills`, and `phone`. Optional organization columns are
  `organization_name`, `organization_description`, `organization_website`,
  `organization_city`, and `organization_country`. The page provides a
  downloadable CSV template.
- New volunteers receive an email with an eight-digit activation code. They
  choose **Activate imported account** on the login screen, verify the code,
  and set their own password. Codes expire after 24 hours and allow five
  attempts. Existing email addresses and duplicates in the file are skipped.
- Email invitations use the existing `SENDER_EMAIL`, `SENDER_PASSWORD`, and
  optional `DISPLAY_NAME` environment settings.
- This desktop build stores data in a local SQLite database. Volunteers can
  activate accounts only in an app instance connected to the same database;
  cross-device invitations require a shared hosted backend.