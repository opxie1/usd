import os
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from statsmodels.tsa.vector_ar.vecm import coint_johansen

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")

RATES = ["rate_federal_implied", "rate_state_local_implied_expension", "rate_mortgage_30y",
         "rate_business_implied", "rate_consumer_implied"]
DET = {0: "constant (statsmodels det_order=0)", 1: "linear trend (statsmodels det_order=1)"}


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    df["money_g"] = 400.0 * (np.log(df["m2_less_base"]) - np.log(df["m2_less_base"].shift(1)))
    return df


def johansen_rows(data, form, k):
    rows = []
    for det, label in DET.items():
        jo = coint_johansen(data.values, det, k)
        for r in range(len(jo.lr1)):
            rows.append(dict(form=form, deterministic=label, k_ar_diff=k, null_rank_at_most=r,
                             trace_stat=round(float(jo.lr1[r]), 2),
                             cv_90=round(float(jo.cvt[r, 0]), 2),
                             cv_95=round(float(jo.cvt[r, 1]), 2),
                             cv_99=round(float(jo.cvt[r, 2]), 2),
                             reject_at_5pct=bool(jo.lr1[r] > jo.cvt[r, 1])))
    return rows


def whiteness(res, nlags):
    try:
        t = res.test_whiteness(nlags=nlags, adjusted=True)
        return round(float(t.pvalue), 4), round(float(t.test_statistic), 2)
    except Exception as e:
        return float("nan"), str(e)[:40]


def main():
    df = load()
    levels = df[RATES].dropna()
    p_lev = max(int(VAR(levels).select_order(8).aic), 2)
    k = max(p_lev - 1, 1)

    jo_rows = []
    jo_rows += johansen_rows(levels, "levels", k)
    diffs = levels.diff().dropna()
    jo_rows += johansen_rows(diffs, "differences", k)
    jo = pd.DataFrame(jo_rows)
    jo.to_csv(os.path.join(TAB, "task23_johansen_rates_levels_diffs.csv"), index=False)

    sys_levels = df[["money_g"] + RATES].dropna()
    res_lev = VAR(sys_levels).fit(maxlags=8, ic="aic")
    p_sys = res_lev.k_ar

    dsys = pd.DataFrame(index=df.index)
    dsys["money_g"] = df["money_g"]
    for c in RATES:
        dsys[f"d_{c}"] = df[c].diff()
    dsys = dsys.dropna()
    res_diff = VAR(dsys).fit(maxlags=8, ic="aic")
    p_diff = res_diff.k_ar

    dfed = "d_rate_federal_implied"
    others = [f"d_{c}" for c in RATES if c != "rate_federal_implied"]
    g_fed_to_others = res_diff.test_causality(others, [dfed], kind="f")
    g_others_to_fed = res_diff.test_causality(dfed, others, kind="f")
    g_money_to_business = res_diff.test_causality("d_rate_business_implied", ["money_g"], kind="f")

    lb_lev_p, lb_lev_s = whiteness(res_lev, p_sys + 6)
    lb_diff_p, lb_diff_s = whiteness(res_diff, p_diff + 6)

    diag = pd.DataFrame([
        dict(system="levels (rates + money)", lag_aic=p_sys, stable=bool(res_lev.is_stable()),
             whiteness_p=lb_lev_p, whiteness_stat=lb_lev_s),
        dict(system="differences (d rates + money)", lag_aic=p_diff, stable=bool(res_diff.is_stable()),
             whiteness_p=lb_diff_p, whiteness_stat=lb_diff_s),
    ])
    diag.to_csv(os.path.join(TAB, "task23_diff_var_diagnostics.csv"), index=False)

    granger = pd.DataFrame([
        dict(test="federal jointly Granger-causes other rates (differences)", p_value=round(float(g_fed_to_others.pvalue), 4)),
        dict(test="other rates jointly Granger-cause federal (differences)", p_value=round(float(g_others_to_fed.pvalue), 4)),
        dict(test="money growth Granger-causes business rate (differences)", p_value=round(float(g_money_to_business.pvalue), 4)),
    ])
    granger.to_csv(os.path.join(TAB, "task23_diff_granger.csv"), index=False)

    print("=== JOHANSEN trace test, 5 implied rates, levels and differences, k_ar_diff =", k, "===")
    print("note: statsmodels coint_johansen supports no-constant/constant/trend only;")
    print("restricted vs unrestricted constant/trend (Johansen 5-case) is not in its trace test.")
    print(jo.to_string(index=False))
    print()
    print("=== RATE SYSTEM: levels vs differences, AIC lag, stability, residual whiteness ===")
    print(diag.to_string(index=False))
    print()
    print("=== GRANGER in the differenced system ===")
    print(granger.to_string(index=False))


if __name__ == "__main__":
    main()
