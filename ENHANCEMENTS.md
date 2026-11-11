# The Stampede – enhancement build

This is an enhanced copy of the original project. It does not include a local SQLite database; create a fresh database with migrations after extracting it.

## Included changes

- Refreshed responsive visual design and postal-stamp-inspired event cards.
- Dedicated Explore/Search page and a location dropdown populated from the campus location list plus locations already used by events.
- Homepage sections for upcoming events, followed organizers, and suggestions based on categories, locations, and words in events the signed-in user has joined.
- User profile pages with display name, bio, interests, campus location, created events, and joined events.
- Profile edits staged until a six-digit confirmation code is sent to the user's current verified UNO email address.
- Follow/unfollow organizers.
- Event creator controls to edit, cancel/reopen, and delete their own events.
- Report button and report submission form for events; reports can be reviewed and marked from Django admin.
- Django admin registrations for stamps, profiles, follows, participation, and reports.

## Run locally

Use the same environment variables as the original local test:

```powershell
$env:STAMPEDE_SECRET_KEY = "local-testing-secret-key-123456789"
$env:STAMPEDE_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
python manage.py migrate
python manage.py check
python manage.py test stamps
python manage.py runserver
```

The console email backend prints verification and profile-confirmation emails in the terminal. For actual email delivery, configure SMTP environment variables privately; do not commit credentials.

## Notes

- Extract this ZIP into a separate folder from the original project. It intentionally has no `db.sqlite3` so it uses its own test data.
- `0008_profile_follow_and_stamp_status.py` adds the new profile/follow models and event status fields.
- This was only tested locally.
