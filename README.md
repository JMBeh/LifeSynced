# LifeSynced

![Type](https://img.shields.io/badge/Type-App-blue)
![Status](https://img.shields.io/badge/Status-Active-green)
![Stack](https://img.shields.io/badge/Stack-Python%20%7C%20Next.js-blue)

Unified calendar application that syncs work Outlook and personal iCloud calendars into a single SQLite database and surfaces everything in a focused web UI with overlap detection and smart deduplication.

## Features

- **Unified view:** Combine work Outlook and personal iCloud calendars into one timeline.
- **Time-grid week view:** 24‑hour time grid (0000–2400) with color‑coded sources and side‑by‑side overlap display.
- **Overlap detection:** Highlight conflicts between work and personal events (excludes all‑day/multi‑day "Free" blocks).
- **Smart deduplication:** Avoid duplicate events across sync sources.
- **Ignore events:** Hide recurring series or individual occurrences you do not want to see.
- **Mobile-friendly:** Responsive design with Day view default on mobile, Week view on desktop.
- **Timezone selector:** Switch timezones when traveling to see events in local time.
- **Local-first automation:** Daily sync via macOS `launchd` or `cron`.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
cd calendar-ui
npm install
cd ..
```

### 2. Configure environment

```bash
cp .env.example .env
```

Set the core variables in `.env`:

- **Outlook (work)**:
  - `CLIENT_ID`, `TENANT_ID` for Microsoft Graph API (recommended).
  - `OUTLOOK_ICS_URL` as a fallback ICS feed if Graph API is not available.
- **iCloud (personal)**:
  - `APPLE_CALENDAR_ICS_URL` – one or more public iCloud calendar ICS URLs (comma‑separated).
- **Database**:
  - `DB_PATH` – SQLite path (defaults to `calendar.db`).

Optional:

- `APPLE_CALENDAR_ICS_PATH`, `APPLE_CALENDAR_DB_PATH` – alternate Apple Calendar sources.
- `SKIP_GRAPH_API` – set to `true` to force ICS‑only sync.

See `CLAUDE.md` for provider‑specific setup details and advanced options.

### 3. Sync calendars

```bash
python3 sync_all_calendars.py
```

### 4. Start the web UI

```bash
cd calendar-ui
npm run dev
```

Open `http://localhost:3002` in your browser.

---

## Scripts

### Backend (Python)

```bash
python3 sync_all_calendars.py
python3 sync_calendar.py
python3 sync_calendar_ics.py
python3 sync_apple_calendar.py
python3 query_db.py list
python3 query_db.py stats
python3 cleanup_duplicates.py
python3 manage_ignored_base_ids.py list
```

### Frontend (Next.js)

```bash
cd calendar-ui
npm run dev
npm run build
npm run start
npm run lint
```

## Environment Variables

- **`CLIENT_ID`** – Azure app client ID for Microsoft Graph API.
- **`TENANT_ID`** – Azure tenant ID for Microsoft Graph API.
- **`OUTLOOK_ICS_URL`** – Outlook ICS feed URL (fallback or alternative to Graph API).
- **`APPLE_CALENDAR_ICS_URL`** – one or more public iCloud calendar ICS URLs (comma‑separated).
- **`APPLE_CALENDAR_ICS_PATH`** – optional path(s) to local Apple Calendar `.ics` exports.
- **`APPLE_CALENDAR_DB_PATH`** – optional path to macOS `Calendar.sqlite`.
- **`DB_PATH`** – SQLite database path (defaults to `calendar.db` in the project root).
- **`SKIP_GRAPH_API`** – when `true`, skip Graph API and use ICS‑only sync.

## Deployment & Automation (macOS)

For local automation with `launchd`:

```bash
cp com.lifesynced.calendar.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.lifesynced.calendar.plist
```

Or using `cron`:

```bash
crontab -e
```

Then add:

```bash
0 6 * * * cd "/Users/jmbeh/Builder_Lab/LifeSynced" && /usr/bin/python3 sync_all_calendars.py >> /tmp/calendar_sync.log 2>&1
```

## Data Model

- **`appointments`** – unified events from Graph API, ICS, and Apple calendars with subject, start/end times, location, organizer, attendees (JSON), and metadata.
- **`ignored_base_ids`** – recurring event identifiers you want hidden, with subject and reason.

Deduplication:

- Graph API wins over ICS when both exist.
- Within the same source, duplicates are detected by `subject`, `start_time`, and `organizer_email`.

## Troubleshooting

- **Missing events:** Check calendar sharing permissions and prefer Graph API over ICS for full details.
- **Timezone issues:** Events are normalized to Pacific time (including DST); only some complex recurrence rules may misbehave.
- **ModuleNotFoundError:** Ensure you are using the Python environment with dependencies installed:

```bash
python3 -c "import msal; print('msal installed')"
```

## Development

- See `CLAUDE.md` for full project structure, environment details, and advanced commands.
- Use the template and refinement prompt in `Docs_MyPrompts/READMEs` to keep this README concise and up to date as the project evolves.

---

**Status:** Active  
**Purpose:** Personal productivity tool – unified calendar view
