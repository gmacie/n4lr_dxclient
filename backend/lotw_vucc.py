# lotw_vucc.py - Download VUCC confirmations from LoTW
"""
Downloads confirmed QSOs from LoTW for VUCC/FFMA tracking
Uses LoTW API to get ADIF file with gridsquare confirmations
"""

import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlencode
import time

from backend.file_paths import get_user_data_directory

def download_vucc_qsos(username, password, band="6m", since_date=None, progress_callback=None):
    """
    Download confirmed QSOs from LoTW for a specific band
    
    Args:
        username: LoTW username (usually callsign)
        password: LoTW password
        band: Band to download (e.g., "6m", "2m", "70cm")
        since_date: Optional - only download QSOs confirmed after this date (YYYY-MM-DD)
        progress_callback: Optional function(message: str) to report progress
    
    Returns:
        tuple: (success: bool, adif_text: str or error_message: str)
    """
    
    params = {
        'login': username,
        'password': password,
        'qso_query': '1',
        'qso_qsl': 'yes',
        'qso_qsldetail': 'yes',
        'qso_mydetail': 'yes',
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
    
    if progress_callback:
        progress_callback("Connecting to LoTW...")
        time.sleep(0.5)
    
    try:
        # Make request with streaming
        if progress_callback:
            progress_callback("Downloading...")
            time.sleep(0.5)
        
        response = requests.get(url, timeout=60, stream=True)
        
        # Check for errors
        if response.status_code != 200:
            return False, f"HTTP Error {response.status_code}"
        
        # Download with progress tracking
        chunks = []
        downloaded_bytes = 0
        last_update = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                chunks.append(chunk)
                downloaded_bytes += len(chunk)
                
                # Update progress every 100KB
                if progress_callback and downloaded_bytes - last_update > 100000:
                    mb = downloaded_bytes / 1024 / 1024
                    progress_callback(f"Downloading... {mb:.1f} MB")
                    last_update = downloaded_bytes
        
        # Combine chunks
        text = b''.join(chunks).decode('utf-8')
        
        # Calculate final size and report
        size_kb = len(text) / 1024
        size_mb = size_kb / 1024
        
        if size_mb > 1:
            size_str = f"{size_mb:.1f} MB"
            print(f"Downloaded {size_str}")
            if progress_callback:
                progress_callback(f"Downloaded {size_str}")
                time.sleep(0.5)
        else:
            size_str = f"{size_kb:.1f} KB"
            print(f"Downloaded {size_str}")
            if progress_callback:
                progress_callback(f"Downloaded {size_str}")
                time.sleep(0.5)
        
        # Check if login failed (LoTW returns HTML on auth failure)
        if '<html' in text.lower() or 'login' in text.lower()[:200]:
            return False, "Authentication failed - check username/password"
        
        # Check if we got ADIF data
        if '<CALL:' not in text.upper() and '<EOR>' not in text.upper():
            return False, "No data returned - check credentials or band"
        
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


def download_and_parse_ffma(username, password, progress_callback=None):
    """
    Download 6m VUCC data and parse for FFMA grids
    
    Args:
        username: LoTW username
        password: LoTW password
        progress_callback: Optional function to report progress
    
    Returns:
        tuple: (success: bool, worked_grids: dict or error_message: str)
    """
    
    # Download 6m confirmations
    success, result = download_vucc_qsos(username, password, band="6m", progress_callback=progress_callback)
    
    if not success:
        return False, result
    
    # Save ADIF to user data directory
    adif_file = get_user_data_directory() / "vucc_6m.adi"
    adif_file.write_text(result, encoding='utf-8')
    print(f"Saved to {adif_file}")
    
    # Parse for FFMA grids
    if progress_callback:
        progress_callback("Parsing FFMA grids...")
        time.sleep(0.5)
    
    from backend.ffma_tracking import parse_lotw_adif_for_ffma, save_ffma_data
    
    try:
        worked_grids = parse_lotw_adif_for_ffma(str(adif_file))
        ffma_data = save_ffma_data(worked_grids)
        
        if progress_callback:
            total = len(worked_grids)
            pct = ffma_data.get("completion_pct", 0)
            progress_callback(f"Complete! {total}/488 grids ({pct}%)")
            time.sleep(0.5)
        
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