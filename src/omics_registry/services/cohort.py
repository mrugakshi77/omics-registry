"""Cohort querying: the core "why this platform exists" feature.

A researcher's real question is never "give me a list of experiments" --
it's "which samples have ALL of these assay types together?" (e.g. WGS +
RNA-seq + ATAC-seq on the same tumor sample, for a multimodal analysis).
That's a set-containment question, not a simple filter, which is why this
uses PostgreSQL's array containment operator (`@>`) rather than `IN`.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from omics_registry.models.enums import AssayType, SampleType


def find_cohort(
    db: Session,
    assays: list[AssayType],
    sample_type: SampleType | None = None,
    tissue: str | None = None,
) -> list[dict]:
    """Return samples that have ALL of the requested assay types.

    `IN` would match a sample with *any* of the requested assays -- a
    fundamentally different (and less useful) question than what a
    researcher building a multimodal cohort actually wants.
    """
    sql = text("""
        SELECT
            p.patient_id,
            s.sample_id,
            s.sample_type::text AS sample_type,
            s.tissue,
            array_agg(DISTINCT e.assay ORDER BY e.assay) AS assays
        FROM samples s
        JOIN patients p ON p.id = s.patient_id
        JOIN experiments e ON e.sample_id = s.id
        WHERE (:sample_type IS NULL OR s.sample_type = CAST(:sample_type AS sample_type_enum))
          AND (:tissue IS NULL OR s.tissue = :tissue)
        GROUP BY p.patient_id, s.id
        HAVING array_agg(DISTINCT e.assay) @> CAST(:assays AS assay_type_enum[])
        ORDER BY s.sample_id
    """)

    result = db.execute(
        sql,
        {
            "sample_type": sample_type.value if sample_type else None,
            "tissue": tissue,
            "assays": [a.value for a in assays],
        },
    )
    rows = [dict(row._mapping) for row in result]
    for row in rows:
        if isinstance(row["assays"], str):
            row["assays"] = row["assays"].strip("{}").split(",")
    return rows
