# LifeSynced – Project Plan

## Executive Summary

LifeSynced is a personal productivity tool that unifies work (Outlook) and personal (iCloud) calendars into a single view, detects conflicts between them, and gives the user control to declutter what they see. The system pulls events from multiple sources (Graph API, ICS feeds, iCloud exports), normalizes and deduplicates them into a local SQLite database, and exposes the data through a modern web UI with rich visualization and filtering.

---

## Problem & Goals

### Problem

- **Fragmented calendar management:** Work (Outlook) and personal (iCloud) calendars live in separate systems with no native unified view.
- **Hidden conflicts:** It is hard to spot scheduling conflicts between work commitments and personal obligations across those silos.

### Primary Objectives

- **Unified calendar view:** Single, cohesive interface that displays both work and personal calendar events.
- **Conflict detection:** Automatically detect and highlight overlaps between work and personal events.
- **User-centric control:** Allow users to selectively ignore or hide events to keep the unified view focused and decluttered.

### Success Criteria

- All relevant calendar events are visible in one place.
- Overlaps between work and personal calendars are clearly identified.
- No duplicate events appear from multiple sync sources.
- Sync can run reliably and automatically.
- The web interface is intuitive, responsive, and pleasant to use.

---

## Functional Requirements

### Calendar Synchronization

- **Work (Outlook):**
  - Support Microsoft Graph API with full event details.
  - Support ICS feed as a no‑admin‑consent alternative.
  - Handle authentication (OAuth 2.0) and token refresh automatically.
- **Personal (iCloud):**
  - Support public calendar ICS URLs (recommended).
  - Support ICS file imports as an alternative.
  - Support multiple personal calendars simultaneously.
- **Storage:**
  - Persist all events in a single unified database.
  - Perform automatic deduplication across sync methods.

### Data Management

- Store all events in a centralized SQLite database.
- Normalize timezones so events align correctly across sources.
- Handle recurring events by expanding RRULE patterns where feasible.
- Track event source (work vs personal, Graph vs ICS vs Apple).
- Preserve rich event metadata:
  - Subject/title.
  - Start/end time.
  - Location.
  - Organizer and attendees.
  - Description/body preview.

### Conflict Detection

- Identify overlapping events between work and personal calendars based on time ranges.
- Provide clear visual indicators for conflicts.
- Alert or highlight conflicts in the UI.
- Allow filtering to emphasize only overlapping events when desired.

### User Interface

- Web‑based calendar view accessible from a browser.
- Multiple view modes:
  - Day (default on mobile).
  - Week (default on desktop).
  - 4‑week.
- Time‑grid week view covering the full 24‑hour day (0000–2400).
- Color‑coding to distinguish work vs personal events.
- Sticky headers for easier navigation.
- Option to hide weekends.
- Option to emphasize conflicts.
- Controls to add/remove ignored events.
- Responsive design for mobile and desktop browsers.
- Timezone selector for travel or remote work scenarios.
- Event details tooltip on hover or tap.

### Event Management

- Ignore or hide specific recurring and non‑recurring events.
- Ignore individual occurrences or entire recurring series.
- Trigger manual sync/refresh from the UI.
- View event details (time, location, organizer, description) via hover tooltip.
- Support basic filtering and search across events.
- Automatic exclusion of all‑day/multi‑day "Free" events from overlap detection.

### Automation

- Support scheduled automatic sync (daily or hourly).
- Run sync tasks in the background.
- Log sync operations for troubleshooting and observability.

---

## Non‑Functional Requirements

- **Reliability:** Sync should handle source‑level failures gracefully and continue with other sources.
- **Performance:** Queries over the event set should remain fast even as the database grows.
- **Privacy:** Calendar data is stored locally; no cloud sync of personal data.
- **Flexibility:** Multiple sync methods exist to handle organizational constraints (e.g., lack of admin consent).
- **Maintainability:** Clear separation of concerns between sync logic, storage/query logic, and UI/presentation.

---

## Data Sources

### Work Calendar (Outlook)

- **Microsoft Graph API**
  - Requires: Azure app registration and admin consent.
  - Provides: Full event details (title, time, location, organizer, attendees, description).
  - Authentication: OAuth 2.0 with token caching.

