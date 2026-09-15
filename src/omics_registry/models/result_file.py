from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omics_registry.db.base import Base
from omics_registry.models.enums import FileType

if TYPE_CHECKING:
    from omics_registry.models.analysis import Analysis

class ResultFile(Base):
    __tablename__ = "result_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)

    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType, name="file_type_enum", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        index=True,
    )
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    analysis: Mapped[Analysis] = relationship(back_populates="result_files")
