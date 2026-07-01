import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "catalog")
TAB = os.path.join(ROOT, "tables")
OUT = os.path.join(ROOT, "paper")
os.makedirs(OUT, exist_ok=True)

SRC = {
    "m2": "Federal Reserve (H.6)", "monetary_base": "Federal Reserve (H.3)",
    "cpi": "BLS", "pce_price": "BEA (NIPA)", "ppi_allcommodities": "BLS", "gdp_deflator": "BEA (NIPA)",
    "real_gdp": "BEA (NIPA)",
    "rate_federal_10y": "Federal Reserve (H.15)", "rate_fedfunds_policy": "Federal Reserve (H.15)",
    "rate_state_local_muni": "Bond Buyer", "rate_mortgage_30y": "Freddie Mac (PMMS)",
    "rate_business_baa": "Moody's", "rate_consumer_personal24m": "Federal Reserve (G.19)",
    "debt_federal": "U.S. Treasury", "debt_state_local": "Federal Reserve Financial Accounts (Z.1)",
    "debt_mortgage_household": "Federal Reserve Financial Accounts (Z.1)",
    "debt_business_corporate": "Federal Reserve Financial Accounts (Z.1)",
    "debt_consumer_credit": "Federal Reserve (G.19)",
    "fed_total_assets": "Federal Reserve (H.4.1)", "fed_treasuries": "Federal Reserve (H.4.1)",
    "fed_mbs": "Federal Reserve (H.4.1)", "bank_credit_total": "Federal Reserve (H.8)",
    "int_federal": "BEA (NIPA)", "int_state_local": "BEA (NIPA)", "int_business": "BEA (NIPA)",
    "int_personal": "BEA (NIPA)", "int_state_local_pension": "BEA (NIPA)",
    "pce_nominal": "BEA (NIPA)", "investment_nominal": "BEA (NIPA)",
    "government_nominal": "BEA (NIPA)", "netexports_nominal": "BEA (NIPA)",
}

GROUP_TITLE = {
    "money_supply": "Money and reserves", "inflation_index": "Price indices",
    "real_output": "Real output", "rate_federal": "Interest rate: federal",
    "rate_state_local": "Interest rate: state and local", "rate_mortgage": "Interest rate: mortgage",
    "rate_business": "Interest rate: business", "rate_consumer": "Interest rate: consumer",
    "debt_federal": "Debt: federal", "debt_state_local": "Debt: state and local",
    "debt_mortgage": "Debt: mortgage", "debt_business": "Debt: business", "debt_consumer": "Debt: consumer",
    "fed_balance_sheet": "Federal Reserve balance sheet", "bank_credit": "Bank credit",
    "nipa_interest": "NIPA interest payments", "gdp_components": "GDP components",
}
GROUP_ORDER = list(GROUP_TITLE)


def esc(s):
    return (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%")
            .replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
            .replace("<", "\\textless{}").replace(">", "\\textgreater{}"))


def read(fname):
    return pd.read_csv(os.path.join(TAB, fname), dtype=str, keep_default_na=False)


def variable_table():
    df = pd.read_csv(os.path.join(CAT, "variable_catalog.csv"), dtype=str, keep_default_na=False)
    df = df[df["status"] == "primary"]
    lines = [
        "\\begin{longtable}{@{}llp{5.4cm}llc@{}}",
        "\\caption{Variables, units, and sources. All series were retrieved from FRED (Federal Reserve Bank of St.\\ Louis); the column ``Source'' gives the originating agency. Coverage is the first and last year available.}\\label{tab:variables}\\\\",
        "\\toprule",
        "Variable & Series ID & Description & Units & Source & Coverage \\\\",
        "\\midrule",
        "\\endfirsthead",
        "\\multicolumn{6}{@{}l}{\\emph{Table \\ref{tab:variables} continued}}\\\\",
        "\\toprule",
        "Variable & Series ID & Description & Units & Source & Coverage \\\\",
        "\\midrule",
        "\\endhead",
        "\\midrule \\multicolumn{6}{r@{}}{\\emph{continued}}\\\\",
        "\\endfoot",
        "\\bottomrule",
        "\\endlastfoot",
    ]
    for g in GROUP_ORDER:
        sub = df[df["group"] == g]
        if sub.empty:
            continue
        lines.append(f"\\multicolumn{{6}}{{@{{}}l}}{{\\textbf{{{GROUP_TITLE[g]}}}}}\\\\")
        for _, r in sub.iterrows():
            cov = f"{r['obs_start'][:4]}--{r['obs_end'][:4]}"
            src = SRC.get(r["name"], "FRED")
            lines.append(" & ".join([esc(r["name"]), esc(r["fred_id"]), esc(r["title"]),
                                     esc(r["units"]), esc(src), cov]) + " \\\\")
        lines.append("\\addlinespace")
    lines.append("\\end{longtable}")
    return "\n".join(lines)


