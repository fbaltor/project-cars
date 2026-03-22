# Data Sources — Access & Status

> Living reference for all data sources. Update as access changes or new sources are added.

## Accessible (Phase 1)

| Source | Access Method | Format | Rate Limit | Key Data |
|---|---|---|---|---|
| FIPE (Parallelum API) | REST API, no auth | JSON | 500 req/day free | Current + historical pricing |
| FIPE (BrasilAPI) | REST API, no auth | JSON | Undocumented | Price history by FIPE code |
| Latin NCAP | `get_res.php` endpoint, no auth | JSON | None observed | 166 vehicles, stars + 4 sub-scores |
| Carros na Web | HTML scraping (`analise.asp`, `opiniaolista.asp`, `roubadosestatistica.asp`) | HTML tables | ~1 req/sec recommended | Maintenance costs, owner ratings (16 dims), theft index, sales volume, recalls |
| CarroClub | HTML scraping (`/carros/{brand}/{model}/opiniao-do-dono/`) | HTML | ~1 req/sec recommended | Owner ratings (9 dims), aggregate scores, review count |
| Inmetro PBEV | PDF download from gov.br | PDF (needs pdfplumber) | N/A (one-time) | Fuel efficiency for ~895 models, energy rating A-E |

## Blocked / Limited (Phase 2 or manual)

| Source | Status | What's Needed | Key Data |
|---|---|---|---|
| KBB Brasil | 403 on all HTTP (Cloudflare) | Playwright/headless browser | Market-adjusted pricing by condition/mileage/region |
| Reclame Aqui | 403 on HTTP; internal API now requires auth | Playwright or commercial API (OAuth2) | Complaint volume, resolution rates, per-brand scores |
| FlatOut! | Soft paywall (~40% free, 7 articles/mo) | Subscription (R$14.90/mo) for full text | Qualitative editorial reviews |
| Quatro Rodas | Hard network block + paywall | Subscription + manual reading | Buyer's guide ("Qual Comprar"), long-term tests |
| Insurance comparators | Requires form submission | Playwright or manual lookup | Annual insurance cost estimates |

## API Details

### FIPE — Parallelum API v2

```
Base: https://parallelum.com.br/fipe/api/v2
GET /cars/brands
GET /cars/brands/{brandId}/models/{modelId}/years/{yearId}
```

Year code format: `{year}-{fuelCode}` (5=Flex, 6=Hybrid, 1=Gasoline).

### FIPE — BrasilAPI

```
Base: https://brasilapi.com.br/api/fipe
GET /tabelas/v1              # 331 reference months
GET /marcas/v1/carros        # 89 brands
GET /veiculos/v1/carros/{brandId}
GET /preco/v1/{codigoFipe}   # All years for a FIPE code in one call
```

### Latin NCAP

```
POST https://www.latinncap.com/get_res.php
Returns JSON: { "a15": [...], "a19": [...], "a20": [...] }
Fields: id, tit_marca, nombre, a20_main_stars, a20_percentage_a/c/p/s
Detail: https://www.latinncap.com/en/result/{id}/{slug}
```

### Carros na Web

```
Base: https://www.carrosnaweb.com.br
Analysis:       /analise.asp?codigo={numeric_id}
Owner opinions: /opiniaolista.asp?fabricante={brand}&modelo={model}
Theft stats:    /roubadosestatistica.asp
Rankings:       /rankinglista.asp?ordem={N}
Safety:         /rankinglistaseguranca.asp?ordem=9
```

Note: `fichadetalhe.asp` pages (depreciation, specs) returned HTTP 500 during testing — may be rate-limited or unstable.

### CarroClub

```
Base: https://www.carroclub.com.br
All reviews:  /carros/{brand}/{model}/opiniao-do-dono/
By year:      /carros/{brand}/{model}/{year}/opiniao-do-dono/
```

### Inmetro PBEV

PDFs downloadable from gov.br. No CSV/JSON alternative exists publicly.

```
2025: .../mascara-pbev-2025-mar-11.pdf/@@download/file  (800 KB, 895 models)
2024: .../pbe-veicular-2024-1.pdf/@@download/file       (615 KB)
```
