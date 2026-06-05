import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 60)

panel = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"))

print("=== COVERAGE (first/last quarter with data, per column) ===")
for c in panel.columns:
    if c in ("quarter", "quarter_end"):
        continue
    s = panel[c]
    nz = panel.loc[s.notna(), "quarter"]
    if len(nz):
        print(f"{c:32s} {nz.iloc[0]} .. {nz.iloc[-1]}  n={s.notna().sum()}")
    else:
        print(f"{c:32s} EMPTY")

show = ["quarter", "m2", "monetary_base", "m2_less_base", "fed_total_assets",
        "rate_fedfunds_policy", "rate_federal_10y", "rate_mortgage_30y",
        "rate_business_baa", "rate_consumer_personal24m", "rate_state_local_muni",
        "debt_federal", "debt_business", "debt_consumer_credit", "real_gdp",
        "infl_cpi_yoy", "infl_pce_price_yoy", "infl_gdp_deflator_yoy"]
show = [c for c in show if c in panel.columns]
print("\n=== LAST 6 QUARTERS (headline series) ===")
print(panel[show].tail(6).to_string(index=False))
