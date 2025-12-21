# solar.py - Fetch solar indices from NOAA
import datetime
import requests

SOLAR_DATA = {
    "sfi": "—",
    "a": "—",
    "k": "—",
    "updated": None,
}

def fetch_solar_data():
    """Fetch SFI, A-index, and K-index from NOAA SWPC (rock-solid)."""
    global SOLAR_DATA
    try:
        # -----------------------------
        # 1. Get Solar Flux (SFI)
        # -----------------------------
        flux = requests.get(
            "https://services.swpc.noaa.gov/json/f107_cm_flux.json",
            timeout=6,
            headers={"User-Agent": "N4LR_DXClient/1.0"}
        ).json()
        if isinstance(flux, list) and len(flux) > 0:
            last = flux[-1]
            SOLAR_DATA["sfi"] = last.get("flux", "—")
        
        # -----------------------------
        # 2. Get K-index (Planetary Kp)
        # -----------------------------
        kdata = requests.get(
            "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
            timeout=6,
            headers={"User-Agent": "N4LR_DXClient/1.0"}
        ).json()
        if isinstance(kdata, list) and len(kdata) > 0:
            last = kdata[-1]
            SOLAR_DATA["k"] = last.get("kp_index", "—")
        
        # -----------------------------
        # 3. A-index (daily planetary A)
        # -----------------------------
        adata = requests.get(
            "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
            timeout=6,
            headers={"User-Agent": "N4LR_DXClient/1.0"}
        ).json()
        # Format: [header_row, [time_tag, kp, a], ...]
        if isinstance(adata, list) and len(adata) > 1:
            last = adata[-1]  # [time_tag, kp, a]
            if len(last) >= 3:
                SOLAR_DATA["a"] = last[2]
        
        SOLAR_DATA["updated"] = datetime.datetime.utcnow()
        print(f"[solar.py] Updated: SFI={SOLAR_DATA['sfi']}, K={SOLAR_DATA['k']}, A={SOLAR_DATA['a']}")
        
    except Exception as ex:
        print(f"[solar.py] NOAA fetch failed: {ex}")
        # Keep older values

def get_solar_data():
    """Get current solar data"""
    return SOLAR_DATA.copy()

def get_solar_summary():
    """Get formatted solar data string"""
    data = SOLAR_DATA
    return f"SFI:{data['sfi']} K:{data['k']} A:{data['a']}"


if __name__ == "__main__":
    # Test the solar data fetch
    print("Testing solar data fetch...")
    fetch_solar_data()
    print(f"Result: {get_solar_summary()}")
    print(f"Full data: {get_solar_data()}")
