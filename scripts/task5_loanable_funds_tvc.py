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

PERIODS = {
    "pre_covid_2010_2019": ("2010-01-01", "2019-12-31"),
    "covid_2020_2021": ("2020-01-01", "2021-12-31"),
    "post_2022_2026": ("2022-01-01", None),
}

REGRESSORS = ["d_rate_mortgage_lag1", "pce_real_g_lag1", "fed_debt_g_lag1"]


def g400(x):
    return 400.0 * (np.log(x) - np.log(x.shift(1)))


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    out = pd.DataFrame(index=df.index)
    private_debt = df["debt_mortgage_household"] + df["debt_business"] + df["debt_consumer_credit"]
    out["private_borrow_g"] = g400(private_debt)
    out["pce_real_g"] = g400(df["real_pce"])
    out["fed_debt_g"] = g400(df["debt_federal"])
    out["d_rate_mortgage_lag1"] = df["rate_mortgage_30y"].diff().shift(1)
    out["pce_real_g_lag1"] = out["pce_real_g"].shift(1)
    out["fed_debt_g_lag1"] = out["fed_debt_g"].shift(1)
    out["gdp_real_g"] = g400(df["real_gdp"])
    out["money_g"] = g400(df["m2_less_base"])
    out["infl_cpi_yoy"] = df["infl_cpi_yoy"]
    for sector in ["debt_mortgage_household", "debt_business", "debt_consumer_credit", "debt_federal", "debt_state_local"]:
        out[f"{sector}_g"] = g400(df[sector])
    for comp in ["pce_nominal", "investment_nominal", "government_nominal", "netexports_nominal"]:
        out[f"share_{comp}"] = 100.0 * df[comp] / df["nominal_gdp"]
    return out


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


def fig_shares(d):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    labels = {
        "share_pce_nominal": "Consumption (PCE)",
        "share_investment_nominal": "Investment (GPDI)",
        "share_government_nominal": "Government (GCE)",
        "share_netexports_nominal": "Net exports",
    }
    for col, lab in labels.items():
        ax.plot(d.index, d[col], label=lab, linewidth=1.4)
    ax.axvline(pd.Timestamp("2020-03-31"), color="gray", linestyle=":", linewidth=1.0)
    ax.set_title("GDP components as shares of nominal GDP")
    ax.set_ylabel("Percent of GDP")
    ax.set_xlabel("Quarter")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "task5_gdp_shares.png"), dpi=150)
    plt.close(fig)


def period_table(d):
    rows = []
    cols = ["gdp_real_g", "pce_real_g", "private_borrow_g", "money_g", "infl_cpi_yoy",
            "debt_mortgage_household_g", "debt_business_g", "debt_consumer_credit_g",
            "debt_federal_g", "debt_state_local_g", "share_pce_nominal"]
    for name, (start, end) in PERIODS.items():
        w = d.loc[start:end] if end else d.loc[start:]
        row = dict(period=name, n_quarters=int(w["gdp_real_g"].notna().sum()))
        for c in cols:
            row[c] = round(float(w[c].mean()), 2)
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(TAB, "task5_period_growth.csv"), index=False)
    return out


def run_tvp(d):
    data = d[["private_borrow_g"] + REGRESSORS].dropna()
    y = data["private_borrow_g"].values
    X = sm.add_constant(data[REGRESSORS]).values
    names = ["const"] + REGRESSORS
    mod = TVPRegression(y, X, names)
    res = mod.fit(disp=False, maxiter=500)
    converged = bool(res.mle_retvals.get("converged", False))
    betas = pd.DataFrame(res.smoothed_state.T, index=data.index, columns=names)
    ses = pd.DataFrame(
        np.sqrt(np.clip(np.array([np.diag(res.smoothed_state_cov[:, :, t]) for t in range(len(data))]), 0, None)),
        index=data.index, columns=names)
    out = pd.concat([betas.add_prefix("beta_"), ses.add_prefix("se_")], axis=1)
    out.rename_axis("quarter_end").to_csv(os.path.join(TAB, "task5_tvp_betas.csv"))

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, name in zip(axes.ravel(), names):
        b = betas[name]
        s = ses[name]
        ax.plot(b.index, b.values, linewidth=1.5)
        ax.fill_between(b.index, b - 1.96 * s, b + 1.96 * s, alpha=0.25)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.axvline(pd.Timestamp("2020-03-31"), color="gray", linestyle=":", linewidth=1.0)
        ax.set_title(f"TVP coefficient: {name}")
        ax.grid(True, alpha=0.3)
    fig.suptitle(f"Kalman-smoothed time-varying coefficients, private borrowing growth equation (converged={converged})")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "task5_tvc_coefficients.png"), dpi=150)
    plt.close(fig)
    return res, converged, data


def run_rolling(d, window=40):
    data = d[["private_borrow_g"] + REGRESSORS].dropna()
    y = data["private_borrow_g"]
    X = sm.add_constant(data[REGRESSORS])
    res = RollingOLS(y, X, window=window).fit()
    params = res.params
    bse = res.bse
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, name in zip(axes.ravel(), X.columns):
        p = params[name]
        s = bse[name]
        ax.plot(p.index, p.values, linewidth=1.5)
        ax.fill_between(p.index, p - 1.96 * s, p + 1.96 * s, alpha=0.2)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.axvline(pd.Timestamp("2020-03-31"), color="gray", linestyle=":", linewidth=1.0)
        ax.set_title(f"Rolling {window}q OLS coefficient: {name}")
        ax.grid(True, alpha=0.3)
    fig.suptitle(f"Rolling {window}q OLS coefficients with 95% bands, private borrowing growth equation")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "task5_rolling_betas.png"), dpi=150)
    plt.close(fig)


def main():
    d = load()
    fig_shares(d)
    pt = period_table(d)
    res, converged, data = run_tvp(d)
    run_rolling(d)

    print("=== PERIOD AVERAGES (annualized growth, percent) ===")
    print(pt.to_string(index=False))
    print()
    print("=== TVP MODEL ===")
    print("sample:", data.index.min().date(), "to", data.index.max().date(), "| n =", len(data))
    print("converged:", converged)
    print(res.summary().tables[1])
    b = pd.read_csv(os.path.join(TAB, "task5_tvp_betas.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    snap = b.loc[[b.index[0], pd.Timestamp("2019-12-31"), b.index[-1]],
                 ["beta_const"] + [f"beta_{r}" for r in REGRESSORS]]
    print()
    print("=== TVP beta snapshots (start, 2019Q4, end) ===")
    print(snap.round(3).to_string())


if __name__ == "__main__":
    main()
