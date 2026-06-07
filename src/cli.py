import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.config import load_config
from src.db import (
    get_cursor,
    query_fipe_prices,
    query_fuel_efficiency,
    query_maintenance_costs,
    query_owner_ratings,
    query_safety_ratings,
    query_theft_index,
    query_vehicle_models,
    upsert_model_score,
)
from src.scorer import score_candidates

app = typer.Typer(help="Car model selection engine for the Brazilian market.")
console = Console()


@app.command()
def candidates(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without fetching"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
) -> None:
    """Discover candidate models from FIPE within budget range."""
    typer.echo("candidates: not implemented yet")
    raise typer.Exit(1)


@app.command()
def collect(
    source: str = typer.Option("all", help="Source: fipe|ncap|cnw|carroclub|inmetro|all"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without fetching"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
) -> None:
    """Run data collectors for candidate models."""
    typer.echo(f"collect ({source}): not implemented yet")
    raise typer.Exit(1)


@app.command()
def score(
    weights_file: str = typer.Option(
        "config/scoring-weights.yaml", "--weights-file", help="Path to scoring weights YAML"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Score without writing to the DB"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
) -> None:
    """Score and rank all candidates."""
    cfg = load_config(scoring_path=Path(weights_file))

    with get_cursor() as cur:
        vehicles = query_vehicle_models(cur)
        fipe = query_fipe_prices(cur)
        safety = query_safety_ratings(cur)
        fuel = query_fuel_efficiency(cur)
        maintenance = query_maintenance_costs(cur)
        owners = query_owner_ratings(cur)
        theft = query_theft_index(cur)

        scores = score_candidates(
            vehicles,
            fipe,
            safety,
            fuel,
            maintenance,
            owners,
            theft,
            cfg.scoring,
        )

        if not dry_run:
            for ms in scores:
                upsert_model_score(cur, ms)

    if json_output:
        typer.echo(json.dumps([ms.model_dump(mode="json") for ms in scores]))
        return

    if not scores:
        console.print("[yellow]No candidates to score. Run collectors first.[/yellow]")
        raise typer.Exit(1)

    table = Table(title="Ranked candidates")
    table.add_column("Rank", justify="right")
    table.add_column("Brand")
    table.add_column("Model")
    table.add_column("Weighted total", justify="right")
    for ms in scores:
        table.add_row(str(ms.rank), ms.brand, ms.model, f"{ms.weighted_total:.4f}")
    console.print(table)
    if dry_run:
        console.print("[dim]--dry-run: no scores were written to the database.[/dim]")


@app.command()
def report(
    top: int = typer.Option(10, help="Number of top models to include"),
    output_dir: str = typer.Option("output/", help="Output directory for report"),
) -> None:
    """Generate markdown report with ranked shortlist."""
    typer.echo("report: not implemented yet")
    raise typer.Exit(1)


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
) -> None:
    """Show data collection progress per source per model."""
    typer.echo("status: not implemented yet")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
