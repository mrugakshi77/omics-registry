from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omics_registry.db.base import Base
from omics_registry.models.enums import SampleType

if TYPE_CHECKING:
    from omics_registry.models.experiment import Experiment
    from omics_registry.models.patient import Patient

class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    sample_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)

    sample_type: Mapped[SampleType] = mapped_column(
        Enum(SampleType, name="sample_type_enum", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    tissue: Mapped[str] = mapped_column(String(64), nullable=False)
    collection_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    sample_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[Patient] = relationship(back_populates="samples")
    experiments: Mapped[list[Experiment]] = relationship(back_populates="sample", cascade="all, delete-orphan")
