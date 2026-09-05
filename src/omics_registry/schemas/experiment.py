from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from omics_registry.models.enums import AssayType


class ExperimentCreate(BaseModel):
    experiment_id: str
    sample_id: str  # references Sample.sample_id (business key)
    assay: AssayType
    sequencing_platform: str
    genome_build: str
    fastq_path: str | None = None
    bam_path: str | None = None
    experiment_metadata: dict = {}


class ExperimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: str
    assay: AssayType
    sequencing_platform: str
    genome_build: str
    fastq_path: str | None
    bam_path: str | None
    experiment_metadata: dict
    created_at: dt.datetime
