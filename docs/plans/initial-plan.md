# Phase 1 Plan — Model Selection Engine

## Context

We're buying a used car in Brazil (R$ 60k-90k, up to 5yr/80k km, city+highway mix, all categories). Phase 1 builds a data-driven scoring engine that collects data from accessible sources, scores candidate models across multiple dimensions, and outputs a ranked shortlist. This is the foundation for Phases 2 (marketplace scraper) and 3 (Telegram bot).

The system is designed **agent-first** following harness engineering principles: CLI-first tools, declarative config, structured output, idempotent operations, and tests as verification oracle. An autonomous agent (Claude Code) should be able to operate the entire pipeline without human intervention for routine runs.

## Buyer Profile (configurable via YAML)

```yaml
# config/buyer-profile.yaml
budget:
  min: 60000
  max: 90000
vehicle:
  max_age_years: 5
  max_mileage_km: 80000
  categories: [hatch, sedan, suv, crossover]
  fuel_types: [flex, hybrid]
use_case: city_highway_mix
```

## Architecture

```
project-cars/
├── CLAUDE.md                    # Agent conventions & commands
├── mise.toml                    # Single entry point: tools + env + tasks
├── compose.yml                  # Docker Compose for Postgres
├── .githooks/pre-commit         # Runs mise run check before every commit
├── config/
│   ├── buyer-profile.yaml       # Buyer constraints (above)
│   ├── scoring-weights.yaml     # Dimension weights for ranking
│   └── sources.yaml             # Data source URLs, rate limits, selectors
├── db/
│   └── migrations/              # SQL migration files (yoyo-migrations)
├── src/
│   ├── collectors/              # One module per data source
│   │   ├── __init__.py
│   │   ├── fipe.py              # FIPE Parallelum API client
│   │   ├── latin_ncap.py        # Latin NCAP JSON endpoint
│   │   ├── carros_na_web.py     # Carros na Web HTML scraper
│   │   ├── carroclub.py         # CarroClub HTML scraper
│   │   └── inmetro_pbev.py      # Inmetro PDF parser (one-time)
│   ├── models.py                # Pydantic data models
│   ├── scoring.py               # Scoring & ranking engine
│   ├── candidates.py            # Candidate discovery (FIPE scan)
│   ├── db.py                    # Postgres persistence (psycopg3, upserts)
│   ├── db_migrate.py            # yoyo migration runner
│   └── cli.py                   # CLI entry point (typer)
├── data/
│   ├── raw/                     # Raw fetched data (JSON/HTML snapshots)
│   └── processed/               # Cleaned, normalized data
├── tests/
│   ├── unit/                    # Unit tests per collector
│   ├── integration/             # End-to-end pipeline tests
│   └── fixtures/                # Sample API responses, HTML pages
├── output/                      # Generated reports & rankings
├── pyproject.toml               # Python project config (uv)
└── uv.lock                      # Locked dependencies
```

## Implementation Steps

### Step 1 — Project Scaffolding & Harness ✅

Set up the agent-friendly foundation before any data work.

**Version this plan:** Copy this plan to `docs/plans/phase-1-model-selection.md` so it's git-tracked from the start. All plans and architectural decisions live in `docs/` as versioned artifacts (harness engineering principle: knowledge must live in the repository).

**Files to create:**
- `CLAUDE.md` — project conventions, exact commands, architectural rules
- `mise.toml` — standardized targets: `mise run test`, `mise run lint`, `mise run collect`, `mise run score`, `mise run report`
- `pyproject.toml` — Python 3.12+, dependencies: `httpx`, `beautifulsoup4`, `pdfplumber`, `pydantic`, `typer`, `rich`, `sqlite-utils`, `pyyaml`, `pytest`
- `config/buyer-profile.yaml`, `config/scoring-weights.yaml`, `config/sources.yaml`