- **ICS Feed**
  - Requires: Calendar published in Outlook on the Web.
  - Provides: Availability‑only (Free/Busy/Tentative) or full details depending on permissions.
  - Authentication: None (public URL).

### Personal Calendar (iCloud)

- **Public Calendar ICS URL**
  - Requires: Calendar shared as public in iCloud.
  - Provides: Full event details.
  - Authentication: None (public URL).

- **ICS File Export**
  - Requires: Manual export from iCloud.com or macOS Calendar app.
  - Provides: Full event details.
  - Authentication: None (local file).

---

## Architecture & Data Flow

### Logical Layers

1. **Sync Layer**
   - Multiple sync scripts pull events from different calendar sources.
   - Each sync method owns its authentication and data fetching flow.
   - Events are normalized (timezone, format) before writing to storage.

2. **Storage Layer**
   - Single SQLite database stores all events.
   - Deduplication logic prevents duplicate entries.
   - Precedence rules determine which source wins when conflicts occur.
   - Ignored events are tracked separately from active events.

3. **Query Layer**
   - Database queries filter events by date range and other criteria.
   - Ignored events are excluded from default result sets.
   - Filters allow selection by source (work vs personal).

4. **Presentation Layer**
   - Web interface queries the database via API endpoints.
   - Events are grouped and displayed in multiple calendar views.
   - Overlap detection runs on the client or server side.
   - User interactions (ignore, refresh) trigger database updates and re‑queries.

### Sync Workflow

1. User or scheduler triggers sync (manual or scheduled).
2. Each configured sync method runs independently:
   - Authenticate (if needed).
   - Fetch events from its calendar source.
   - Parse and normalize event data.
   - Check for duplicates using the deduplication strategy.
   - Save to database (insert new records, update existing ones).
3. Sync completes and logs results.
4. Web interface reflects updated data on next query/refresh.

### Deduplication Strategy

- **Primary:** Match by event ID (each source has a unique ID format).
- **Secondary:** Within the same source, treat events with identical subject + start time + organizer email as duplicates.
- **Precedence:** For Outlook events, Graph API entries take precedence over ICS feed entries.
- **Cross‑source:** No deduplication between work and personal calendars (they represent distinct domains).

### Overlap Detection

- Compare event time ranges between work and personal calendars.
- Identify overlapping intervals where events conflict.
- Mark overlapping events visually in the UI and allow views that show only overlaps.

---

## Key Design Decisions

### Why SQLite?

- Keeps all data local for privacy.
- Avoids the need for a separate database server.
- Simple to deploy and back up.
- More than sufficient for personal‑scale event volumes.

### Why Multiple Sync Methods?

- Organizational constraints may prevent Graph API admin consent.
- Different users or accounts may need different data quality (full details vs availability‑only).
- Provides fallbacks if one method fails or is temporarily unavailable.

### Why a Web Interface?

- Cross‑platform access from any modern browser.
- No native app installation required.
- Easy to update UI/UX over time.
- Enables rich, interactive visualizations and filters.

### Why the Ignore Feature?

- Recurring events can clutter the unified view and obscure important items.
- Users often have recurring meetings they do not want to see in this context.
- Ignoring events improves focus on relevant commitments.
- Changing recurring event times can generate new base IDs, leading to multiple logical copies of the “same” meeting; the ignore mechanism helps manage that complexity and avoid confusion in the calendar view.

---

## Future Considerations

### Potential Enhancements

- Add support for additional calendar sources (Google Calendar, CalDAV).
- Allow event editing from within LifeSynced.
- Explore two‑way sync (create and modify events from LifeSynced).
- Build a native mobile client (PWA or React Native).
- Add calendar export functionality.
- Implement more advanced filtering and search.
- Provide event reminders and notifications.

### Recently Implemented

- ✅ Mobile‑responsive design with adaptive default views.
- ✅ Timezone selector for travel scenarios.
- ✅ Event details tooltip on hover/tap.
- ✅ Ignore individual occurrences or entire recurring series.
- ✅ Automatic filtering of all‑day/multi‑day "Free" events from overlap detection.
- ✅ Side‑by‑side display for overlapping events in week view.

### Scalability Considerations

- Current design is optimized for a single user / personal use.
- SQLite should comfortably handle thousands of events.
- The web interface can be deployed to the cloud if needed.
- Sync frequency can be tuned based on usage patterns and performance.
