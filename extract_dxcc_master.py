#!/usr/bin/env python3
"""
Extract DXCC entities from cty.dat and create master list
Creates dxcc_entities.json with all entities for verification
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def parse_cty_dat(filename="cty.dat"):
    """
    Parse cty.dat file and extract all DXCC entities
    
    Returns:
        dict: {dxcc_num: {"name": str, "prefix": str, "cq_zone": int, "itu_zone": int}}
    """
    
    if not Path(filename).exists():
        print(f"Error: {filename} not found!")
        return {}
    
    entities = {}
    
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Split by record (ends with ;)
    records = content.split(';')
    
    print(f"Processing {len(records)} records from cty.dat...")
    
    for record in records:
        if not record.strip():
            continue
        
        # First line has: Country Name:CQ:ITU:Continent:Lat:Long:TZ:Primary Prefix
        lines = record.strip().split('\n')
        if not lines:
            continue
        
        header = lines[0].strip()
        
        # Parse header
        parts = header.split(':')
        if len(parts) < 8:
            continue
        
        country_name = parts[0].strip()
        cq_zone = parts[1].strip()
        itu_zone = parts[2].strip()
        continent = parts[3].strip()
        primary_prefix = parts[7].strip()
        
        # Parse prefix lines to find DXCC number
        # Format: =prefix(dxcc)[cq]<itu>{lat/long}~tz,
        # We want the (dxcc) number
        
        dxcc_numbers = set()
        all_prefixes = []
        
        for line in lines[1:]:
            # Find all prefixes with DXCC numbers
            # Pattern: =prefix(123) or just prefix(123)
            matches = re.findall(r'[=]?([A-Z0-9/]+)\((\d+)\)', line)
            for prefix, dxcc in matches:
                dxcc_numbers.add(int(dxcc))
                all_prefixes.append(prefix)
            
            # Also look for prefixes without explicit DXCC (use default)
            # These will be in format: prefix[cq]<itu>
            simple_matches = re.findall(r'\s+([A-Z0-9/]+)[\[<,]', line)
            for prefix in simple_matches:
                if prefix not in all_prefixes:
                    all_prefixes.append(prefix)
        
        # Store each DXCC number found
        for dxcc in dxcc_numbers:
            if dxcc not in entities:
                entities[dxcc] = {
                    "name": country_name,
                    "prefix": primary_prefix,
                    "cq_zone": cq_zone,
                    "itu_zone": itu_zone,
                    "continent": continent,
                    "all_prefixes": []
                }
            
            # Add any new prefixes
            for p in all_prefixes:
                if p not in entities[dxcc]["all_prefixes"]:
                    entities[dxcc]["all_prefixes"].append(p)
    
    print(f"Extracted {len(entities)} unique DXCC entities")
    return entities


def create_master_list(entities):
    """
    Create master DXCC list with current/deleted status
    
    Known deleted entities will be marked, rest assumed current
    You'll need to manually verify the 340 current ones
    """
    
    # Some known deleted entities (partial list - you'll need to verify all)
    # This is just a starting point
    known_deleted = {
        # These are examples - you need the complete list from ARRL
        14,   # Mariana Islands (now part of 166)
        17,   # East Malaysia (now part of 46)
        20,   # Sikkim (now part of India)
        21,   # Sumatra (now part of Indonesia)
        # ... add more as you verify
    }
    
    master = {}
    current_count = 0
    deleted_count = 0
    
    for dxcc_num, data in sorted(entities.items()):
        is_deleted = dxcc_num in known_deleted
        
        master[str(dxcc_num)] = {
            "dxcc": dxcc_num,
            "name": data["name"],
            "prefix": data["prefix"],
            "continent": data["continent"],
            "cq_zone": data["cq_zone"],
            "itu_zone": data["itu_zone"],
            "deleted": is_deleted,
            "current": not is_deleted,
            "all_prefixes": data["all_prefixes"][:10],  # Limit to first 10
        }
        
        if is_deleted:
            deleted_count += 1
        else:
            current_count += 1
    
    print(f"\nCurrent entities: {current_count}")
    print(f"Deleted entities: {deleted_count}")
    print(f"Total entities: {len(master)}")
    
    return master


def save_master_list(master, filename="dxcc_entities.json"):
    """Save master list to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print(f"\nSaved master list to {filename}")


def save_verification_csv(master, filename="dxcc_verify.csv"):
    """
    Create CSV file for manual verification against ARRL list
    Format: DXCC#, Name, Prefix, Current/Deleted
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("DXCC,Name,Prefix,Continent,Status,Action\n")
        
        for dxcc_num, data in sorted(master.items(), key=lambda x: int(x[0])):
            status = "DELETED" if data["deleted"] else "CURRENT"
            # Action column for you to fill in: KEEP, DELETE, or VERIFY
            action = "VERIFY" if not data["deleted"] else "DELETED"
            
            f.write(f'{data["dxcc"]},"{data["name"]}",{data["prefix"]},{data["continent"]},{status},{action}\n')
    
    print(f"Saved verification CSV to {filename}")
    print("\nNext steps:")
    print("1. Open dxcc_verify.csv in Excel/spreadsheet")
    print("2. Compare against ARRL current list")
    print("3. Mark Action column: KEEP (current), DELETE (not current), or VERIFY (unsure)")
    print("4. Count should be exactly 340 KEEP entries")


def create_stats_report(master):
    """Print statistics about the extracted data"""
    print("\n" + "="*80)
    print("DXCC EXTRACTION STATISTICS")
    print("="*80)
    
    current = [d for d in master.values() if d["current"]]
    deleted = [d for d in master.values() if d["deleted"]]
    
    print(f"\nTotal entities extracted: {len(master)}")
    print(f"Marked as CURRENT: {len(current)} (target: 340)")
    print(f"Marked as DELETED: {len(deleted)}")
    
    print("\nBy Continent (CURRENT only):")
    continents = defaultdict(int)
    for entity in current:
        continents[entity["continent"]] += 1
    
    for cont in sorted(continents.keys()):
        print(f"  {cont}: {continents[cont]}")
    
    print("\nSample current entities:")
    for entity in sorted(current, key=lambda x: x["dxcc"])[:10]:
        print(f"  {entity['dxcc']:3d} - {entity['name']:30s} ({entity['prefix']})")
    
    print("\nSample deleted entities:")
    for entity in sorted(deleted, key=lambda x: x["dxcc"])[:5]:
        print(f"  {entity['dxcc']:3d} - {entity['name']:30s} ({entity['prefix']}) [DELETED]")
    
    if len(current) != 340:
        print(f"\n⚠️  WARNING: Current count is {len(current)}, should be 340!")
        print("    You need to manually verify against ARRL current list")


if __name__ == "__main__":
    print("DXCC Master List Extractor")
    print("="*80)
    
    # Step 1: Parse cty.dat
    entities = parse_cty_dat("cty.dat")
    
    if not entities:
        print("Failed to parse cty.dat!")
        exit(1)
    
    # Step 2: Create master list
    master = create_master_list(entities)
    
    # Step 3: Save JSON
    save_master_list(master, "dxcc_entities.json")
    
    # Step 4: Create verification CSV
    save_verification_csv(master, "dxcc_verify.csv")
    
    # Step 5: Show statistics
    create_stats_report(master)
    
    print("\n" + "="*80)
    print("DONE! Next steps:")
    print("="*80)
    print("1. Open dxcc_verify.csv and verify against ARRL list")
    print("2. Ensure exactly 340 entities are marked CURRENT")
    print("3. Update dxcc_entities.json based on your verification")
    print("4. Use dxcc_entities.json as single source of truth")
    print("="*80)
