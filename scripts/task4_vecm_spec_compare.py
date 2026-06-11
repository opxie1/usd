import os
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.vecm import VECM, select_coint_rank
from statsmodels.tsa.vector_ar.vecm import select_order as vecm_select_order

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")


def load_levels():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    lv = pd.DataFrame(index=df.index)
    lv["log_fed_sec"] = np.log(df["fed_securities_total"])
    lv["log_base"] = np.log(df["monetary_base"])
    lv["log_m2_less_base"] = np.log(df["m2_less_base"])
    lv["ffr"] = df["rate_fedfunds_policy"]
    lv["gs10"] = df["rate_federal_10y"]
    lv["log_cpi"] = np.log(df["cpi"])
    return lv.dropna()


def main():
    lv = load_levels()
    k = max(int(vecm_select_order(lv, maxlags=4, deterministic="co").aic), 1)

    specs = [
        dict(label="constant_only", det_order=0, deterministic="co"),
        dict(label="constant_plus_trend", det_order=1, deterministic="colo"),
    ]

    summary_rows = []
    alpha_frames = []
    beta_frames = []
    for spec in specs:
        rank = int(select_coint_rank(lv.values, spec["det_order"], k, method="trace", signif=0.05).rank)
        if rank == 0:
            summary_rows.append(dict(spec=spec["label"], deterministic=spec["deterministic"],
                                     k_ar_diff=k, rank=0, n_obs=len(lv), llf=np.nan,
                                     note="no cointegration at 5 percent"))
            continue
        res = VECM(lv, k_ar_diff=k, coint_rank=rank, deterministic=spec["deterministic"]).fit()
        summary_rows.append(dict(spec=spec["label"], deterministic=spec["deterministic"],
                                 k_ar_diff=k, rank=rank, n_obs=len(lv),
                                 llf=round(float(res.llf), 1), note=""))
        a = pd.DataFrame(res.alpha, index=lv.columns,
                         columns=[f"{spec['label']}_alpha_ec{i+1}" for i in range(rank)])
        b = pd.DataFrame(res.beta, index=lv.columns,
                         columns=[f"{spec['label']}_beta_ec{i+1}" for i in range(rank)])
        alpha_frames.append(a.round(4))
        beta_frames.append(b.round(4))

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(os.path.join(TAB, "task4_vecm_specs_summary.csv"), index=False)
    coefs = pd.concat(alpha_frames + beta_frames, axis=1)
    coefs.rename_axis("variable").to_csv(os.path.join(TAB, "task4_vecm_specs_coefficients.csv"))

    print("=== VECM SPEC COMPARISON (Fed transactions system, 2003Q1+) ===")
    print(summary.to_string(index=False))
    print()
    print("=== ALPHA (loadings) and BETA (cointegrating vectors) ===")
    print(coefs.to_string())


if __name__ == "__main__":
    main()
