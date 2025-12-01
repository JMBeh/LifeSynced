#!/usr/bin/env python3
"""
Query Database API

Called by Next.js API route to fetch events from SQLite database.
"""

import sys
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to Python path to import shared_db
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared_db import CalendarDatabase

DB_PATH = Path(__file__).parent.parent / 'calendar.db'

def main():
    try:
        days_ahead = int(sys.argv[1]) if len(sys.argv) > 1 else 30
        
        # Validate input
        if days_ahead < 0 or days_ahead > 365:
            print(json.dumps({'error': 'days_ahead must be between 0 and 365'}), file=sys.stderr)
            sys.exit(1)
        
        if not DB_PATH.exists():
            print(json.dumps({'error': f'Database not found: {DB_PATH}'}), file=sys.stderr)
            sys.exit(1)
        
        db = CalendarDatabase(str(DB_PATH))
        events = db.query_events(days_back=0, days_ahead=days_ahead)
        
        print(json.dumps(events))
    except ValueError as e:
        print(json.dumps({'error': f'Invalid days_ahead parameter: {e}'}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'error': f'Database query failed: {str(e)}'}), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

