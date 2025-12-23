from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Set, Tuple


@dataclass
class ChallengeSummary:
    total_entities: int
    total_challenge_slots: int
    entities_by_band: Dict[str, int]
    entities_by_mode: Dict[str, int]
    raw_entity_set: Set[str]
    raw_band_entity_pairs: Set[Tuple[str, str]]


def parse_adif_file(path: Path) -> ChallengeSummary:
    """
    Parse an ADIF file exported from LoTW DXCC credits.

    We look for: <DXCC:>, <BAND:>, <MODE:>
    """

    if not path.exists():
        raise FileNotFoundError(f"ADIF file not found: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")
    text_lower = text.lower()

    # Split records at <eor>
    raw_records = text_lower.split("<eor>")
    
    entities: Set[str] = set()
    band_entity: Set[Tuple[str, str]] = set()
    entities_by_band: Dict[str, Set[str]] = {}
    entities_by_mode: Dict[str, Set[str]] = {}

    for record in raw_records:
        record = record.strip()
        if not record:
            continue

        dxcc = extract_field(record, "dxcc")
        band = extract_field(record, "band")
        mode = extract_field(record, "mode")

        if not dxcc:
            continue  # No DXCC = not a credit record

        entities.add(dxcc)

        # Challenge band/entity
        if band:
            band_entity.add((band, dxcc))
            entities_by_band.setdefault(band, set()).add(dxcc)

        if mode:
            entities_by_mode.setdefault(mode, set()).add(dxcc)

    summary = ChallengeSummary(
        total_entities=len(entities),
        total_challenge_slots=len(band_entity),
        entities_by_band={b: len(s) for b, s in entities_by_band.items()},
        entities_by_mode={m: len(s) for m, s in entities_by_mode.items()},
        raw_entity_set=entities,
        raw_band_entity_pairs=band_entity,
    )

    return summary


def extract_field(record: str, field: str) -> str | None:
    """
    Extract ADIF fields of the form:
    <FIELDNAME:length>value
    """
    tag = f"<{field}:"
    idx = record.find(tag)
    if idx == -1:
        return None

    # Find end of the <field:length> header
    end_tag = record.find(">", idx)
    if end_tag == -1:
        return None

    # Extract length
    header = record[idx + len(tag) : end_tag]
    try:
        length = int(header)
    except:
        return None

    start_val = end_tag + 1
    end_val = start_val + length

    return record[start_val:end_val].strip().upper() or None


def save_summary(summary: ChallengeSummary, json_path: Path):
    """Write Challenge summary to JSON."""
    data = asdict(summary)
    data["raw_entity_set"] = sorted(list(summary.raw_entity_set))
    data["raw_band_entity_pairs"] = sorted(
        [list(p) for p in summary.raw_band_entity_pairs],
        key=lambda x: (x[0], x[1]),
    )
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_summary(json_path: Path) -> ChallengeSummary:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return ChallengeSummary(
        total_entities=data["total_entities"],
        total_challenge_slots=data["total_challenge_slots"],
        entities_by_band=data["entities_by_band"],
        entities_by_mode=data["entities_by_mode"],
        raw_entity_set=set(data["raw_entity_set"]),
        raw_band_entity_pairs={tuple(p) for p in data["raw_band_entity_pairs"]},
    )
