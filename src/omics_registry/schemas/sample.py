from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from omics_registry.models.enums import SampleType


class SampleCreate(BaseModel):
    sample_id: str
    patient_id: str  # references Patient.patient_id (business key, not the internal int id)
    sample_type: SampleType
    tissue: str
    collection_date: dt.date | None = None
    sample_metadata: dict = {}


class SampleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sample_id: str
    sample_type: SampleType
    tissue: str
    collection_date: dt.date | None
    sample_metadata: dict
    created_at: dt.datetime
