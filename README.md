# Project Cars

Data-driven car buying tool for the Brazilian market. Collects pricing, safety, efficiency, maintenance, and owner satisfaction data from multiple sources, scores candidate models across weighted dimensions, and outputs a ranked shortlist.

## Why

Buying a used car in Brazil means cross-referencing half a dozen websites manually — FIPE tables, Latin NCAP results, owner forums, government efficiency PDFs. This project automates that research into a repeatable, data-backed pipeline.

## How it works

```
FIPE API ─────┐
Latin NCAP ───┤
Carros na Web ┤──→ Collectors ──→ Postgres ──→ Scoring Engine ──→ Ranked Report
CarroClub ────┤       (one per source,          (upsert on           (weighted
Inmetro PBEV ─┘        stateless)              natural keys)        dimensions)
```

1. **Discover** candidate models from FIPE within a configurable budget range
2. **Collect** data from each source into typed Pydantic models
3. **Store** everything in Postgres via idempotent upserts
4. **Score** candidates across 8 dimensions with configurable weights
5. **Report** a ranked shortlist as markdown

All behavior is configurable via YAML in `config/` — budget, vehicle constraints, scoring weights, source URLs, and rate limits.

## Prerequisites

- [mise](https://mise.jdx.dev/) (manages Python, uv, and task runner)
- [Docker](https://docs.docker.com/get-docker/) (for Postgres)

## Quick start

```bash
# Install runtimes and dependencies
mise install
mise run install

# Start Postgres and apply migrations
mise run db:up
mise run db:migrate

# Verify everything works
mise run check          # lint + unit tests
mise run test:integ     # integration tests (needs Postgres)
```

## Project structure

```
mise.toml              # Single entry point: tools, env vars, tasks
compose.yml            # Docker Compose for Postgres
config/
  buyer-profile.yaml   # Budget, age, mileage, categories, fuel types
  scoring-weights.yaml # Dimension weights (must sum to 1.0)
  sources.yaml         # API URLs, rate limits, selectors
src/
  cli.py               # CLI entry point (typer) — only user-facing interface
  config.py            # Loads and validates YAML config via Pydantic
  models.py            # Domain models (VehicleModel, FipePrice, SafetyRating, ...)
  errors.py            # Structured error taxonomy (RFC 7807 pattern)
  db.py                # Postgres persistence — upserts and queries
  db_migrate.py        # yoyo migration runner
  collectors/          # One module per data source, independent and stateless
db/migrations/         # SQL migration files (yoyo-migrations)
tests/
  unit/                # Fast tests with fixtures — no network, no DB
  integration/         # Tests against real Postgres
  fixtures/            # Saved API/HTML responses for deterministic tests
docs/
  plans/               # Implementation plans and ADRs
  architecture/        # Harness principles, data source reference
```

## Common tasks

```bash
mise run test           # Run all tests
mise run test:unit      # Unit tests only (fast, no dependencies)
mise run test:integ     # Integration tests (needs Postgres)
mise run lint           # ruff check + format check
mise run format         # Auto-format with ruff
mise run check          # lint + test:unit (pre-commit gate)

mise run db:up          # Start Postgres via Docker Compose
mise run db:migrate     # Apply pending schema migrations
mise run db:shell       # Open psql shell against dev database
mise run db:status      # Show Postgres container health
mise run db:reset       # Destroy and recreate DB (DELETES ALL DATA)

mise run candidates     # Discover candidate models from FIPE
mise run collect        # Run all collectors
mise run collect:fipe   # Run a specific collector
mise run score          # Score and rank candidates
mise run report         # Generate markdown report
mise run status         # Show data collection progress
```

All pipeline commands support `--json` (machine output) and `--dry-run` (preview without side effects).

Run `mise tasks` to see everything available.

## Configuration

**`config/buyer-profile.yaml`** — What you're looking for:
```yaml
budget:
  min: 60000
  max: 90000
vehicle:
  max_age_years: 5
  max_mileage_km: 80000
  categories: [hatch, sedan, suv, crossover]
  fuel_types: [flex, hybrid]
```

**`config/scoring-weights.yaml`** — How to rank candidates (weights must sum to 1.0):
```yaml
weights:
  depreciation: 0.20
  maintenance_cost: 0.15
  owner_satisfaction: 0.15
  safety: 0.15
  fuel_efficiency: 0.10
  theft_risk: 0.10
  resale_liquidity: 0.10
  price_vs_fipe: 0.05
```

**`config/sources.yaml`** — Where data comes from (URLs, rate limits).

## Key design decisions

- **Upsert everything** — All DB writes use `INSERT ... ON CONFLICT DO UPDATE` on natural keys. Running the pipeline twice produces the same result.
- **Collectors are stateless** — Each collector takes input, calls an API/scrapes a page, and returns typed Pydantic models. No DB access, no shared state.
- **All DB access through `db.py`** — Single persistence layer, no direct SQL in collectors or CLI.
- **Structured errors** — Every error carries a type (RETRIABLE, NON_RETRIABLE, CONFIG_ERROR, RATE_LIMITED) and actionable suggestions.
- **Config over code** — Change behavior by editing YAML, not source files.

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Model selection engine (scoring pipeline) | In progress |
| 2 | Marketplace scraper (OLX, Webmotors, Playwright) | Planned |
| 3 | Telegram bot for alerts and queries | Planned |

See `docs/plans/` for detailed plans.
