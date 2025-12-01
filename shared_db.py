#!/usr/bin/env python3
"""
Shared Database Module

Provides unified database operations for all calendar sync scripts.
Eliminates code duplication and ensures consistency.
"""

import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import os

from timezone_utils import normalize_to_utc, parse_iso_datetime

logger = logging.getLogger(__name__)


class CalendarDatabase:
    """Unified database interface for calendar events."""
    
    def __init__(self, db_path: str):
        """Initialize database connection and schema."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite database and create tables/indexes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create appointments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id TEXT PRIMARY KEY,
                    subject TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    location TEXT,
                    organizer_email TEXT,
                    organizer_name TEXT,
                    attendees TEXT,
                    body_preview TEXT,
                    is_all_day INTEGER,
                    source TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # Add source column if it doesn't exist (migration for existing databases)
            try:
                cursor.execute('ALTER TABLE appointments ADD COLUMN source TEXT')
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Create indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_start_time 
                ON appointments(start_time)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_source 
                ON appointments(source)
            ''')
            
            # Create composite index for common queries (subject + source + start_time)
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_subject_source_time 
                ON appointments(subject, source, start_time)
            ''')
            
            # Create index for end_time (used in date range queries)
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_end_time 
                ON appointments(end_time)
            ''')
            
            # Create ignored_base_ids table (for ignoring entire recurring series)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ignored_base_ids (
                    base_id TEXT PRIMARY KEY,
                    subject TEXT,
                    ignored_at TEXT,
                    reason TEXT
                )
            ''')
            
            # Create ignored_event_ids table (for ignoring specific occurrences)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ignored_event_ids (
                    event_id TEXT PRIMARY KEY,
                    subject TEXT,
                    start_time TEXT,
                    ignored_at TEXT,
                    reason TEXT
                )
            ''')
            
            conn.commit()
    
    def find_duplicate(self, subject: str, start_time: str, organizer_email: str, source: str, exclude_id: Optional[str] = None) -> Optional[str]:
        """Find duplicate event by subject, start_time, and organizer_email."""
        try:
            start_dt = parse_iso_datetime(start_time)
            if not start_dt:
                return None
            
            start_utc = normalize_to_utc(start_dt)
            # Calculate time window (1 minute before and after)
            time_window_start = (start_utc - timedelta(seconds=60)).isoformat()
            time_window_end = (start_utc + timedelta(seconds=60)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Optimized query: filter by subject, source, and time window in SQL
                # Then check exact time match and organizer_email in Python
                if exclude_id:
                    cursor.execute('''
                        SELECT id, start_time, organizer_email FROM appointments 
                        WHERE subject = ? AND source = ? 
                        AND start_time >= ? AND start_time <= ?
                        AND id != ?
                    ''', (subject, source, time_window_start, time_window_end, exclude_id))
                else:
                    cursor.execute('''
                        SELECT id, start_time, organizer_email FROM appointments 
                        WHERE subject = ? AND source = ? 
                        AND start_time >= ? AND start_time <= ?
                    ''', (subject, source, time_window_start, time_window_end))
                
                for row_id, row_start_time, row_org_email in cursor.fetchall():
                    if row_id == exclude_id:
                        continue
                    
                    row_start_dt = parse_iso_datetime(row_start_time)
                    if not row_start_dt:
                        continue
                    
                    row_start_utc = normalize_to_utc(row_start_dt)
                    
                    # Check if times match within 1 minute
                    time_diff = abs((start_utc - row_start_utc).total_seconds())
                    if time_diff < 60:
                        # Check organizer_email
                        if (organizer_email or '') == (row_org_email or ''):
                            return row_id
                
                return None
        except Exception as e:
            logger.warning(f"Error finding duplicate: {e}")
            return None
    
    def save_appointments(self, appointments: List[Dict[str, Any]], deduplication_rules: Optional[Dict[str, Any]] = None) -> Tuple[int, int]:
        """Save appointments to database with deduplication."""
        if not appointments:
            return (0, 0)
        
        saved_count = 0
        updated_count = 0
        
        deduplication_rules = deduplication_rules or {}
        skip_same_source = deduplication_rules.get('skip_same_source', False)
        precedence = deduplication_rules.get('precedence', {})
        current_source = deduplication_rules.get('source', '')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            
            for event_data in appointments:
                if not event_data:
                    continue
                
                event_id = event_data.get('id')
                if not event_id:
                    continue
                
                # Check if event already exists
                cursor.execute('SELECT id, source FROM appointments WHERE id = ?', (event_id,))
                existing = cursor.fetchone()
                
                if existing:
                    existing_id, existing_source = existing
                    # Check precedence rules
                    if current_source and existing_source:
                        current_precedence = precedence.get(current_source, 0)
                        existing_precedence = precedence.get(existing_source, 0)
                        
                        if current_precedence < existing_precedence:
                            # Current source has lower precedence, skip
                            continue
                        elif current_precedence > existing_precedence:
                            # Current source has higher precedence, update
                            pass
                        elif skip_same_source and current_source == existing_source:
                            # Same source, skip if skip_same_source is True
                            continue
                    
                    # Update existing record
                    cursor.execute('''
                        UPDATE appointments
                        SET subject = ?, start_time = ?, end_time = ?, location = ?,
                            organizer_email = ?, organizer_name = ?, attendees = ?,
                            body_preview = ?, is_all_day = ?, source = ?, updated_at = ?
                        WHERE id = ?
                    ''', (
                        event_data.get('subject', ''),
                        event_data.get('start_time', ''),
                        event_data.get('end_time', ''),
                        event_data.get('location', ''),
                        event_data.get('organizer_email', ''),
                        event_data.get('organizer_name', ''),
                        event_data.get('attendees', '[]'),
                        event_data.get('body_preview', ''),
                        event_data.get('is_all_day', 0),
                        event_data.get('source', ''),
                        now,
                        event_id
                    ))
                    updated_count += 1
                else:
                    # Check for duplicates by subject/start/organizer
                    duplicate_id = self.find_duplicate(
                        event_data.get('subject', ''),
                        event_data.get('start_time', ''),
                        event_data.get('organizer_email', ''),
                        event_data.get('source', ''),
                        exclude_id=event_id
                    )
                    
                    if duplicate_id:
                        # Check precedence
                        cursor.execute('SELECT source FROM appointments WHERE id = ?', (duplicate_id,))
                        dup_source = cursor.fetchone()
                        dup_source = dup_source[0] if dup_source else ''
                        
                        if current_source and dup_source:
                            current_precedence = precedence.get(current_source, 0)
                            dup_precedence = precedence.get(dup_source, 0)
                            
                            if current_precedence < dup_precedence:
                                # Lower precedence, skip
                                continue
                            elif current_precedence > dup_precedence:
                                # Higher precedence, update the duplicate
                                cursor.execute('''
                                    UPDATE appointments
                                    SET subject = ?, start_time = ?, end_time = ?, location = ?,
                                        organizer_email = ?, organizer_name = ?, attendees = ?,
                                        body_preview = ?, is_all_day = ?, source = ?, updated_at = ?
                                    WHERE id = ?
                                ''', (
                                    event_data.get('subject', ''),
                                    event_data.get('start_time', ''),
                                    event_data.get('end_time', ''),
                                    event_data.get('location', ''),
                                    event_data.get('organizer_email', ''),
                                    event_data.get('organizer_name', ''),
                                    event_data.get('attendees', '[]'),
                                    event_data.get('body_preview', ''),
                                    event_data.get('is_all_day', 0),
                                    event_data.get('source', ''),
                                    now,
                                    duplicate_id
                                ))
                                updated_count += 1
                                continue
                            elif skip_same_source and current_source == dup_source:
                                # Same source, skip
                                continue
                        else:
                            # No precedence rules or same precedence, skip duplicate
                            continue
                    
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO appointments 
                        (id, subject, start_time, end_time, location, organizer_email, 
                         organizer_name, attendees, body_preview, is_all_day, source, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event_id,
                        event_data.get('subject', ''),
                        event_data.get('start_time', ''),
                        event_data.get('end_time', ''),
                        event_data.get('location', ''),
                        event_data.get('organizer_email', ''),
                        event_data.get('organizer_name', ''),
                        event_data.get('attendees', '[]'),
                        event_data.get('body_preview', ''),
                        event_data.get('is_all_day', 0),
                        event_data.get('source', ''),
                        now,
                        now
                    ))
                    saved_count += 1
            
            conn.commit()
        
        return (saved_count, updated_count)
    
    def save_appointments_batch(self, appointments: List[Dict[str, Any]], deduplication_rules: Optional[Dict[str, Any]] = None) -> Tuple[int, int]:
        """Save appointments in batch for better performance."""
        return self.save_appointments(appointments, deduplication_rules)
    
    def query_events(self, days_back: int = 0, days_ahead: int = 30, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query events from database."""
        now = datetime.now(timezone.utc)
        # Use date-only strings for SQL comparison to avoid timezone offset issues
        # SQLite string comparison fails with mixed timezone offsets (e.g., -08:00 vs +00:00)
        start_date = (now - timedelta(days=days_back)).date()
        end_date = (now + timedelta(days=days_ahead)).date()
        
        # Get ignored base IDs and specific event IDs
        ignored_base_ids = self.get_ignored_base_ids()
        ignored_event_ids = self.get_ignored_event_ids()
        
        # Use date-only strings (YYYY-MM-DD) for reliable comparison
        start_date_str = start_date.isoformat()
        end_date_str = (end_date + timedelta(days=1)).isoformat()  # Include full end day
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query using date prefix comparison (works regardless of timezone offset in stored times)
            # This ensures we get all events that START on or after start_date and START before end_date+1
            query = '''
                SELECT * FROM appointments 
                WHERE substr(start_time, 1, 10) >= ? AND substr(start_time, 1, 10) < ?
            '''
            params = [start_date_str, end_date_str]
            
            if source:
                query += ' AND source = ?'
                params.append(source)
            
            query += ' ORDER BY start_time ASC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                # Check if event is ignored (by base ID or specific event ID)
                event_id = row['id']
                if event_id in ignored_event_ids:
                    continue
                base_id = self.get_base_id_from_event_id(event_id)
                if base_id in ignored_base_ids:
                    continue
                
                events.append({
                    'id': event_id,
                    'subject': row['subject'],
                    'start_time': row['start_time'],
                    'end_time': row['end_time'],
                    'location': row['location'] or '',
                    'organizer_email': row['organizer_email'] or '',
                    'organizer_name': row['organizer_name'] or '',
                    'attendees': row['attendees'] or '[]',
                    'body_preview': row['body_preview'] or '',
                    'is_all_day': row['is_all_day'],
                    'source': row['source'] or ''
                })
            
            return events
    
    def get_ignored_base_ids(self) -> set:
        """Get set of ignored base IDs."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT base_id FROM ignored_base_ids')
            return {row[0] for row in cursor.fetchall()}
    
    def get_ignored_base_ids_list(self) -> List[Dict[str, Any]]:
        """Get list of ignored base IDs with details."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT base_id, subject, ignored_at FROM ignored_base_ids ORDER BY ignored_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def add_ignored_base_id(self, base_id: str, subject: str, reason: str = 'User ignored') -> None:
        """Add a base ID to the ignored list."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute('''
                INSERT OR REPLACE INTO ignored_base_ids (base_id, subject, ignored_at, reason)
                VALUES (?, ?, ?, ?)
            ''', (base_id, subject, now, reason))
            conn.commit()
    
    def remove_ignored_base_id(self, base_id: str) -> None:
        """Remove a base ID from the ignored list."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM ignored_base_ids WHERE base_id = ?', (base_id,))
            conn.commit()
    
    def get_ignored_event_ids(self) -> set:
        """Get set of ignored specific event IDs."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT event_id FROM ignored_event_ids')
            return {row[0] for row in cursor.fetchall()}
    
    def get_ignored_event_ids_list(self) -> List[Dict[str, Any]]:
        """Get list of ignored specific event IDs with details."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT event_id, subject, start_time, ignored_at FROM ignored_event_ids ORDER BY ignored_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def add_ignored_event_id(self, event_id: str, subject: str, start_time: str, reason: str = 'User ignored') -> None:
        """Add a specific event ID to the ignored list."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute('''
                INSERT OR REPLACE INTO ignored_event_ids (event_id, subject, start_time, ignored_at, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (event_id, subject, start_time, now, reason))
            conn.commit()
    
    def remove_ignored_event_id(self, event_id: str) -> None:
        """Remove a specific event ID from the ignored list."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM ignored_event_ids WHERE event_id = ?', (event_id,))
            conn.commit()
    
    def get_base_id_from_event_id(self, event_id: str) -> str:
        """Extract base ID from event ID (handles {base_id}_{timestamp} format)."""
        if '_' in event_id:
            parts = event_id.split('_')
            if len(parts) >= 2:
                last_part = parts[-1]
                # Check if last part is a timestamp (YYYYMMDDTHHMMSS format, e.g., 20251201T150000)
                # Format: 8 digits + 'T' + 6 digits = 15 chars total
                if len(last_part) == 15 and last_part[8] == 'T' and last_part[:8].isdigit() and last_part[9:].isdigit():
                    return '_'.join(parts[:-1])
        return event_id
