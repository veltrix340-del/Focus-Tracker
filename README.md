# Focus Reset — 30-Day Tracker

Full-stack starter: HTML/CSS/JavaScript frontend, Django REST Framework API, SQLite database, and a native Kotlin Android companion using Android Usage Access.

## Windows setup
1. Install Python 3.10+ and Android Studio.
2. In PowerShell:
   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   py manage.py migrate
   py manage.py createsuperuser
   py manage.py runserver 0.0.0.0:8000
   ```
3. Open `frontend/index.html`, enter API URL `http://127.0.0.1:8000`, and register/login.
4. For phone sync, use the laptop's LAN IP (for example `http://192.168.1.10:8000`) in both dashboard and Android app, allow Python through Windows Firewall on private networks, and keep both devices on the same Wi-Fi.
5. Open `android` in Android Studio, sync Gradle, set `API_BASE_URL` in `MainActivity.kt`, run on the phone, grant Usage Access, paste the API token from dashboard Settings, and tap Sync now.

## Features
- User registration and token login
- Starts a 30-day challenge automatically; start/restart endpoint included
- Daily usage totals and per-app breakdown stored by date
- Dashboard history, daily goal, focus session logging, progress calendar
- Authenticated Android sync API and Django admin
- SQLite database is created at `backend/db.sqlite3`

## MySQL
SQLite is the default. To use MySQL, install a compatible MySQL driver, create a database, and replace `DATABASES` in `backend/focusreset/settings.py` with a `django.db.backends.mysql` configuration using environment variables. Never commit real passwords.

## API
`GET /api/health/`; `POST /api/auth/register/`; `POST /api/auth/token/`; `GET /api/dashboard/?days=30`; `GET/POST /api/usage/sync/`; `GET/PATCH /api/settings/`; `GET/POST /api/focus-sessions/`; `GET /api/challenge/`; `POST /api/challenge/start/`.

## Notes
- Android usage is only read after the user grants Usage Access.
- Android sync is manual in this starter; scheduled background sync is not implemented.
- Android UsageStatsManager cannot reliably distinguish YouTube Shorts from ordinary YouTube or Instagram Reels from other Instagram usage.
- Local HTTP is for development only. Use HTTPS, secure secrets, backups, and tighter security before public deployment.
- Source files are provided; no APK was built or tested on your physical phone in this environment.
