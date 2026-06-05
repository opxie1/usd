import csv
import json
import os
import time
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
START = "1959-01-01"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
CAT = os.path.join(ROOT, "catalog")

SERIES = [
    dict(name="m2", fred_id="M2SL", group="money_supply", agg="last", role="stock", status="primary"),
    dict(name="monetary_base", fred_id="BOGMBASE", group="money_supply", agg="last", role="stock", status="primary"),
    dict(name="m2_real", fred_id="M2REAL", group="money_supply", agg="last", role="stock", status="alternate"),
    dict(name="reserve_balances", fred_id="WRESBAL", group="money_supply", agg="last", role="stock", status="alternate"),
    dict(name="total_reserves", fred_id="TRESEGUSM052N", group="money_supply", agg="last", role="stock", status="alternate"),

    dict(name="cpi", fred_id="CPIAUCSL", group="inflation_index", agg="avg", role="price", status="primary"),
    dict(name="pce_price", fred_id="PCEPI", group="inflation_index", agg="avg", role="price", status="primary"),
    dict(name="ppi_allcommodities", fred_id="PPIACO", group="inflation_index", agg="avg", role="price", status="primary"),
    dict(name="gdp_deflator", fred_id="GDPDEF", group="inflation_index", agg="avg", role="price", status="primary"),
    dict(name="ppi_finaldemand", fred_id="PPIFIS", group="inflation_index", agg="avg", role="price", status="alternate"),
    dict(name="cpi_core", fred_id="CPILFESL", group="inflation_index", agg="avg", role="price", status="alternate"),
    dict(name="pce_price_core", fred_id="PCEPILFE", group="inflation_index", agg="avg", role="price", status="alternate"),

    dict(name="real_gdp", fred_id="GDPC1", group="real_output", agg="last", role="level", status="primary"),
    dict(name="nominal_gdp", fred_id="GDP", group="real_output", agg="last", role="level", status="alternate"),
    dict(name="potential_gdp", fred_id="GDPPOT", group="real_output", agg="last", role="level", status="alternate"),
    dict(name="real_pce", fred_id="PCECC96", group="real_output", agg="last", role="level", status="alternate"),

    dict(name="rate_federal_10y", fred_id="GS10", group="rate_federal", agg="avg", role="rate", status="primary"),
    dict(name="rate_fedfunds_policy", fred_id="FEDFUNDS", group="rate_federal", agg="avg", role="rate", status="primary"),
    dict(name="rate_tbill_3m", fred_id="TB3MS", group="rate_federal", agg="avg", role="rate", status="alternate"),
    dict(name="rate_treasury_2y", fred_id="GS2", group="rate_federal", agg="avg", role="rate", status="alternate"),

    dict(name="rate_state_local_muni", fred_id="MSLB20", group="rate_state_local", agg="avg", role="rate", status="primary"),

    dict(name="rate_mortgage_30y", fred_id="MORTGAGE30US", group="rate_mortgage", agg="avg", role="rate", status="primary"),

    dict(name="rate_business_baa", fred_id="BAA", group="rate_business", agg="avg", role="rate", status="primary"),
    dict(name="rate_business_prime", fred_id="MPRIME", group="rate_business", agg="avg", role="rate", status="alternate"),
    dict(name="rate_business_aaa", fred_id="AAA", group="rate_business", agg="avg", role="rate", status="alternate"),

    dict(name="rate_consumer_personal24m", fred_id="TERMCBPER24NS", group="rate_consumer", agg="avg", role="rate", status="primary"),
    dict(name="rate_consumer_creditcard", fred_id="TERMCBCCALLNS", group="rate_consumer", agg="avg", role="rate", status="alternate"),
    dict(name="rate_consumer_auto48m", fred_id="TERMCBAUTO48NS", group="rate_consumer", agg="avg", role="rate", status="alternate"),

    dict(name="debt_federal", fred_id="GFDEBTN", group="debt_federal", agg="last", role="stock", status="primary"),
    dict(name="debt_federal_public", fred_id="FYGFDPUN", group="debt_federal", agg="last", role="stock", status="alternate"),

    dict(name="debt_state_local", fred_id="SLGSDODNS", group="debt_state_local", agg="last", role="stock", status="primary"),

    dict(name="debt_mortgage_total", fred_id="ASTMA", group="debt_mortgage", agg="last", role="stock", status="primary"),
    dict(name="debt_mortgage_household", fred_id="HHMSDODNS", group="debt_mortgage", agg="last", role="stock", status="alternate"),

    dict(name="debt_business", fred_id="TBSDODNS", group="debt_business", agg="last", role="stock", status="primary"),
    dict(name="debt_business_corporate", fred_id="BCNSDODNS", group="debt_business", agg="last", role="stock", status="alternate"),

    dict(name="debt_consumer_credit", fred_id="TOTALSL", group="debt_consumer", agg="last", role="stock", status="primary"),
    dict(name="debt_household_total", fred_id="CMDEBT", group="debt_consumer", agg="last", role="stock", status="alternate"),

    dict(name="fed_total_assets", fred_id="WALCL", group="fed_balance_sheet", agg="last", role="stock", status="primary"),
    dict(name="fed_treasuries", fred_id="TREAST", group="fed_balance_sheet", agg="last", role="stock", status="primary"),
    dict(name="fed_mbs", fred_id="WSHOMCB", group="fed_balance_sheet", agg="last", role="stock", status="primary"),
    dict(name="fed_securities_total", fred_id="WSHOSHO", group="fed_balance_sheet", agg="last", role="stock", status="alternate"),

    dict(name="bank_credit_total", fred_id="TOTBKCR", group="bank_credit", agg="last", role="stock", status="primary"),
    dict(name="bank_loans_leases", fred_id="TOTLL", group="bank_credit", agg="last", role="stock", status="alternate"),
    dict(name="bank_ci_loans", fred_id="BUSLOANS", group="bank_credit", agg="last", role="stock", status="alternate"),
    dict(name="bank_realestate_loans", fred_id="REALLN", group="bank_credit", agg="last", role="stock", status="alternate"),
    dict(name="bank_consumer_loans", fred_id="CONSUMER", group="bank_credit", agg="last", role="stock", status="alternate"),
]


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
            time.sleep(1.5)
    return "ERR", "unreachable"


