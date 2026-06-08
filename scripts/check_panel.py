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

show = ["quarter", "rate_federal_implied", "rate_state_local_implied",
        "rate_business_implied", "rate_consumer_implied", "rate_mortgage_30y",
        "int_federal", "debt_federal", "int_state_local", "debt_state_local",
        "int_business", "debt_business_corporate", "int_personal", "debt_consumer_credit",
        "m2_less_base", "fed_total_assets", "infl_cpi_yoy"]
show = [c for c in show if c in panel.columns]
print("\n=== LAST 6 QUARTERS (headline series) ===")
print(panel[show].tail(6).to_string(index=False))
