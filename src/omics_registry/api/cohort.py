from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from omics_registry.db.session import get_db
from omics_registry.models.enums import AssayType, SampleType
from omics_registry.services.cohort import find_cohort

router = APIRouter(prefix="/cohort", tags=["cohort"])


@router.get("")
def get_cohort(
    assays: list[AssayType] = Query(..., description="Sample must have ALL of these assays"),
    sample_type: SampleType | None = Query(None),
    tissue: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    return find_cohort(db, assays=assays, sample_type=sample_type, tissue=tissue)
