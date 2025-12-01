#!/usr/bin/env python3
"""
Unified Timezone Handling Utilities

Provides consistent timezone conversion and parsing across all sync scripts.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    from zoneinfo import ZoneInfo
    _pytz = None  # Not needed
except ImportError:
    # Fallback for Python < 3.9
    try:
        from backports.zoneinfo import ZoneInfo
        _pytz = None  # Not needed
    except ImportError:
        ZoneInfo = None
        try:
            import pytz as _pytz
        except ImportError:
            _pytz = None


def normalize_to_utc(dt: datetime) -> datetime:
    """
    Normalize any datetime to UTC.
    
    Args:
        dt: Datetime object (timezone-aware or naive)
    
    Returns:
        Timezone-aware datetime in UTC
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_iso_datetime(iso_str: str) -> Optional[datetime]:
    """
    Parse ISO8601 string to timezone-aware datetime.
    
    Handles multiple formats:
    - '2025-12-01T15:00:00Z' (UTC)
    - '2025-12-01T15:00:00+00:00' (UTC with offset)
    - '2025-12-01T15:00:00-08:00' (PST)
    - '2025-12-01T15:00:00' (naive - assumes UTC)
    
    Args:
        iso_str: ISO8601 formatted datetime string
    
    Returns:
        Timezone-aware datetime, or None if parsing fails
    """
    if not iso_str:
        return None
    
    try:
        # Handle 'Z' suffix (UTC indicator)
        if iso_str.endswith('Z'):
            iso_str = iso_str.replace('Z', '+00:00')
        
        # Parse ISO8601 string
        dt = datetime.fromisoformat(iso_str)
        
        # Ensure timezone-aware (assume UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt
    except (ValueError, AttributeError) as e:
        return None


def format_iso_datetime(dt: datetime, preserve_timezone: bool = False) -> str:
    """
    Format datetime to ISO8601 string.
    
    Args:
        dt: Datetime object
        preserve_timezone: If True, preserve original timezone; if False, convert to UTC
    
    Returns:
        ISO8601 formatted string
    """
    if preserve_timezone:
        return dt.isoformat()
    else:
        # Convert to UTC and format
        utc_dt = normalize_to_utc(dt)
        return utc_dt.isoformat()


def compare_datetimes(dt1: datetime, dt2: datetime, tolerance_seconds: int = 60) -> bool:
    """
    Compare two datetimes with tolerance.
    
    Args:
        dt1: First datetime
        dt2: Second datetime
        tolerance_seconds: Maximum difference in seconds to consider equal
    
    Returns:
        True if datetimes are within tolerance, False otherwise
    """
    dt1_utc = normalize_to_utc(dt1)
    dt2_utc = normalize_to_utc(dt2)
    
    time_diff = abs((dt1_utc - dt2_utc).total_seconds())
    return time_diff < tolerance_seconds


def get_date_range(days_back: int = 0, days_forward: int = 30) -> tuple[datetime, datetime]:
    """
    Get date range for querying events.
    
    Args:
        days_back: Number of days to look back
        days_forward: Number of days to look forward
    
    Returns:
        Tuple of (start_date, end_date) in UTC
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days_back)
    end_date = now + timedelta(days=days_forward)
    return (start_date, end_date)


def normalize_to_pacific(dt: datetime) -> datetime:
    """
    Normalize datetime to Pacific timezone (America/Los_Angeles).
    
    This function handles DST correctly and is useful for fixing timezone issues
    in iCloud ICS feeds where events may have incorrect timezone offsets.
    
    The function:
    1. If datetime is naive, assumes it's already in Pacific timezone and attaches Pacific tzinfo
    2. If datetime has timezone info, converts it to Pacific timezone (handles DST correctly)
    
    Args:
        dt: Datetime object (timezone-aware or naive)
    
    Returns:
        Timezone-aware datetime in Pacific timezone (PST/PDT as appropriate)
    
    Raises:
        RuntimeError: If neither zoneinfo nor pytz is available
    """
    if ZoneInfo:
        pacific_tz = ZoneInfo('America/Los_Angeles')
        # If naive, assume it's already in Pacific timezone
        if dt.tzinfo is None:
            return dt.replace(tzinfo=pacific_tz)
        # Convert to Pacific timezone (handles DST correctly)
        return dt.astimezone(pacific_tz)
    elif _pytz:
        # Fallback to pytz if zoneinfo not available
        pacific_tz = _pytz.timezone('America/Los_Angeles')
        # If naive, assume it's already in Pacific timezone
        if dt.tzinfo is None:
            return pacific_tz.localize(dt)
        # Convert to Pacific timezone
        return dt.astimezone(pacific_tz)
    else:
        # No timezone library available - return with fixed UTC-8 offset as last resort
        # Note: This does NOT handle DST correctly
        from datetime import timezone as tz
        pst_offset = tz(timedelta(hours=-8))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=pst_offset)
        return dt.astimezone(pst_offset)

