from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from omics_registry.db.session import get_db
from omics_registry.models import Experiment
from omics_registry.schemas import ExperimentCreate, ExperimentRead
from omics_registry.services.registry import create_experiment

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentRead, status_code=201)
def register_experiment(data: ExperimentCreate, db: Session = Depends(get_db)) -> Experiment:
    return create_experiment(db, data)
