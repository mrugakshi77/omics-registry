"""Typer CLI for the Omics Registry -- the Isabl-style command-line
interface researchers use to register analyses and explore cohorts
without needing to know the REST API exists.
"""

import csv

import typer
from rich.console import Console
from rich.table import Table

from omics_registry.db.session import session_scope
from omics_registry.models.enums import AnalysisStatus, AssayType, FileType, SampleType
from omics_registry.schemas import AnalysisCreate
from omics_registry.schemas.analysis import ResultFileCreate
from omics_registry.services.cohort import find_cohort
from omics_registry.services.registry import NotFoundError, register_analysis

app = typer.Typer(help="Omics Registry CLI")
console = Console()


@app.command("register-analysis")
def register_analysis_cmd(
    experiment_id: str = typer.Option(..., help="Business-key experiment_id this analysis belongs to"),
    pipeline: str = typer.Option(..., "--pipeline", help="Pipeline name, e.g. gatk-germline"),
    version: str = typer.Option(..., "--version", help="Pipeline version, e.g. 4.5.0"),
    reference_genome: str = typer.Option(..., help="Reference genome build, e.g. GRCh38"),
    status: AnalysisStatus = typer.Option(AnalysisStatus.COMPLETED, help="Analysis status"),
    git_commit: str = typer.Option(None, help="Git commit SHA of the pipeline code, if applicable"),
    output: str = typer.Option(None, "--output", help="Path to the output result file, if any"),
    file_type: FileType = typer.Option(None, help="Type of the output file (required if --output is given)"),
) -> None:
    """Register a pipeline run's provenance, optionally with its output file."""
    result_file = None
    if output is not None:
        if file_type is None:
            console.print("[red]Error:[/red] --file-type is required when --output is given")
            raise typer.Exit(code=1)
        result_file = ResultFileCreate(file_path=output, file_type=file_type)

    data = AnalysisCreate(
        experiment_id=experiment_id,
        pipeline_name=pipeline,
        pipeline_version=version,
        git_commit=git_commit,
        reference_genome=reference_genome,
        status=status,
        result_file=result_file,
    )

    try:
        with session_scope() as db:
            analysis = register_analysis(db, data)
            console.print(
                f"[green]Registered analysis[/green] {analysis.pipeline_name}:{analysis.pipeline_version} "
                f"(status={analysis.status.value}) for experiment {experiment_id}"
            )
            if result_file:
                console.print(f"  -> output: {output}")
    except NotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e

@app.command("cohort")
def cohort_cmd(
    assays: list[AssayType] = typer.Option(..., "--assays", help="Comma-separated or repeated: --assays WGS --assays RNA-seq"),
    sample_type: SampleType = typer.Option(None, help="Filter by sample type"),
    tissue: str = typer.Option(None, help="Filter by tissue"),
) -> None:
    """Find samples that have ALL of the requested assay types."""
    with session_scope() as db:
        results = find_cohort(db, assays=assays, sample_type=sample_type, tissue=tissue)

    if not results:
        console.print("[yellow]No samples matched.[/yellow]")
        return

    table = Table(title=f"Cohort: {len(results)} samples")
    table.add_column("Patient")
    table.add_column("Sample")
    table.add_column("Type")
    table.add_column("Tissue")
    table.add_column("Assays")
    for r in results:
        table.add_row(r["patient_id"], r["sample_id"], r["sample_type"], r["tissue"], ", ".join(r["assays"]))
    console.print(table)


@app.command("cohort-export")
def cohort_export_cmd(
    assays: list[AssayType] = typer.Option(..., "--assays"),
    sample_type: SampleType = typer.Option(None),
    tissue: str = typer.Option(None),
    output: str = typer.Option(..., "--output", help="Path to write the manifest CSV"),
) -> None:
    """Export a cohort as an analysis-ready manifest CSV."""
    with session_scope() as db:
        results = find_cohort(db, assays=assays, sample_type=sample_type, tissue=tissue)

    if not results:
        console.print("[yellow]No samples matched -- nothing exported.[/yellow]")
        raise typer.Exit(code=1)

    fieldnames = ["patient_id", "sample_id", "sample_type", "tissue", "assays"]
    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({**r, "assays": "|".join(r["assays"])})

    console.print(f"[green]Exported {len(results)} samples[/green] to {output}")

if __name__ == "__main__":
    app()