**CLAUDE.md essentials:**
- Build/test commands: `mise run test`, `mise run lint`, `mise run check`
- Architecture: collectors are independent, stateless functions; db.py handles all persistence; cli.py is the only entry point
- Conventions: all CLI commands support `--json` and `--dry-run`; collectors return typed Pydantic models; never print — use `rich` for human output, JSON for machine output
- Never do: hardcode URLs (use sources.yaml), commit raw HTML/API snapshots to git

### Step 2 — Shared Infrastructure (finish the harness) ✅

Before any feature code, build the downstream enforcement and shared utilities that all collectors depend on. This is still harness — not features.

#### 2a. Error Types (`src/errors.py`)

Implement the error taxonomy defined in harness principles as Python classes:
- `CollectorError` base class with `error_type`, `detail`, `suggestions`, `retriable`, `retry_after_seconds`
- Subclasses: `RetriableError`, `NonRetriableError`, `ConfigError`, `RateLimitedError`
- All errors serialize to RFC 7807-style dicts for structured output
- Tests: verify serialization, verify `suggestions` is always non-empty

#### 2b. Config Loader (`src/config.py`)

Load and validate YAML config files using Pydantic:
- `BuyerProfile` model from `config/buyer-profile.yaml`
- `ScoringWeights` model from `config/scoring-weights.yaml` (validate weights sum to 1.0)
- `SourcesConfig` model from `config/sources.yaml`
- Single `load_config()` function that returns all three, with path overrides for testing
- Tests: valid config loads, invalid config raises clear errors, missing file raises `ConfigError`

#### 2c. Database Layer (`src/db.py` + `src/db_migrate.py`)

**Migration runner (`src/db_migrate.py`):**
- Wraps `yoyo-migrations` to apply SQL files from `db/migrations/`
- Reads `DATABASE_URL` from environment
- Tests: migration runner applies and rolls back cleanly

**First migration (`db/migrations/0001.create-core-tables.sql`):**
- `vehicle_models` — brand, model, category, fipe_code (natural key: brand+model)
- `fipe_prices` — fipe_code, year, reference_month, price_brl, fuel_type (natural key: fipe_code+year+reference_month+fuel_type)
- `safety_ratings` — brand, model, protocol, stars, adult_pct, child_pct, pedestrian_pct, safety_assist_pct
- `fuel_efficiency` — brand, model, version, city_kml, highway_kml, rating
- `maintenance_costs` — brand, model, interval_km, cost_brl
- `owner_ratings` — brand, model, source, dimension_scores (jsonb), overall, review_count
- `theft_index` — brand, model, index_value
- `model_scores` — brand, model, dimension_scores (jsonb), weighted_total, rank

All tables include `created_at` and `updated_at` timestamps.

**Persistence layer (`src/db.py`):**
- `get_connection()` — returns a `psycopg` connection from `DATABASE_URL`
- `upsert_*()` helpers for each table — `INSERT ... ON CONFLICT DO UPDATE`
- `query_*()` helpers for reading (candidates list, scores, etc.)
- All writes keyed on natural identifiers, never auto-increment
- Tests: upsert idempotency (insert twice → same result), query returns expected shape

#### 2d. Test Infrastructure

- `tests/conftest.py` — shared fixtures: test DB setup/teardown, config loader with test defaults
- `tests/fixtures/` — sample JSON/HTML responses (start with FIPE API sample)
- `tests/helpers.py` — HTTP response mocking pattern using `pytest-httpx`
- Integration test: `mise run db:up` → migrate → insert sample row → query → verify → teardown

**Pydantic data models (`src/models.py`):**
- `VehicleModel` — brand, model, category, fipe_code
- `FipePrice` — fipe_code, year, price_brl, reference_month, fuel_type
- `DepreciationCurve` — model, prices over time, annual_depreciation_pct
- `SafetyRating` — brand, model, protocol, stars, adult/child/pedestrian/safety_assist percentages
- `FuelEfficiency` — brand, model, version, city_kml, highway_kml, rating (A-E)
- `MaintenanceCost` — brand, model, interval_km, cost_brl
- `OwnerRating` — brand, model, source, dimension_scores (dict), overall, review_count
- `TheftIndex` — brand, model, index_value
- `ModelScore` — brand, model, dimension_scores (dict), weighted_total, rank

