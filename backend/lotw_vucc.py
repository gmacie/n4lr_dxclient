# lotw_vucc.py - Download VUCC confirmations from LoTW
"""
Downloads confirmed QSOs from LoTW for VUCC/FFMA tracking
Uses LoTW API to get ADIF file with gridsquare confirmations
"""

import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlencode


def download_vucc_qsos(username, password, band="6m", since_date=None):
    """
    Download confirmed QSOs from LoTW for a specific band
    
    Args:
        username: LoTW username (usually callsign)
        password: LoTW password
        band: Band to download (e.g., "6m", "2m", "70cm")
        since_date: Optional - only download QSOs confirmed after this date (YYYY-MM-DD)
    
    Returns:
        tuple: (success: bool, adif_text: str or error_message: str)
    """
    
    # Build query parameters
    #params = {
    #    'login': username,
    #    'password': password,
    #    'qso_qsl': 'yes',  # Only confirmed QSOs
    #    'qso_query': '1',  # Include QSO records
    #    'qso_band': band,
    #    'qso_qslinc': 'yes',
    #    'qso_qsldetail': 'yes'
    #    'qso_mydetail': 'yes',
    #    'qso_qso': 'no',
    #}
    
    params = {
        'login': username,
        'password': password,
        'qso_query': '1',
        'qso_qsl': 'yes',
        'qso_qsldetail': 'yes',  # This might be the one instead of qso_qslinc
        'qso_band': band,
    }
    
    if since_date:
        params['qso_qslsince'] = since_date
    
    # Construct URL
    base_url = "https://lotw.arrl.org/lotwuser/lotwreport.adi"
    url = f"{base_url}?{urlencode(params)}"
    
    print(f"Downloading VUCC data for {band}...")
    print(f"Username: {username}")
    if since_date:
        print(f"Since: {since_date}")
    
    try:
        # Make request
        response = requests.get(url, timeout=60)
        
        # Check for errors
        if response.status_code != 200:
            return False, f"HTTP Error {response.status_code}"
        
        # Check if login failed (LoTW returns HTML on auth failure)
        text = response.text
        if '<html' in text.lower() or 'login' in text.lower()[:200]:
            return False, "Authentication failed - check username/password"
        
        # Check if we got ADIF data
        if '<CALL:' not in text.upper() and '<EOR>' not in text.upper():
            return False, "No data returned - check credentials or band"
        
        print(f"Downloaded {len(text)} bytes")
        return True, text
        
    except requests.Timeout:
        return False, "Connection timeout - LoTW server not responding"
    except requests.RequestException as e:
        return False, f"Network error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def save_vucc_adif(adif_text, filename="vucc_6m.adi"):
    """Save VUCC ADIF data to file"""
    try:
        Path(filename).write_text(adif_text, encoding='utf-8')
        print(f"Saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False


def download_and_parse_ffma(username, password):
    """
    Download 6m VUCC data and parse for FFMA grids
    
    Returns:
        tuple: (success: bool, worked_grids: dict or error_message: str)
    """
    
    # Download 6m confirmations
    success, result = download_vucc_qsos(username, password, band="6m")
    
    if not success:
        return False, result
    
    # Save ADIF
    adif_file = "vucc_6m.adi"
    save_vucc_adif(result, adif_file)
    
    # Parse for FFMA grids
    from backend.ffma_tracking import parse_lotw_adif_for_ffma, save_ffma_data
    
    try:
        worked_grids = parse_lotw_adif_for_ffma(adif_file)
        ffma_data = save_ffma_data(worked_grids)
        
        return True, {
            "worked_grids": worked_grids,
            "total_worked": len(worked_grids),
            "completion_pct": ffma_data.get("completion_pct", 0),
            "last_updated": datetime.now().isoformat(),
        }
        
    except Exception as e:
        return False, f"Error parsing ADIF: {str(e)}"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python lotw_vucc.py <username> <password> [band]")
        print("\nExample:")
        print("  python lotw_vucc.py N4LR mypassword 6m")
        print("\nThis downloads your VUCC confirmations from LoTW")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    band = sys.argv[3] if len(sys.argv) > 3 else "6m"
    
    success, result = download_vucc_qsos(username, password, band)
    
    if success:
        print("\n✓ Download successful!")
        
        # Save it
        filename = f"vucc_{band}.adi"
        save_vucc_adif(result, filename)
        
        # Parse for FFMA if 6m
        if band == "6m":
            print("\nParsing for FFMA grids...")
            from backend.ffma_tracking import parse_lotw_adif_for_ffma, save_ffma_data
            worked = parse_lotw_adif_for_ffma(filename)
            save_ffma_data(worked)
    else:
        print(f"\n✗ Download failed: {result}")
        sys.exit(1)