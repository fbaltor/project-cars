# Project Roadmap

## Architecture Overview

```
[Scheduler/Cron] → [Scraper (Playwright)] → [Scoring/Filtering Engine]
                                                      ↓
                                              [Database (Postgres)]
                                                      ↓
                                              [Notification Service]
                                                      ↓
                                              [Telegram Bot]
```

## Phase 1 — Model Selection (current)

Detailed plan: `docs/plans/initial-plan.md`

Narrow down to 2-3 target models using quantitative data from FIPE, Latin NCAP, Carros na Web, CarroClub, and Inmetro PBEV. Python + mise + Postgres.

## Phase 2 — Marketplace Scraper

Build a crawler that routinely scans Brazilian car marketplaces for the target models selected in Phase 1.

**Target marketplaces:** OLX, Webmotors, iCarros, Kavak/InstaCarro.

**Scoring criteria per listing:**
- Deviation from FIPE/mean price
- Mileage-to-age ratio
- Seller reputation
- Listing age
- Location

**Technical considerations:**
- These sites use anti-bot measures (Cloudflare, CAPTCHAs)
- Likely need Playwright (TypeScript) with rotating proxies
- Scheduled via cron or similar
- Also adds KBB and Reclame Aqui data via headless browser

## Phase 3 — Telegram Bot Integration

Wire the scraper to a Telegram bot for notifications and commands.

**Features:**
- Receive alerts when a listing scores above threshold
- Query current top listings on demand
- Send messages / interact with interesting listings
- Configure filters and thresholds via chat

**Why Telegram over WhatsApp:**
- Official Bot API — free, stable, well-documented
- No account ban risk
- Trivial to set up vs. WhatsApp Business API approval or unofficial library fragility
