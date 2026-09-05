from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from omics_registry.db.session import get_db
from omics_registry.schemas import PatientCreate, PatientRead
from omics_registry.services.registry import create_patient

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientRead, status_code=201)
def register_patient(data: PatientCreate, db: Session = Depends(get_db)) -> PatientRead:
    return create_patient(db, data)
