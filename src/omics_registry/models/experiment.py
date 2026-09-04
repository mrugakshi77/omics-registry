from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omics_registry.db.base import Base
from omics_registry.models.enums import AssayType


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id", ondelete="CASCADE"), index=True)

    assay: Mapped[AssayType] = mapped_column(
        Enum(AssayType, name="assay_type_enum", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        index=True,
    )
    sequencing_platform: Mapped[str] = mapped_column(String(64), nullable=False)
    genome_build: Mapped[str] = mapped_column(String(16), nullable=False)
    fastq_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bam_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    experiment_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sample: Mapped["Sample"] = relationship(back_populates="experiments")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="experiment", cascade="all, delete-orphan")
