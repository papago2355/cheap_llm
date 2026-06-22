# IS IT WORTH IT? — AI Service Cost-Worth Index

A 2D-dot / pixel-art dashboard that answers one brutal question for AI subscriptions:

> **How much real value do you actually get per dollar?**

It scores AI **coding**, **image generation**, **music**, and **research** plans on a
**Cost-Worth Index (CWI, 0–100)** — normalized within each category so the best-value
plan in a class scores 100 and everything else scales against it. Updated weekly, with a
6-week trend sparkline on every card so you can *see* when a service quietly got worse
(e.g. GitHub Copilot's premium-request shift gutting frontier-model value).

![pixel dashboard](https://img.shields.io/badge/style-2d--dot-54f0b8) ![weekly](https://img.shields.io/badge/refresh-weekly-ffd23f)

---

## How it works

```
value-per-dollar  =  usable monthly value (quota + access + features)  ÷  monthly price
CWI (0–100)       =  that value-per-dollar, normalized within its category (best = 100)
```

Verdict bands: `85+ WORTH IT` · `65–84 SOLID` · `45–64 MEH` · `<45 OVERPRICED`.

CWI measures **quantity-per-dollar**. Quality, aesthetics and lock-in are deliberately
*not* in the number — they live in each card's **best for / watch out** notes. A low score
doesn't mean "bad", it means you pay a premium per unit (Midjourney is the classic case).

> Figures are **curated human estimates** of usable value, not scraped invoices.
> Compare classes, not absolutes.

## Tech stack

Zero-build static site — just HTML/CSS/vanilla JS. No framework, no bundler, nothing to
break on deploy. Data is generated into `js/data.js` by a small Python script.

```
.
├── index.html              # the page
├── css/styles.css          # pixel-art theme (Press Start 2P + VT323, CRT scanlines)
├── js/app.js               # renders cards from window.DATA
├── js/data.js              # GENERATED — window.DATA = {...}
├── data/
│   ├── services.seed.json  # SOURCE OF TRUTH — edit this
│   └── services.json       # GENERATED — portable copy of the computed data
├── scripts/update_data.py  # computes CWI + appends weekly snapshot
├── vercel.json             # static deploy config + cache headers
└── .github/workflows/weekly-update.yml  # auto-refresh every Monday
```

## Run locally

Any static server works (needed so the browser can load the scripts):

```powershell
# from the project root
python -m http.server 8000
# then open http://localhost:8000
```

Or with the Vercel CLI: `vercel dev`.

## Update the data

1. Edit prices / `valuePoints` / notes in **`data/services.seed.json`**.
2. Recompute and regenerate the site data:

```powershell
python scripts/update_data.py
# or stamp a specific ISO week:
python scripts/update_data.py --week 2026-06-29
```

This rewrites `data/services.json` and `js/data.js`, and appends this week's CWI to each
service's `history` (keeping the last 12 weeks).

## Deploy to Vercel

This is a plain static site, so deployment is trivial:

- **Git integration (recommended):** push to GitHub, "Import Project" on Vercel. Framework
  preset = **Other**, no build command, output directory = project root. Done.
- **CLI:** `npm i -g vercel` then `vercel` (preview) / `vercel --prod` (production).

### Automatic weekly refresh

`.github/workflows/weekly-update.yml` runs `update_data.py` every Monday 06:00 UTC, commits
the regenerated `data/services.json` + `js/data.js`, and the push triggers Vercel to
redeploy automatically. You can also trigger it manually from the GitHub **Actions** tab.

> Why a GitHub Action instead of a Vercel Cron? Vercel's runtime filesystem is read-only,
> so a cron function can't persist regenerated data without external storage. Committing
> from CI is the simplest durable path and keeps the data in version control.

## Adding a service

Append an object to `services[]` in `data/services.seed.json`:

```jsonc
{
  "id": "unique-slug",
  "name": "Service Name",
  "plan": "Plan Name",
  "vendor": "Vendor",
  "category": "coding",         // coding | generation | music | research
  "priceMonthly": 20,
  "valuePoints": 100,           // your usable-value estimate (same unit across the category)
  "bestFor": "One line on who it's for.",
  "weakness": "One line on the catch.",
  "link": "https://...",
  "history": []                 // leave empty; the script fills it weekly
}
```

Re-run `update_data.py` and redeploy. The CWI, rank, and verdict are computed for you.
