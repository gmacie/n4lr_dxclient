# solar.py - 2025-12-30
# Fetch solar data from N0NBH (hamqsl.com)
"""
Fetches real-time solar and geomagnetic data from N0NBH's XML feed.
Currently displays: SFI, A-index, K-index
Future expansion ready for: X-ray, sunspots, aurora, band conditions, etc.
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Optional

# N0NBH Solar XML feed
SOLAR_URL = "http://www.hamqsl.com/solarxml.php"

# Global cache
_solar_data = {
    'sfi': '—',
    'a': '—',
    'k': '—',
    'last_updated': None,
    # Future expansion fields (not displayed yet)
    'xray': None,
    'sunspots': None,
    'aurora': None,
    'band_conditions': {},
}


def fetch_solar_data() -> bool:
    """
    Fetch solar data from N0NBH and update global cache.
    
    Returns:
        bool: True if successful, False otherwise
    """
    global _solar_data
    
    try:
        print(f"Fetching solar data from {SOLAR_URL}...")
        response = requests.get(SOLAR_URL, timeout=10)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.text)
        solar = root.find('solardata')
        
        if solar is None:
            print("ERROR: Could not find solardata in XML")
            return False
        
        # Extract core values (currently displayed)
        sfi = solar.findtext('solarflux', '—')
        a_index = solar.findtext('aindex', '—')
        k_index = solar.findtext('kindex', '—')
        
        # Convert to numbers if possible
        try:
            sfi = float(sfi)
        except (ValueError, TypeError):
            sfi = '—'
        
        try:
            a_index = int(a_index)
        except (ValueError, TypeError):
            a_index = '—'
        
        try:
            k_index = int(k_index)
        except (ValueError, TypeError):
            k_index = '—'
        
        # Update cache
        _solar_data['sfi'] = sfi
        _solar_data['a'] = a_index
        _solar_data['k'] = k_index
        _solar_data['last_updated'] = datetime.now()
        
        # Store additional fields for future use (not displayed yet)
        _solar_data['xray'] = solar.findtext('xray')
        _solar_data['sunspots'] = solar.findtext('sunspots')
        _solar_data['aurora'] = solar.findtext('aurora')
        _solar_data['updated_date'] = solar.findtext('updateddate')
        _solar_data['updated_time'] = solar.findtext('updatedtime')
        
        # Band conditions (for future use)
        _solar_data['band_conditions'] = {
            '80m-40m': solar.findtext('signalnoise'),  # Day/Night
            'calculated_conditions': solar.findtext('calculatedconditions'),
        }
        
        print(f"Solar data updated: SFI={sfi}, A={a_index}, K={k_index}")
        return True
        
    except requests.RequestException as e:
        print(f"Error fetching solar data: {e}")
        return False
    except ET.ParseError as e:
        print(f"Error parsing solar XML: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error in fetch_solar_data: {e}")
        return False


def get_solar_data() -> Dict:
    """
    Get cached solar data.
    
    Returns:
        dict: Solar data with keys: sfi, a, k (and future expansion fields)
    """
    return _solar_data.copy()


def get_sfi() -> str:
    """Get Solar Flux Index"""
    return str(_solar_data['sfi'])


def get_a_index() -> str:
    """Get A-index (geomagnetic activity)"""
    return str(_solar_data['a'])


def get_k_index() -> str:
    """Get K-index (geomagnetic activity)"""
    return str(_solar_data['k'])


# Future expansion functions (not used yet, but ready when needed)
def get_xray() -> Optional[str]:
    """Get X-ray flux level (e.g., 'M1.2', 'C5.3')"""
    return _solar_data.get('xray')


def get_sunspots() -> Optional[str]:
    """Get sunspot number"""
    return _solar_data.get('sunspots')


def get_aurora() -> Optional[str]:
    """Get aurora activity level"""
    return _solar_data.get('aurora')


def get_band_conditions() -> Dict:
    """Get HF band conditions"""
    return _solar_data.get('band_conditions', {})


# For testing
if __name__ == "__main__":
    print("Testing N0NBH solar data fetch...")
    success = fetch_solar_data()
    
    if success:
        data = get_solar_data()
        print("\nCurrent Solar Data:")
        print(f"  SFI: {data['sfi']}")
        print(f"  A-index: {data['a']}")
        print(f"  K-index: {data['k']}")
        print(f"  Last updated: {data['last_updated']}")
        
        print("\nFuture expansion data (not displayed yet):")
        print(f"  X-ray: {data.get('xray')}")
        print(f"  Sunspots: {data.get('sunspots')}")
        print(f"  Aurora: {data.get('aurora')}")
        print(f"  Updated: {data.get('updated_date')} {data.get('updated_time')}")
    else:
        print("Failed to fetch solar data")