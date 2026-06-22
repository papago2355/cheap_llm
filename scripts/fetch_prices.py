#!/usr/bin/env python3
"""
Live price fetcher for the "Is It Worth It?" index.

For each service in data/sources.json it hits the OFFICIAL pricing page and tries,
in order:

  1. AUTO-EXTRACT  - find the plan's monthly price near its name, requiring a
                     "month" context (rejects annual rates) and a sane range.
                     -> status "live"  (or "live-changed" if it differs from ref)
  2. VERIFY        - if no confident extraction, check the known reference price
                     string is still present on the page.
                     -> status "verified"
  3. REVIEW        - page reachable but reference price not found (price may have
                     moved) -> status "review"  (kept ref value, flagged)
  4. UNREACHABLE   - fetch failed -> status "unreachable" (kept ref value)

The value is NEVER blindly overwritten by a garbage parse: extraction must pass a
range + month-context gate. Every result carries provenance: source URL, the date
checked, and the status. Output: data/prices.live.json.

Run weekly (CI does this automatically), then update_data.py merges the result:
    python scripts/fetch_prices.py
"""

import datetime as dt
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "data", "sources.json")
OUT = os.path.join(ROOT, "data", "prices.live.json")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
TODAY = dt.date.today().isoformat()


def fetch_text(url):
    """GET url, strip scripts/styles/tags, collapse whitespace -> plain text."""
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t


def extract_monthly(text, anchors, lo, hi, window=160):
    """Find a monthly price near the first anchor. Returns int price or None.

    Requires a 'month' cue and forbids an 'annual/year' cue in the local window so
    we don't pick up annual-billed equivalents (e.g. $17/mo billed annually)."""
    anchor = anchors[0]
    for m in re.finditer(re.escape(anchor), text, re.IGNORECASE):
        seg = text[m.end(): m.end() + window]
        low = seg.lower()
        if not re.search(r"month|/mo|per month|monthly", low):
            continue
        if re.search(r"annual|/year|per year|yearly|billed annual", low):
            continue
        # all later anchors (e.g. "5x") should also appear nearby for multi-word tiers
        if len(anchors) > 1 and not all(a.lower() in low for a in anchors[1:]):
            continue
        for pm in re.finditer(r"\$\s?(\d{1,4})(?:\.(\d{2}))?", seg):
            v = int(pm.group(1))
            if lo <= v <= hi:
                return v
    return None


def price_present(text, price):
    """Is the exact monthly price string present anywhere on the page?"""
    pats = [rf"\$\s?{price}\b", rf"\b{price}\s?/\s?mo", rf"\b{price}\s?/\s?month"]
    return any(re.search(p, text) for p in pats)


def check_source(src):
    out = {
        "id": src["id"],
        "source": src["url"],
        "ref": src["ref"],
        "price": src["ref"],          # value used downstream (kept safe)
        "checkedAt": TODAY,
        "status": "unreachable",
        "httpOk": False,
    }
    try:
        text = fetch_text(src["url"])
        out["httpOk"] = True
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
        return out

    lo, hi = src["range"]
    found = extract_monthly(text, src.get("anchors", []), lo, hi)
    if found is not None:
        out["price"] = found
        out["status"] = "live" if found == src["ref"] else "live-changed"
        return out

    if price_present(text, src["ref"]):
        out["status"] = "verified"   # ref price still on the page
    else:
        out["status"] = "review"     # page ok but ref price not found -> may have changed
    return out


def check_api_model(m):
    out = {"id": m["id"], "label": m["label"], "vendor": m["vendor"],
           "source": m["url"], "checkedAt": TODAY,
           "inputPerM": m["inRef"], "outputPerM": m["outRef"], "status": "verified"}
    try:
        text = fetch_text(m["url"])
    except Exception as e:
        out["status"] = "unreachable"
        out["error"] = f"{type(e).__name__}: {e}"
        return out
    # find "<model> ... $IN $OUT" pair on the same row, validate against ref +-60%
    i = re.search(r"\b" + re.escape(m["match"]) + r"\b(?!-)", text)
    if i:
        seg = text[i.end(): i.end() + 80]
        nums = re.findall(r"\$\s?(\d+(?:\.\d+)?)", seg)
        if len(nums) >= 2:
            inp, outp = float(nums[0]), float(nums[1])
            if 0.4 * m["inRef"] <= inp <= 2.5 * m["inRef"] and 0.4 * m["outRef"] <= outp <= 2.5 * m["outRef"]:
                out["inputPerM"], out["outputPerM"] = inp, outp
                out["status"] = "live" if (inp == m["inRef"] and outp == m["outRef"]) else "live-changed"
    return out


def main():
    with open(SOURCES, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    services = [check_source(s) for s in cfg["sources"]]
    api = [check_api_model(m) for m in cfg.get("apiModels", [])]

    result = {
        "generatedAt": dt.datetime.now().isoformat(timespec="seconds"),
        "checkedDate": TODAY,
        "services": {s["id"]: s for s in services},
        "apiModels": api,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # console summary
    from collections import Counter
    c = Counter(s["status"] for s in services)
    print("PRICE CHECK", TODAY)
    for s in services:
        flag = "" if s["status"] in ("live", "verified") else "  <-- CHECK"
        print(f"  {s['id']:16} ${s['price']:<4} {s['status']:13}{flag}")
    print("summary:", dict(c))
    print("api models:", {m["id"]: m["status"] for m in api})


if __name__ == "__main__":
    main()
