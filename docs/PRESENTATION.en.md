# 💸 IS IT WORTH IT? — AI Service Cost-Worth Index (Deck)

> A 2D-dot dashboard that answers one question on a single screen: **"Is this AI subscription actually worth the money?"**

---

## 1. One-liner

A pixel-art web dashboard that scores AI **coding / image / music / research** subscriptions
by **real value-per-dollar** (a **Cost-Worth Index, CWI 0–100**) and **fetches + verifies
prices weekly from each service's official pricing page.**

## 2. Problem

- Every AI sub advertises "cheap / best value" — but **real value is hard to compare.**
- Pricing **changes quietly.** e.g. GitHub Copilot's shift to *premium-request* billing made
  frontier-model (Opus) usage dramatically less cost-effective.
- Users have **no number** to decide "Is Claude Code Max 20x ($200) really a better deal than Pro ($20)?"

## 3. Solution

| Pillar | What |
|--------|------|
| **Cost-Worth Index (0–100)** | Value-per-dollar normalized within a category. **100 = best value in its class.** |
| **Weekly auto-refresh** | Every Monday: fetch official pricing pages → verify → recompute → auto-deploy. |
| **Provenance on every card** | `● LIVE / ✓ VERIFIED / ⚠ REVIEW / EST.` badge + source link + check date. |
| **Trend sparkline** | 6-week history shows *when* a service's value dropped. |

## 4. This week's winners (sample · 2026-06-22)

| Category | #1 by value | CWI | Price | Price status |
|----------|-------------|-----|-------|--------------|
| AI Coding | Claude Code **Max 20x** | 100 | $200 | ✓ VERIFIED |
| AI Image | NovelAI **Opus** | 100 | $25 | ● LIVE |
| AI Music | Suno **Premier** | 100 | $30 | ⚠ REVIEW |
| AI Research | Consensus **Premium** | 100 | $9 | ⚠ REVIEW |

Bands: `85+ WORTH IT` · `65–84 SOLID` · `45–64 MEH` · `<45 OVERPRICED`

## 5. Methodology

```
value-per-dollar = (usable monthly value: quota + access + features) ÷ monthly price
CWI (0–100)      = that value-per-dollar normalized within its category (best = 100)
```
CWI measures **quantity-per-dollar**; quality/aesthetics/lock-in live in each card's notes.
A low score isn't "bad" — it means you pay a premium per unit (Midjourney = quality play).

## 6. ⭐ Live data pipeline (no more assumptions)

```
[Mondays 06:00 UTC · GitHub Actions]
  fetch_prices.py  → fetch each official pricing page
                     ├ auto-extract monthly price (month-context + sane-range gate) → ● LIVE
                     ├ else verify the reference price is present on the page        → ✓ VERIFIED
                     └ else flag it (keep known value, human review)                 → ⚠ REVIEW
  update_data.py   → merge live prices + recompute CWI + append weekly snapshot
  git commit/push  → Vercel auto-redeploys
```

**Trust guards — never overwrite with a low-confidence parse:** extraction is accepted only
with a *month* context inside the expected range, blocking the classic mistake of publishing
an annual-billed rate ($17/mo billed annually) as the monthly price. Every price carries a
source URL + check date + status.

**Coverage now:** 9 of 21 plans auto **LIVE/VERIFIED**, the rest honestly flagged **REVIEW**.
JS-rendered tiers (Cursor Ultra, ChatGPT Plus/Pro) → Playwright headless is the upgrade path.

## 7. Architecture

- **Frontend:** zero-build static site (HTML/CSS/vanilla JS) — nothing to break on deploy.
- **Engine:** Python (`fetch_prices.py`, `update_data.py`) → generates `js/data.js` + `data/services.json`.
- **Automation:** GitHub Actions weekly cron → commit → Vercel Git auto-redeploy.
- **Design:** Press Start 2P + VT323, CRT scanlines, dot Worth Meter.

## 8. Deliverables

| Item | Link |
|------|------|
| 📊 Deck (Notion) | *paste this doc into Notion* |
| 🌐 Live site (Vercel) | `https://<project>.vercel.app` *(after deploy)* |
| 💻 GitHub repo | https://github.com/papago2355/cheap_llm |
| 🎬 Demo video (YouTube) | *(recorded by you)* |

## 9. Roadmap

- Playwright headless scraper for JS-rendered tiers → full LIVE coverage
- Auto GitHub Issue on price drift
- "Cost per task" calculator combining live API token prices × subscription quota
- USD/KRW currency + regional pricing
- Personalized CWI from a user's own usage input
