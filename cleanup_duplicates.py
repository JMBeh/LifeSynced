#!/usr/bin/env python3
"""
Cleanup duplicate events in the calendar database.

Removes duplicate events that have the same subject, start_time (normalized to UTC), and organizer_email
within the same source, keeping only the first occurrence (by created_at).
"""

import sqlite3
import sys
from pathlib import Path
from timezone_utils import parse_iso_datetime, normalize_to_utc

DB_PATH = Path(__file__).parent / 'calendar.db'

def main():
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        
        # Get all events grouped by source
        cursor.execute('SELECT DISTINCT source FROM appointments WHERE source IS NOT NULL')
        sources = [row[0] for row in cursor.fetchall()]
        
        # Also handle NULL sources
        if sources:
            sources.append(None)
        
        total_removed = 0
        
        for source in sources:
            if source is None:
                # Update NULL sources to 'ics' before deduplication
                cursor.execute('UPDATE appointments SET source = ? WHERE source IS NULL', ('ics',))
                source = 'ics'
            
            # Get all events for this source
            cursor.execute('''
                SELECT id, subject, start_time, organizer_email, created_at 
                FROM appointments 
                WHERE source = ?
                ORDER BY created_at ASC
            ''', (source,))
            
            events = cursor.fetchall()
            seen = {}
            to_remove = []
            
            for event_id, subject, start_time, organizer_email, created_at in events:
                start_dt = parse_iso_datetime(start_time)
                if not start_dt:
                    continue
                
                start_utc = normalize_to_utc(start_dt)
                org_email = organizer_email or ''
                
                # Create key for deduplication
                key = (subject, start_utc.isoformat(), org_email)
                
                if key in seen:
                    # This is a duplicate
                    to_remove.append(event_id)
                    print(f"Duplicate found: {subject} at {start_time} (keeping {seen[key]}, removing {event_id})")
                else:
                    seen[key] = event_id
            
            # Remove duplicates
            for event_id in to_remove:
                cursor.execute('DELETE FROM appointments WHERE id = ?', (event_id,))
                total_removed += 1
            
            conn.commit()
        
        print(f"\nRemoved {total_removed} duplicate events")

if __name__ == '__main__':
    main()

