import typer

app = typer.Typer(help="Car model selection engine for the Brazilian market.")


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
        "config/scoring-weights.yaml", help="Path to scoring weights YAML"
    ),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
) -> None:
    """Score and rank all candidates."""
    typer.echo("score: not implemented yet")
    raise typer.Exit(1)


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
