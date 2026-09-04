"""Fetch real TCGA case/sample/file metadata from the public GDC API.

This hits the GDC 'files' endpoint via POST (to avoid GET URL-length
limits), scoped to TCGA-LGG and TCGA-GBM -- the two projects where WGS,
RNA-Seq, and ATAC-Seq genuinely coexist for the same patients. Only
metadata is fetched; no sequencing files are downloaded (most are
controlled-access anyway; we only need to know they exist).

The raw response is saved as a checked-in JSON snapshot so the rest of
the project (seed script, tests, CI) never depends on GDC being
reachable at build time.

Usage:
    pixi run python scripts/fetch_gdc_metadata.py
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

GDC_FILES_ENDPOINT = "https://api.gdc.cancer.gov/files"

FIELDS = [
    "file_id",
    "file_name",
    "data_format",
    "data_type",
    "experimental_strategy",
    "platform",
    "file_size",
    "md5sum",
    "cases.case_id",
    "cases.submitter_id",
    "cases.disease_type",
    "cases.primary_site",
    "cases.project.project_id",
    "cases.samples.sample_id",
    "cases.samples.submitter_id",
    "cases.samples.sample_type",
    "cases.samples.tissue_type",
]

FILTERS = {
    "op": "and",
    "content": [
        {
            "op": "in",
            "content": {
                "field": "cases.project.project_id",
                "value": ["TCGA-LGG", "TCGA-GBM"],
            },
        },
        {
            "op": "in",
            "content": {
                "field": "experimental_strategy",
                "value": ["WGS", "WXS", "RNA-Seq", "ATAC-Seq"],
            },
        },
    ],
}


def fetch_all(page_size: int = 500) -> list[dict]:
    """Page through the GDC files endpoint until all matching records are collected."""
    all_hits: list[dict] = []
    offset = 0

    with httpx.Client(timeout=60.0) as client:
        while True:
            payload = {
                "filters": FILTERS,
                "fields": ",".join(FIELDS),
                "format": "JSON",
                "size": page_size,
                "from": offset,
            }
            response = client.post(GDC_FILES_ENDPOINT, json=payload)
            response.raise_for_status()
            body = response.json()

            hits = body["data"]["hits"]
            total = body["data"]["pagination"]["total"]
            all_hits.extend(hits)

            print(f"Fetched {len(all_hits)} / {total} records...")

            offset += page_size
            if offset >= total:
                break

    return all_hits


def main() -> None:
    records = fetch_all()

    out_path = Path(__file__).resolve().parents[1] / "data" / "gdc_snapshot.json"
    out_path.write_text(json.dumps(records, indent=2))

    print(f"\nSaved {len(records)} records to {out_path}")

    strategies: dict[str, int] = {}
    for r in records:
        s = r.get("experimental_strategy", "unknown")
        strategies[s] = strategies.get(s, 0) + 1
    print("Breakdown by experimental_strategy:", strategies)


if __name__ == "__main__":
    main()
