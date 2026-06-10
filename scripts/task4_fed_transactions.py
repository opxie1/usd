import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen, select_coint_rank
from statsmodels.tsa.vector_ar.vecm import select_order as vecm_select_order

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")
FIG = os.path.join(ROOT, "figures")

ORDERING_NOTE = "Cholesky ordering: fed_g, base_g, money_g, d_ffr, d_gs10, infl_cpi (Fed instrument first, then base money, broad money, rates, prices)"

SAMPLES = {
    "full_2003_2026": (None, None),
    "pre_covid_2003_2019": (None, "2019-12-31"),
}

GRANGER_PAIRS = [
    ("money_g", "fed_g"),
    ("base_g", "fed_g"),
    ("d_ffr", "fed_g"),
    ("d_gs10", "fed_g"),
    ("infl_cpi", "fed_g"),
    ("fed_g", "d_ffr"),
    ("infl_cpi", "money_g"),
]


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    out = pd.DataFrame(index=df.index)
    out["fed_g"] = 400.0 * (np.log(df["fed_securities_total"]) - np.log(df["fed_securities_total"].shift(1)))
    out["base_g"] = 400.0 * (np.log(df["monetary_base"]) - np.log(df["monetary_base"].shift(1)))
    out["money_g"] = 400.0 * (np.log(df["m2_less_base"]) - np.log(df["m2_less_base"].shift(1)))
    out["d_ffr"] = df["rate_fedfunds_policy"].diff()
    out["d_gs10"] = df["rate_federal_10y"].diff()
    out["infl_cpi"] = df["infl_cpi_qoq_ann"]
    lv = pd.DataFrame(index=df.index)
    lv["log_fed_sec"] = np.log(df["fed_securities_total"])
    lv["log_base"] = np.log(df["monetary_base"])
    lv["log_m2_less_base"] = np.log(df["m2_less_base"])
    lv["ffr"] = df["rate_fedfunds_policy"]
    lv["gs10"] = df["rate_federal_10y"]
    lv["log_cpi"] = np.log(df["cpi"])
    return out.dropna(), lv.dropna()


def fevd_share(irf, names, response, impulse):
    psi = irf.orth_irfs
    i = names.index(response)
    j = names.index(impulse)
    return float((psi[:, i, j] ** 2).sum() / (psi[:, i, :] ** 2).sum())


def run_var(d, sample_name, start, end):
    w = d.copy()
    if start:
        w = w.loc[w.index >= start]
    if end:
        w = w.loc[w.index <= end]
    n = len(w)
    model = VAR(w)
    sel = model.select_order(maxlags=4)
    p = max(int(sel.selected_orders["aic"]), 1)
    res = model.fit(p)
    names = list(res.names)
    rows = []
    for caused, causing in GRANGER_PAIRS:
        g = res.test_causality(caused, [causing], kind="f")
        rows.append(dict(sample=sample_name, n_obs=n, lag_aic=p, stable=bool(res.is_stable()),
                         caused=caused, causing=causing, granger_p=round(float(g.pvalue), 4)))
    irf = res.irf(12)
    extras = dict(
        fevd_money_from_fed_h12=round(fevd_share(irf, names, "money_g", "fed_g"), 3),
        fevd_infl_from_money_h12=round(fevd_share(irf, names, "infl_cpi", "money_g"), 3),
        fevd_gs10_from_fed_h12=round(fevd_share(irf, names, "d_gs10", "fed_g"), 3),
    )
    return rows, extras, res, irf


def main():
    d, lv = load()

    all_rows = []
    extras_rows = []
    for sample_name, (start, end) in SAMPLES.items():
        rows, extras, res, irf = run_var(d, sample_name, start, end)
        all_rows.extend(rows)
        extras_rows.append(dict(sample=sample_name, **extras))
        if sample_name == "full_2003_2026":
            fig = irf.plot(orth=True, impulse="fed_g")
            fig.suptitle(f"Orthogonalized IRFs to a Fed securities growth shock (full sample 2003-2026)\n{ORDERING_NOTE}", fontsize=9)
            fig.tight_layout()
            fig.savefig(os.path.join(FIG, "task4_irf_fed_shock.png"), dpi=150)
            plt.close(fig)
            fig = irf.plot(orth=True, impulse="money_g", response="infl_cpi")
            fig.suptitle("Orthogonalized IRF: money growth shock, CPI inflation response (2003-2026)", fontsize=10)
            fig.tight_layout()
            fig.savefig(os.path.join(FIG, "task4_irf_money_to_infl.png"), dpi=150)
            plt.close(fig)

    granger = pd.DataFrame(all_rows)
    granger.to_csv(os.path.join(TAB, "task4_granger.csv"), index=False)
    fevd = pd.DataFrame(extras_rows)
    fevd.to_csv(os.path.join(TAB, "task4_fevd.csv"), index=False)

    ksel = vecm_select_order(lv, maxlags=4, deterministic="co")
    k = max(int(ksel.aic), 1)
    jo_rows = []
    for det_order, det_label in [(0, "constant"), (1, "linear_trend")]:
        jo = coint_johansen(lv.values, det_order, k)
        for r in range(len(jo.lr1)):
            jo_rows.append(dict(deterministic=det_label, k_ar_diff=k, null_rank_at_most=r,
                                trace_stat=round(float(jo.lr1[r]), 2),
                                cv_95=round(float(jo.cvt[r, 1]), 2),
                                reject_at_5pct=bool(jo.lr1[r] > jo.cvt[r, 1])))
    jo_df = pd.DataFrame(jo_rows)
    jo_df.to_csv(os.path.join(TAB, "task4_johansen.csv"), index=False)

    rank = select_coint_rank(lv.values, 1, k, method="trace", signif=0.05).rank
    if rank > 0:
        vecm = VECM(lv, k_ar_diff=k, coint_rank=rank, deterministic="co").fit()
        alpha = pd.DataFrame(vecm.alpha, index=lv.columns,
                             columns=[f"ec{i+1}" for i in range(rank)])
        beta = pd.DataFrame(vecm.beta, index=lv.columns,
                            columns=[f"ec{i+1}" for i in range(rank)])
        out = pd.concat([alpha.add_prefix("alpha_"), beta.add_prefix("beta_")], axis=1)
        out.rename_axis("variable").to_csv(os.path.join(TAB, "task4_vecm_alpha_beta.csv"))
    else:
        pd.DataFrame([dict(note="no cointegration at 5 percent, VECM not fit")]).to_csv(
            os.path.join(TAB, "task4_vecm_alpha_beta.csv"), index=False)

    print("=== GRANGER (Fed transactions system) ===")
    print(granger.to_string(index=False))
    print()
    print("=== FEVD shares at h=12 ===")
    print(fevd.to_string(index=False))
    print()
    print("=== JOHANSEN trace test (levels system, k_ar_diff =", k, ") ===")
    print(jo_df.to_string(index=False))
    print()
    print("selected cointegration rank (trend spec, 5 percent):", int(rank))
    print(ORDERING_NOTE)


if __name__ == "__main__":
    main()
