from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class PatientCreate(BaseModel):
    """What a client must send to register a new patient."""

    patient_id: str


class PatientRead(BaseModel):
    """What we send back when returning a patient."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: str
    created_at: dt.datetime
