"""
parse_existing_adif.py - 2025-12-30
Parse existing lotwreport_challenge.adi file without re-downloading from LoTW

Purpose: 
  Use this if you already have the ADIF downloaded (saves ~20 minutes)
  Rebuilds challenge_data.json from existing lotwreport_challenge.adi

Usage:
  python scripts/parse_existing_adif.py

Author: N4LR
Last modified: 2025-12-30
"""

from backend.lotw_challenge import parse_challenge_adif, save_challenge_data
from pathlib import Path

# Check if file exists
adif_file = Path("lotwreport_challenge.adi")

if not adif_file.exists():
    print("ERROR: lotwreport_challenge.adi not found")
    print("Please make sure the file is in the root directory")
    exit(1)

print("Reading ADIF file...")
adif_text = adif_file.read_text(encoding='utf-8', errors='ignore')

print(f"File size: {len(adif_text)} bytes")
print("\nParsing Challenge data...")

# Parse without existing data (fresh parse)
challenge_data = parse_challenge_adif(adif_text, existing_data=None)

# Save
if save_challenge_data(challenge_data):
    print("\nSuccess!")
    print(f"Total Entities: {challenge_data['total_entities']}")
    print(f"Total Slots: {challenge_data['total_challenge_slots']}")
    print(f"\nBand breakdown:")
    for band, count in sorted(challenge_data['entities_by_band'].items()):
        print(f"  {band}: {count}")
else:
    print("ERROR: Failed to save challenge data")