**Step 2 exit criteria:** `mise run check` passes with error types, config loader, DB layer, and Pydantic models all tested. `mise run db:migrate` creates all tables. An agent can run `mise run db:status` and get meaningful output.

**Step 2 manual verification:**
- [ ] `mise run db:up` starts Postgres, `mise run db:status` shows healthy
- [ ] `mise run db:migrate` creates all 8 tables (vehicle_models, fipe_prices, safety_ratings, fuel_efficiency, maintenance_costs, owner_ratings, theft_index, model_scores) — verify with `mise run db:shell` then `\dt`
- [ ] Running `mise run db:migrate` a second time prints "No pending migrations." (idempotent)
- [ ] `mise run db:reset && mise run db:migrate` recreates everything cleanly from scratch
- [ ] `mise run test:integ` passes (upserts and idempotency against real Postgres)
- [ ] Config validation: edit `config/scoring-weights.yaml` to make weights sum to 0.5, run `uv run python -c "from src.config import load_config; load_config()"` — should raise a clear error about weights summing to 1.0. Revert after.
- [ ] Error serialization: run `uv run python -c "from src.errors import RateLimitedError; print(RateLimitedError('429 on /cars').to_dict())"` — should print RFC 7807-style dict with suggestions and retry_after_seconds

### Step 3 — First Vertical Slice (FIPE collector end-to-end)

Prove the full collect → store → query pattern with the simplest source before building the rest.

#### 3a. Candidate Discovery (`src/candidates.py` + `src/collectors/fipe.py`)

1. Scan FIPE API (Parallelum v2) for all brands → all models → filter by year range (2021-2026)
2. For each model+year, fetch FIPE price
3. Filter to budget range from `config/buyer-profile.yaml` (R$ 60k-90k)
4. Persist candidate list to DB via `db.py`
5. CLI: `mise run candidates` → outputs candidate list as table or JSON

**Rate limit management:** Parallelum API = 500 req/day free.
- Cache aggressively — only fetch what's not in DB
- Use BrasilAPI as fallback/supplement (different rate limit, returns all years in one call)
- Run discovery incrementally, resumable via DB state
- `--dry-run` shows what would be fetched without making requests

**Expected output:** ~30-60 candidate models across all categories in the target price range.

#### 3b. FIPE Historical Prices (depreciation curves)

For each candidate, fetch prices across multiple reference months to build depreciation curve. Calculate annual depreciation %.

**Rate limit:** 500/day Parallelum, supplement with BrasilAPI `/fipe/preco/v1/{code}` (returns all years in one call).

#### 3c. Tests & Verification

- Unit tests with fixtures: saved FIPE API JSON responses in `tests/fixtures/fipe/`
- Test the full loop: mock API → collector returns Pydantic models → `db.py` upserts → query returns data
- Integration test: `mise run collect:fipe --dry-run` shows planned requests; `mise run status` shows progress

**Step 3 exit criteria:** `mise run candidates` populates the DB. `mise run collect:fipe` fetches and stores historical prices. `mise run status` shows per-model collection progress. All tests pass.

### Step 4 — Remaining Collectors (replicate proven pattern)

Each collector follows the exact pattern from Step 3: fetch → parse → return Pydantic models → store via `db.py`. Each has unit tests with fixtures.

#### 4a. Latin NCAP Collector (`latin_ncap.py`)
- **Source:** `https://www.latinncap.com/get_res.php` (JSON, no auth)
- **Data:** Stars, adult/child/pedestrian/safety_assist percentages
- **Key logic:** Single fetch returns all 166 tested vehicles. Match against candidates by brand+model fuzzy matching (names differ between FIPE and NCAP). Cache the full dataset.
- **Edge case:** Many budget models may not have NCAP ratings — flag these as "not tested"

