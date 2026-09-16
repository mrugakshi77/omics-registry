# omics-registry

A small, production-style genomics metadata, provenance, and cohort-management platform, inspired by [Isabl](https://github.com/zeng-lab/isabl_api).

Researchers running a cancer genomics study need to know: which samples have which assays, what analyses have been run against them, and where the results live. This project models that as a relational schema, exposes it via a REST API and CLI, and — the actual point of the whole thing — lets a researcher ask "which samples have complete multimodal coverage?" and get back an analysis-ready manifest.

Built as a portfolio project targeting bioinformatics/software engineering roles, using real public cancer genomics data (not synthetic).

## The killer workflow

```
Real GDC/TCGA metadata (LGG + GBM)
        |
        v
  Curated + deduplicated (35,828 raw file records -> 1,930 samples)
        |
        v
     PostgreSQL
        |
        v
"Find tumor samples with WGS + WES + RNA-seq + ATAC-seq"
        |
        v
   Cohort query (Postgres array containment)
        |
        v
   16 verified real samples
        |
        v
   Manifest CSV, ready for a downstream pipeline
```

Run it yourself:
```bash
omics cohort --assays WGS --assays WES --assays RNA-seq --assays ATAC-seq
omics cohort-export --assays WGS --assays WES --assays RNA-seq --assays ATAC-seq --output cohort.csv
```

## Architecture

```
        Researcher
            |
     Python CLI / REST API
            |
         FastAPI
            |
      Service layer
            |
       PostgreSQL
            |
   +--------+---------+
   |        |         |
Patients Samples  Experiments
                       |
                    Analyses
                       |
                  Result Files
```

## Schema

Five tables, an Isabl-inspired provenance hierarchy:

```
patients -> samples -> experiments -> analyses -> result_files
```

- **patients / samples / experiments**: core metadata (assay type, tissue, sample type, sequencing platform, genome build), with JSONB columns for flexible, non-relational metadata (QC status, batch ID, etc.)
- **analyses**: full pipeline provenance — pipeline name, version, git commit, reference genome, status, parameters (JSONB) — so any result can be traced back to exactly what produced it
- **result_files**: output file metadata (path, type, checksum, size) — never the actual sequencing files themselves

Native PostgreSQL ENUM types for `AssayType` (WGS/WES/RNA-seq/ATAC-seq), `SampleType`, `AnalysisStatus`, and `FileType`. See [docs/isabl_mapping.md](docs/isabl_mapping.md) for how this maps onto Isabl's own concepts.

## The data

Real metadata from the [NCI Genomic Data Commons](https://gdc.cancer.gov/) (GDC), fetched via their public API — no synthetic data. Scoped to TCGA-LGG and TCGA-GBM (glioma), the two TCGA projects where WGS, WES, RNA-seq, and ATAC-seq genuinely coexist for the same patients.

Filtered to `data_type == "Aligned Reads"` only (raw sequencing alignments, excluding derived analysis products like VCFs), then deduplicated:

| | Count |
|---|---|
| Raw file records fetched | 35,828 |
| Unique samples (after curation) | 1,930 |
| Unique patients | 944 |
| **Samples with all 4 assays (WGS+WES+RNA-seq+ATAC-seq)** | **16** |

That 16-sample cohort was computed, not assumed — see `scripts/curate_gdc_metadata.py`. All 16 are real TCGA glioma tumor samples.

Only metadata is stored; the actual sequencing files are controlled-access (require a dbGaP application) and are never downloaded.

Current database snapshot (from `pixi run python scripts/seed_data.py`):

| | Count |
|---|---|
| Patients | 944 |
| Samples | 1,930 |
| Experiments | 4,364 |
| Analyses | 4,364 |
| Result files | 4,364 |

## Running it

### Option A: Docker (recommended, fewest moving parts)

```bash
docker compose up --build -d
docker compose exec app pixi run alembic upgrade head
docker compose exec app pixi run python scripts/seed_data.py
curl http://localhost:8000/health
```
Interactive API docs at `http://localhost:8000/docs`.

### Option B: Native (pixi + local PostgreSQL)

```bash
pixi install
sudo service postgresql start
# create the omics/omics role and omics_registry database if not already present
pixi run alembic upgrade head
pixi run python scripts/fetch_gdc_metadata.py    # optional: re-fetch from GDC yourself
pixi run python scripts/curate_gdc_metadata.py   # optional: re-curate
pixi run python scripts/seed_data.py
pixi run uvicorn omics_registry.main:app --reload
```

### CLI

```bash
pixi run omics register-analysis --experiment-id <id> --pipeline gatk-germline --version 4.5.0 --reference-genome GRCh38 --output /path/to.vcf.gz --file-type VCF
pixi run omics cohort --assays WGS --assays RNA-seq
pixi run omics cohort-export --assays WGS --assays RNA-seq --output cohort.csv
```

## Testing & CI

13 tests (unit, integration, and API-level), run against a real PostgreSQL instance — not SQLite or mocks — using SQLAlchemy's `join_transaction_mode="create_savepoint"` for per-test isolation.

```bash
pixi run pytest
pixi run ruff check .
pixi run mypy src
```

GitHub Actions runs all of the above, plus a Docker image build, on every push.

## What's deliberately not included

- **No frontend UI.** The auto-generated `/docs` (Swagger) page serves as the exploration interface.
- **No synthetic data.** The real ~944-patient GDC dataset was sufficient on its own.

## Future work

- HPC deployment via Singularity/Apptainer containers, alongside the existing Docker setup
- Nextflow pipeline integration, registering its own outputs via this platform's CLI
- A lightweight cohort-exploration UI

## Project layout

```
src/omics_registry/
|-- api/          FastAPI routes
|-- cli/          Typer CLI
|-- models/       SQLAlchemy ORM models
|-- schemas/      Pydantic request/response schemas
|-- services/     business logic (registration, cohort queries)
|-- db/           engine/session setup
`-- config.py     environment-driven settings

tests/
|-- unit/
|-- integration/
`-- (API-level tests live in integration/)

alembic/          DB migrations
scripts/          GDC fetch/curate/seed scripts
data/             checked-in curated metadata snapshot
docs/             Isabl conceptual mapping
```
