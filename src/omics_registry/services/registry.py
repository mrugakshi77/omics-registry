"""Core write operations: registering patients, samples, experiments, and analyses.

Each function takes a validated Pydantic *Create schema and a DB session,
does the actual insert, and returns the resulting SQLAlchemy object. Both
the FastAPI routes and the Typer CLI call these same functions, so the
logic only exists once.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from omics_registry.models import Analysis, Experiment, Patient, ResultFile, Sample
from omics_registry.schemas import (
    AnalysisCreate,
    ExperimentCreate,
    PatientCreate,
    SampleCreate,
)


class NotFoundError(Exception):
    """Raised when a referenced business-key (patient_id, sample_id, ...) doesn't exist."""


def create_patient(db: Session, data: PatientCreate) -> Patient:
    patient = Patient(patient_id=data.patient_id)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _get_patient_by_business_key(db: Session, patient_id: str) -> Patient:
    patient = db.scalar(select(Patient).where(Patient.patient_id == patient_id))
    if patient is None:
        raise NotFoundError(f"No patient with patient_id={patient_id!r}")
    return patient


def create_sample(db: Session, data: SampleCreate) -> Sample:
    patient = _get_patient_by_business_key(db, data.patient_id)
    sample = Sample(
        sample_id=data.sample_id,
        patient_id=patient.id,
        sample_type=data.sample_type,
        tissue=data.tissue,
        collection_date=data.collection_date,
        sample_metadata=data.sample_metadata,
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


def _get_sample_by_business_key(db: Session, sample_id: str) -> Sample:
    sample = db.scalar(select(Sample).where(Sample.sample_id == sample_id))
    if sample is None:
        raise NotFoundError(f"No sample with sample_id={sample_id!r}")
    return sample


def create_experiment(db: Session, data: ExperimentCreate) -> Experiment:
    sample = _get_sample_by_business_key(db, data.sample_id)
    experiment = Experiment(
        experiment_id=data.experiment_id,
        sample_id=sample.id,
        assay=data.assay,
        sequencing_platform=data.sequencing_platform,
        genome_build=data.genome_build,
        fastq_path=data.fastq_path,
        bam_path=data.bam_path,
        experiment_metadata=data.experiment_metadata,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


def _get_experiment_by_business_key(db: Session, experiment_id: str) -> Experiment:
    experiment = db.scalar(select(Experiment).where(Experiment.experiment_id == experiment_id))
    if experiment is None:
        raise NotFoundError(f"No experiment with experiment_id={experiment_id!r}")
    return experiment


def register_analysis(db: Session, data: AnalysisCreate) -> Analysis:
    """Register a pipeline run against an experiment, optionally with its output file.

    This is the core Isabl-inspired provenance action: recording *which*
    pipeline, version, and parameters produced a result, in one atomic step.
    """
    experiment = _get_experiment_by_business_key(db, data.experiment_id)

    analysis = Analysis(
        experiment_id=experiment.id,
        pipeline_name=data.pipeline_name,
        pipeline_version=data.pipeline_version,
        git_commit=data.git_commit,
        reference_genome=data.reference_genome,
        status=data.status,
        parameters=data.parameters,
    )

    if data.result_file is not None:
        analysis.result_files.append(
            ResultFile(
                file_path=data.result_file.file_path,
                file_type=data.result_file.file_type,
                checksum=data.result_file.checksum,
                size_bytes=data.result_file.size_bytes,
            )
        )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis
