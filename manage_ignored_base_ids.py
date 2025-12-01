#!/usr/bin/env python3
"""
Manage Ignored Base IDs

CLI tool to manage ignored recurring event base IDs.
"""

import sys
import json
from pathlib import Path
from shared_db import CalendarDatabase

DB_PATH = Path(__file__).parent / 'calendar.db'

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 manage_ignored_base_ids.py [list|add|remove] [args...]")
        sys.exit(1)
    
    command = sys.argv[1]
    db = CalendarDatabase(str(DB_PATH))
    
    if command == 'list':
        ignored = db.get_ignored_base_ids_list()
        print(json.dumps(ignored))
    
    elif command == 'add':
        if len(sys.argv) < 3:
            print("Usage: python3 manage_ignored_base_ids.py add <base_id> [subject] [reason]")
            sys.exit(1)
        
        base_id = sys.argv[2]
        subject = sys.argv[3] if len(sys.argv) > 3 else ''
        reason = sys.argv[4] if len(sys.argv) > 4 else 'User ignored'
        
        db.add_ignored_base_id(base_id, subject, reason)
        print(f"Added {base_id} to ignored list")
    
    elif command == 'remove':
        if len(sys.argv) < 3:
            print("Usage: python3 manage_ignored_base_ids.py remove <base_id>")
            sys.exit(1)
        
        base_id = sys.argv[2]
        db.remove_ignored_base_id(base_id)
        print(f"Removed {base_id} from ignored list")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
