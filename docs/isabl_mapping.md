# Relationship to Isabl

This project is architecturally inspired by [Isabl](https://github.com/zeng-lab/isabl_api), a metadata and data-management platform used in cancer genomics research, including work published from the Curtis Lab. It is **not** a re-implementation of Isabl, does not use Isabl's codebase, and was not built with hands-on production experience with an Isabl deployment. What follows is an honest account of what was studied, what was borrowed conceptually, and where this project diverges.

## What was studied

Isabl's public documentation and API structure, specifically its core data model: a hierarchy of `Individual` -> `Sample` -> `Experiment` -> `Analysis`, with each `Analysis` carrying provenance about the application/pipeline that produced it, and `Analysis` outputs tracked as versioned, typed result objects.

## Conceptual mapping

| This project | Isabl concept | Notes |
|---|---|---|
| `Patient` | `Individual` | Renamed for clarity in a clinical/TCGA context |
| `Sample` | `Sample` | Tumor/normal, tissue, and free-form metadata |
| `Experiment` | roughly `Experiment`/assay input | An assay run (WGS/WES/RNA-seq/ATAC-seq) on a sample |
| `Analysis` | `Analysis` | A pipeline run, with provenance fields |
| `Analysis.pipeline_name` + `pipeline_version` | `Application` + version | Which tool produced this analysis |
| `Analysis.parameters` (JSONB) | Analysis parameters | Arbitrary pipeline arguments |
| `ResultFile` | `Analysis` result/output | A typed, checksummed output artifact |

## Where this project intentionally diverges

- **Scale and scope**: Isabl is a full production platform with a web UI, permissions, application/pipeline execution orchestration, and years of real-world use across multiple labs. This project is a scoped, single-developer build focused on the metadata/provenance/cohort-query layer specifically.
- **No pipeline orchestration**: Isabl (in some deployments) integrates with pipeline execution. This project only *records* that a pipeline ran, via `register-analysis`; it does not launch or manage pipeline execution itself. Nextflow integration is listed as future work.
- **No UI**: Isabl ships a web dashboard (sample tree, analysis views, result browsers). This project relies on FastAPI's auto-generated `/docs` for interactive exploration; a custom UI was deliberately scoped out.
- **Simplified hierarchy**: this project's schema is intentionally smaller than Isabl's full data model, to fit a multi-day build rather than a production system.

## Honest summary

The goal of this mapping is not to claim Isabl experience that doesn't exist. It's to show that the core data-modeling problem Isabl solves — tracking multimodal genomic samples, their assays, and full analysis provenance, in a way that supports cohort discovery — was understood well enough to independently design a working, tested system around the same conceptual structure.
