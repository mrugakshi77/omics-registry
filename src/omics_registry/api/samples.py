from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from omics_registry.db.session import get_db
from omics_registry.schemas import SampleCreate, SampleRead
from omics_registry.services.registry import create_sample

router = APIRouter(prefix="/samples", tags=["samples"])


@router.post("", response_model=SampleRead, status_code=201)
def register_sample(data: SampleCreate, db: Session = Depends(get_db)) -> SampleRead:
    return create_sample(db, data)
