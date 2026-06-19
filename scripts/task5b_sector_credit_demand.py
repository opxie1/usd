import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS
from statsmodels.tsa.statespace.mlemodel import MLEModel

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")
FIG = os.path.join(ROOT, "figures")

SECTORS = [
    ("mortgage", "debt_mortgage_household", {"market": "rate_mortgage_30y", "implied": "rate_mortgage_30y"}),
    ("consumer", "debt_consumer_credit", {"market": "rate_consumer_personal24m", "implied": "rate_consumer_implied"}),
    ("business", "debt_business_corporate", {"market": "rate_business_baa", "implied": "rate_business_implied"}),
]
RATE_TYPES = ["market", "implied"]
MONEY = [("m2_less_base", "m2_less_base"), ("base", "monetary_base")]
WINDOW = 40
COVID = pd.Timestamp("2020-03-31")


def g400(x):
    return 400.0 * (np.log(x) - np.log(x.shift(1)))


class TVPRegression(MLEModel):
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

    def transform_params(self, unconstrained):
        return unconstrained ** 2

    def untransform_params(self, constrained):
        return np.sqrt(constrained)

    def update(self, params, **kwargs):
        params = super().update(params, **kwargs)
        self["obs_cov", 0, 0] = params[0]
        for i in range(self.k):
            self["state_cov", i, i] = params[i + 1]


def load():
    return pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")


def build(df, debt_col, rate_col, money_col):
    d = pd.DataFrame(index=df.index)
    d["y"] = g400(df[debt_col])
    d["d_rate_lag1"] = df[rate_col].diff().shift(1)
    d["money_lag1"] = g400(df[money_col]).shift(1)
    return d.dropna()


def fit_tvp(d):
    y = d["y"].values
    X = np.column_stack([np.ones(len(d)), d["d_rate_lag1"].values, d["money_lag1"].values])
    names = ["const", "d_rate_lag1", "money_lag1"]
    res = TVPRegression(y, X, names).fit(disp=False, maxiter=500)
    conv = bool(res.mle_retvals.get("converged", False))
    beta = pd.Series(res.smoothed_state[2], index=d.index)
    var = np.array([res.smoothed_state_cov[2, 2, t] for t in range(len(d))])
    se = pd.Series(np.sqrt(np.clip(var, 0.0, None)), index=d.index)
    return beta, se, conv


def fit_rolling(d):
    y = d["y"]
    X = sm.add_constant(d[["d_rate_lag1", "money_lag1"]])
    res = RollingOLS(y, X, window=WINDOW).fit()
    return res.params["money_lag1"], res.bse["money_lag1"]


def summarize(beta, se, sector, money_label, rate_type, method, n_obs, converged):
    z = beta / se
    pre = (beta.index >= pd.Timestamp("2010-01-01")) & (beta.index < pd.Timestamp("2020-01-01"))
    post = beta.index >= pd.Timestamp("2020-01-01")
    bd = beta.dropna()
    sed = se.reindex(bd.index)
    return dict(sector=sector, money=money_label, rate_type=rate_type, method=method, n_obs=n_obs, converged=converged,
                coef_2010_2019_mean=round(float(beta[pre].mean()), 3),
                coef_2020plus_mean=round(float(beta[post].mean()), 3),
                coef_end=round(float(bd.iloc[-1]), 3),
                se_end=round(float(sed.iloc[-1]), 3),
                frac_2020plus_sig=round(float((z[post].abs() > 1.96).mean()), 2) if post.any() else float("nan"))


def panel_plot(ax, store, sector, method, rate_type):
    colors = {"m2_less_base": "tab:blue", "base": "tab:orange"}
    labels = {"m2_less_base": "M2 less base", "base": "Base money"}
    for money_label in ["m2_less_base", "base"]:
        beta, se = store[(sector, money_label, method, rate_type)]
        ax.plot(beta.index, beta.values, color=colors[money_label], linewidth=1.4, label=labels[money_label])
        ax.fill_between(beta.index, beta - 1.96 * se, beta + 1.96 * se, color=colors[money_label], alpha=0.18)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(COVID, color="gray", linestyle=":", linewidth=1.0)
    ax.set_title(f"{sector} borrowing ({rate_type} rate): coefficient on lagged money growth")
    ax.set_ylabel("Coefficient")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)


def main():
    df = load()
    store = {}
    rows = []
    tvp_wide = {}
    roll_wide = {}

    for sector, debt_col, rate_cols in SECTORS:
        for rate_type in RATE_TYPES:
            rate_col = rate_cols[rate_type]
            for money_label, money_col in MONEY:
                d = build(df, debt_col, rate_col, money_col)
                tb, ts, conv = fit_tvp(d)
                store[(sector, money_label, "tvp", rate_type)] = (tb, ts)
                tvp_wide[f"beta_{sector}_{money_label}_{rate_type}"] = tb
                tvp_wide[f"se_{sector}_{money_label}_{rate_type}"] = ts
                rows.append(summarize(tb, ts, sector, money_label, rate_type, "tvp_kalman", len(d), conv))

                rb, rs = fit_rolling(d)
                store[(sector, money_label, "rolling", rate_type)] = (rb, rs)
                roll_wide[f"beta_{sector}_{money_label}_{rate_type}"] = rb
                roll_wide[f"se_{sector}_{money_label}_{rate_type}"] = rs
                rows.append(summarize(rb, rs, sector, money_label, rate_type, "rolling_ols", len(d), True))

    summary = pd.DataFrame(rows)
    summary.to_csv(os.path.join(TAB, "task5b_money_coefficients.csv"), index=False)
    pd.DataFrame(tvp_wide).rename_axis("quarter_end").to_csv(os.path.join(TAB, "task5b_tvp_money_betas.csv"))
    pd.DataFrame(roll_wide).rename_axis("quarter_end").to_csv(os.path.join(TAB, "task5b_rolling_money_betas.csv"))

    plans = [
        ("tvp", "market", "task5b_tvp_money_coef.png", "Kalman-smoothed coefficient on money growth, by debt type (market rates)"),
        ("rolling", "market", "task5b_rolling_money_coef.png", f"Rolling {WINDOW}q OLS coefficient on money growth, 95% bands, by debt type (market rates)"),
        ("tvp", "implied", "task5b_tvp_money_coef_implied.png", "Kalman-smoothed coefficient on money growth, by debt type (implied rates)"),
        ("rolling", "implied", "task5b_rolling_money_coef_implied.png", f"Rolling {WINDOW}q OLS coefficient on money growth, 95% bands, by debt type (implied rates)"),
    ]
    for method, rate_type, fname, suptitle in plans:
        fig, axes = plt.subplots(3, 1, figsize=(10, 11), sharex=True)
        for ax, (sector, _, _) in zip(axes, SECTORS):
            panel_plot(ax, store, sector, method, rate_type)
        axes[-1].set_xlabel("Quarter")
        fig.suptitle(suptitle)
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, fname), dpi=150)
        plt.close(fig)

    print("=== MONEY-GROWTH COEFFICIENT BY DEBT TYPE (market and implied rates) ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