#### 4b. Carros na Web Collector (`carros_na_web.py`)
- **Source:** HTML scraping of `analise.asp`, `opiniaolista.asp`, `roubadosestatistica.asp`
- **Data:** Maintenance schedule + costs, owner ratings (16 dimensions), theft index, annual sales volume, recall history
- **Key logic:** Need to discover numeric `codigo` IDs per model. Scrape `analiseindice.asp` or build a mapping. Parse HTML tables positionally (no CSS classes, Classic ASP).
- **Rate limit:** Be respectful — 1 req/sec with exponential backoff on 500s

#### 4c. CarroClub Collector (`carroclub.py`)
- **Source:** HTML scraping of `/carros/{brand}/{model}/opiniao-do-dono/`
- **Data:** Owner ratings (9 dimensions), aggregate score, review count
- **Key logic:** URL pattern is clean and predictable. Paginated (10 per page). Parse aggregate scores from model page, individual reviews from paginated list.
- **Cross-reference:** Overlap with Carros na Web owner data — keep both, average in scoring

#### 4d. Inmetro PBEV Collector (`inmetro_pbev.py`)
- **Source:** PDF download from gov.br
- **Data:** Fuel efficiency (city/highway km/L), energy rating (A-E) for ~895 models
- **Key logic:** One-time extraction. Download 2024 + 2025 PDFs, extract tables with `pdfplumber`. Match models by brand+model+version fuzzy matching.
- **Caching:** Parse once, store in DB. Re-parse only when a new PDF is published.

**Step 4 exit criteria:** `mise run collect` runs all collectors. `mise run status` shows complete data coverage. All tests pass.

### Step 5 — Scoring Engine

Normalize and weight all dimensions to produce a ranked output.

**Scoring config (`scoring-weights.yaml`):**
```yaml
weights:
  depreciation: 0.20      # Lower annual depreciation = better
  maintenance_cost: 0.15   # Lower avg annual cost = better
  owner_satisfaction: 0.15  # Higher aggregate rating = better
  safety: 0.15             # Higher NCAP stars/% = better
  fuel_efficiency: 0.10    # Higher km/L = better
  theft_risk: 0.10         # Lower theft index = better
  resale_liquidity: 0.10   # Higher annual sales volume = better
  price_vs_fipe: 0.05      # How close to budget sweet spot
```

**Normalization:** Min-max scaling within each dimension across candidates. Missing data → penalize by assigning median score (not zero, to avoid unfair punishment for missing NCAP test).

**Output:**
- Ranked table with scores per dimension and weighted total
- Per-model detail cards (all raw data + scores)
- Comparison charts (exportable)
- CLI: `mise run score` → ranked table; `mise run report` → full markdown report in `output/`

**Step 5 exit criteria:** `mise run score` reads collected data from DB, normalizes, weights, and outputs a ranked table. Tests cover edge cases: missing dimensions, ties, boundary values.

### Step 6 — Report Generation

Generate a human-readable report with the ranked shortlist.

- Markdown report in `output/report-{date}.md`
- Top 10 ranked models with score breakdown
- Per-model deep dive for top 5
- Data quality notes (which models had missing data, from which sources)
- Recommended shortlist of 2-3 models with rationale

**Step 6 exit criteria:** `mise run report` produces a complete markdown report. The full pipeline (`mise run candidates` → `mise run collect` → `mise run score` → `mise run report`) runs end-to-end.

## CLI Interface

```
car-selector candidates [--budget-min N] [--budget-max N] [--max-age N] [--dry-run] [--json]
car-selector collect [--source fipe|ncap|cnw|carroclub|inmetro|all] [--model MODEL] [--dry-run] [--json]
car-selector score [--weights-file PATH] [--json]
car-selector report [--top N] [--output-dir PATH]
car-selector status                    # Show collection progress per source per model
```