def get_metadata(fred_id):
    url = f"{BASE}/series?series_id={fred_id}&api_key={API_KEY}&file_type=json"
    status, body = fetch_json(url)
    if status == 200 and isinstance(body, dict) and body.get("seriess"):
        return body["seriess"][0]
    return None


def get_observations(fred_id):
    url = f"{BASE}/series/observations?series_id={fred_id}&api_key={API_KEY}&file_type=json&observation_start={START}"
    status, body = fetch_json(url)
    if status == 200 and isinstance(body, dict) and body.get("observations") is not None:
        dates, values = [], []
        for o in body["observations"]:
            v = o.get("value", ".")
            dates.append(o.get("date"))
            values.append(float(v) if v not in (".", "", None) else float("nan"))
        s = pd.Series(values, index=pd.to_datetime(dates), name=fred_id)
        return s
    return None


def to_quarterly(s, agg):
    r = s.resample("QE")
    out = r.mean() if agg == "avg" else r.last()
    return out


def main():
    catalog_rows = []
    quarterly_primary = {}
    quarterly_all = {}

    for spec in SERIES:
        fid = spec["fred_id"]
        meta = get_metadata(fid)
        time.sleep(0.1)
        if meta is None:
            catalog_rows.append(dict(name=spec["name"], fred_id=fid, group=spec["group"], status=spec["status"],
                                     fetch="FAILED", title="", units="", frequency="", obs_start="", obs_end="",
                                     seasonal_adjustment="", agg_rule=spec["agg"], source="FRED",
                                     notes="series metadata not retrieved"))
            continue
        obs = get_observations(fid)
        time.sleep(0.1)
        if obs is None or obs.dropna().empty:
            catalog_rows.append(dict(name=spec["name"], fred_id=fid, group=spec["group"], status=spec["status"],
                                     fetch="NO_DATA", title=meta.get("title", ""), units=meta.get("units", ""),
                                     frequency=meta.get("frequency", ""), obs_start=meta.get("observation_start", ""),
                                     obs_end=meta.get("observation_end", ""),
                                     seasonal_adjustment=meta.get("seasonal_adjustment_short", ""),
                                     agg_rule=spec["agg"], source="FRED", notes="no observations in window"))
            continue

        obs.to_frame("value").rename_axis("date").to_csv(os.path.join(RAW, f"{fid}.csv"))
        q = to_quarterly(obs, spec["agg"])
        quarterly_all[spec["name"]] = q
        if spec["status"] == "primary":
            quarterly_primary[spec["name"]] = q

        catalog_rows.append(dict(name=spec["name"], fred_id=fid, group=spec["group"], status=spec["status"],
                                 fetch="OK", title=meta.get("title", ""), units=meta.get("units", ""),
                                 frequency=meta.get("frequency", ""), obs_start=meta.get("observation_start", ""),
                                 obs_end=meta.get("observation_end", ""),
                                 seasonal_adjustment=meta.get("seasonal_adjustment_short", ""),
                                 agg_rule=spec["agg"], source="FRED",
                                 notes="DISCONTINUED" if "DISCONTINUED" in meta.get("title", "") else ""))

    panel = pd.DataFrame(quarterly_all).sort_index()
    panel.index.name = "quarter_end"

    core_cols = [c for c in panel.columns if c != "potential_gdp"]
    if core_cols:
        last_valid = panel[core_cols].dropna(how="all").index.max()
        panel = panel.loc[:last_valid]

    if "m2" in panel and "monetary_base" in panel:
        panel["m2_less_base"] = panel["m2"] - panel["monetary_base"]

    for idx_name in ["cpi", "pce_price", "ppi_allcommodities", "gdp_deflator"]:
        if idx_name in panel:
            x = panel[idx_name].astype(float)
            panel[f"infl_{idx_name}_qoq_ann"] = 400.0 * (np.log(x) - np.log(x.shift(1)))
            panel[f"infl_{idx_name}_yoy"] = 100.0 * (x / x.shift(4) - 1.0)

    panel_out = panel.copy()
    panel_out.insert(0, "quarter", panel_out.index.to_period("Q").astype(str))
    panel_out.to_csv(os.path.join(PROC, "quarterly_panel.csv"))

    primary_panel = pd.DataFrame(quarterly_primary).sort_index()
    primary_panel.index.name = "quarter_end"
    if "m2" in primary_panel and "monetary_base" in primary_panel:
        primary_panel["m2_less_base"] = primary_panel["m2"] - primary_panel["monetary_base"]
    for idx_name in ["cpi", "pce_price", "ppi_allcommodities", "gdp_deflator"]:
        if idx_name in primary_panel:
            x = primary_panel[idx_name].astype(float)
            primary_panel[f"infl_{idx_name}_qoq_ann"] = 400.0 * (np.log(x) - np.log(x.shift(1)))
            primary_panel[f"infl_{idx_name}_yoy"] = 100.0 * (x / x.shift(4) - 1.0)
    primary_panel.insert(0, "quarter", primary_panel.index.to_period("Q").astype(str))
    primary_panel.to_csv(os.path.join(PROC, "quarterly_panel_primary.csv"))

    fieldnames = ["name", "fred_id", "group", "status", "fetch", "title", "units", "frequency",
                  "seasonal_adjustment", "obs_start", "obs_end", "agg_rule", "source", "notes"]
    with open(os.path.join(CAT, "variable_catalog.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in catalog_rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})

    ok = sum(1 for r in catalog_rows if r["fetch"] == "OK")
    print(f"series_ok={ok} of {len(catalog_rows)}")
    print(f"panel_all shape={panel_out.shape} range={panel_out['quarter'].iloc[0]}..{panel_out['quarter'].iloc[-1]}")
    print(f"panel_primary shape={primary_panel.shape}")
    for r in catalog_rows:
        if r["fetch"] != "OK":
            print(f"NON-OK: {r['name']} {r['fred_id']} -> {r['fetch']} {r['notes']}")


if __name__ == "__main__":
    main()
