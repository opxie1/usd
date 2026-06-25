import os
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.mlemodel import MLEModel

warnings.filterwarnings("ignore")
np.random.seed(12345)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")

TRIM = 0.15
NBOOT = 399


def g400(x):
    return 400.0 * (np.log(x) - np.log(x.shift(1)))


def load():
    return pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")


def ols_rss(X, y):
    b, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    return float(e @ e), b


def sup_wald(y, X):
    n, k = X.shape
    rss0, b0 = ols_rss(X, y)
    lo, hi = int(n * TRIM), int(n * (1 - TRIM))
    best_w, best_t = -1.0, lo
    for t in range(lo, hi):
        rss1, _ = ols_rss(X[:t], y[:t])
        rss2, _ = ols_rss(X[t:], y[t:])
        rss = rss1 + rss2
        w = ((rss0 - rss) / k) / (rss / (n - 2 * k))
        if w > best_w:
            best_w, best_t = w, t
    return best_w, best_t, b0


def break_test(df, infl_col, label):
    d = pd.DataFrame(index=df.index)
    d["y"] = df[infl_col]
    d["infl_lag1"] = df[infl_col].shift(1)
    d["money_lag1"] = g400(df["m2_less_base"]).shift(1)
    d["gdp_lag1"] = g400(df["real_gdp"]).shift(1)
    d = d.dropna()
    y = d["y"].values
    X = np.column_stack([np.ones(len(d)), d["infl_lag1"].values, d["money_lag1"].values, d["gdp_lag1"].values])
    w_obs, t_obs, b0 = sup_wald(y, X)
    resid = y - X @ b0
    fitted = X @ b0
    count = 0
    for _ in range(NBOOT):
        e = resid[np.random.randint(0, len(resid), len(resid))]
        yb = fitted + e
        wb, _, _ = sup_wald(yb, X)
        if wb >= w_obs:
            count += 1
    pval = (count + 1) / (NBOOT + 1)
    return dict(series=label, sup_wald=round(float(w_obs), 2),
                break_quarter=str(d.index[t_obs].to_period("Q")),
                bootstrap_p=round(float(pval), 4), n_obs=len(d))


class TVP(MLEModel):
    def __init__(self, y, X, names):
        k = X.shape[1]
        super().__init__(endog=y, k_states=k, initialization="approximate_diffuse", loglikelihood_burn=k)
        self.k = k
        self.names_ = names
        self.ssm["design"] = X.T[np.newaxis, :, :]
        self.ssm["transition"] = np.eye(k)
        self.ssm["selection"] = np.eye(k)

    @property
    def param_names(self):
        return ["sigma.obs"] + [f"sigma.{n}" for n in self.names_]

    @property
    def start_params(self):
        return np.r_[np.std(self.endog) * 0.7, [0.08] * self.k]

    def transform_params(self, u):
        return u ** 2

    def untransform_params(self, c):
        return np.sqrt(c)

    def update(self, params, **kwargs):
        params = super().update(params, **kwargs)
        self["obs_cov", 0, 0] = params[0]
        for i in range(self.k):
            self["state_cov", i, i] = params[i + 1]


def state_sds(d, regressors, model_label):
    sub = d[["y"] + regressors].dropna()
    X = np.column_stack([np.ones(len(sub))] + [sub[c].values for c in regressors])
    names = ["const"] + regressors
    res = TVP(sub["y"].values, X, names).fit(disp=False, maxiter=500)
    sds = np.sqrt(np.clip(res.params[1:], 0.0, None))
    rows = []
    for nm, sd in zip(names, sds):
        rows.append(dict(model=model_label, coefficient=nm, state_innovation_sd=round(float(sd), 4),
                         verdict="effectively constant" if sd < 0.01 else "time varying"))
    return rows


def main():
    df = load()

    breaks = pd.DataFrame([
        break_test(df, "infl_cpi_qoq_ann", "cpi inflation"),
        break_test(df, "infl_pce_price_qoq_ann", "pce inflation"),
    ])
    breaks.to_csv(os.path.join(TAB, "task7_structural_break.csv"), index=False)

    base = pd.DataFrame(index=df.index)
    base["y"] = g400(df["debt_mortgage_household"] + df["debt_business"] + df["debt_consumer_credit"])
    base["d_rate_mortgage_lag1"] = df["rate_mortgage_30y"].diff().shift(1)
    base["pce_real_g_lag1"] = g400(df["real_pce"]).shift(1)
    base["fed_debt_g_lag1"] = g400(df["debt_federal"]).shift(1)

    rows = state_sds(base, ["d_rate_mortgage_lag1", "pce_real_g_lag1", "fed_debt_g_lag1"], "task5 aggregate private borrowing")

    sectors = [("mortgage", "debt_mortgage_household", "rate_mortgage_30y"),
               ("consumer", "debt_consumer_credit", "rate_consumer_personal24m"),
               ("business", "debt_business_corporate", "rate_business_baa")]
    for name, debt, rate in sectors:
        s = pd.DataFrame(index=df.index)
        s["y"] = g400(df[debt])
        s["d_rate_lag1"] = df[rate].diff().shift(1)
        s["money_lag1"] = g400(df["m2_less_base"]).shift(1)
        rows += state_sds(s, ["d_rate_lag1", "money_lag1"], f"task5b {name} (market, lean)")
    constancy = pd.DataFrame(rows)
    constancy.to_csv(os.path.join(TAB, "task3_tvp_constancy.csv"), index=False)

    print("=== 7. STRUCTURAL BREAK (Quandt-Andrews sup-Wald, residual bootstrap p, 15% trim) ===")
    print(breaks.to_string(index=False))
    print("\n=== 3. TVP PARAMETER CONSTANCY (estimated random-walk innovation sd per coefficient) ===")
    print(constancy.to_string(index=False))


if __name__ == "__main__":
    main()
