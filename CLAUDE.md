# Project Cars

Agent-driven car buying tool for the Brazilian market. Polyglot (Python + TypeScript), CLI-first.

@docs/architecture/harness-principles.md

## Commands

```
mise run test           # Run all tests
mise run test:unit      # Unit tests only
mise run test:integ     # Integration tests (needs Postgres running)
mise run lint           # ruff check + format check
mise run check          # lint + test:unit (pre-commit gate)
mise run db:up          # Start Postgres (docker compose)
mise run db:migrate     # Apply pending schema migrations
mise run db:status      # Show Postgres container health
mise run db:reset       # Destroy and recreate DB (DELETES ALL DATA)
mise run db:shell       # Open psql shell
mise run candidates     # Discover candidate models from FIPE
mise run collect        # Run all collectors
mise run collect:fipe   # Run a specific collector
mise run score          # Score and rank candidates
mise run report         # Generate markdown report
mise run status         # Show data collection progress
```

Discover all tasks: `mise tasks` or `mise tasks --json`

## Architecture

```
mise.toml              # Single entry point: tools + env + tasks
compose.yml            # Docker Compose for Postgres
config/                # Declarative YAML (buyer profile, weights, sources)
src/errors.py          # Structured error taxonomy (RFC 7807 pattern)
src/config.py          # Config loader — validates YAML via Pydantic
src/models.py          # Pydantic data models (all domain entities)
src/collectors/        # One module per data source — independent, stateless
src/scoring.py         # Scoring & ranking engine
src/db.py              # Postgres persistence (psycopg3, all DB access goes through here)
src/db_migrate.py      # yoyo migration runner
src/cli.py             # CLI entry point (only user-facing interface)
db/migrations/         # SQL migration files (yoyo-migrations)
data/raw/              # Cached raw responses (not versioned)
data/processed/        # Cleaned data (not versioned)
tests/fixtures/        # Saved API/HTML responses for unit tests
tests/conftest.py      # Shared test fixtures
tests/helpers.py       # HTTP mocking utilities
docs/plans/            # Versioned plans and ADRs
docs/architecture/     # Architecture docs and principles
```

## Conventions

- Python 3.14+, runtimes managed with `mise`, packages managed with `uv`
- All CLI commands support `--json` and `--dry-run`
- Collectors return typed Pydantic models — never raw dicts
- DB writes use upsert on natural keys — never blind inserts
- Errors must be classified: RETRIABLE, NON_RETRIABLE, CONFIG_ERROR, RATE_LIMITED
- Config in `config/*.yaml` — never hardcode URLs, thresholds, or credentials
- Use `mise run <task>` (not `mise <task>`) in scripts to avoid future name conflicts

## Never

- Commit raw data (`data/`) or output (`output/`) to git
- Hardcode source URLs — use `config/sources.yaml`
- Make collectors touch the DB directly — always go through `db.py`
- Skip `--dry-run` support on mutating commands
- Commit secrets or API keys
