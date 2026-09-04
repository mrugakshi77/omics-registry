"""Seed the database from real GDC/TCGA metadata, with optional synthetic
augmentation for scale.

Real data comes from data/gdc_curated.json (see scripts/fetch_gdc_metadata.py
and scripts/curate_gdc_metadata.py). Synthetic patients use a SYNTH- prefix
so they're never confused with real TCGA identifiers.

Usage:
    pixi run python scripts/seed_data.py --reset
    pixi run python scripts/seed_data.py --reset --synthetic-patients 80 --seed 42
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from omics_registry.db.base import Base
from omics_registry.db.session import SessionLocal, engine
from omics_registry.models import (
    Analysis,
    AnalysisStatus,
    AssayType,
    Experiment,
    FileType,
    Patient,
    ResultFile,
    Sample,
    SampleType,
)

CURATED_PATH = Path(__file__).resolve().parents[1] / "data" / "gdc_curated.json"

ASSAY_MAP = {
    "WGS": AssayType.WGS,
    "WXS": AssayType.WES,
    "RNA-Seq": AssayType.RNA_SEQ,
    "ATAC-Seq": AssayType.ATAC_SEQ,
}
SAMPLE_TYPE_MAP = {"Tumor": SampleType.TUMOR, "Normal": SampleType.NORMAL}
RESULT_FILE_TYPE = {
    AssayType.WGS: FileType.BAM,
    AssayType.WES: FileType.BAM,
    AssayType.RNA_SEQ: FileType.BAM,
    AssayType.ATAC_SEQ: FileType.BAM,
}


def load_real_cohort() -> list[Patient]:
    """Build ORM objects from the curated real GDC snapshot."""
    curated = json.loads(CURATED_PATH.read_text())

    patients_by_case: dict[str, Patient] = {}

    for rec in curated:
        case_id = rec["case_submitter_id"]
        if case_id not in patients_by_case:
            patients_by_case[case_id] = Patient(patient_id=case_id)
        patient = patients_by_case[case_id]

        sample_type = SAMPLE_TYPE_MAP.get(rec["tissue_type"], SampleType.TUMOR)
        sample = Sample(
            sample_id=rec["sample_submitter_id"],
            sample_type=sample_type,
            tissue=rec["primary_site"].lower(),
            sample_metadata={
                "disease_type": rec["disease_type"],
                "gdc_project_id": rec["project_id"],
                "gdc_sample_type": rec["sample_type"],
            },
        )

        for gdc_assay, file_info in rec["assays"].items():
            assay = ASSAY_MAP[gdc_assay]
            experiment = Experiment(
                experiment_id=f"{rec['sample_submitter_id']}-{assay.value.replace('-', '')}",
                assay=assay,
                sequencing_platform=file_info.get("platform") or "unknown",
                genome_build="GRCh38",  # GDC harmonized pipeline aligns everything to GRCh38
                bam_path=f"gdc://{file_info['file_id']}/{file_info['file_name']}",
                experiment_metadata={"source": "GDC", "gdc_file_id": file_info["file_id"]},
            )

            analysis = Analysis(
                pipeline_name="GDC-harmonization",
                pipeline_version="unknown",
                git_commit=None,
                reference_genome="GRCh38",
                status=AnalysisStatus.COMPLETED,
                parameters={"source": "GDC public API", "note": "pre-harmonized by GDC, not run by us"},
            )
            analysis.result_files.append(
                ResultFile(
                    file_path=f"gdc://{file_info['file_id']}/{file_info['file_name']}",
                    file_type=RESULT_FILE_TYPE[assay],
                    checksum=file_info.get("md5sum"),
                    size_bytes=file_info.get("file_size"),
                )
            )
            experiment.analyses.append(analysis)
            sample.experiments.append(experiment)

        patient.samples.append(sample)

    return list(patients_by_case.values())


def build_synthetic_cohort(n_patients: int, rng: random.Random) -> list[Patient]:
    """Synthetic patients for scale/edge cases, clearly namespaced with SYNTH-."""
    tissues = ["breast", "lung", "colon", "prostate", "pancreas", "liver", "kidney", "skin"]
    platforms = ["Illumina NovaSeq 6000", "Illumina HiSeq 4000", "Illumina NovaSeq X"]
    pipelines = {
        AssayType.WGS: ("gatk-germline", "4.5.0"),
        AssayType.WES: ("gatk-germline", "4.5.0"),
        AssayType.RNA_SEQ: ("star-salmon", "1.3.2"),
        AssayType.ATAC_SEQ: ("nf-core-atacseq", "2.1.2"),
    }

    patients: list[Patient] = []
    for i in range(n_patients):
        patient_id = f"SYNTH-{i:04d}"
        patient = Patient(patient_id=patient_id)
        tissue = rng.choice(tissues)

        sample_type = rng.choice([SampleType.TUMOR, SampleType.TUMOR, SampleType.NORMAL])
        sample = Sample(
            sample_id=f"{patient_id}-S1",
            sample_type=sample_type,
            tissue=tissue,
            sample_metadata={
                "batch": f"batch-{rng.randint(1, 12):02d}",
                "qc_status": rng.choices(["pass", "pass", "pass", "warn", "fail"], k=1)[0],
            },
        )

        n_assays = rng.choices([1, 2, 3, 4], weights=[15, 30, 30, 25])[0]
        for assay in rng.sample(list(AssayType), k=n_assays):
            experiment = Experiment(
                experiment_id=f"{sample.sample_id}-{assay.value.replace('-', '')}",
                assay=assay,
                sequencing_platform=rng.choice(platforms),
                genome_build="GRCh38",
                bam_path=f"/data/{patient_id}/{sample.sample_id}.{assay.value}.bam",
                experiment_metadata={"source": "synthetic"},
            )
            status = rng.choices(list(AnalysisStatus), weights=[10, 10, 70, 10])[0]
            pipeline_name, pipeline_version = pipelines[assay]
            analysis = Analysis(
                pipeline_name=pipeline_name,
                pipeline_version=pipeline_version,
                git_commit="".join(rng.choices("abcdef0123456789", k=12)),
                reference_genome="GRCh38",
                status=status,
                parameters={"source": "synthetic"},
            )
            if status == AnalysisStatus.COMPLETED:
                analysis.result_files.append(
                    ResultFile(
                        file_path=f"/data/{patient_id}/{sample.sample_id}.{assay.value}.vcf.gz",
                        file_type=FileType.VCF,
                        checksum="".join(rng.choices("abcdef0123456789", k=32)),
                        size_bytes=rng.randint(50_000_000, 5_000_000_000),
                    )
                )
            experiment.analyses.append(analysis)
            sample.experiments.append(experiment)

        patient.samples.append(sample)
        patients.append(patient)

    return patients


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-patients", type=int, default=0, help="Number of synthetic patients to add")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for synthetic data")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables first")
    args = parser.parse_args()

    if args.reset:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    real_patients = load_real_cohort()
    rng = random.Random(args.seed)
    synthetic_patients = build_synthetic_cohort(args.synthetic_patients, rng) if args.synthetic_patients else []

    all_patients = real_patients + synthetic_patients

    db = SessionLocal()
    try:
        db.add_all(all_patients)
        db.commit()

        n_samples = sum(len(p.samples) for p in all_patients)
        n_experiments = sum(len(s.experiments) for p in all_patients for s in p.samples)
        print(
            f"Seeded {len(real_patients)} real GDC patients + {len(synthetic_patients)} synthetic patients "
            f"= {len(all_patients)} total, {n_samples} samples, {n_experiments} experiments."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
