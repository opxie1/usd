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
    "nipa_interest": "NIPA Interest Payments (for implied rates)",
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
    lines.append("**Implied interest rates (per Prof. Gmeiner: interest payments divided by debt).** Computed as annual NIPA interest payment (SAAR, billions) divided by the end-of-quarter debt stock (converted to billions), times 100, giving an annualized weighted-average rate in percent:")
    lines.append("- `rate_federal_implied` = `int_federal` (A091RC1Q027SBEA) / `debt_federal` (GFDEBTN)")
    lines.append("- `rate_state_local_implied` = `int_state_local` (B111RC1Q027SBEA) / `debt_state_local` (SLGSDODNS)")
    lines.append("- `rate_business_implied` = `int_business` (W272RC1Q027SBEA) / `debt_business_corporate` (BCNSDODNS)")
    lines.append("- `rate_consumer_implied` = `int_personal` (B069RC1Q027SBEA) / `debt_consumer_credit` (TOTALSL)")
    lines.append("- `rate_business_implied_nonfin` = `int_business` / `debt_business` (TBSDODNS); broader-business alternate.")
    lines.append("- `rate_state_local_implied_expension` = (`int_state_local` - `int_state_local_pension`) / `debt_state_local`; the pension correction chosen by Prof. Gmeiner (option 1). `int_state_local_pension` is NIPA table 7.24 'Imputed interest on plans' claims on employers' (Y315RC1A027NBEA), the actuarial pension interest that BEA folds into state/local interest payments (Table 3.3 note 1). The series is annual, carried forward across the quarters of each year; it currently ends with the 2024 annual value, so the corrected rate ends 2024Q4 until BEA releases 2025. Validation: over 1990-2016 the corrected rate tracks the Bond Buyer GO 20-bond muni index with a mean absolute gap of 0.8 percentage points, against roughly 3.5 points uncorrected.")
    lines.append("- Mortgage rate uses the market series `rate_mortgage_30y` (MORTGAGE30US) per Prof. Gmeiner, since long mortgage durations make a current rate more informative than a weighted average.")
    lines.append("")
    lines.append("**status:** `primary` = series intended for the baseline specification; `alternate` = comparable series kept for robustness and selection, per Prof. Gmeiner's note that the best of several similar series will become clear during the econometrics.")
    lines.append("")

    lines.append("## Open data issues")
    lines.append("")
    lines.append("1. **State/local implied rate pension bias - RESOLVED (Gmeiner chose option a, net out the pension interest).** BEA Table 3.3 footnote 1: state/local 'interest payments' includes interest accrued on the actuarial liabilities of defined-benefit public pension plans, which pushed the uncorrected ratio to 7-8%. `rate_state_local_implied_expension` subtracts the table 7.24 pension-interest imputation (Y315RC1A027NBEA) and lands at 3-4%, in line with municipal yields. The uncorrected `rate_state_local_implied` is retained for reference. Remaining caveat: the pension series is annual (carried forward within each year) and ends with the 2024 release, so the corrected rate stops at 2024Q4 for now.")
    lines.append("2. **Federal implied rate also contains pension interest** (BEA Table 3.2 footnote 4: federal-employee DB pension interest), but the very large debt base makes the relative effect small; the federal implied rate of about 3.2% is consistent with the average rate on total public debt.")
    lines.append("3. **Business implied rate uses NET interest and miscellaneous payments** (domestic industries), not gross interest, and the interest concept spans domestic private industries while the debt base is nonfinancial corporate (`BCNSDODNS`). Treat it as a cost-of-funds index rather than a precise contractual rate; `rate_business_implied_nonfin` (over `TBSDODNS`) is provided as an alternate.")
    lines.append("4. **Federal Reserve balance-sheet series begin 2002Q4** (weekly H.4.1). Any specification including Fed total assets / securities held is capped at a 2002Q4 start.")
    lines.append("5. **Z.1 Financial Accounts (debt levels) lag about one quarter.** The latest debt point is 2025Q4, so the federal, state/local, and business implied rates end 2025Q4; the consumer implied rate extends to 2026Q1 because consumer credit (`TOTALSL`) is monthly.")
    lines.append("6. **Several market rate series are not seasonally adjusted (NSA);** see the `SA` column. The TERMCB consumer rates are reported on a quarterly cadence (Feb/May/Aug/Nov).")
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
