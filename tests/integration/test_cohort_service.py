import pytest

from omics_registry.models import Experiment, Patient, Sample
from omics_registry.models.enums import AssayType, SampleType
from omics_registry.services.cohort import find_cohort


@pytest.fixture()
def multimodal_fixture(db_session):
    """Three samples with deliberately different assay coverage.

    - FULL: has WGS + RNA-seq + ATAC-seq (should match a 3-assay query)
    - PARTIAL: has WGS + RNA-seq only (should NOT match a 3-assay query)
    - EXTRA: has WGS + RNA-seq + ATAC-seq + WES (should still match --
      containment means "at least these", not "exactly these")
    """
    patient = Patient(patient_id="FIXTURE-P1")

    full = Sample(sample_id="FIXTURE-FULL", sample_type=SampleType.TUMOR, tissue="brain")
    full.experiments = [
        Experiment(experiment_id="FIXTURE-FULL-WGS", assay=AssayType.WGS,
                   sequencing_platform="Illumina", genome_build="GRCh38"),
        Experiment(experiment_id="FIXTURE-FULL-RNA", assay=AssayType.RNA_SEQ,
                   sequencing_platform="Illumina", genome_build="GRCh38"),
        Experiment(experiment_id="FIXTURE-FULL-ATAC", assay=AssayType.ATAC_SEQ,
                   sequencing_platform="Illumina", genome_build="GRCh38"),
    ]

    partial = Sample(sample_id="FIXTURE-PARTIAL", sample_type=SampleType.TUMOR, tissue="brain")
    partial.experiments = [
        Experiment(experiment_id="FIXTURE-PARTIAL-WGS", assay=AssayType.WGS,
                   sequencing_platform="Illumina", genome_build="GRCh38"),
        Experiment(experiment_id="FIXTURE-PARTIAL-RNA", assay=AssayType.RNA_SEQ,
                   sequencing_platform="Illumina", genome_build="GRCh38"),
    ]

    extra = Sample(sample_id="FIXTURE-EXTRA", sample_type=SampleType.NORMAL, tissue="brain")
    extra.experiments = [
        Experiment(experiment_id="FIXTURE-EXTRA-WGS", assay=AssayType.WGS,
                   sequencing_platform="Illumina", genome_build="GRCh38"),
        Experiment(experiment_id="FIXTURE-EXTRA-RNA", assay=AssayType.RNA_SEQ,
                   sequencing_platform="Illumina", genome_build="GRCh38"),
        Experiment(experiment_id="FIXTURE-EXTRA-ATAC", assay=AssayType.ATAC_SEQ,
                   sequencing_platform="Illumina", genome_build="GRCh38"),
        Experiment(experiment_id="FIXTURE-EXTRA-WES", assay=AssayType.WES,
                   sequencing_platform="Illumina", genome_build="GRCh38"),
    ]

    patient.samples = [full, partial, extra]
    db_session.add(patient)
    db_session.commit()

    return {"full": full, "partial": partial, "extra": extra}


def test_finds_samples_with_all_requested_assays(db_session, multimodal_fixture):
    results = find_cohort(db_session, assays=[AssayType.WGS, AssayType.RNA_SEQ, AssayType.ATAC_SEQ])
    sample_ids = {r["sample_id"] for r in results}

    assert sample_ids == {"FIXTURE-FULL", "FIXTURE-EXTRA"}


def test_excludes_samples_missing_a_requested_assay(db_session, multimodal_fixture):
    results = find_cohort(db_session, assays=[AssayType.WGS, AssayType.RNA_SEQ, AssayType.ATAC_SEQ])
    sample_ids = {r["sample_id"] for r in results}

    assert "FIXTURE-PARTIAL" not in sample_ids


def test_filters_by_sample_type(db_session, multimodal_fixture):
    results = find_cohort(
        db_session,
        assays=[AssayType.WGS, AssayType.RNA_SEQ, AssayType.ATAC_SEQ],
        sample_type=SampleType.NORMAL,
    )
    sample_ids = {r["sample_id"] for r in results}

    assert sample_ids == {"FIXTURE-EXTRA"}


def test_single_assay_query_matches_any_sample_with_it(db_session, multimodal_fixture):
    results = find_cohort(db_session, assays=[AssayType.WGS])
    sample_ids = {r["sample_id"] for r in results}

    assert sample_ids == {"FIXTURE-FULL", "FIXTURE-PARTIAL", "FIXTURE-EXTRA"}
