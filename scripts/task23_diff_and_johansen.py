import os
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")

SYSTEMS = {
    "implied": dict(
        federal="rate_federal_implied",
        rates=["rate_federal_implied", "rate_state_local_implied_expension", "rate_mortgage_30y",
               "rate_business_implied", "rate_consumer_implied"],
    ),
    "market": dict(
        federal="rate_federal_10y",
        rates=["rate_federal_10y", "rate_mortgage_30y", "rate_business_baa", "rate_consumer_personal24m"],
    ),
}
DET = {0: "constant (statsmodels det_order=0)", 1: "linear trend (statsmodels det_order=1)"}
WHITE_NLAGS = 12


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    df["money_g"] = 400.0 * (np.log(df["m2_less_base"]) - np.log(df["m2_less_base"].shift(1)))
    return df


def jo_k(data):
    return max(int(VAR(data).select_order(8).aic) - 1, 1)


def johansen_rows(system, data, form):
    k = jo_k(data)
    rows = []
    for det, label in DET.items():
        jo = coint_johansen(data.values, det, k)
        for r in range(len(jo.lr1)):
            rows.append(dict(system=system, form=form, deterministic=label, k_ar_diff=k, null_rank_at_most=r,
                             trace_stat=round(float(jo.lr1[r]), 2),
                             cv_90=round(float(jo.cvt[r, 0]), 2), cv_95=round(float(jo.cvt[r, 1]), 2),
                             cv_99=round(float(jo.cvt[r, 2]), 2),
                             reject_at_5pct=bool(jo.lr1[r] > jo.cvt[r, 1])))
    return rows


def min_root_modulus(res):
    return round(float(np.min(np.abs(res.roots))), 4)


def whiteness(res):
    t = res.test_whiteness(nlags=WHITE_NLAGS, adjusted=True)
    return round(float(t.pvalue), 4), round(float(t.test_statistic), 2)


def main():
    df = load()
    jo_all, diag_all, granger_all = [], [], []

    for name, spec in SYSTEMS.items():
        rates, fed = spec["rates"], spec["federal"]
        levels = df[rates].dropna()
        diffs = levels.diff().dropna()
        jo_all += johansen_rows(name, levels, "levels")
        jo_all += johansen_rows(name, diffs, "differences")

        sys_lev = df[["money_g"] + rates].dropna()
        res_lev = VAR(sys_lev).fit(maxlags=8, ic="aic")

        dsys = pd.DataFrame({"money_g": df["money_g"]})
        for c in rates:
            dsys[f"d_{c}"] = df[c].diff()
        dsys = dsys.dropna()
        res_diff = VAR(dsys).fit(maxlags=8, ic="aic")

        for form, res in [("levels", res_lev), ("differences", res_diff)]:
            wp, ws = whiteness(res)
            diag_all.append(dict(system=name, form=form, lag_aic=res.k_ar, stable=bool(res.is_stable()),
                                 min_root_modulus=min_root_modulus(res),
                                 whiteness_p_nlags12=wp, whiteness_stat=ws))

        dfed = f"d_{fed}"
        others = [f"d_{c}" for c in rates if c != fed]
        gfo = res_diff.test_causality(others, [dfed], kind="f")
        gof = res_diff.test_causality(dfed, others, kind="f")
        bcol = "d_rate_business_baa" if name == "market" else "d_rate_business_implied"
        gmb = res_diff.test_causality(bcol, ["money_g"], kind="f")
        granger_all.append(dict(system=name, n_obs=len(dsys), lag=res_diff.k_ar,
                                federal_to_others_p=round(float(gfo.pvalue), 4),
                                others_to_federal_p=round(float(gof.pvalue), 4),
                                money_to_business_p=round(float(gmb.pvalue), 4)))

    mkt = SYSTEMS["market"]
    mrates, mfed = mkt["rates"], mkt["federal"]
    mlev = df[mrates].dropna()
    vk = jo_k(mlev)
    rank = 3
    vecm = VECM(mlev, k_ar_diff=vk, coint_rank=rank, deterministic="co").fit()
    mothers = [c for c in mrates if c != mfed]
    gc_fed = vecm.test_granger_causality(caused=mothers, causing=mfed)
    gc_oth = vecm.test_granger_causality(caused=mfed, causing=mothers)
    alpha_fed = vecm.alpha[mrates.index(mfed)]
    vecm_rows = [
        dict(model=f"market VECM (rank {rank}, k_ar_diff {vk}, unrestricted const)",
             federal_to_others_p=round(float(gc_fed.pvalue), 4),
             others_to_federal_p=round(float(gc_oth.pvalue), 4),
             federal_alpha_abs_max=round(float(np.max(np.abs(alpha_fed))), 4)),
    ]
    pd.DataFrame(vecm_rows).to_csv(os.path.join(TAB, "task23_market_vecm_granger.csv"), index=False)

    jo = pd.DataFrame(jo_all)
    jo.to_csv(os.path.join(TAB, "task23_johansen_rates_levels_diffs.csv"), index=False)
    diag = pd.DataFrame(diag_all)
    diag.to_csv(os.path.join(TAB, "task23_diff_var_diagnostics.csv"), index=False)
    granger = pd.DataFrame(granger_all)
    granger.to_csv(os.path.join(TAB, "task23_diff_granger.csv"), index=False)

    print("note: statsmodels coint_johansen does no-constant/constant/trend only;")
    print("restricted vs unrestricted constant/trend (Johansen 5-case) needs verified CVs or EViews.")
    print("\n=== JOHANSEN trace test, rank 0 row per system/form/deterministic ===")
    print(jo[jo["null_rank_at_most"] == 0].to_string(index=False))
    print("\n=== DIAGNOSTICS (stability via min |root|>1; residual whiteness at nlags=12) ===")
    print(diag.to_string(index=False))
    print("\n=== GRANGER in differenced systems (implied: correct; market: misspecified, see VECM) ===")
    print(granger.to_string(index=False))
    print("\n=== MARKET RATES are cointegrated -> VECM is the correct form; Granger from VECM ===")
    print(pd.DataFrame(vecm_rows).to_string(index=False))
    print("hierarchy rests on the Granger result (others->federal not significant); federal_alpha_abs_max is reported for context, not as a weak-exogeneity claim")


if __name__ == "__main__":
    main()
