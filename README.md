# The Stampede — Purple Team T3 authentication

Requires Python 3.11+; dependencies are pinned to Django 5.2.17 and django-allauth 65.20.1.

## Start locally (PowerShell)

From this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# Configure the environment variables below privately in this PowerShell session.
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Set `STAMPEDE_SECRET_KEY` to a private, stable random value and retain it across restarts. Startup fails if it is missing. Set `STAMPEDE_EMAIL_HOST`, `STAMPEDE_EMAIL_PORT` (default 587), `STAMPEDE_EMAIL_USER`, `STAMPEDE_EMAIL_PASSWORD`, and `STAMPEDE_FROM_EMAIL` for your SMTP provider. TLS is enabled. Do not put values in source control or chat. This copy does not load .env files. Keep the database and secrets local. Port 8001 is suggested to avoid an existing server.

## Authentication and scope

Register with a username, @unomaha.edu email, and a separate Stampede password. Allauth sends a six-digit code through Django SMTP. Complete verification in the same browser within ten minutes. Django-allauth handles verification codes, expiration, incorrect attempts, and resend limits. Rate limiting uses a database cache. These are application limits, not a substitute for production abuse protection.

Mandatory verification gates login. Stamp endpoints also check active account status and a verified UNO address matching the user's current email. Inbox ownership does **not** prove current student enrollment. Basic Create records the signed-in user as owner. Stamp details are readable by verified UNO users; there are no edit/delete routes or private account-data views.

T3 belongs to Michael and Sarah. Full Stamp management belongs to T4. The Join Stamp endpoint is **only a permission demonstration**: it does not add participants or change counts; actual participation belongs to T6. Existing team models and migrations remain. No existing accounts or databases are included; migrating live accounts requires a separate review.

## Checks

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test stamps
```

Tests use Django's in-memory email backend and isolated test data, never real inboxes. For a manual SMTP check, start locally with your private email environment configured, register using an inbox you control, verify receipt of the six-digit code, confirm protected access is blocked before verification, enter the code, create a Stamp, then log out and log in again. A delivery failure leaves the account unverified; correct SMTP configuration and retry login. Production error pages are generic (DEBUG is off).

Configuration references: [allauth settings](https://docs.allauth.org/en/dev/account/configuration.html), [installation](https://docs.allauth.org/en/latest/installation/quickstart.html). The installed 65.20.1 package was used to verify exact configuration names.