"""
LoTW Challenge Data Download and Parser
Downloads DXCC credits from LoTW and parses into challenge_data.json
Supports incremental updates using qso_qslsince parameter
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import re
import time

from backend.file_paths import get_challenge_data_file

def download_challenge_qsos(username, password, since_date=None, start_date=None, callsign=None, progress_callback=None):
    """
    Download Challenge confirmations from LoTW
    
    Args:
        username: LoTW username
        password: LoTW password
        since_date: Optional YYYY-MM-DD for incremental update
        start_date: Optional YYYY-MM-DD for earliest QSO date
        callsign: Optional callsign filter (e.g., N4LR)
        progress_callback: Optional function(message: str) to report progress
        
    Returns:
        tuple: (success, adif_text or error_message)
    """
    
    # Build URL for LoTW DXCC credits download
    url = "https://lotw.arrl.org/lotwuser/lotwreport.adi"
    
    params = {
        "login": username,
        "password": password,
        "qso_query": "1",
        "qso_qsl": "yes",  # Only confirmed QSOs
        "qso_qsldetail": "yes",  # Include details
    }
    
    # Add callsign filter if provided
    if callsign:
        params["qso_mydetail"] = "yes"  # Include station details
        params["qso_owncall"] = callsign
        print(f"Filtering for callsign: {callsign}")
    
    # Add start date if provided
    if start_date:
        params["qso_startdate"] = start_date
        print(f"Starting from date: {start_date}")
    
    # Add incremental update parameter if provided
    if since_date:
        params["qso_qslsince"] = since_date
        print(f"Downloading Challenge data since {since_date}...")
        if progress_callback:
            progress_callback(f"Downloading updates since {since_date}...")
            time.sleep(0.5)
    else:
        print("Downloading full Challenge data (first time)...")
        if progress_callback:
            progress_callback("Downloading Challenge data (this may take 1-2 minutes)...")
            time.sleep(0.5)
    
    try:
        # Debug: show the full URL
        from urllib.parse import urlencode
        full_url = f"{url}?{urlencode(params)}"
        print(f"\nAPI URL: {full_url}\n")
        
        if progress_callback:
            progress_callback("Connecting to LoTW...")
            time.sleep(0.5)
        
        # Make request with streaming
        if progress_callback:
            progress_callback("Downloading...")
            time.sleep(0.5)
        
        response = requests.get(url, params=params, timeout=300, stream=True)
        
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        
        # Download with progress tracking
        chunks = []
        downloaded_bytes = 0
        last_update = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                chunks.append(chunk)
                downloaded_bytes += len(chunk)
                
                # Update progress every 500KB (more frequent for larger file)
                if progress_callback and downloaded_bytes - last_update > 500000:
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
        
        # Check if response is HTML (error page)
        if text.strip().startswith('<html'):
            return False, "Authentication failed or LoTW error"
        
        return True, text
        
    except requests.exceptions.Timeout:
        return False, "Download timeout (try again)"
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}"


def parse_challenge_adif(adif_text, existing_data=None):
    """
    Parse ADIF text and extract Challenge data (all bands including 60m)
    Tracks BOTH confirmed (QSL_RCVD=Y) and credited (CREDIT_GRANTED) slots
    
    Args:
        adif_text: ADIF format text
        existing_data: Optional existing challenge data for incremental update
        
    Returns:
        dict: Challenge statistics with both confirmed and credited data
    """
    
    # Start with existing data or empty
    if existing_data:
        confirmed_pairs = set(tuple(pair) for pair in existing_data.get("raw_band_entity_pairs", []))
        credited_pairs = set(tuple(pair) for pair in existing_data.get("credited_band_entity_pairs", []))
    else:
        confirmed_pairs = set()
        credited_pairs = set()
    
    # Parse ADIF records
    # Split by <eor> or <EOR>
    records = re.split(r'<eor>|<EOR>', adif_text, flags=re.IGNORECASE)
    
    new_confirmed = 0
    new_credited = 0
    
    for record in records:
        if not record.strip():
            continue
        
        # Extract fields using regex
        fields = {}
        for match in re.finditer(r'<([^:>]+):(\d+)(?::([^>]+))?>([^<]*)', record, re.IGNORECASE):
            field_name = match.group(1).upper()
            field_value = match.group(4).strip()
            fields[field_name] = field_value
        
        # Need BAND and DXCC
        band = fields.get('BAND', '').upper()
        dxcc = fields.get('DXCC', '')
        qsl_rcvd = fields.get('QSL_RCVD', '').upper()
        credit_granted = fields.get('CREDIT_GRANTED', '').upper()
        
        # Only count confirmed QSOs
        if qsl_rcvd != 'Y':
            continue
        
        if not band or not dxcc:
            continue
        
        # Filter out invalid DXCC entities
        try:
            dxcc_int = int(dxcc)
            # DXCC 0 = Maritime Mobile, negative = invalid
            # Valid DXCC range is 1-999
            if dxcc_int <= 0 or dxcc_int > 999:
                continue
        except ValueError:
            continue  # Not a valid integer
        
        # Normalize band names
        band_map = {
            '160M': '160M',
            '80M': '80M',
            '60M': '60M',
            '40M': '40M',
            '30M': '30M',
            '20M': '20M',
            '17M': '17M',
            '15M': '15M',
            '12M': '12M',
            '10M': '10M',
            '6M': '6M',
        }
        
        band = band_map.get(band, band)
        
        # Add to confirmed set (QSL_RCVD = Y)
        pair = (band, int(dxcc))
        if pair not in confirmed_pairs:
            new_confirmed += 1
        confirmed_pairs.add(pair)
        
        # Add to credited set if CREDIT_GRANTED exists
        if credit_granted and credit_granted != '':
            if pair not in credited_pairs:
                new_credited += 1
            credited_pairs.add(pair)
    
    print(f"Found {new_confirmed} new confirmed band/entity pairs")
    print(f"Found {new_credited} new credited band/entity pairs")
    print(f"Total confirmed pairs: {len(confirmed_pairs)}")
    print(f"Total credited pairs: {len(credited_pairs)}")
    
    # Count entities by band for CONFIRMED
    confirmed_entities_by_band = {}
    confirmed_unique_entities = set()
    
    for band, dxcc in confirmed_pairs:
        if band not in confirmed_entities_by_band:
            confirmed_entities_by_band[band] = set()
        confirmed_entities_by_band[band].add(dxcc)
        confirmed_unique_entities.add(dxcc)
    
    # Count entities by band for CREDITED
    credited_entities_by_band = {}
    credited_unique_entities = set()
    
    for band, dxcc in credited_pairs:
        if band not in credited_entities_by_band:
            credited_entities_by_band[band] = set()
        credited_entities_by_band[band].add(dxcc)
        credited_unique_entities.add(dxcc)
    
    # Convert sets to counts
    confirmed_entities_by_band = {band: len(entities) for band, entities in confirmed_entities_by_band.items()}
    credited_entities_by_band = {band: len(entities) for band, entities in credited_entities_by_band.items()}
    
    # Build result
    result = {
        # Confirmed data (QSL_RCVD = Y) - used for highlighting
        "total_entities": len(confirmed_unique_entities),
        "total_challenge_slots": len(confirmed_pairs),
        "entities_by_band": confirmed_entities_by_band,
        "raw_band_entity_pairs": list(confirmed_pairs),
        
        # Credited data (CREDIT_GRANTED) - for comparison with LoTW
        "credited_total_entities": len(credited_unique_entities),
        "credited_total_slots": len(credited_pairs),
        "credited_entities_by_band": credited_entities_by_band,
        "credited_band_entity_pairs": list(credited_pairs),
        
        "last_updated": datetime.now().isoformat(),
    }
    
    return result

def save_challenge_data(data, filename=None):    
    """Save challenge data to JSON file"""
    if filename is None:
        from backend.file_paths import get_challenge_data_file
        filename = get_challenge_data_file()
        
    try:
        Path(filename).write_text(json.dumps(data, indent=2))
        print(f"Saved challenge data to {filename}")
        return True
    except Exception as e:
        print(f"Error saving challenge data: {e}")
        return False


def download_and_parse_challenge(username, password, since_date=None, start_date="2000-01-01", callsign=None, progress_callback=None):
    """
    Complete workflow: download from LoTW and parse Challenge data
    
    Args:
        username: LoTW username
        password: LoTW password
        since_date: Optional YYYY-MM-DD for incremental update
        start_date: Optional YYYY-MM-DD for earliest QSO date (default: 2000-01-01)
        callsign: Optional callsign filter (e.g., N4LR)
        progress_callback: Optional function to report progress
        
    Returns:
        tuple: (success, result_dict or error_message)
    """
    
    # Download from LoTW
    success, result = download_challenge_qsos(username, password, since_date, start_date, callsign, progress_callback=progress_callback)
    
    if not success:
        return False, result
    
    adif_text = result
    
    # Save raw ADIF for debugging
    try:
        Path("lotwreport_challenge.adi").write_text(adif_text)
        print("Saved raw ADIF to lotwreport_challenge.adi")
    except:
        pass
    
    # Load existing data for incremental update
    existing_data = None
    if since_date:
        
        challenge_file = get_challenge_data_file()
        if challenge_file.exists():
            try:
                existing_data = json.loads(challenge_file.read_text())
                print(f"Loaded existing data: {existing_data.get('total_challenge_slots', 0)} slots")
            except:
                print("Could not load existing data, doing full parse")
    
    # Parse ADIF
    if progress_callback:
        progress_callback("Parsing Challenge data...")
        time.sleep(0.5)
    
    challenge_data = parse_challenge_adif(adif_text, existing_data)
    
    # Save to file
    if save_challenge_data(challenge_data):
        if progress_callback:
            entities = challenge_data.get('total_entities', 0)
            slots = challenge_data.get('total_challenge_slots', 0)
            progress_callback(f"Complete! {entities} entities, {slots} slots")
            time.sleep(0.5)
        
        return True, challenge_data
    else:
        return False, "Failed to save challenge data"


if __name__ == "__main__":
    # Test
    print("Challenge Data Download Test")
    print("=" * 50)
    
    # You would need to provide credentials
    username = input("LoTW Username: ").strip()
    password = input("LoTW Password: ").strip()
    callsign = input("Filter by callsign (e.g., N4LR, or press Enter for all): ").strip().upper() or None
    start_date = input("Start date (YYYY-MM-DD, or press Enter for 2000-01-01): ").strip() or "2000-01-01"
    
    if username and password:
        success, result = download_and_parse_challenge(username, password, None, start_date, callsign)
        
        if success:
            print("\nSuccess!")
            print(f"Total Entities: {result['total_entities']}")
            print(f"Total Slots: {result['total_challenge_slots']}")
            print(f"\nBand breakdown:")
            for band, count in sorted(result['entities_by_band'].items()):
                print(f"  {band}: {count}")
        else:
            print(f"\nError: {result}")