def tbl(fname, cols, headers, caption, label, colspec, filt=None):
    df = read(fname)
    if filt is not None:
        df = filt(df)
    df = df[cols]
    lines = ["\\begin{table}[htbp]", "\\centering", "\\small",
             f"\\caption{{{caption}}}", f"\\label{{{label}}}",
             f"\\begin{{tabular}}{{{colspec}}}", "\\toprule",
             " & ".join(headers) + " \\\\", "\\midrule"]
    for _, r in df.iterrows():
        lines.append(" & ".join(esc(str(r[c])) for c in cols) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(lines)


def main():
    parts = [variable_table(), ""]

    parts.append(tbl(
        "task1_var_summary.csv",
        ["measure", "sample", "n_obs", "lag_aic", "granger_money_to_infl_p", "granger_infl_to_money_p",
         "fevd_money_share_h12", "irf_peak_infl_resp"],
        ["Measure", "Sample", "$N$", "Lags", "$p$ money$\\to\\pi$", "$p$ $\\pi\\to$money",
         "FEVD money", "IRF peak"],
        "Money supply and inflation: trivariate VAR of real output growth, growth of M2 less the monetary base, and inflation. $p$-values are Granger-causality tests; the FEVD share is the fraction of inflation forecast-error variance at horizon 12 attributable to a money-growth shock.",
        "tab:task1", "llrrrrrr"))

    parts.append(tbl(
        "task1_unit_roots.csv",
        ["variable", "deterministic", "n", "adf_stat", "adf_p", "kpss_stat", "kpss_p"],
        ["Variable", "Det.", "$N$", "ADF", "ADF $p$", "KPSS", "KPSS $p$"],
        "Unit-root tests. ADF is the augmented Dickey--Fuller statistic (null: unit root); KPSS is the Kwiatkowski--Phillips--Schmidt--Shin statistic (null: stationarity). ``ct'' includes a constant and trend, ``c'' a constant only.",
        "tab:unitroots", "llrrrrr"))

    parts.append(tbl(
        "task23_johansen_rates_levels_diffs.csv",
        ["system", "form", "null_rank_at_most", "trace_stat", "cv_95", "reject_at_5pct"],
        ["Rates", "Form", "$r\\le$", "Trace", "95\\% c.v.", "Reject"],
        "Johansen trace tests for the interest-rate systems, unrestricted constant. The implied rates are not cointegrated in levels; the market rates are. Differenced series reject all ranks, confirming stationarity. Restricted-constant and trend cases give the same ranks.",
        "tab:johansen", "llrrrc",
        filt=lambda d: d[d["deterministic"].str.startswith("constant")]))

    parts.append(tbl(
        "task23_var_meta.csv",
        ["sample", "n_obs", "lag_aic", "min_root_modulus", "resid_whiteness_p",
         "joint_federal_to_others_p", "joint_others_to_federal_p"],
        ["Sample", "$N$", "Lags", "min$|$root$|$", "Whiteness $p$", "Fed$\\to$others $p$", "Others$\\to$fed $p$"],
        "Differenced implied-rate VAR (the implied rates are not cointegrated). Joint Granger tests of the federal-rate hierarchy; min$|$root$|$ is the smallest modulus of the characteristic roots.",
        "tab:ratehier_implied", "lrrrrrr"))

    parts.append(tbl(
        "task23_market_vecm_granger.csv",
        ["model", "federal_to_others_p", "others_to_federal_p", "federal_alpha_abs_max"],
        ["Model", "Fed$\\to$others $p$", "Others$\\to$fed $p$", "max$|\\alpha_{\\text{fed}}|$"],
        "Market-rate VECM (the market rates are cointegrated). The federal rate Granger-causes the others while the reverse is insignificant, giving a one-way hierarchy in the correctly specified model.",
        "tab:ratehier_market", "lrrr"))

    parts.append(tbl(
        "task4_granger.csv",
        ["sample", "caused", "causing", "granger_p"],
        ["Sample", "Caused", "Causing", "$p$"],
        "Federal Reserve transactions: Granger tests in the six-variable system (Fed securities growth, base growth, M2-less-base growth, change in the funds rate, change in the ten-year yield, CPI inflation), 2003Q1 onward.",
        "tab:task4granger", "lllr"))

    parts.append(tbl(
        "task4_vecm_specs_summary.csv",
        ["spec", "rank", "n_obs", "llf", "resid_whiteness_p", "resid_normality_p"],
        ["Deterministic", "Rank", "$N$", "Log-lik.", "Whiteness $p$", "Normality $p$"],
        "Federal Reserve transactions VECM under two deterministic specifications. Residuals are white at the five percent level; normality is rejected, as is common for macroeconomic data.",
        "tab:task4vecm", "lrrrrr"))

    parts.append(tbl(
        "task5_period_growth.csv",
        ["period", "gdp_real_g", "pce_real_g", "private_borrow_g", "money_g", "infl_cpi_yoy", "share_pce_nominal"],
        ["Period", "Real GDP", "Real PCE", "Priv.\\ borrow.", "M2$-$base", "CPI (yoy)", "PCE share"],
        "Period averages, annualized percent (PCE share is percent of nominal GDP). Private borrowing is the growth of household mortgages plus nonfinancial business plus consumer credit.",
        "tab:task5period", "lrrrrrr"))

    parts.append(tbl(
        "task5b_money_coefficients.csv",
        ["sector", "money", "spec", "coef_2010_2019_mean", "coef_2020plus_mean", "frac_2020plus_sig"],
        ["Sector", "Money", "Spec.", "Coef.\\ 2010--19", "Coef.\\ 2020+", "Frac.\\ sig.\\ 2020+"],
        "Per-sector demand for loanable funds: coefficient on lagged money growth in each debt type's borrowing equation, Kalman-smoothed time-varying estimates under market rates. Full grid (both rate definitions, both estimators) is in the replication files.",
        "tab:task5b", "lllrrr",
        filt=lambda d: d[(d["rate_type"] == "market") & (d["method"] == "tvp_kalman")]))

    parts.append(tbl(
        "task_robustness_ordering.csv",
        ["system", "ordering", "money_to_infl_fevd_h12", "fed_to_money_fevd_h12"],
        ["System", "Cholesky ordering", "Money$\\to\\pi$ FEVD", "Fed$\\to$money FEVD"],
        "Ordering robustness: forecast-error variance shares at horizon 12 across alternative Cholesky orderings. The shares stay in a narrow band, so the conclusions are not an artifact of one ordering.",
        "tab:ordering", "llrr"))

    parts.append(tbl(
        "task_robustness_inflation_form.csv",
        ["measure", "money_to_infl_p_level", "money_fevd_level", "money_to_dinfl_p", "money_fevd_dinfl"],
        ["Measure", "$p$ (level)", "FEVD (level)", "$p$ ($\\Delta$)", "FEVD ($\\Delta$)"],
        "Inflation-form sensitivity: money-to-inflation results with inflation in levels versus first differences. The conclusions are stable across the two treatments.",
        "tab:inflform", "lrrrr"))

    parts.append(tbl(
        "task7_structural_break.csv",
        ["series", "sup_wald", "break_quarter", "bootstrap_p", "n_obs"],
        ["Series", "sup-Wald", "Break", "Bootstrap $p$", "$N$"],
        "Quandt--Andrews sup-Wald test for a structural break in the money-inflation relation, with a residual-bootstrap $p$-value and fifteen percent trimming. The dominant break is the early-1980s regime change, not 2020.",
        "tab:break", "lrlrr"))

    parts.append(tbl(
        "task3_tvp_constancy.csv",
        ["model", "coefficient", "state_innovation_sd", "verdict"],
        ["Model", "Coefficient", "Innovation s.d.", "Verdict"],
        "Time-varying-coefficient constancy: the estimated random-walk innovation standard deviation of each coefficient. A value of zero means the coefficient is effectively constant.",
        "tab:constancy", "llll"))

    parts.append(tbl(
        "task_robustness_fragility.csv",
        ["test", "p_value", "verdict"],
        ["Test", "$p$-value", "Verdict"],
        "Fragility of the headline money-to-inflation result across the four inflation measures.",
        "tab:fragility", "lll"))

    with open(os.path.join(OUT, "tables_auto.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("wrote", os.path.join(OUT, "tables_auto.tex"), "with", len(parts) - 1, "tables")


if __name__ == "__main__":
    main()
