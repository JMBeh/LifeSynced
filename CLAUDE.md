# LifeSynced

## Project Type
Hybrid application: Python backend (calendar sync) + Next.js frontend (web UI)

## Key Commands

### Backend (Calendar Sync)
```bash
# Sync all calendars (work Outlook + personal iCloud)
python3 sync_all_calendars.py

# Sync individual calendars
python3 sync_calendar.py              # Outlook via Graph API
python3 sync_calendar_ics.py          # Outlook via ICS feed
python3 sync_apple_calendar.py        # iCloud calendars

# Query database
python3 query_db.py list              # List upcoming events
python3 query_db.py stats             # Database statistics

# Cleanup duplicates
python3 cleanup_duplicates.py

# Manage ignored events
python3 manage_ignored_base_ids.py list
python3 manage_ignored_base_ids.py add <base_id> [subject] [reason]
python3 manage_ignored_base_ids.py remove <base_id>
```

### Frontend (Web UI)
```bash
cd calendar-ui

# Development
npm install                           # First time only
npm run dev                           # Start dev server (port 3002)

# Production
npm run build                         # Build for production
npm run start                         # Start production server

# Linting
npm run lint                          # Run ESLint
```

### Automation
```bash
# macOS launchd (recommended)
cp com.lifesynced.calendar.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.lifesynced.calendar.plist

# Or use cron
crontab -e
# Add: 0 6 * * * cd "/Users/jmbeh/Builder_Lab/LifeSynced" && /usr/bin/python3 sync_all_calendars.py >> /tmp/calendar_sync.log 2>&1
```

## Project Structure
```
LifeSynced/
├── sync_calendar.py              # Outlook sync via Microsoft Graph API
├── sync_calendar_ics.py          # Outlook sync via ICS feed (no admin consent)
├── sync_apple_calendar.py        # iCloud calendar sync
├── sync_all_calendars.py         # Master sync script (runs all syncs)
├── shared_db.py                  # Unified database interface
├── timezone_utils.py             # Timezone handling utilities
├── query_db.py                   # CLI database query tool
├── cleanup_duplicates.py         # Remove duplicate events
├── manage_ignored_base_ids.py    # Manage ignored recurring events
├── calendar.db                   # SQLite database (gitignored)
├── .token_cache.json             # MSAL token cache (gitignored)
├── calendar-ui/                  # Next.js web interface
│   ├── app/                      # Next.js app directory
│   │   ├── page.tsx              # Main calendar view
│   │   ├── api/                  # API routes
│   │   │   ├── events/           # GET /api/events
│   │   │   ├── sync/             # POST /api/sync
│   │   │   └── ignored-base-ids/ # Manage ignored events
│   │   └── globals.css           # TailwindCSS styles
│   ├── query_db_api.py           # Python script called by API routes
│   └── package.json              # Next.js dependencies
└── requirements.txt              # Python dependencies
```

## Environment Variables
Required in root `.env`:
- `CLIENT_ID` - Azure app client ID (for Graph API method)
- `TENANT_ID` - Azure tenant ID (for Graph API method)
- `OUTLOOK_ICS_URL` - Outlook ICS feed URL (alternative to Graph API)
- `APPLE_CALENDAR_ICS_URL` - iCloud calendar ICS URL(s), comma-separated
- `APPLE_CALENDAR_ICS_PATH` - Alternative: path to ICS file(s), comma-separated
- `APPLE_CALENDAR_DB_PATH` - Fallback: macOS Calendar.sqlite path
- `DB_PATH` - SQLite database path (default: `calendar.db`)
- `SKIP_GRAPH_API` - Set to `true` to disable Graph API sync (default: `False`)

## Development Notes

### Backend
- Python 3.9+ required
- Uses `msal` for Microsoft Graph API authentication
- Uses `icalendar` and `python-dateutil` for ICS parsing
- SQLite database stores all events with deduplication
- Timezone handling via `timezone_utils.py` (normalizes to UTC/Pacific)

### Frontend
- Next.js 14 with App Router
- TypeScript + React
- TailwindCSS for styling
- Port 3002 (to avoid conflicts with other Next.js apps)
- API routes call Python scripts via `execSync`
- Time-grid week view with sticky headers and side-by-side overlap display
- Overlap detection between work and personal calendars
- Mobile-responsive: Day view default on mobile (<768px), Week view on desktop
- Timezone selector for travel scenarios
- View modes: Day, Week, 4-Week

### Database Schema
- `appointments` table: id, subject, start_time, end_time, location, organizer_email, organizer_name, attendees (JSON), body_preview, is_all_day, source, created_at, updated_at
- `ignored_base_ids` table: base_id, subject, ignored_at, reason
- `ignored_event_ids` table: event_id, subject, start_time, reason, ignored_at (for individual occurrences)

### Sync Methods
1. **Microsoft Graph API** (best data quality, requires admin consent)
2. **ICS Feed** (no admin consent, limited event details)
3. **iCloud Public Calendar** (recommended for personal calendars)

### Known Issues
- Some complex RRULE patterns fail to parse (recurring events)
- ICS feeds may show "[Busy]" instead of actual event titles (Outlook privacy)
- Timezone normalization fixes most DST issues

### Testing
```bash
# Test sync
python3 sync_all_calendars.py

# Test database query
python3 query_db.py stats

# Test web UI
cd calendar-ui && npm run dev
# Open http://localhost:3002
```

---

**Last Updated:** 2025-12-01

