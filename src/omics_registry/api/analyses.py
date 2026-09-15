from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from omics_registry.db.session import get_db
from omics_registry.models import Analysis
from omics_registry.schemas import AnalysisCreate, AnalysisRead
from omics_registry.services.registry import register_analysis

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisRead, status_code=201)
def create_analysis(data: AnalysisCreate, db: Session = Depends(get_db)) -> Analysis:
    return register_analysis(db, data)
