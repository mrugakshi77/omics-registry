from fastapi import FastAPI

from omics_registry.api import analyses, cohort, experiments, patients, samples

app = FastAPI(
    title="Omics Registry",
    description="A small, production-style genomics metadata, provenance, and cohort-management platform.",
    version="0.1.0",
)

app.include_router(patients.router)
app.include_router(samples.router)
app.include_router(experiments.router)
app.include_router(analyses.router)
app.include_router(cohort.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}
