# N4LR DX Client - Utility Scripts

This directory contains utility scripts for maintaining and analyzing your DX client data.

## Scripts

### parse_existing_adif.py
**Purpose:** Parse an existing LoTW ADIF file without re-downloading
**Usage:** `python scripts/parse_existing_adif.py`
**When to use:** 
- When you already have `lotwreport_challenge.adi` downloaded
- To rebuild `challenge_data.json` after code updates
- Saves 20 minutes vs re-downloading from LoTW

### challenge_compare.py
**Purpose:** Compare your Challenge data with LoTW expected values
**Usage:** `python scripts/challenge_compare.py`
**Output:** Detailed report showing:
- Band-by-band comparison with LoTW online
- Invalid entities (DXCC 0, etc.)
- Single-slot entities (possible paper QSLs)
- Explains differences between your data and LoTW

## Notes

- Keep your `lotwreport_challenge.adi` file for future re-parsing
- Scripts expect to be run from the root directory
- All scripts work with files in the root directory (config.ini, challenge_data.json, etc.)
