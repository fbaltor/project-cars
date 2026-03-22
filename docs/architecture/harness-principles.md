# Harness Engineering Principles

> Actionable subset of agent-driven architecture patterns for this project.
> Full research: `~/.claude/research/2026-03-22-harness-engineering-agent-driven-architecture.md`

## CLI Design

- Every command supports `--json` (machine output) and `--dry-run` (preview without side effects)
- Exit codes: 0=success, 1=expected failure (no data, validation error), 2=unexpected error
- `--verbose` / `--quiet` for log control
- Never print raw — use `rich` for humans, JSON for machines
- Prefer `typer` or `click` for Python CLIs

## Data Integrity

- **Upsert semantics** for all DB writes — never blind inserts
- Key records on **natural identifiers** (brand+model+year, URL+date), not auto-increment
- Include `run_id` in output artifacts so re-runs are detectable
- All operations must be **idempotent** — running twice = same result as once

## Scraping & Data Pipelines

- **Checkpoint progress** to DB at defined intervals; support `--resume <job_id>`
- **Cache raw responses** to `data/raw/` for debugging and replay
- **Rate limit management**: respect targets, exponential backoff, configurable concurrency
- **Error taxonomy** — every error must be classified:
  - `RETRIABLE`: HTTP 429, transient 503 → wait and retry
  - `NON_RETRIABLE`: 404, structural change → alert and skip
  - `CONFIG_ERROR`: wrong selector, wrong URL → halt, require human
  - `RATE_LIMITED`: backoff, rotate proxy
- Emit structured events at stage boundaries: `scrape_started`, `page_fetched`, `parse_failed`, `record_written`, `job_completed`

## Structured Errors

Follow RFC 7807 pattern in internal error handling:
```python
{
    "error_type": "RATE_LIMITED",
    "detail": "429 on /cars/page/12",
    "suggestions": ["Wait 60s", "Reduce concurrency"],
    "retriable": True,
    "retry_after_seconds": 60
}
```
Always include `suggestions` — without them, the agent hallucinates recovery steps.

## Configuration

- **Declarative YAML** for all behavior-changing settings (buyer profile, scoring weights, source URLs, rate limits)
- Change behavior by editing config, not code
- Config files live in `config/` — never hardcode values that could vary

## Testing

- Tests are the **verification oracle** — the single highest-leverage investment
- Unit tests with **fixtures** (saved API responses, HTML snapshots) — no live network calls
- Integration tests clearly separated (`tests/integration/`) — may hit real APIs, slower
- Every collector must be independently testable

## Repository as Source of Truth

- All knowledge lives in the repo — Slack threads, verbal context, external docs are invisible to agents
- Plans and architectural decisions go in `docs/` (versioned)
- Research and investigation notes reference external sources with URLs

## Context Management

- Keep CLAUDE.md under 100 lines — progressive disclosure to deeper docs
- Use `@imports` for domain-specific docs, not inline dumps
- Prefer many small focused files over large omnibus files
- Command outputs should return only relevant data — truncate with direction, not silently

## Entropy Prevention

- Follow existing patterns in the codebase — check before creating new ones
- One way to do each thing — if a pattern exists, use it
- Linters and formatters as mechanical enforcement (ruff for Python)
- Structural tests for architectural boundaries where applicable

## Module Design

- Collectors are **independent, stateless functions** — take input, return typed Pydantic models
- `db.py` handles all persistence — collectors never touch the DB directly
- `cli.py` is the only user-facing entry point
- Clear separation: collect → store → score → report
