"""Curate the raw GDC snapshot into a small, deduplicated file ready to seed.

Filters to raw sequencing files only (data_type == 'Aligned Reads'), then
collapses many files-per-sample down to one record per (sample, assay).
Also reports the real multimodal overlap across assays, computed from
actual identifiers rather than assumed.

Usage:
    pixi run python scripts/curate_gdc_metadata.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "gdc_snapshot.json"
CURATED_PATH = Path(__file__).resolve().parents[1] / "data" / "gdc_curated.json"


def main() -> None:
    raw = json.loads(RAW_PATH.read_text())
    aligned = [r for r in raw if r.get("data_type") == "Aligned Reads"]
    print(f"Raw records: {len(raw)}  |  Aligned Reads only: {len(aligned)}")

    # Flatten: one row per (sample, assay), keyed by sample submitter_id.
    curated: dict[str, dict] = {}
    for rec in aligned:
        for case in rec.get("cases", []):
            for sample in case.get("samples", []):
                key = sample["submitter_id"]
                if key not in curated:
                    curated[key] = {
                        "sample_submitter_id": sample["submitter_id"],
                        "sample_type": sample["sample_type"],
                        "tissue_type": sample["tissue_type"],
                        "case_submitter_id": case["submitter_id"],
                        "primary_site": case["primary_site"],
                        "disease_type": case["disease_type"],
                        "project_id": case["project"]["project_id"],
                        "assays": {},
                    }
                curated[key]["assays"][rec["experimental_strategy"]] = {
                    "file_id": rec["file_id"],
                    "file_name": rec["file_name"],
                    "platform": rec.get("platform"),
                    "file_size": rec.get("file_size"),
                    "md5sum": rec.get("md5sum"),
                }

    records = list(curated.values())
    CURATED_PATH.write_text(json.dumps(records, indent=2))
    print(f"Saved {len(records)} unique samples to {CURATED_PATH}")

    # Real multimodal overlap, computed -- not assumed.
    assay_counts: dict[str, int] = defaultdict(int)
    for r in records:
        for assay in r["assays"]:
            assay_counts[assay] += 1
    print("\nSamples per assay:", dict(assay_counts))

    def has_all(sample: dict, assays: set[str]) -> bool:
        return assays.issubset(sample["assays"].keys())

    combos = [
        {"WGS", "RNA-Seq"},
        {"WXS", "RNA-Seq"},
        {"WGS", "ATAC-Seq"},
        {"WGS", "RNA-Seq", "ATAC-Seq"},
        {"WXS", "RNA-Seq", "ATAC-Seq"},
    ]
    print("\nMultimodal overlap (by sample):")
    for combo in combos:
        n = sum(1 for r in records if has_all(r, combo))
        print(f"  {' + '.join(sorted(combo))}: {n} samples")


if __name__ == "__main__":
    main()
