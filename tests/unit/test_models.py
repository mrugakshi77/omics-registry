import pytest
from sqlalchemy.exc import IntegrityError

from omics_registry.models import Patient, Sample, SampleType


def test_create_patient(db_session):
    patient = Patient(patient_id="TEST-0001")
    db_session.add(patient)
    db_session.commit()

    assert patient.id is not None
    assert patient.created_at is not None


def test_patient_id_must_be_unique(db_session):
    db_session.add(Patient(patient_id="TEST-0002"))
    db_session.commit()

    db_session.add(Patient(patient_id="TEST-0002"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_deleting_patient_cascades_to_samples(db_session):
    patient = Patient(patient_id="TEST-0003")
    patient.samples.append(Sample(sample_id="TEST-0003-S1", sample_type=SampleType.TUMOR, tissue="lung"))
    db_session.add(patient)
    db_session.commit()

    sample_id = patient.samples[0].id
    db_session.delete(patient)
    db_session.commit()

    assert db_session.get(Sample, sample_id) is None
