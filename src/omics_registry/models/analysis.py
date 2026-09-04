from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omics_registry.db.base import Base
from omics_registry.models.enums import AnalysisStatus


class Analysis(Base):
    """A pipeline run against an experiment, with full provenance."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), index=True)

    pipeline_name: Mapped[str] = mapped_column(String(128), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(32), nullable=False)
    git_commit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reference_genome: Mapped[str] = mapped_column(String(16), nullable=False)

    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status_enum", values_callable=lambda e: [m.value for m in e]),
        default=AnalysisStatus.QUEUED,
        server_default=AnalysisStatus.QUEUED.value,
        nullable=False,
        index=True,
    )
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    experiment: Mapped["Experiment"] = relationship(back_populates="analyses")
    result_files: Mapped[list["ResultFile"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
