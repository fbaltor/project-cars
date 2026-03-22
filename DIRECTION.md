# Project Cars — Direction Document

## Goal

Buy a used car in Brazil through a systematic, data-driven approach.

## Approach — Three Phases

### Phase 1 — Model Selection

Narrow down to 2-3 target models using quantitative data across multiple dimensions:

| Dimension | Primary Source | Access Method |
|---|---|---|
| Pricing & depreciation | FIPE (Parallelum API / BrasilAPI) | REST JSON API, 500 req/day free |
| Maintenance cost | Carros na Web (`analise.asp`) | HTML scraping |
| Owner satisfaction | CarroClub (9 dimensions) + Carros na Web (16 dimensions) | HTML scraping |
| Safety ratings | Latin NCAP (`get_res.php`) | JSON endpoint, no auth |
| Fuel efficiency | Inmetro PBEV | One-time PDF extraction |
| Theft index | Carros na Web (`roubadosestatistica.asp`) | HTML scraping |
| Recall history | Carros na Web | HTML scraping |

**Gaps (require headless browser or manual lookup, not blocking for Phase 1):**

- KBB Brasil market-adjusted pricing — Cloudflare-blocked, needs Playwright
- Reclame Aqui complaint data — 403 on HTTP, needs Playwright
- Insurance cost estimates — manual lookup or Playwright
- Quatro Rodas / FlatOut editorial reviews — paywalled, best consumed manually

### Phase 2 — Marketplace Scraper

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
- Likely need Playwright/Puppeteer with rotating proxies
- Scheduled via cron or similar

### Phase 3 — Telegram Bot Integration

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

## Architecture Overview

```
[Scheduler/Cron] → [Scraper (Playwright)] → [Scoring/Filtering Engine]
                                                      ↓
                                              [Database (SQLite/Postgres)]
                                                      ↓
                                              [Notification Service]
                                                      ↓
                                              [Telegram Bot]
```

## Data Source Access Summary

| Source | Status | Format |
|---|---|---|
| FIPE (Parallelum API) | Full access | JSON API |
| FIPE (BrasilAPI) | Full access | JSON API |
| Latin NCAP | Full access | JSON endpoint |
| Carros na Web | Full access | HTML scraping |
| CarroClub | Full access | HTML scraping |
| Inmetro PBEV | Partial (PDF) | PDF → extract with pdfplumber |
| FlatOut! | Limited (7 articles/mo, ~40% free) | HTML |
| Reclame Aqui | Blocked (needs Playwright) | HTML/internal API |
| KBB Brasil | Blocked (needs Playwright) | HTML |
| Quatro Rodas | Fully blocked + paywalled | N/A |
