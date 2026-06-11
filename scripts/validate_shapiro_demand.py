import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
RAW = os.path.join(ROOT, "data", "raw", "shapiro")
TAB = os.path.join(ROOT, "tables")
FIG = os.path.join(ROOT, "figures")

DEMAND = "Demand-driven Inflation (headline, y/y)"
SUPPLY = "Supply-driven Inflation (headline, y/y)"

SAMPLES = {
    "full_1971_2026": (None, None),
    "qe_era_2003_2026": ("2003-01-01", None),
}


def load():
    sh = pd.read_excel(os.path.join(RAW, "supply-demand-pce-inflation.xlsx"), sheet_name="Data")
    sh["date"] = pd.to_datetime(sh["time_month"].str.strip().str.replace("m", "-"), format="%Y-%m")
    sh = sh.set_index("date")
    q = sh[[DEMAND, SUPPLY]].resample("QE").mean()
    q.columns = ["demand_yoy", "supply_yoy"]

    panel = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    q["money_yoy"] = 100.0 * (np.log(panel["m2_less_base"]) - np.log(panel["m2_less_base"].shift(4)))
    return q


def granger_rows(q):
    rows = []
    for comp in ["demand_yoy", "supply_yoy"]:
        for sample_name, (start, end) in SAMPLES.items():
            d = q[["money_yoy", comp]].dropna()
            if start:
                d = d.loc[d.index >= start]
            if end:
                d = d.loc[d.index <= end]
            model = VAR(d)
            sel = model.select_order(maxlags=8)
            p = max(int(sel.selected_orders["aic"]), 1)
            res = model.fit(p)
            g1 = res.test_causality(comp, ["money_yoy"], kind="f")
            g2 = res.test_causality("money_yoy", [comp], kind="f")
            rows.append(dict(component=comp, sample=sample_name, n_obs=len(d), lag_aic=p,
                             stable=bool(res.is_stable()),
                             money_to_component_p=round(float(g1.pvalue), 4),
                             component_to_money_p=round(float(g2.pvalue), 4)))
    return pd.DataFrame(rows)


def lag_corr_table(q):
    d = q.dropna()
    rows = []
    for k in range(0, 13):
        rows.append(dict(lag_quarters=k,
                         corr_money_demand=round(float(d["money_yoy"].shift(k).corr(d["demand_yoy"])), 3),
                         corr_money_supply=round(float(d["money_yoy"].shift(k).corr(d["supply_yoy"])), 3)))
    return pd.DataFrame(rows)


def make_figure(q, best_lag):
    d = q.dropna()
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax = axes[0]
    ax.plot(d.index, d["demand_yoy"], label="Demand-driven PCE inflation (y/y contribution)", linewidth=1.4)
    ax2 = ax.twinx()
    ax2.plot(d.index, d["money_yoy"].shift(best_lag), label=f"M2-less-base growth (y/y), lagged {best_lag}q", color="darkorange", linewidth=1.2, alpha=0.8)
    ax.set_title(f"Shapiro demand-driven inflation vs lagged money growth (lag {best_lag}q)")
    ax.set_ylabel("Demand contribution, pp")
    ax2.set_ylabel("Money growth, percent")
    ax.legend(loc="upper left", fontsize=8)
    ax2.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax = axes[1]
    ax.plot(d.index, d["supply_yoy"], label="Supply-driven PCE inflation (y/y contribution)", linewidth=1.4, color="green")
    ax2 = ax.twinx()
    ax2.plot(d.index, d["money_yoy"].shift(best_lag), label=f"Money growth, lagged {best_lag}q", color="darkorange", linewidth=1.2, alpha=0.8)
    ax.set_title("Supply-driven inflation vs the same lagged money growth (placebo)")
    ax.set_ylabel("Supply contribution, pp")
    ax2.set_ylabel("Money growth, percent")
    ax.legend(loc="upper left", fontsize=8)
    ax2.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "shapiro_validation.png"), dpi=150)
    plt.close(fig)


def main():
    q = load()
    granger = granger_rows(q)
    granger.to_csv(os.path.join(TAB, "shapiro_validation_granger.csv"), index=False)
    corr = lag_corr_table(q)
    corr.to_csv(os.path.join(TAB, "shapiro_validation_lagcorr.csv"), index=False)
    best_lag = int(corr.loc[corr["corr_money_demand"].idxmax(), "lag_quarters"])
    make_figure(q, best_lag)
    print("=== GRANGER: money growth vs Shapiro components ===")
    print(granger.to_string(index=False))
    print()
    print("=== LAG CORRELATIONS (money_yoy shifted k quarters) ===")
    print(corr.to_string(index=False))
    print()
    print("best demand-corr lag:", best_lag)


if __name__ == "__main__":
    main()
