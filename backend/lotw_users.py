# lotw_users.py - LoTW user activity lookup
"""
Downloads and caches LoTW user activity data.
Checks if callsigns are LoTW users and when they last uploaded.
"""

import requests
from datetime import datetime, timedelta
from pathlib import Path
import json

LOTW_URL = "https://lotw.arrl.org/lotw-user-activity.csv"
LOTW_FALLBACK_URL = "https://www.hb9bza.net/lotw/lotw-user-activity.csv"
CACHE_FILE = Path("lotw_users.json")
CACHE_DAYS = 7  # Refresh weekly

# Global cache: callsign -> last_upload_date
_lotw_users = {}
_last_loaded = None


def download_lotw_users():
    """Download LoTW user activity CSV from ARRL (with HB9BZA fallback)"""
    print("Downloading LoTW user activity data...")
    
    text = None
    
    # Try ARRL first
    try:
        print("Trying ARRL primary source...")
        response = requests.get(LOTW_URL, timeout=30, headers={"User-Agent": "N4LR_DXClient/1.0"})
        response.raise_for_status()
        
        text = response.text.strip()
        
        # Guard against HTML error pages
        if text.lower().startswith("<!doctype") or "<html" in text.lower():
            raise Exception("ARRL returned HTML instead of CSV")
        
        print("Successfully downloaded from ARRL")
        
    except Exception as e:
        print(f"ARRL download failed: {e}")
        print("Trying HB9BZA fallback mirror...")
        
        try:
            response = requests.get(LOTW_FALLBACK_URL, timeout=30, headers={"User-Agent": "N4LR_DXClient/1.0"})
            response.raise_for_status()
            
            text = response.text.strip()
            
            if text.lower().startswith("<!doctype") or "<html" in text.lower():
                raise Exception("Fallback returned HTML instead of CSV")
            
            print("Successfully downloaded from HB9BZA mirror")
            
        except Exception as e2:
            print(f"ERROR: Both sources failed! ARRL: {e}, HB9BZA: {e2}")
            return None
    
    # Parse the CSV (runs after either source succeeds)
    if not text:
        return None
    
    lines = text.splitlines()
    if len(lines) < 2:
        print("ERROR: LoTW CSV is empty")
        return None
    
    # Detect delimiter (, or ;)
    delimiter = ";" if ";" in lines[0] else ","
    
    users = {}
    for line in lines[1:]:  # Skip header
        parts = [p.strip() for p in line.split(delimiter)]
        if len(parts) >= 2:
            callsign = parts[0].upper()
            date_str = parts[1]  # Format: YYYY-MM-DD
            if callsign and date_str:
                users[callsign] = date_str
    
    print(f"Downloaded {len(users)} LoTW users")
    return users


def save_cache(users):
    """Save users dict to JSON cache"""
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "users": users
        }
        CACHE_FILE.write_text(json.dumps(data, indent=2))
        print(f"SUCCESS: Saved {len(users)} LoTW users to {CACHE_FILE.absolute()}")
    except Exception as e:
        print(f"ERROR saving LoTW cache to {CACHE_FILE.absolute()}: {e}")
        import traceback
        traceback.print_exc()


def load_cache():
    """Load users dict from JSON cache"""
    global _lotw_users, _last_loaded
    
    if not CACHE_FILE.exists():
        # Only print this once, not every time
        if len(_lotw_users) == 0:  # First time checking
            print("No LoTW cache file found - will download on first refresh")
        return False
    
    try:
        data = json.loads(CACHE_FILE.read_text())
        _lotw_users = data.get("users", {})
        timestamp = data.get("timestamp", "")
        
        if timestamp:
            _last_loaded = datetime.fromisoformat(timestamp)
            age_days = (datetime.now() - _last_loaded).days
            print(f"Loaded LoTW cache ({len(_lotw_users)} users, {age_days} days old)")
            return True
        
        return False
    
    except Exception as e:
        print(f"ERROR loading LoTW cache: {e}")
        return False


def refresh_if_needed(force=False):
    """Refresh LoTW user data if cache is old"""
    global _lotw_users, _last_loaded
    
    # Check if refresh needed
    if not force and _last_loaded:
        age = datetime.now() - _last_loaded
        if age.days < CACHE_DAYS:
            return  # Cache is still fresh
    
    # Download fresh data
    users = download_lotw_users()
    if users:
        _lotw_users = users
        _last_loaded = datetime.now()
        save_cache(users)


def is_lotw_user(callsign):
    """Check if callsign is a LoTW user"""
    if not _lotw_users:
        load_cache()
    
    # Remove portable suffixes (/P, /M, /QRP, etc)
    base_call = callsign.upper().split('/')[0]
    
    return base_call in _lotw_users


def get_last_upload(callsign):
    """Get last upload date for callsign (YYYY-MM-DD string or None)"""
    if not _lotw_users:
        load_cache()
    
    # Remove portable suffixes
    base_call = callsign.upper().split('/')[0]
    
    return _lotw_users.get(base_call)


def get_upload_age_days(callsign):
    """Get number of days since last upload (or None if not a user)"""
    last_upload = get_last_upload(callsign)
    if not last_upload:
        return None
    
    try:
        upload_date = datetime.strptime(last_upload, "%Y-%m-%d")
        age = datetime.now() - upload_date
        return age.days
    except:
        return None


def is_active_user(callsign, days=90):
    """Check if user uploaded within specified days (default 90)"""
    age = get_upload_age_days(callsign)
    if age is None:
        return False
    return age <= days


# Load cache on module import
load_cache()


if __name__ == "__main__":
    # Test the module
    print("Testing LoTW user lookup...")
    refresh_if_needed(force=True)
    
    test_calls = ["N4LR", "W1AW", "AA7V", "NOTAUSER"]
    for call in test_calls:
        is_user = is_lotw_user(call)
        last_up = get_last_upload(call)
        age = get_upload_age_days(call)
        active = is_active_user(call)
        
        print(f"{call:12} User: {is_user:5}  Last: {last_up if last_up else 'Never':12}  Age: {age if age else 'N/A':>4} days  Active: {active}")
