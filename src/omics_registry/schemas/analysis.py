from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from omics_registry.models.enums import AnalysisStatus, FileType


class ResultFileCreate(BaseModel):
    file_path: str
    file_type: FileType
    checksum: str | None = None
    size_bytes: int | None = None


class ResultFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    file_type: FileType
    checksum: str | None
    size_bytes: int | None
    created_at: dt.datetime


class AnalysisCreate(BaseModel):
    experiment_id: str  # references Experiment.experiment_id (business key)
    pipeline_name: str
    pipeline_version: str
    git_commit: str | None = None
    reference_genome: str
    status: AnalysisStatus = AnalysisStatus.QUEUED
    parameters: dict = {}
    result_file: ResultFileCreate | None = None  # optional: register the output file in the same call


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pipeline_name: str
    pipeline_version: str
    git_commit: str | None
    reference_genome: str
    status: AnalysisStatus
    parameters: dict
    started_at: dt.datetime | None
    completed_at: dt.datetime | None
    created_at: dt.datetime
    result_files: list[ResultFileRead] = []
