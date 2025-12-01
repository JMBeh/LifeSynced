#!/bin/bash
# Launcher script for LifeSynced Calendar Sync
# Ensures the correct Python environment is used

cd "$(dirname "$0")"
exec /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 sync_calendar.py "$@"
