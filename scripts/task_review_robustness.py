import itertools
import os
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")

INFL = {
    "cpi": "infl_cpi_qoq_ann",
    "pce": "infl_pce_price_qoq_ann",
    "ppi": "infl_ppi_allcommodities_qoq_ann",
    "gdpdef": "infl_gdp_deflator_qoq_ann",
}


def g400(x):
    return 400.0 * (np.log(x) - np.log(x.shift(1)))


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    out = pd.DataFrame(index=df.index)
    out["gdp_g"] = g400(df["real_gdp"])
    out["money_g"] = g400(df["m2_less_base"])
    out["base_g"] = g400(df["monetary_base"])
    out["fed_g"] = g400(df["fed_securities_total"])
    out["d_ffr"] = df["rate_fedfunds_policy"].diff()
    out["d_gs10"] = df["rate_federal_10y"].diff()
    for k, col in INFL.items():
        out[f"infl_{k}"] = df[col]
    return out


def fit_var(d):
    return VAR(d.dropna()).fit(maxlags=8, ic="aic")


def fevd_share(res, response, impulse, h=12):
    psi = res.irf(h).orth_irfs[:h]
    names = list(res.names)
    i = names.index(response)
    j = names.index(impulse)
    return float((psi[:, i, j] ** 2).sum() / (psi[:, i, :] ** 2).sum())


def ordering_robustness(df):
    rows = []
    cols = ["gdp_g", "money_g", "infl_cpi"]
    for order in itertools.permutations(cols):
        res = fit_var(df[list(order)])
        rows.append(dict(system="task1 (gdp,money,cpi)", ordering=" > ".join(order),
                         money_to_infl_fevd_h12=round(fevd_share(res, "infl_cpi", "money_g"), 3)))
    fed_cols = ["fed_g", "base_g", "money_g", "d_ffr", "d_gs10", "infl_cpi"]
    alts = {
        "baseline (fed first)": fed_cols,
        "money block first": ["money_g", "base_g", "fed_g", "d_ffr", "d_gs10", "infl_cpi"],
        "prices first": ["infl_cpi", "d_gs10", "d_ffr", "money_g", "base_g", "fed_g"],
    }
    sub = df[fed_cols].dropna()
    sub = sub.loc[sub.index >= "2003-01-01"]
    for label, order in alts.items():
        res = fit_var(sub[order])
        rows.append(dict(system="task4 (2003+)", ordering=label,
                         money_to_infl_fevd_h12=round(fevd_share(res, "infl_cpi", "money_g"), 3),
                         fed_to_money_fevd_h12=round(fevd_share(res, "money_g", "fed_g"), 3)))
    return pd.DataFrame(rows)


def inflation_form(df):
    rows = []
    for k in INFL:
        lvl = df[["gdp_g", "money_g", f"infl_{k}"]].dropna()
        r1 = fit_var(lvl)
        p1 = float(r1.test_causality(f"infl_{k}", ["money_g"], kind="f").pvalue)
        f1 = fevd_share(r1, f"infl_{k}", "money_g")
        dd = df[["gdp_g", "money_g"]].copy()
        dd[f"dinfl_{k}"] = df[f"infl_{k}"].diff()
        dd = dd.dropna()
        r2 = fit_var(dd)
        p2 = float(r2.test_causality(f"dinfl_{k}", ["money_g"], kind="f").pvalue)
        f2 = fevd_share(r2, f"dinfl_{k}", "money_g")
        rows.append(dict(measure=k,
                         money_to_infl_p_level=round(p1, 4), money_fevd_level=round(f1, 3),
                         money_to_dinfl_p=round(p2, 4), money_fevd_dinfl=round(f2, 3)))
    return pd.DataFrame(rows)


def fragility(df):
    rows = []
    for k in INFL:
        d = df[["gdp_g", "money_g", f"infl_{k}"]].dropna()
        res = fit_var(d)
        p = float(res.test_causality(f"infl_{k}", ["money_g"], kind="f").pvalue)
        flag = "significant<0.05" if p < 0.05 else ("fragile 0.05-0.10" if p < 0.10 else "not significant")
        rows.append(dict(test=f"money growth -> {k} inflation (full sample)", p_value=round(p, 4), verdict=flag))
    return pd.DataFrame(rows)


def main():
    df = load()
    ob = ordering_robustness(df)
    ob.to_csv(os.path.join(TAB, "task_robustness_ordering.csv"), index=False)
    inf = inflation_form(df)
    inf.to_csv(os.path.join(TAB, "task_robustness_inflation_form.csv"), index=False)
    fr = fragility(df)
    fr.to_csv(os.path.join(TAB, "task_robustness_fragility.csv"), index=False)

    print("=== 6. ORDERING ROBUSTNESS (FEVD shares across Cholesky orderings) ===")
    print(ob.to_string(index=False))
    print("\n=== 8. INFLATION FORM SENSITIVITY (inflation level vs change) ===")
    print(inf.to_string(index=False))
    print("\n=== 9. FRAGILITY of the headline money->inflation result ===")
    print(fr.to_string(index=False))


if __name__ == "__main__":
    main()
