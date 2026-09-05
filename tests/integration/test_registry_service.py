import pytest

from omics_registry.models.enums import AssayType, FileType, SampleType
from omics_registry.schemas import AnalysisCreate, ExperimentCreate, PatientCreate, SampleCreate
from omics_registry.schemas.analysis import ResultFileCreate
from omics_registry.services.registry import (
    NotFoundError,
    create_experiment,
    create_patient,
    create_sample,
    register_analysis,
)


def test_full_registration_chain(db_session):
    """Patient -> sample -> experiment -> analysis -> result file, end to end."""
    patient = create_patient(db_session, PatientCreate(patient_id="IT-TEST-01"))
    assert patient.id is not None

    sample = create_sample(
        db_session,
        SampleCreate(
            sample_id="IT-TEST-01-S1",
            patient_id="IT-TEST-01",
            sample_type=SampleType.TUMOR,
            tissue="lung",
        ),
    )
    assert sample.patient_id == patient.id

    experiment = create_experiment(
        db_session,
        ExperimentCreate(
            experiment_id="IT-TEST-01-S1-WGS",
            sample_id="IT-TEST-01-S1",
            assay=AssayType.WGS,
            sequencing_platform="Illumina NovaSeq X",
            genome_build="GRCh38",
        ),
    )
    assert experiment.sample_id == sample.id

    analysis = register_analysis(
        db_session,
        AnalysisCreate(
            experiment_id="IT-TEST-01-S1-WGS",
            pipeline_name="gatk-germline",
            pipeline_version="4.5.0",
            reference_genome="GRCh38",
            result_file=ResultFileCreate(
                file_path="/data/test.vcf.gz", file_type=FileType.VCF, size_bytes=12345
            ),
        ),
    )
    assert analysis.experiment_id == experiment.id
    assert len(analysis.result_files) == 1
    assert analysis.result_files[0].file_path == "/data/test.vcf.gz"


def test_create_sample_with_unknown_patient_raises(db_session):
    with pytest.raises(NotFoundError):
        create_sample(
            db_session,
            SampleCreate(
                sample_id="ORPHAN-S1",
                patient_id="DOES-NOT-EXIST",
                sample_type=SampleType.NORMAL,
                tissue="blood",
            ),
        )


def test_register_analysis_with_unknown_experiment_raises(db_session):
    with pytest.raises(NotFoundError):
        register_analysis(
            db_session,
            AnalysisCreate(
                experiment_id="DOES-NOT-EXIST",
                pipeline_name="gatk-germline",
                pipeline_version="4.5.0",
                reference_genome="GRCh38",
            ),
        )
