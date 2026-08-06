import os
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")

SECTORS = {
    "mortgage": "debt_mortgage_household",
    "consumer": "debt_consumer_credit",
    "federal": "debt_federal",
}
CREDIT = [f"g_{s}" for s in SECTORS]
MEASURES = {"cpi": "infl_cpi_qoq_ann", "pce": "infl_pce_price_qoq_ann"}
LAGS = 4

POLICY_SETS = {
    "none": [],
    "base money": ["base_g"],
    "funds rate": ["d_ffr"],
    "funds rate + 10y": ["d_ffr", "d_gs10"],
    "base + funds rate": ["base_g", "d_ffr"],
}
SAMPLES = {
    "full 1959-2026": (None, None),
    "post-1981": ("1982-01-01", None),
    "post-1981 pre-2008": ("1982-01-01", "2007-12-31"),
    "pre-2008": (None, "2007-12-31"),
}


def g400(x):
    return 400.0 * (np.log(x) - np.log(x.shift(1)))


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    out = pd.DataFrame(index=df.index)
    for s, col in SECTORS.items():
        out[f"g_{s}"] = g400(df[col])
    out["base_g"] = g400(df["monetary_base"])
    out["gdp_g"] = g400(df["real_gdp"])
    out["d_ffr"] = df["rate_fedfunds_policy"].diff()
    out["d_gs10"] = df["rate_federal_10y"].diff()
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


def build_lags(w, cols, lags):
    X = pd.DataFrame(index=w.index)
    for c in cols:
        for L in range(1, lags + 1):
            X[f"{c}_L{L}"] = w[c].shift(L)
    return X


def fit_hac(y, X, lags):
    dat = pd.concat([y, X], axis=1).dropna()
    if len(dat) < 40:
        return None, None
    yv = dat[y.name]
    Xv = sm.add_constant(dat.drop(columns=[y.name]))
    return sm.OLS(yv, Xv).fit(cov_type="HAC", cov_kwds={"maxlags": lags + 2}), dat


def block_test(res, prefix, lags):
    names = [f"{prefix}_L{L}" for L in range(1, lags + 1)]
    names = [n for n in names if n in res.params.index]
    if not names:
        return np.nan, np.nan
    t = res.f_test(" = 0, ".join(names) + " = 0")
    return round(float(sum(res.params[n] for n in names)), 4), round(float(t.pvalue), 4)


def part_a(d):
    rows = []
    for measure in MEASURES:
        y = f"infl_{measure}"
        for sample, (start, end) in SAMPLES.items():
            for pname, pol in POLICY_SETS.items():
                cols = CREDIT + pol + ["gdp_g"]
                w = window(d[[y] + cols].dropna(), start, end)
                X = build_lags(w, cols + [y], LAGS)
                res, dat = fit_hac(w[y], X, LAGS)
                if res is None:
                    continue
                for c in CREDIT + pol:
                    coef, p = block_test(res, c, LAGS)
                    rows.append(dict(measure=measure, sample=sample, policy_control=pname,
                                     regressor=c.replace("g_", "").replace("d_ffr", "FUNDS RATE").replace("base_g", "BASE MONEY").replace("d_gs10", "10Y YIELD"),
                                     n_obs=int(res.nobs), sum_coef=coef, joint_p=p))
    return pd.DataFrame(rows)


def part_b(d):
    rows = []
    for sample, (start, end) in SAMPLES.items():
        for measure in MEASURES:
            cols = CREDIT + ["gdp_g", f"infl_{measure}"]
            w = window(d[["d_ffr"] + cols].dropna(), start, end)
            X = build_lags(w, cols + ["d_ffr"], LAGS)
            res, dat = fit_hac(w["d_ffr"], X, LAGS)
            if res is None:
                continue
            for c in CREDIT:
                coef, p = block_test(res, c, LAGS)
                rows.append(dict(sample=sample, taylor_inflation=measure, n_obs=int(res.nobs),
                                 credit=c.replace("g_", ""), sum_coef=coef, joint_p=p))
            names = [f"{c}_L{L}" for c in CREDIT for L in range(1, LAGS + 1)]
            t = res.f_test(" = 0, ".join(names) + " = 0")
            rows.append(dict(sample=sample, taylor_inflation=measure, n_obs=int(res.nobs),
                             credit="ALL THREE (joint)", sum_coef=np.nan, joint_p=round(float(t.pvalue), 4)))
    return pd.DataFrame(rows)


def part_c(d):
    rows = []
    for measure in MEASURES:
        y = f"infl_{measure}"
        cols = CREDIT + ["base_g", "gdp_g"]
        w = d[[y] + cols].dropna().copy()
        post = (w.index >= "1982-01-01").astype(float)
        X = build_lags(w, cols + [y], LAGS)
        for c in CREDIT:
            for L in range(1, LAGS + 1):
                X[f"POST_{c}_L{L}"] = X[f"{c}_L{L}"] * post
        X["POST"] = post
        res, dat = fit_hac(w[y], X, LAGS)
        if res is None:
            continue
        for c in CREDIT:
            names = [f"POST_{c}_L{L}" for L in range(1, LAGS + 1)]
            t = res.f_test(" = 0, ".join(names) + " = 0")
            pre = sum(res.params[f"{c}_L{L}"] for L in range(1, LAGS + 1))
            shift = sum(res.params[n] for n in names)
            rows.append(dict(measure=measure, credit=c.replace("g_", ""), n_obs=int(res.nobs),
                             coef_pre_1982=round(float(pre), 4),
                             change_after_1982=round(float(shift), 4),
                             coef_post_1982=round(float(pre + shift), 4),
                             p_change_is_zero=round(float(t.pvalue), 4)))
    return pd.DataFrame(rows)


def main():
    d = load()

    a = part_a(d)
    a.to_csv(os.path.join(TAB, "task7_policy_controls.csv"), index=False)
    b = part_b(d)
    b.to_csv(os.path.join(TAB, "task7_fed_responds_to_credit.csv"), index=False)
    c = part_c(d)
    c.to_csv(os.path.join(TAB, "task7_break_interaction.csv"), index=False)

    print("=== A. CONSUMER CREDIT COEFFICIENT UNDER ALTERNATIVE POLICY CONTROLS ===")
    print("(inflation on 4 lags of credit growth, policy control, output growth, own lags)")
    sub = a[(a.regressor == "consumer")]
    print(sub.pivot_table(index=["measure", "sample"], columns="policy_control",
                          values="sum_coef").round(4).to_string())
    print()
    print("p-values:")
    print(sub.pivot_table(index=["measure", "sample"], columns="policy_control",
                          values="joint_p").round(4).to_string())
    print()
    print("=== A2. THE POLICY CONTROLS' OWN COEFFICIENTS ===")
    pol = a[a.regressor.isin(["BASE MONEY", "FUNDS RATE", "10Y YIELD"])]
    print(pol.pivot_table(index=["measure", "sample"], columns=["policy_control", "regressor"],
                          values="sum_coef").round(4).to_string())
    print()
    print("=== B. DOES CREDIT GROWTH FORECAST FED TIGHTENING? ===")
    print("(change in funds rate on 4 lags of credit growth, inflation, output growth, own lags)")
    print("(a positive, significant credit coefficient means the Fed raises rates after credit expands)")
    print(b.to_string(index=False))
    print()
    print("=== C. IS THE 1981 SIGN CHANGE STATISTICALLY REAL? ===")
    print("(single regression with post-1982 interactions; p tests whether the change is zero)")
    print(c.to_string(index=False))


if __name__ == "__main__":
    main()
