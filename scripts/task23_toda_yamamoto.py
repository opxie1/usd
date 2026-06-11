import os
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.api import VAR

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")

COLS = {
    "money_g": None,
    "rate_federal": "rate_federal_10y",
    "rate_mortgage": "rate_mortgage_30y",
    "rate_business": "rate_business_baa",
    "rate_consumer": "rate_consumer_personal24m",
}
D_MAX = 1


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    out = pd.DataFrame(index=df.index)
    out["money_g"] = 400.0 * (np.log(df["m2_less_base"]) - np.log(df["m2_less_base"].shift(1)))
    for short, col in COLS.items():
        if col:
            out[short] = df[col]
    return out[list(COLS)].dropna()


def build_design(d, lags):
    names = list(d.columns)
    k = len(names)
    Y = d.values
    n = len(d)
    rows = n - lags
    X = np.ones((rows, 1 + k * lags))
    for l in range(1, lags + 1):
        X[:, 1 + (l - 1) * k:1 + l * k] = Y[lags - l:n - l, :]
    Yt = Y[lags:, :]
    return Yt, X, names


def ty_pvalue(res, k, p, causing_idx, n_params):
    rows = []
    for l in range(1, p + 1):
        idx = 1 + (l - 1) * k + causing_idx
        r = np.zeros(n_params)
        r[idx] = 1.0
        rows.append(r)
    R = np.vstack(rows)
    f = res.f_test(R)
    return float(np.squeeze(f.pvalue))


def main():
    d = load()
    var_sel = VAR(d).select_order(maxlags=8)
    p = max(int(var_sel.selected_orders["aic"]), 1)
    lags = p + D_MAX
    Yt, X, names = build_design(d, lags)
    k = len(names)
    n_params = X.shape[1]

    mat = pd.DataFrame(index=names, columns=names, dtype=float)
    joint_rows = []
    for i, caused in enumerate(names):
        res = sm.OLS(Yt[:, i], X).fit()
        for j, causing in enumerate(names):
            if i == j:
                continue
            mat.loc[caused, causing] = round(ty_pvalue(res, k, p, j, n_params), 4)
        if caused == "rate_federal":
            rows = []
            for j, causing in enumerate(names):
                if causing == "rate_federal" or causing == "money_g":
                    continue
                for l in range(1, p + 1):
                    idx = 1 + (l - 1) * k + j
                    r = np.zeros(n_params)
                    r[idx] = 1.0
                    rows.append(r)
            R = np.vstack(rows)
            joint_rows.append(dict(test="other_rates_to_federal_joint",
                                   p_value=round(float(np.squeeze(res.f_test(R).pvalue)), 4)))

    mat.rename_axis("caused").to_csv(os.path.join(TAB, "task23_toda_yamamoto_matrix.csv"))
    pd.DataFrame(joint_rows).to_csv(os.path.join(TAB, "task23_toda_yamamoto_joint.csv"), index=False)

    std = pd.read_csv(os.path.join(TAB, "task23_market_granger_market4_full_1972_2026.csv")).set_index("caused")

    print(f"=== TODA-YAMAMOTO, market-rate system, levels VAR({p}+{D_MAX}), n={len(Yt)} ===")
    print(mat.to_string())
    print()
    for row in joint_rows:
        print(f"{row['test']}: p={row['p_value']}")
    print()
    print("=== STANDARD VAR GRANGER (for comparison, from task23 market run) ===")
    print(std.to_string())


if __name__ == "__main__":
    main()
