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
- Organizers can check volunteers in or out from the event roster, review
  hours, and mark no-shows from **View signups**.
- Volunteers receive an in-app notification when a registered event is
  within 24 hours while their dashboard is open.
- Volunteers can export their approved hours as a shareable CSV impact
  record. Recommendations explain skill, country, and remote matches.

### Monitor Participation
- Reports tab: hours by volunteer, hours by opportunity, custom date
  range, CSV export.
- Leaderboard of top volunteers.
- "Needs attention" card surfaces unverified hours and under-filled
  events.
- Reports also summarize repeat volunteers and overall opportunity
  capacity filled. Opportunity details can be copied to share in a message.

### Protect Local Data
- Organization admins can back up the local SQLite database and restore a
  backup from the dashboard. Restoring first saves a safety backup and
  closes Moxie; reopen the app to use the restored data.
- The desktop app remains local-first. Cross-device syncing and phone-to-PC
  QR check-in require a shared hosted backend, which is not part of this
  SQLite build.

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