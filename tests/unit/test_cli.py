from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Car model selection engine" in result.output


def test_cli_candidates_help():
    result = runner.invoke(app, ["candidates", "--help"])
    assert result.exit_code == 0
    assert "--dry-run" in result.output
    assert "--json" in result.output


def test_cli_collect_help():
    result = runner.invoke(app, ["collect", "--help"])
    assert result.exit_code == 0
    assert "--source" in result.output


def test_cli_score_help():
    result = runner.invoke(app, ["score", "--help"])
    assert result.exit_code == 0
    assert "--weights-file" in result.output


def test_cli_status_help():
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0
    assert "--json" in result.output
