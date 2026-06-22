#!/usr/bin/env python3
"""
Weekly updater for the "Is It Worth It?" AI Cost-Worth Index.

What it does
------------
1. Reads data/services.seed.json (the curated source of truth).
2. Computes each service's value-per-dollar, then normalizes it to a
   Cost-Worth Index (CWI) of 0-100 *within its category* (best-in-category = 100).
3. Assigns a plain-English verdict band.
4. Appends this week's CWI snapshot to each service's history (dedup by week).
5. Writes two outputs:
     - data/services.json   (portable data file)
     - js/data.js           (window.DATA = ... so the static site works on file:// too)

Run weekly (then redeploy to Vercel):
    python scripts/update_data.py
    python scripts/update_data.py --week 2026-06-29   # force a specific ISO week date

The numbers in the seed are curated human estimates of usable value, not scraped
prices. Edit the seed to keep them honest, re-run, redeploy.
"""

import argparse
import datetime as dt
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "data", "services.seed.json")
LIVE = os.path.join(ROOT, "data", "prices.live.json")
OUT_JSON = os.path.join(ROOT, "data", "services.json")
OUT_JS = os.path.join(ROOT, "js", "data.js")


def load_live():
    """Load fetch_prices.py output if present; otherwise return None (curated mode)."""
    if not os.path.exists(LIVE):
        return None
    with open(LIVE, "r", encoding="utf-8") as f:
        return json.load(f)


def verdict_for(cwi):
    if cwi is None:
        return "FREE TIER"
    if cwi >= 85:
        return "WORTH IT"
    if cwi >= 65:
        return "SOLID"
    if cwi >= 45:
        return "MEH"
    return "OVERPRICED"


def monday_of(date):
    """Return the ISO Monday (start of week) for a given date as YYYY-MM-DD."""
    monday = date - dt.timedelta(days=date.weekday())
    return monday.isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", help="ISO date YYYY-MM-DD to stamp this snapshot (default: this week's Monday)")
    args = ap.parse_args()

    if args.week:
        week = dt.date.fromisoformat(args.week)
        week_str = monday_of(week)
    else:
        # Date.now() isn't available offline-safe here; use system date at run time.
        week_str = monday_of(dt.date.today())

    with open(SEED, "r", encoding="utf-8") as f:
        data = json.load(f)

    services = data["services"]

    # 0. merge live price provenance (from fetch_prices.py) onto each service
    live = load_live()
    if live:
        lsvc = live.get("services", {})
        for s in services:
            info = lsvc.get(s["id"])
            if not info:
                s["priceStatus"] = "manual"
                continue
            # adopt an auto-extracted live price only when the fetcher is confident
            if info["status"] in ("live", "live-changed"):
                s["priceMonthly"] = info["price"]
            s["priceStatus"] = info["status"]
            s["priceSource"] = info["source"]
            s["priceCheckedAt"] = info["checkedAt"]
        data["apiModels"] = live.get("apiModels", [])
        data["meta"]["priceCheckedAt"] = live.get("checkedDate")
    else:
        for s in services:
            s["priceStatus"] = "manual"

    # 1. value-per-dollar for each paid service
    for s in services:
        price = s.get("priceMonthly", 0)
        vp = s.get("valuePoints", 0)
        s["valuePerDollar"] = round(vp / price, 2) if price > 0 else None

    # 2. normalize within category -> CWI 0..100
    cats = {c["id"] for c in data["categories"]}
    for cat in cats:
        members = [s for s in services if s["category"] == cat and s.get("valuePerDollar")]
        if not members:
            continue
        best = max(s["valuePerDollar"] for s in members)
        for s in members:
            s["cwi"] = round(100 * s["valuePerDollar"] / best)
    # free / priceless plans
    for s in services:
        if s.get("valuePerDollar") is None:
            s["cwi"] = None

    # 3 + 4. verdict + append weekly snapshot
    for s in services:
        s["verdict"] = verdict_for(s.get("cwi"))
        hist = s.setdefault("history", [])
        hist = [h for h in hist if h.get("week") != week_str]
        if s.get("cwi") is not None:
            hist.append({"week": week_str, "cwi": s["cwi"]})
        hist.sort(key=lambda h: h["week"])
        s["history"] = hist[-12:]  # keep last 12 weeks

    # category rank (1 = most worth it)
    for cat in cats:
        members = sorted(
            [s for s in services if s["category"] == cat and s.get("cwi") is not None],
            key=lambda s: s["cwi"],
            reverse=True,
        )
        for i, s in enumerate(members, start=1):
            s["rank"] = i

    data["meta"]["weekOf"] = week_str
    data["meta"]["generatedAt"] = dt.datetime.now().isoformat(timespec="seconds")

    # 5. write outputs
    os.makedirs(os.path.dirname(OUT_JS), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("// AUTO-GENERATED by scripts/update_data.py — do not edit by hand.\n")
        f.write("window.DATA = ")
        json.dump(data, f, ensure_ascii=False)
        f.write(";\n")

    n = len([s for s in services if s.get("cwi") is not None])
    print(f"OK  week={week_str}  services={n}  -> data/services.json, js/data.js")


if __name__ == "__main__":
    main()
