import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "catalog")

GROUP_TITLES = {
    "money_supply": "Money Supply and Reserves",
    "inflation_index": "Price Indices (for Inflation)",
    "real_output": "Real Output (Controls)",
    "rate_federal": "Interest Rate: Federal",
    "rate_state_local": "Interest Rate: State and Local",
    "rate_mortgage": "Interest Rate: Mortgage",
    "rate_business": "Interest Rate: Business",
    "rate_consumer": "Interest Rate: Consumer/Personal",
    "debt_federal": "Debt: Federal",
    "debt_state_local": "Debt: State and Local",
    "debt_mortgage": "Debt: Mortgage",
    "debt_business": "Debt: Business",
    "debt_consumer": "Debt: Consumer/Personal",
    "fed_balance_sheet": "Federal Reserve Balance Sheet",
    "bank_credit": "Bank Credit (Thesis Variables)",
}
GROUP_ORDER = list(GROUP_TITLES.keys())


def main():
    rows = []
    with open(os.path.join(CAT, "variable_catalog.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    lines = []
    lines.append("# Variable Catalog - The Long Shadow of Easy Money")
    lines.append("")
    lines.append("All series retrieved from FRED (Federal Reserve Bank of St. Louis) via the FRED API.")
    lines.append("Metadata below (title, units, frequency, coverage) is captured live from the API at fetch time, not transcribed by hand.")
    lines.append("")
    lines.append("**Frequency:** native series resampled to quarterly per Prof. Gmeiner's instruction.")
    lines.append("")
    lines.append("**Quarterly aggregation rule:**")
    lines.append("- Price indices and interest rates: quarterly = average of the within-quarter observations (`agg_rule = avg`).")
    lines.append("- Stocks (money, debt levels, Federal Reserve balance sheet): quarterly = last (end-of-quarter) observation, matching the point-in-time convention of the Z.1 Financial Accounts (`agg_rule = last`).")
    lines.append("- Series already quarterly (GDP, GDP deflator, Z.1 debt) are placed in their quarter bucket unchanged.")
    lines.append("")
    lines.append("**Quarter dating:** rows are labeled by quarter end (e.g., `2020-03-31` = 2020Q1).")
    lines.append("")
    lines.append("**Derived variables in the panel:**")
    lines.append("- `m2_less_base` = `m2` (M2SL) minus `monetary_base` (BOGMBASE); both in billions of dollars.")
    lines.append("- `infl_<index>_qoq_ann` = 400 x (ln P_t - ln P_(t-1)); annualized quarterly inflation.")
    lines.append("- `infl_<index>_yoy` = 100 x (P_t / P_(t-4) - 1); year-over-year inflation.")
    lines.append("")
    lines.append("**status:** `primary` = series intended for the baseline specification; `alternate` = comparable series kept for robustness and selection, per Prof. Gmeiner's note that the best of several similar series will become clear during the econometrics.")
    lines.append("")

    lines.append("## Open data issues")
    lines.append("")
    lines.append("1. **State/local (municipal) interest rate has no current FRED series.** The standard Bond Buyer GO 20-Bond Municipal Bond Index (`MSLB20`) was discontinued in 2016Q3, so the panel has no municipal yield after 2016. Options: (a) source a municipal yield elsewhere (Bond Buyer, ICE/S&P municipal indices) for 2016-present; (b) proxy with a high-grade series; or (c) drop the state/local rate from the rate VAR and keep only the state/local debt level. Needs a decision from Prof. Gmeiner.")
    lines.append("2. **Federal Reserve balance-sheet series begin 2002Q4** (weekly H.4.1). Any specification including Fed total assets / securities held is capped at a 2002Q4 start. Pre-2002 detail would require Z.1 or historical Board tables.")
    lines.append("3. **Z.1 Financial Accounts (most debt levels) lag about one quarter,** so the most recent quarter is partial for debt variables.")
    lines.append("4. **Several rate series are not seasonally adjusted (NSA);** see the `SA` column. The TERMCB consumer rates are reported on a quarterly cadence (Feb/May/Aug/Nov).")
    lines.append("")

    for g in GROUP_ORDER:
        grp = [r for r in rows if r["group"] == g]
        if not grp:
            continue
        lines.append(f"## {GROUP_TITLES[g]}")
        lines.append("")
        lines.append("| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        grp.sort(key=lambda r: (r["status"] != "primary", r["name"]))
        for r in grp:
            cov = f"{r['obs_start']} .. {r['obs_end']}"
            note = f" ({r['notes']})" if r["notes"] else ""
            lines.append(f"| {r['status']} | `{r['name']}` | `{r['fred_id']}` | {r['title']}{note} | {r['units']} | {r['frequency']} | {r['seasonal_adjustment']} | {cov} | {r['agg_rule']} |")
        lines.append("")

    with open(os.path.join(CAT, "variable_catalog.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote", os.path.join(CAT, "variable_catalog.md"), "rows:", len(rows))


if __name__ == "__main__":
    main()
