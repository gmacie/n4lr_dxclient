# grid_utils.py - Maidenhead grid locator utilities

def grid_to_latlon(grid):
    """
    Convert Maidenhead grid square to latitude/longitude.
    
    Supports 4-character (AA00) or 6-character (AA00aa) grids.
    Returns (latitude, longitude) as floats in degrees.
    
    Examples:
        grid_to_latlon("EM50") -> (30.0, -90.0)
        grid_to_latlon("EM50vb") -> (30.229, -89.958)
    """
    grid = grid.strip().upper()
    
    # Validate grid format
    if len(grid) not in (4, 6):
        raise ValueError(f"Grid must be 4 or 6 characters, got: {grid}")
    
    # Field (first 2 characters: AA)
    if not grid[0:2].isalpha():
        raise ValueError(f"First 2 characters must be letters: {grid}")
    
    lon_field = (ord(grid[0]) - ord('A')) * 20 - 180
    lat_field = (ord(grid[1]) - ord('A')) * 10 - 90
    
    # Square (next 2 characters: 00)
    if not grid[2:4].isdigit():
        raise ValueError(f"Characters 3-4 must be digits: {grid}")
    
    lon_square = int(grid[2]) * 2
    lat_square = int(grid[3]) * 1
    
    # Start with field + square (gives SW corner of square)
    lon = lon_field + lon_square
    lat = lat_field + lat_square
    
    if len(grid) == 4:
        # For 4-char grid, return center of the square
        lon += 1.0  # Center of 2° square
        lat += 0.5  # Center of 1° square
    else:
        # Subsquare (last 2 characters: aa)
        if not grid[4:6].isalpha():
            raise ValueError(f"Characters 5-6 must be letters: {grid}")
        
        lon_subsquare = (ord(grid[4]) - ord('A')) * (2.0 / 24.0)
        lat_subsquare = (ord(grid[5]) - ord('A')) * (1.0 / 24.0)
        
        lon += lon_subsquare
        lat += lat_subsquare
        
        # For 6-char grid, return center of subsquare
        lon += (2.0 / 24.0) / 2.0  # Center of subsquare
        lat += (1.0 / 24.0) / 2.0
    
    return (lat, lon)


def latlon_to_grid(lat, lon, precision=4):
    """
    Convert latitude/longitude to Maidenhead grid square.
    
    Args:
        lat: Latitude in degrees (-90 to 90)
        lon: Longitude in degrees (-180 to 180)
        precision: 4 or 6 character grid (default: 4)
    
    Returns:
        Grid square string (e.g., "EM50" or "EM50vb")
    """
    if not -90 <= lat <= 90:
        raise ValueError(f"Latitude must be -90 to 90, got: {lat}")
    if not -180 <= lon <= 180:
        raise ValueError(f"Longitude must be -180 to 180, got: {lon}")
    if precision not in (4, 6):
        raise ValueError(f"Precision must be 4 or 6, got: {precision}")
    
    # Adjust to 0-based
    adj_lat = lat + 90
    adj_lon = lon + 180
    
    # Field (18° lon × 10° lat)
    field_lon = int(adj_lon / 20)
    field_lat = int(adj_lat / 10)
    
    # Square (2° lon × 1° lat)
    square_lon = int((adj_lon - field_lon * 20) / 2)
    square_lat = int((adj_lat - field_lat * 10) / 1)
    
    grid = chr(ord('A') + field_lon) + chr(ord('A') + field_lat)
    grid += str(square_lon) + str(square_lat)
    
    if precision == 6:
        # Subsquare (5' lon × 2.5' lat = 2°/24 × 1°/24)
        subsquare_lon = int((adj_lon - field_lon * 20 - square_lon * 2) / (2.0 / 24.0))
        subsquare_lat = int((adj_lat - field_lat * 10 - square_lat * 1) / (1.0 / 24.0))
        
        # Clamp to valid range (0-23)
        subsquare_lon = max(0, min(23, subsquare_lon))
        subsquare_lat = max(0, min(23, subsquare_lat))
        
        grid += chr(ord('a') + subsquare_lon) + chr(ord('a') + subsquare_lat)
    
    return grid


def validate_grid(grid):
    """
    Validate a Maidenhead grid square format.
    
    Returns (is_valid, error_message)
    """
    grid = grid.strip()
    
    if len(grid) not in (4, 6):
        return (False, "Grid must be 4 or 6 characters")
    
    if not grid[0:2].isalpha() or not grid[0:2].isupper():
        return (False, "First 2 characters must be uppercase letters (A-R)")
    
    if not grid[2:4].isdigit():
        return (False, "Characters 3-4 must be digits (0-9)")
    
    if len(grid) == 6:
        if not grid[4:6].isalpha():
            return (False, "Characters 5-6 must be letters (a-x)")
        if not grid[4:6].islower():
            return (False, "Characters 5-6 must be lowercase letters")
    
    # Validate field ranges
    if ord(grid[0]) > ord('R') or ord(grid[1]) > ord('R'):
        return (False, "Field letters must be A-R")
    
    if len(grid) == 6:
        if ord(grid[4]) > ord('x') or ord(grid[5]) > ord('x'):
            return (False, "Subsquare letters must be a-x")
    
    return (True, "")


if __name__ == "__main__":
    # Test the functions
    print("Grid to Lat/Lon tests:")
    test_grids = ["EM50", "EM50vb", "FN31", "JO01", "AA00"]
    
    for g in test_grids:
        try:
            lat, lon = grid_to_latlon(g)
            print(f"  {g:8s} -> ({lat:7.3f}, {lon:8.3f})")
            
            # Convert back
            grid4 = latlon_to_grid(lat, lon, precision=4)
            grid6 = latlon_to_grid(lat, lon, precision=6)
            print(f"           -> {grid4} / {grid6}")
        except Exception as e:
            print(f"  {g:8s} -> ERROR: {e}")
    
    print("\nValidation tests:")
    test_validate = ["EM50", "EM50vb", "em50", "EM5", "EM500", "XM50"]
    for g in test_validate:
        valid, msg = validate_grid(g)
        status = "✓" if valid else "✗"
        print(f"  {status} {g:8s} - {msg if not valid else 'OK'}")
