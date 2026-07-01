import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller, kpss

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")
FIG = os.path.join(ROOT, "figures")

MEASURES = {
    "cpi": "infl_cpi_qoq_ann",
    "pce": "infl_pce_price_qoq_ann",
    "ppi": "infl_ppi_allcommodities_qoq_ann",
    "gdpdef": "infl_gdp_deflator_qoq_ann",
}

SAMPLES = {
    "full_1959_2026": (None, None),
    "pre_covid_1959_2019": (None, "2019-12-31"),
    "covid_post_2020_2026": ("2020-01-01", None),
}

ORDERING_NOTE = "Cholesky ordering: gdp_g, money_g, inflation (output slowest, prices respond contemporaneously to money)"


def load_panel():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    out = pd.DataFrame(index=df.index)
    out["money_g"] = 400.0 * (np.log(df["m2_less_base"]) - np.log(df["m2_less_base"].shift(1)))
    out["gdp_g"] = 400.0 * (np.log(df["real_gdp"]) - np.log(df["real_gdp"].shift(1)))
    for m, col in MEASURES.items():
        out[f"infl_{m}"] = df[col]
    out["log_m2_less_base"] = np.log(df["m2_less_base"])
    out["log_real_gdp"] = np.log(df["real_gdp"])
    for raw in ["cpi", "pce_price", "ppi_allcommodities", "gdp_deflator"]:
        out[f"log_{raw}"] = np.log(df[raw])
    return out


def unit_root_table(df):
    specs = [
        ("log_m2_less_base", "ct"), ("money_g", "c"),
        ("log_real_gdp", "ct"), ("gdp_g", "c"),
        ("log_cpi", "ct"), ("infl_cpi", "c"),
        ("log_pce_price", "ct"), ("infl_pce", "c"),
        ("log_ppi_allcommodities", "ct"), ("infl_ppi", "c"),
        ("log_gdp_deflator", "ct"), ("infl_gdpdef", "c"),
    ]
    rows = []
    for col, reg in specs:
        x = df[col].dropna()
        adf_stat, adf_p, _, adf_n, _, _ = adfuller(x, regression=reg, autolag="AIC")
        k_stat, k_p, _, _ = kpss(x, regression=reg, nlags="auto")
        rows.append(dict(variable=col, deterministic=reg, n=adf_n,
                         adf_stat=round(float(adf_stat), 3), adf_p=round(float(adf_p), 4),
                         kpss_stat=round(float(k_stat), 3), kpss_p=round(float(k_p), 4)))
    return pd.DataFrame(rows)


def fevd_share(irf, names, response, impulse, horizon=12):
    psi = irf.orth_irfs[:horizon]
    i = names.index(response)
    j = names.index(impulse)
    num = float((psi[:, i, j] ** 2).sum())
    den = float((psi[:, i, :] ** 2).sum())
    return num / den


def run_var(df, measure, sample_name, start, end):
    infl_col = f"infl_{measure}"
    d = df[["gdp_g", "money_g", infl_col]].dropna()
    if start:
        d = d.loc[d.index >= start]
    if end:
        d = d.loc[d.index <= end]
    n = len(d)
    if n < 30:
        maxlags = 2
    elif n < 80:
        maxlags = 4
    else:
        maxlags = 8
    model = VAR(d)
    sel = model.select_order(maxlags=maxlags)
    p = max(int(sel.selected_orders["aic"]), 1)
    res = model.fit(p)
    g_money_infl = res.test_causality(infl_col, ["money_g"], kind="f")
    g_infl_money = res.test_causality("money_g", [infl_col], kind="f")
    irf = res.irf(12)
    names = list(res.names)
    oi = irf.orth_irfs[:, names.index(infl_col), names.index("money_g")]
    row = dict(measure=measure, sample=sample_name, n_obs=n, lag_aic=p, maxlags=maxlags,
               stable=bool(res.is_stable()),
               granger_money_to_infl_p=round(float(g_money_infl.pvalue), 4),
               granger_infl_to_money_p=round(float(g_infl_money.pvalue), 4),
               fevd_money_share_h12=round(fevd_share(irf, names, infl_col, "money_g"), 3),
               irf_peak_infl_resp=round(float(np.max(oi)), 3),
               irf_peak_quarter=int(np.argmax(oi)))
    return row, res, irf


def rolling_granger(df, measure, window=60, lag=4):
    infl_col = f"infl_{measure}"
    d = df[["gdp_g", "money_g", infl_col]].dropna()
    dates, pvals = [], []
    for i in range(window, len(d) + 1):
        w = d.iloc[i - window:i]
        try:
            r = VAR(w).fit(lag)
            pv = float(r.test_causality(infl_col, ["money_g"], kind="f").pvalue)
        except Exception:
            pv = np.nan
        dates.append(d.index[i - 1])
        pvals.append(pv)
    return pd.Series(pvals, index=pd.DatetimeIndex(dates), name=measure)


def main():
    df = load_panel()

    ur = unit_root_table(df)
    ur.to_csv(os.path.join(TAB, "task1_unit_roots.csv"), index=False)

    rows = []
    for measure in MEASURES:
        for sample_name, (start, end) in SAMPLES.items():
            row, res, irf = run_var(df, measure, sample_name, start, end)
            rows.append(row)
            if sample_name == "full_1959_2026":
                meas = {"cpi": "CPI", "pce": "PCE", "ppi": "PPI", "gdpdef": "GDP-deflator"}
                fig = irf.plot(orth=True, impulse="money_g", response=f"infl_{measure}")
                for ax in fig.axes:
                    ax.set_title(f"Money-growth shock to {meas[measure]} inflation")
                fig.suptitle("Orthogonalized impulse response, full sample", fontsize=11)
                fig.tight_layout()
                fig.savefig(os.path.join(FIG, f"task1_irf_{measure}.png"), dpi=150)
                plt.close(fig)
    summary = pd.DataFrame(rows)
    summary.to_csv(os.path.join(TAB, "task1_var_summary.csv"), index=False)

    roll = {}
    for measure in MEASURES:
        roll[measure] = rolling_granger(df, measure)
    roll_df = pd.DataFrame(roll)
    roll_df.rename_axis("window_end").to_csv(os.path.join(TAB, "task1_rolling_granger.csv"))

    meas = {"cpi": "CPI", "pce": "PCE", "ppi": "PPI", "gdpdef": "GDP deflator"}
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, measure in zip(axes.ravel(), MEASURES):
        s = roll_df[measure]
        ax.plot(s.index, s.values, linewidth=1.2)
        ax.axhline(0.05, color="red", linestyle="--", linewidth=1.0)
        ax.set_title(f"{meas[measure]}: money growth causes inflation")
        ax.set_ylabel("p-value")
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)
    fig.suptitle("Rolling 60-quarter Granger-causality p-values")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "task1_rolling_granger.png"), dpi=150)
    plt.close(fig)

    print("=== UNIT ROOTS ===")
    print(ur.to_string(index=False))
    print()
    print("=== VAR SUMMARY ===")
    print(summary.to_string(index=False))
    print()
    print(ORDERING_NOTE)


if __name__ == "__main__":
    main()
