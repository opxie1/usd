import csv
import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error

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
BEA = os.path.join(ROOT, "data", "raw", "bea")

TARGETS = {
    "federal": dict(file="bea_table_3_2_federal_government.csv", line="33", label_must="interest"),
    "state_local": dict(file="bea_table_3_3_state_local_government.csv", line="28", label_must="interest"),
    "business": dict(file="bea_table_1_10_gross_domestic_income.csv", line="11", label_must="interest"),
    "personal": dict(file="bea_table_2_1_personal_income.csv", line="30", label_must="interest"),
}

CANDIDATES = {
    "federal": ["A091RC1Q027SBEA"],
    "state_local": ["S210401A027NBEA", "ASLSINT", "W068RC1Q027SBEA"],
    "business": ["W272RC1Q027SBEA", "A180RC1Q027SBEA"],
    "personal": ["B069RC1Q027SBEA"],
}

SEARCH_TEXT = {
    "federal": "Federal government current expenditures interest payments",
    "state_local": "State and local government interest payments",
    "business": "Net interest and miscellaneous payments domestic industries",
    "personal": "Personal interest payments",
}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-fetch"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.status, json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")[:200]
        except Exception as e:
            if attempt == 3:
                return "ERR", str(e)
            time.sleep(1.2)
    return "ERR", "unreachable"


def parse_bea_target(spec):
    path = os.path.join(BEA, spec["file"])
    rows = []
    with open(path, encoding="utf-8") as f:
        for row in csv.reader(f):
            rows.append(row)
    years = rows[3][2:]
    quarters = rows[4][2:]
    periods = []
    for y, q in zip(years, quarters):
        if y and q:
            periods.append(pd.Period(f"{y}{q}", freq="Q"))
    target_row = None
    for row in rows:
        if row and row[0].strip() == spec["line"]:
            target_row = row
            break
    if target_row is None:
        raise SystemExit(f"line {spec['line']} not found in {spec['file']}")
    label = target_row[1].strip()
    assert spec["label_must"].lower() in label.lower(), f"label check failed: {label}"
    vals = []
    for v in target_row[2:2 + len(periods)]:
        vals.append(float(v.replace(",", "")) if v not in ("", None) else float("nan"))
    return pd.Series(vals, index=pd.PeriodIndex(periods, freq="Q")), label


def get_quarterly(fred_id):
    url = f"{BASE}/series/observations?series_id={fred_id}&api_key={API_KEY}&file_type=json"
    status, body = fetch_json(url)
    if status != 200 or not isinstance(body, dict) or body.get("observations") is None:
        return None
    dates, values = [], []
    for o in body["observations"]:
        v = o.get("value", ".")
        dates.append(o.get("date"))
        values.append(float(v) if v not in (".", "", None) else float("nan"))
    s = pd.Series(values, index=pd.to_datetime(dates)).resample("QE").mean()
    s.index = s.index.to_period("Q")
    return s


def get_meta(fred_id):
    url = f"{BASE}/series?series_id={fred_id}&api_key={API_KEY}&file_type=json"
    status, body = fetch_json(url)
    if status == 200 and isinstance(body, dict) and body.get("seriess"):
        return body["seriess"][0]
    return None


def compare(series, target):
    common = target.index.intersection(series.index)
    if len(common) < len(target.dropna()):
        return None
    t = target.reindex(common)
    s = series.reindex(common)
    diff = (s - t).abs()
    rel = diff / t.abs()
    return dict(n=len(common), max_abs=float(diff.max()), max_rel=float(rel.max()),
                first_s=float(s.iloc[0]), first_t=float(t.iloc[0]),
                last_s=float(s.iloc[-1]), last_t=float(t.iloc[-1]))


def search_ids(text):
    q = urllib.parse.quote(text)
    url = f"{BASE}/series/search?search_text={q}&api_key={API_KEY}&file_type=json&filter_variable=frequency&filter_value=Quarterly&limit=40&order_by=popularity"
    status, body = fetch_json(url)
    if status == 200 and isinstance(body, dict) and body.get("seriess"):
        return [s["id"] for s in body["seriess"]]
    return []


def main():
    for sector, spec in TARGETS.items():
        target, label = parse_bea_target(spec)
        print(f"\n=== {sector} :: BEA line {spec['line']} '{label}' ===")
        print("BEA targets:", {str(k): v for k, v in target.items()})
        found = None
        tried = list(CANDIDATES.get(sector, []))
        for fid in tried:
            s = get_quarterly(fid)
            time.sleep(0.1)
            if s is None:
                print(f"  candidate {fid}: not found")
                continue
            c = compare(s, target)
            if c and c["max_rel"] < 0.005:
                found = fid
                print(f"  MATCH {fid}: max_rel={c['max_rel']:.5f} max_abs={c['max_abs']:.3f} n={c['n']}")
                break
            else:
                msg = f"max_rel={c['max_rel']:.4f}" if c else "no overlap"
                print(f"  candidate {fid}: no match ({msg})")
        if not found:
            print(f"  searching FRED for: {SEARCH_TEXT[sector]}")
            for fid in search_ids(SEARCH_TEXT[sector]):
                if fid in tried:
                    continue
                s = get_quarterly(fid)
                time.sleep(0.08)
                if s is None:
                    continue
                c = compare(s, target)
                if c and c["max_rel"] < 0.005:
                    found = fid
                    m = get_meta(fid)
                    print(f"  MATCH via search {fid}: max_rel={c['max_rel']:.5f} max_abs={c['max_abs']:.3f}")
                    if m:
                        print(f"    title: {m.get('title')} | units: {m.get('units_short')} | {m.get('observation_start')}..{m.get('observation_end')}")
                    break
        if found:
            m = get_meta(found)
            if m:
                print(f"  CONFIRMED {found}: {m.get('title')} | {m.get('units_short')} | freq={m.get('frequency_short')} | SA={m.get('seasonal_adjustment_short')} | {m.get('observation_start')}..{m.get('observation_end')}")
        else:
            print(f"  *** NO FRED MATCH for {sector} ***")


if __name__ == "__main__":
    main()
