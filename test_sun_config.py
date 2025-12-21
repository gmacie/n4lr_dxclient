#!/usr/bin/env python3
# test_sun_config.py - Test the new config, grid, and sun modules

print("Testing configuration, grid conversion, and sun times...\n")

# Test 1: Config
print("=" * 60)
print("TEST 1: Configuration")
print("=" * 60)

from backend.config import load_config, save_config, set_user_settings, get_user_callsign, get_user_grid

# Set some test values
print("Setting callsign to N4LR and grid to EM50...")
set_user_settings("N4LR", "EM50")

print(f"Callsign: {get_user_callsign()}")
print(f"Grid: {get_user_grid()}")

config = load_config()
print("\nFull config:")
for section in config.sections():
    print(f"  [{section}]")
    for key, value in config.items(section):
        print(f"    {key} = {value}")

# Test 2: Grid conversion
print("\n" + "=" * 60)
print("TEST 2: Grid Conversion")
print("=" * 60)

from backend.grid_utils import grid_to_latlon, latlon_to_grid, validate_grid

test_grids = ["EM50", "EM50vb", "FN31pr", "JO01"]

for grid in test_grids:
    valid, msg = validate_grid(grid)
    if valid:
        lat, lon = grid_to_latlon(grid)
        print(f"{grid:8s} -> Lat: {lat:7.3f}°  Lon: {lon:8.3f}°")
        # Convert back
        grid4 = latlon_to_grid(lat, lon, precision=4)
        grid6 = latlon_to_grid(lat, lon, precision=6)
        print(f"         <- {grid4} (4-char) / {grid6} (6-char)")
    else:
        print(f"{grid:8s} -> INVALID: {msg}")
    print()

# Test 3: Sun times
print("=" * 60)
print("TEST 3: Sun Times")
print("=" * 60)

from backend.sun_times import get_sun_times, format_sun_times, get_daylight_status

user_grid = get_user_grid()
print(f"Calculating sun times for {user_grid}...")

lat, lon = grid_to_latlon(user_grid)
print(f"Location: {lat:.3f}°, {lon:.3f}°\n")

times = format_sun_times(user_grid)
print(f"Dawn:    {times['dawn']}")
print(f"Sunrise: {times['sunrise']}")
print(f"Noon:    {times['noon']}")
print(f"Sunset:  {times['sunset']}")
print(f"Dusk:    {times['dusk']}")

status = get_daylight_status(user_grid)
print(f"\nCurrent daylight status: {status}")

print("\n" + "=" * 60)
print("All tests complete!")
print("=" * 60)
