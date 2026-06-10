import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error

import numpy as np
import pandas as pd


def load_api_key():
    k = os.environ.get("FRED_API_KEY", "").strip()
    if k:
        return k
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "fred_api_key.txt")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    raise SystemExit("set FRED_API_KEY env var or create config/fred_api_key.txt")


API_KEY = load_api_key()
BASE = "https://api.stlouisfed.org/fred"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
RAW = os.path.join(ROOT, "data", "raw")

QUERIES = [
    "interest accrued on benefit entitlements",
    "state and local government defined benefit pension plans interest",
    "imputed interest state and local pension",
    "state and local pension plans interest accrued",
]


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-fetch"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            return None
        except Exception:
            if attempt == 3:
                return None
            time.sleep(1.2)
    return None


def search(text, freq):
    q = urllib.parse.quote(text)
    url = f"{BASE}/series/search?search_text={q}&api_key={API_KEY}&file_type=json&filter_variable=frequency&filter_value={freq}&limit=50&order_by=search_rank"
    body = fetch_json(url)
    if body and body.get("seriess"):
        return body["seriess"]
    return []


def get_obs(fred_id):
    url = f"{BASE}/series/observations?series_id={fred_id}&api_key={API_KEY}&file_type=json"
    body = fetch_json(url)
    if body is None or body.get("observations") is None:
        return None
    dates, values = [], []
    for o in body["observations"]:
        v = o.get("value", ".")
        dates.append(o.get("date"))
        values.append(float(v) if v not in (".", "", None) else float("nan"))
    return pd.Series(values, index=pd.to_datetime(dates))


def title_ok(t):
    t = t.lower()
    return ("state and local" in t) and ("interest" in t) and ("pension" in t or "benefit entitlement" in t)


def main():
    panel = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    int_sl = panel["int_state_local"]
    debt_sl = panel["debt_state_local"]
    muni = pd.read_csv(os.path.join(RAW, "MSLB20.csv"), parse_dates=["date"]).set_index("date")["value"].resample("QE").mean()

    seen = {}
    for freq in ["Quarterly", "Annual"]:
        for q in QUERIES:
            for s in search(q, freq):
                if s["id"] in seen:
                    continue
                if title_ok(s.get("title", "")):
                    seen[s["id"]] = dict(freq=freq, title=s.get("title"), units=s.get("units_short"),
                                         start=s.get("observation_start"), end=s.get("observation_end"),
                                         sa=s.get("seasonal_adjustment_short"))
            time.sleep(0.1)
        if seen:
            break

    if not seen:
        print("NO CANDIDATES FOUND in quarterly or annual NIPA search")
        return

    rows = []
    for fid, meta in seen.items():
        obs = get_obs(fid)
        time.sleep(0.1)
        if obs is None or obs.dropna().empty:
            continue
        if meta["freq"] == "Annual":
            qs = obs.resample("QE").ffill()
        else:
            qs = obs.resample("QE").mean()
        cand = qs.reindex(panel.index)
        corrected = (int_sl - cand) / (debt_sl / 1000.0) * 100.0
        ov = pd.concat([corrected, muni], axis=1, keys=["corr", "muni"]).dropna()
        ov = ov.loc["1990-01-01":"2016-09-30"]
        gap = float((ov["corr"] - ov["muni"]).abs().mean()) if len(ov) else float("nan")
        last = corrected.dropna()
        rows.append(dict(fred_id=fid, freq=meta["freq"], units=meta["units"], sa=meta["sa"],
                         start=meta["start"], end=meta["end"],
                         mean_abs_gap_vs_muni_1990_2016=round(gap, 3),
                         corrected_rate_last=round(float(last.iloc[-1]), 3) if len(last) else float("nan"),
                         corrected_rate_min=round(float(corrected.min()), 3),
                         title=meta["title"]))
    out = pd.DataFrame(rows).sort_values("mean_abs_gap_vs_muni_1990_2016")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