All commands: `--json` for machine output, `--dry-run` for preview, `--verbose` for debug logging. Exit codes: 0=success, 1=expected failure (no data), 2=unexpected error.

## mise.toml Tasks

```
test            # Run all tests
test:unit       # Unit tests only
test:integ      # Integration tests (hits real APIs, slower)
lint            # ruff check + ruff format --check
format          # ruff format
check           # lint + test:unit (pre-commit gate)
candidates      # Discover candidate models from FIPE
collect         # Run all collectors for all candidates
collect:fipe    # Run FIPE collector only
collect:ncap    # Run Latin NCAP collector only
collect:cnw     # Run Carros na Web collector only
collect:club    # Run CarroClub collector only
collect:inmetro # Run Inmetro collector only
score           # Score and rank all candidates
report          # Generate markdown report
status          # Show data collection progress
```

## Agent-Driven Design Principles Applied

1. **CLAUDE.md as the entry point** — exact commands, architectural rules, permission tiers (always/ask-first/never)
2. **mise.toml as task discovery** — `mise tasks` (or `mise tasks --json`) gives agents the full menu
3. **Declarative config** — buyer profile, weights, sources all in YAML; change behavior without changing code
4. **Idempotent operations** — upsert DB writes, cached API responses, resumable collection
5. **Structured output** — every command supports `--json`; no print-only diagnostics
6. **`--dry-run` on all mutating commands** — agents preview before acting
7. **Tests as verification oracle** — unit tests with fixtures, integration tests against real APIs
8. **Structured errors** — typed error categories (retriable/non-retriable/config) with suggested actions
9. **Progressive disclosure** — CLAUDE.md points to config files and docs, doesn't dump everything

## Verification Plan

**Per-step gates (must pass before moving to next step):**
1. **Step 2 gate:** `mise run check` passes with error types, config, DB layer, and models tested. `mise run db:migrate` creates all tables successfully.
2. **Step 3 gate:** `mise run candidates` populates DB. `mise run collect:fipe` stores data. `mise run status` shows progress. Full vertical slice works.
3. **Step 4 gate:** `mise run collect` runs all collectors. `mise run status` shows complete coverage.
4. **Step 5 gate:** `mise run score` outputs ranked table. Scoring tests cover missing data, ties, boundary values.
5. **Step 6 gate:** Full pipeline end-to-end: `mise run candidates` → `mise run collect` → `mise run score` → `mise run report` produces a complete report.

**Ongoing verification:**
- Unit tests with fixtures for every collector (no live network calls)
- Integration tests clearly separated in `tests/integration/`
- Manual spot-checks: 3-5 models verified against FIPE website and Carros na Web
- Agent verification: Claude Code can run `mise run check && mise run candidates --dry-run && mise run status` and get meaningful, actionable output

## Dependencies

```
httpx              # HTTP client (async-ready, better than requests)
beautifulsoup4     # HTML parsing
pdfplumber         # PDF table extraction (Inmetro)
pydantic           # Data models + validation
typer              # CLI framework
rich               # Human-readable terminal output
psycopg[binary]    # PostgreSQL driver (psycopg3)
yoyo-migrations    # Schema migrations (plain SQL files)
pyyaml             # Config parsing
ruff               # Linter + formatter
pytest             # Testing
pytest-httpx       # HTTP mocking for tests
```

Package manager: `uv` (fast, lockfile support). Runtimes managed by `mise`.

## What This Plan Does NOT Cover (deferred to later)

- Playwright/headless browser scraping (KBB, Reclame Aqui) — Phase 2 concern
- Marketplace listing scraping (OLX, Webmotors) — Phase 2
- Telegram bot — Phase 3
- MCP server exposure — will add when Phase 2 needs cross-language integration
- TypeScript components — not needed until Playwright scraping in Phase 2
