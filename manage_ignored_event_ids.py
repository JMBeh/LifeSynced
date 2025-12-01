#!/usr/bin/env python3
"""
Manage Ignored Event IDs

CLI tool to manage ignored specific event occurrences.
"""

import sys
import json
from pathlib import Path
from shared_db import CalendarDatabase

DB_PATH = Path(__file__).parent / 'calendar.db'

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 manage_ignored_event_ids.py [list|add|remove] [args...]")
        sys.exit(1)
    
    command = sys.argv[1]
    db = CalendarDatabase(str(DB_PATH))
    
    if command == 'list':
        ignored = db.get_ignored_event_ids_list()
        print(json.dumps(ignored))
    
    elif command == 'add':
        if len(sys.argv) < 3:
            print("Usage: python3 manage_ignored_event_ids.py add <event_id> [subject] [start_time] [reason]")
            sys.exit(1)
        
        event_id = sys.argv[2]
        subject = sys.argv[3] if len(sys.argv) > 3 else ''
        start_time = sys.argv[4] if len(sys.argv) > 4 else ''
        reason = sys.argv[5] if len(sys.argv) > 5 else 'User ignored'
        
        db.add_ignored_event_id(event_id, subject, start_time, reason)
        print(f"Added {event_id} to ignored list")
    
    elif command == 'remove':
        if len(sys.argv) < 3:
            print("Usage: python3 manage_ignored_event_ids.py remove <event_id>")
            sys.exit(1)
        
        event_id = sys.argv[2]
        db.remove_ignored_event_id(event_id)
        print(f"Removed {event_id} from ignored list")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()

