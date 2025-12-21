# sun_times.py - Calculate sunrise/sunset times
from datetime import datetime, timezone
from astral import LocationInfo
from astral.sun import sun
from backend.grid_utils import grid_to_latlon


def get_sun_times(grid_square, date=None):
    """
    Calculate sunrise and sunset times for a given grid square.
    
    Args:
        grid_square: Maidenhead grid (4 or 6 char), e.g., "EM50"
        date: datetime object (default: today in local timezone)
    
    Returns:
        dict with keys:
            'sunrise': datetime object (local time)
            'sunset': datetime object (local time)
            'dawn': datetime object (local time)
            'dusk': datetime object (local time)
            'noon': datetime object (local time)
    
    Example:
        times = get_sun_times("EM50")
        print(f"Sunrise: {times['sunrise'].strftime('%H:%M')}")
        print(f"Sunset: {times['sunset'].strftime('%H:%M')}")
    """
    # Convert grid to lat/lon
    lat, lon = grid_to_latlon(grid_square)
    
    # Use today if no date specified
    if date is None:
        date = datetime.now()
    
    # Create location info
    location = LocationInfo(
        name="Station",
        region="",
        timezone="UTC",  # We'll convert to local time
        latitude=lat,
        longitude=lon
    )
    
    # Calculate sun times
    s = sun(location.observer, date=date, tzinfo=timezone.utc)
    
    # Convert to local timezone
    local_tz = datetime.now().astimezone().tzinfo
    
    return {
        'dawn': s['dawn'].astimezone(local_tz),
        'sunrise': s['sunrise'].astimezone(local_tz),
        'noon': s['noon'].astimezone(local_tz),
        'sunset': s['sunset'].astimezone(local_tz),
        'dusk': s['dusk'].astimezone(local_tz),
    }


def format_sun_times(grid_square, time_format="%H:%M"):
    """
    Get formatted sunrise/sunset times as strings.
    
    Args:
        grid_square: Maidenhead grid
        time_format: strftime format string (default: "%H:%M" for 24-hour time)
    
    Returns:
        dict with 'sunrise' and 'sunset' as formatted strings
    
    Example:
        times = format_sun_times("EM50")
        print(f"Sunrise: {times['sunrise']} | Sunset: {times['sunset']}")
    """
    try:
        times = get_sun_times(grid_square)
        return {
            'sunrise': times['sunrise'].strftime(time_format),
            'sunset': times['sunset'].strftime(time_format),
            'dawn': times['dawn'].strftime(time_format),
            'dusk': times['dusk'].strftime(time_format),
            'noon': times['noon'].strftime(time_format),
        }
    except Exception as e:
        return {
            'sunrise': '--:--',
            'sunset': '--:--',
            'dawn': '--:--',
            'dusk': '--:--',
            'noon': '--:--',
            'error': str(e)
        }


def get_daylight_status(grid_square):
    """
    Determine if it's currently day or night at a location.
    
    Args:
        grid_square: Maidenhead grid
    
    Returns:
        str: "day", "night", "dawn", "dusk", or "error"
    """
    try:
        times = get_sun_times(grid_square)
        now = datetime.now().astimezone()
        
        if times['dawn'] <= now < times['sunrise']:
            return "dawn"
        elif times['sunrise'] <= now < times['sunset']:
            return "day"
        elif times['sunset'] <= now < times['dusk']:
            return "dusk"
        else:
            return "night"
    except Exception:
        return "error"


if __name__ == "__main__":
    # Test the functions
    print("Sun times calculator test\n")
    
    test_grids = ["EM50", "FN31", "JO01"]
    
    for grid in test_grids:
        print(f"Grid: {grid}")
        try:
            lat, lon = grid_to_latlon(grid)
            print(f"  Location: {lat:.2f}°, {lon:.2f}°")
            
            times = format_sun_times(grid)
            print(f"  Dawn:    {times['dawn']}")
            print(f"  Sunrise: {times['sunrise']}")
            print(f"  Noon:    {times['noon']}")
            print(f"  Sunset:  {times['sunset']}")
            print(f"  Dusk:    {times['dusk']}")
            
            status = get_daylight_status(grid)
            print(f"  Current: {status}")
            print()
        except Exception as e:
            print(f"  ERROR: {e}\n")
