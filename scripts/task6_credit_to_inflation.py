import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.api import VAR

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")
FIG = os.path.join(ROOT, "figures")

SECTORS = {
    "mortgage": "debt_mortgage_household",
    "consumer": "debt_consumer_credit",
    "federal": "debt_federal",
    "business": "debt_business_corporate",
}
MEASURES = {
    "cpi": "infl_cpi_qoq_ann",
    "pce": "infl_pce_price_qoq_ann",
    "ppi": "infl_ppi_allcommodities_qoq_ann",
    "gdpdef": "infl_gdp_deflator_qoq_ann",
}
SAMPLES = {
    "full_1959_2026": (None, None),
    "post_1981_break": ("1982-01-01", None),
    "pre_covid_1959_2019": (None, "2019-12-31"),
}
CREDIT = ["g_mortgage", "g_consumer", "g_federal"]
MAXLAG = 4


def g400(x):
    return 400.0 * (np.log(x) - np.log(x.shift(1)))


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    out = pd.DataFrame(index=df.index)
    for s, col in SECTORS.items():
        out[f"g_{s}"] = g400(df[col])
    out["base_g"] = g400(df["monetary_base"])
    out["money_g"] = g400(df["m2_less_base"])
    out["gdp_g"] = g400(df["real_gdp"])
    for m, col in MEASURES.items():
        out[f"infl_{m}"] = df[col]
    return out


def window(d, start, end):
    w = d.copy()
    if start:
        w = w.loc[w.index >= start]
    if end:
        w = w.loc[w.index <= end]
    return w


def predictive_ols(d, measure, sample, start, end, lags, controls):
    y = f"infl_{measure}"
    cols = [y] + CREDIT + controls
    w = window(d[cols].dropna(), start, end)
    X = pd.DataFrame(index=w.index)
    for c in CREDIT + controls:
        for L in range(1, lags + 1):
            X[f"{c}_L{L}"] = w[c].shift(L)
    for L in range(1, lags + 1):
        X[f"{y}_L{L}"] = w[y].shift(L)
    dat = pd.concat([w[y], X], axis=1).dropna()
    if len(dat) < 40:
        return None
    yv = dat[y]
    Xv = sm.add_constant(dat.drop(columns=[y]))
    res = sm.OLS(yv, Xv).fit(cov_type="HAC", cov_kwds={"maxlags": lags + 2})
    tag = "base+output" if len(controls) > 1 else ("base" if controls else "none")
    rows = []
    for c in CREDIT + controls:
        names = [f"{c}_L{L}" for L in range(1, lags + 1)]
        w_test = res.f_test(" = 0, ".join(names) + " = 0")
        rows.append(dict(
            measure=measure, sample=sample, lags=lags, controls=tag,
            regressor=c.replace("g_", "").replace("base_g", "BASE MONEY").replace("gdp_g", "output"),
            n_obs=int(res.nobs),
            sum_coef=round(float(sum(res.params[n] for n in names)), 4),
            joint_p=round(float(w_test.pvalue), 4),
        ))
    names_all = [f"{c}_L{L}" for c in CREDIT for L in range(1, lags + 1)]
    joint = res.f_test(" = 0, ".join(names_all) + " = 0")
    rows.append(dict(
        measure=measure, sample=sample, lags=lags, controls=tag,
        regressor="ALL THREE (joint)", n_obs=int(res.nobs),
        sum_coef=np.nan, joint_p=round(float(joint.pvalue), 4),
    ))
    return rows


def var_granger(d, measure, sample, start, end):
    cols = ["gdp_g", "base_g"] + CREDIT + [f"infl_{measure}"]
    w = window(d[cols].dropna(), start, end)
    if len(w) < 60:
        return None, None
    model = VAR(w)
    p = max(int(model.select_order(maxlags=MAXLAG).selected_orders["aic"]), 1)
    res = model.fit(p)
    y = f"infl_{measure}"
    rows = []
    for c in CREDIT:
        t = res.test_causality(y, [c], kind="f")
        rows.append(dict(measure=measure, sample=sample, n_obs=len(w), lags=p,
                         causing=c.replace("g_", ""), caused="inflation",
                         granger_p=round(float(t.pvalue), 4)))
    tj = res.test_causality(y, CREDIT, kind="f")
    rows.append(dict(measure=measure, sample=sample, n_obs=len(w), lags=p,
                     causing="ALL THREE (joint)", caused="inflation",
                     granger_p=round(float(tj.pvalue), 4)))
    irf = res.irf(12)
    names = list(res.names)
    psi = irf.orth_irfs[:12]
    i = names.index(y)
    fev = dict(measure=measure, sample=sample)
    den = float((psi[:, i, :] ** 2).sum())
    for c in CREDIT:
        j = names.index(c)
        fev[f"fevd_{c.replace('g_', '')}"] = round(float((psi[:, i, j] ** 2).sum()) / den, 4)
    return rows, fev


def main():
    d = load()

    ols_rows = []
    for measure in MEASURES:
        for sample, (start, end) in SAMPLES.items():
            for lags in (2, 4):
                for controls in ([], ["base_g"], ["base_g", "gdp_g"]):
                    r = predictive_ols(d, measure, sample, start, end, lags, controls)
                    if r:
                        ols_rows.extend(r)
    ols = pd.DataFrame(ols_rows)
    ols.to_csv(os.path.join(TAB, "task6_credit_inflation_ols.csv"), index=False)

    g_rows, fev_rows = [], []
    for measure in MEASURES:
        for sample, (start, end) in SAMPLES.items():
            r, f = var_granger(d, measure, sample, start, end)
            if r:
                g_rows.extend(r)
                fev_rows.append(f)
    granger = pd.DataFrame(g_rows)
    granger.to_csv(os.path.join(TAB, "task6_credit_inflation_granger.csv"), index=False)
    fevd = pd.DataFrame(fev_rows)
    fevd.to_csv(os.path.join(TAB, "task6_credit_inflation_fevd.csv"), index=False)

    head = ols[(ols["lags"] == 4) & (ols["controls"] == "base+output")]
    print("=== PREDICTIVE REGRESSION: inflation on lagged sectoral borrowing growth ===")
    print("(4 lags, controlling for base money growth, real output growth, and own lags; HAC standard errors)")
    print(head.to_string(index=False))
    print()
    print("=== VAR GRANGER: sectoral borrowing growth -> inflation ===")
    print("(system: output growth, base growth, mortgage, consumer, federal borrowing, inflation)")
    print(granger.to_string(index=False))
    print()
    print("=== FEVD: share of inflation forecast-error variance at h=12 from each credit series ===")
    print(fevd.to_string(index=False))

    sub = granger[(granger["causing"] != "ALL THREE (joint)")]
    piv = sub.pivot_table(index=["measure", "sample"], columns="causing", values="granger_p")
    fig, ax = plt.subplots(figsize=(7.5, 7))
    vals = piv.values.astype(float)
    im = ax.imshow(np.ma.masked_invalid(vals), cmap="RdYlGn", vmin=0, vmax=0.2, aspect="auto")
    labs = {"cpi": "CPI", "pce": "PCE", "ppi": "PPI", "gdpdef": "GDP deflator"}
    samp = {"full": "full sample", "post": "post-1981", "pre": "pre-COVID"}
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels([c.capitalize() for c in piv.columns])
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels([f"{labs[m]}, {samp[s.split('_')[0]]}" for m, s in piv.index])
    ax.set_xlabel("Borrowing growth, lagged")
    for r in range(vals.shape[0]):
        for c in range(vals.shape[1]):
            if not np.isnan(vals[r, c]):
                ax.text(c, r, f"{vals[r, c]:.3f}", ha="center", va="center", fontsize=8,
                        fontweight="bold" if vals[r, c] < 0.05 else "normal")
    fig.colorbar(im, ax=ax, label="Granger p-value (red = significant)")
    ax.set_title("Does sectoral borrowing growth forecast inflation?")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "task6_credit_inflation_heatmap.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
