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
    "debt_federal": "U.S. Treasury", "debt_state_local": "Fed.\\ Financial Accounts (Z.1)",
    "debt_mortgage_household": "Fed.\\ Financial Accounts (Z.1)",
    "debt_business_corporate": "Fed.\\ Financial Accounts (Z.1)",
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

LABELS = {
    "full_1959_2026": "Full (1959--2026)", "pre_covid_1959_2019": "Pre-COVID (1959--2019)",
    "covid_post_2020_2026": "Post-2020 (2020--2026)", "full": "Full", "pre_covid": "Pre-COVID",
    "full_2003_2026": "Full (2003--2026)", "pre_covid_2003_2019": "Pre-COVID (2003--2019)",
    "pre_covid_2010_2019": "2010--2019", "covid_2020_2021": "2020--2021", "post_2022_2026": "2022--2026",
    "cpi": "CPI", "pce": "PCE", "ppi": "PPI", "gdpdef": "GDP deflator",
    "log_m2_less_base": "$\\log$(M2$-$base)", "money_g": "M2$-$base growth",
    "log_real_gdp": "$\\log$ real GDP", "gdp_g": "Real GDP growth",
    "log_cpi": "$\\log$ CPI", "infl_cpi": "CPI inflation",
    "log_pce_price": "$\\log$ PCE price index", "infl_pce": "PCE inflation",
    "log_ppi_allcommodities": "$\\log$ PPI", "infl_ppi": "PPI inflation",
    "log_gdp_deflator": "$\\log$ GDP deflator", "infl_gdpdef": "GDP-deflator inflation",
    "fed_g": "Fed securities growth", "base_g": "Base-money growth",
    "d_ffr": "$\\Delta$ funds rate", "d_gs10": "$\\Delta$ 10-yr yield",
    "ct": "$c,t$", "c": "$c$", "True": "Yes", "False": "No",
    "levels": "Levels", "differences": "Differences", "implied": "Implied", "market": "Market",
    "m2_less_base": "M2$-$base", "base": "Base money", "lean": "Baseline", "controlled": "With controls",
    "mortgage": "Mortgage", "consumer": "Consumer", "business": "Business",
    "market VECM (rank 3, k_ar_diff 1, unrestricted const)": "Market rates (rank 3)",
    "const": "Constant", "d_rate_mortgage_lag1": "$\\Delta$ mortgage rate $(t{-}1)$",
    "pce_real_g_lag1": "Real PCE growth $(t{-}1)$", "fed_debt_g_lag1": "Federal debt growth $(t{-}1)$",
    "d_rate_lag1": "$\\Delta$ own rate $(t{-}1)$", "money_lag1": "Money growth $(t{-}1)$",
    "task5 aggregate private borrowing": "Aggregate private borrowing",
    "task5b mortgage (market, lean)": "Mortgage (market rate)",
    "task5b consumer (market, lean)": "Consumer (market rate)",
    "task5b business (market, lean)": "Business (market rate)",
    "time varying": "Time-varying", "effectively constant": "Effectively constant",
    "task1 (gdp,money,cpi)": "Money--inflation VAR", "task4 (2003+)": "Fed-transactions VAR",
    "gdp_g > money_g > infl_cpi": "Output $\\succ$ money $\\succ$ prices",
    "gdp_g > infl_cpi > money_g": "Output $\\succ$ prices $\\succ$ money",
    "money_g > gdp_g > infl_cpi": "Money $\\succ$ output $\\succ$ prices",
    "money_g > infl_cpi > gdp_g": "Money $\\succ$ prices $\\succ$ output",
    "infl_cpi > gdp_g > money_g": "Prices $\\succ$ output $\\succ$ money",
    "infl_cpi > money_g > gdp_g": "Prices $\\succ$ money $\\succ$ output",
    "baseline (fed first)": "Baseline (Fed first)", "money block first": "Money block first",
    "prices first": "Prices first",
    "money growth -> cpi inflation (full sample)": "Money growth $\\to$ CPI inflation",
    "money growth -> pce inflation (full sample)": "Money growth $\\to$ PCE inflation",
    "money growth -> ppi inflation (full sample)": "Money growth $\\to$ PPI inflation",
    "money growth -> gdpdef inflation (full sample)": "Money growth $\\to$ GDP-deflator inflation",
    "fragile 0.05-0.10": "Fragile (0.05--0.10)", "not significant": "Not significant",
    "constant_only": "Constant", "constant_plus_trend": "Constant $+$ trend",
    "cpi inflation": "CPI inflation", "pce inflation": "PCE inflation",
}


def esc(s):
    return (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%")
            .replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
            .replace("<", "\\textless{}").replace(">", "\\textgreater{}"))


def fmtnum(v, kind):
    x = float(v)
    if kind == "p":
        return "$<$0.001" if x < 0.001 else f"{x:.3f}"
    if kind == "f3":
        return "0.000" if abs(x) < 0.0005 else f"{x:.3f}"
    if kind == "f2":
        return f"{x:.2f}"
    if kind == "f1":
        return f"{x:.1f}"
    return v


def cell(raw, col, fmt):
    if raw == "":
        return ""
    if col in fmt:
        return fmtnum(raw, fmt[col])
    if raw in LABELS:
        return LABELS[raw]
    return esc(raw)


def read(fname):
    return pd.read_csv(os.path.join(TAB, fname), dtype=str, keep_default_na=False)


def variable_table():
    df = pd.read_csv(os.path.join(CAT, "variable_catalog.csv"), dtype=str, keep_default_na=False)
    df = df[df["status"] == "primary"]
    lines = [
        "{\\footnotesize\\setlength{\\tabcolsep}{4pt}",
        "\\begin{longtable}{@{}l p{5.3cm} p{2.4cm} p{2.7cm} l@{}}",
        "\\caption{Variables, units, and sources. All series were retrieved from FRED (Federal Reserve Bank of St.\\ Louis); ``Source'' gives the originating agency. Coverage is the first and last year available.}\\label{tab:variables}\\\\",
        "\\toprule",
        "Series ID & Description & Units & Source & Coverage \\\\",
        "\\midrule",
        "\\endfirsthead",
        "\\multicolumn{5}{@{}l}{\\emph{Table \\ref{tab:variables}, continued}}\\\\",
        "\\toprule",
        "Series ID & Description & Units & Source & Coverage \\\\",
        "\\midrule",
        "\\endhead",
        "\\midrule \\multicolumn{5}{r@{}}{\\emph{continued on next page}}\\\\",
        "\\endfoot",
        "\\bottomrule",
        "\\endlastfoot",
    ]
    for g in GROUP_ORDER:
        sub = df[df["group"] == g]
        if sub.empty:
            continue
        lines.append(f"\\addlinespace\\multicolumn{{5}}{{@{{}}l}}{{\\textit{{{GROUP_TITLE[g]}}}}}\\\\[2pt]")
        for _, r in sub.iterrows():
            cov = f"{r['obs_start'][:4]}--{r['obs_end'][:4]}"
            src = SRC.get(r["name"], "FRED")
            lines.append(" & ".join([esc(r["fred_id"]), esc(r["title"]), esc(r["units"]), src, cov]) + " \\\\")
    lines.append("\\end{longtable}}")
    return "\n".join(lines)


def tbl(fname, cols, headers, caption, label, colspec, fmt=None, filt=None, size="\\small"):
    fmt = fmt or {}
    df = read(fname)
    if filt is not None:
        df = filt(df)
    df = df[cols]
    tight = "\\setlength{\\tabcolsep}{4pt}" if size == "\\footnotesize" else ""
    lines = ["\\begin{table}[htbp]", "\\centering", size, tight,
             f"\\caption{{{caption}}}", f"\\label{{{label}}}",
             f"\\begin{{tabular}}{{{colspec}}}", "\\toprule",
             " & ".join(headers) + " \\\\", "\\midrule"]
    for _, r in df.iterrows():
        lines.append(" & ".join(cell(str(r[c]), c, fmt) for c in cols) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(lines)


def main():
    parts = [variable_table(), ""]

    parts.append(tbl(
        "task1_var_summary.csv",
        ["measure", "sample", "n_obs", "lag_aic", "granger_money_to_infl_p", "granger_infl_to_money_p",
         "fevd_money_share_h12", "irf_peak_infl_resp"],
        ["Measure", "Sample", "$N$", "Lags", "$p$: $m\\!\\to\\!\\pi$", "$p$: $\\pi\\!\\to\\!m$",
         "FEVD $m$", "IRF peak"],
        "Money supply and inflation: trivariate VAR of real output growth, growth of M2 less the monetary base ($m$), and inflation ($\\pi$). The $p$-values are Granger-causality tests; the FEVD share is the fraction of inflation forecast-error variance at horizon~12 attributable to a money-growth shock.",
        "tab:task1", "llrrrrrr",
        fmt={"granger_money_to_infl_p": "p", "granger_infl_to_money_p": "p",
             "fevd_money_share_h12": "f3", "irf_peak_infl_resp": "f3"}, size="\\footnotesize"))

    parts.append(tbl(
        "task1_unit_roots.csv",
        ["variable", "deterministic", "n", "adf_stat", "adf_p", "kpss_stat", "kpss_p"],
        ["Variable", "Det.", "$N$", "ADF", "ADF $p$", "KPSS", "KPSS $p$"],
        "Unit-root tests. ADF is the augmented Dickey--Fuller statistic (null: unit root); KPSS is the Kwiatkowski--Phillips--Schmidt--Shin statistic (null: stationarity). ``$c,t$'' includes a constant and trend, ``$c$'' a constant only.",
        "tab:unitroots", "llrrrrr",
        fmt={"adf_stat": "f3", "adf_p": "p", "kpss_stat": "f3", "kpss_p": "p"}))

    parts.append(tbl(
        "task23_johansen_rates_levels_diffs.csv",
        ["system", "form", "null_rank_at_most", "trace_stat", "cv_95", "reject_at_5pct"],
        ["Rates", "Form", "$r\\le$", "Trace", "95\\% c.v.", "Reject"],
        "Johansen trace tests for the interest-rate systems, unrestricted constant. The implied rates are not cointegrated in levels; the market rates are. Differenced series reject all ranks, confirming stationarity. Restricted-constant and trend cases give the same ranks.",
        "tab:johansen", "llrrrc",
        fmt={"trace_stat": "f2", "cv_95": "f2"},
        filt=lambda d: d[d["deterministic"].str.startswith("constant")]))

    parts.append(tbl(
        "task23_var_meta.csv",
        ["sample", "n_obs", "lag_aic", "min_root_modulus", "resid_whiteness_p",
         "joint_federal_to_others_p", "joint_others_to_federal_p"],
        ["Sample", "$N$", "Lags", "min$|$root$|$", "Whiteness $p$", "Fed$\\to$others $p$", "Others$\\to$fed $p$"],
        "Differenced implied-rate VAR (the implied rates are not cointegrated). Joint Granger tests of the federal-rate hierarchy; min$|$root$|$ is the smallest modulus of the characteristic roots.",
        "tab:ratehier_implied", "lrrrrrr",
        fmt={"min_root_modulus": "f3", "resid_whiteness_p": "p",
             "joint_federal_to_others_p": "p", "joint_others_to_federal_p": "p"}))

    parts.append(tbl(
        "task23_market_vecm_granger.csv",
        ["model", "federal_to_others_p", "others_to_federal_p", "federal_alpha_abs_max"],
        ["System", "Fed$\\to$others $p$", "Others$\\to$fed $p$", "$\\max|\\alpha_{\\mathrm{fed}}|$"],
        "Market-rate VECM (the market rates are cointegrated). The federal rate Granger-causes the other rates while the reverse is insignificant, giving a one-way hierarchy in the correctly specified model.",
        "tab:ratehier_market", "lrrr",
        fmt={"federal_to_others_p": "p", "others_to_federal_p": "p", "federal_alpha_abs_max": "f3"}))

    parts.append(tbl(
        "task4_granger.csv",
        ["sample", "caused", "causing", "granger_p"],
        ["Sample", "Caused variable", "Causing variable", "$p$"],
        "Federal Reserve transactions: Granger tests in the six-variable system (Fed securities growth, base growth, M2-less-base growth, change in the funds rate, change in the ten-year yield, CPI inflation), 2003Q1 onward.",
        "tab:task4granger", "lllr",
        fmt={"granger_p": "p"}))

    parts.append(tbl(
        "task4_vecm_specs_summary.csv",
        ["spec", "rank", "n_obs", "llf", "resid_whiteness_p", "resid_normality_p"],
        ["Deterministic", "Rank", "$N$", "Log-lik.", "Whiteness $p$", "Normality $p$"],
        "Federal Reserve transactions VECM under two deterministic specifications. Residuals are white at the five percent level; normality is rejected, as is common for macroeconomic data.",
        "tab:task4vecm", "lrrrrr",
        fmt={"llf": "f1", "resid_whiteness_p": "p", "resid_normality_p": "p"}))

    parts.append(tbl(
        "task5_period_growth.csv",
        ["period", "gdp_real_g", "pce_real_g", "private_borrow_g", "money_g", "infl_cpi_yoy", "share_pce_nominal"],
        ["Period", "Real GDP", "Real PCE", "Priv.\\ borrow.", "M2$-$base", "CPI (yoy)", "PCE share"],
        "Period averages, annualized percent (the PCE share is percent of nominal GDP). Private borrowing is the growth of household mortgages plus nonfinancial business plus consumer credit.",
        "tab:task5period", "lrrrrrr",
        fmt={"gdp_real_g": "f2", "pce_real_g": "f2", "private_borrow_g": "f2", "money_g": "f2",
             "infl_cpi_yoy": "f2", "share_pce_nominal": "f2"}))

    parts.append(tbl(
        "task5b_money_coefficients.csv",
        ["sector", "money", "spec", "coef_2010_2019_mean", "coef_2020plus_mean", "frac_2020plus_sig"],
        ["Sector", "Money measure", "Specification", "Coef.\\ 2010--19", "Coef.\\ 2020$+$", "Frac.\\ sig.\\ 2020$+$"],
        "Per-sector demand for loanable funds: coefficient on lagged money growth in each debt type's borrowing equation, Kalman-smoothed time-varying estimates under market rates. The full grid (both rate definitions and both estimators) is in the replication files.",
        "tab:task5b", "lllrrr",
        fmt={"coef_2010_2019_mean": "f3", "coef_2020plus_mean": "f3", "frac_2020plus_sig": "f2"},
        filt=lambda d: d[(d["rate_type"] == "market") & (d["method"] == "tvp_kalman")]))

    parts.append(tbl(
        "task_robustness_ordering.csv",
        ["system", "ordering", "money_to_infl_fevd_h12", "fed_to_money_fevd_h12"],
        ["System", "Recursive ordering", "Money$\\to\\pi$ FEVD", "Fed$\\to$money FEVD"],
        "Ordering robustness: forecast-error variance shares at horizon~12 across alternative recursive (Cholesky) orderings. The shares stay in a narrow band, so the conclusions are not an artifact of one ordering.",
        "tab:ordering", "llrr",
        fmt={"money_to_infl_fevd_h12": "f3", "fed_to_money_fevd_h12": "f3"}))

    parts.append(tbl(
        "task_robustness_inflation_form.csv",
        ["measure", "money_to_infl_p_level", "money_fevd_level", "money_to_dinfl_p", "money_fevd_dinfl"],
        ["Measure", "$p$ (level)", "FEVD (level)", "$p$ ($\\Delta$)", "FEVD ($\\Delta$)"],
        "Inflation-form sensitivity: money-to-inflation results with inflation in levels versus first differences. The conclusions are stable across the two treatments.",
        "tab:inflform", "lrrrr",
        fmt={"money_to_infl_p_level": "p", "money_fevd_level": "f3",
             "money_to_dinfl_p": "p", "money_fevd_dinfl": "f3"}))

    parts.append(tbl(
        "task7_structural_break.csv",
        ["series", "sup_wald", "break_quarter", "bootstrap_p", "n_obs"],
        ["Series", "sup-Wald", "Break", "Bootstrap $p$", "$N$"],
        "Quandt--Andrews sup-Wald test for a structural break in the money-inflation relation, with a residual-bootstrap $p$-value and fifteen percent trimming. The dominant break is the early-1980s regime change, not 2020.",
        "tab:break", "lrlrr",
        fmt={"sup_wald": "f2", "bootstrap_p": "p"}))

    parts.append(tbl(
        "task3_tvp_constancy.csv",
        ["model", "coefficient", "state_innovation_sd", "verdict"],
        ["Equation", "Coefficient", "Innovation s.d.", "Verdict"],
        "Time-varying-coefficient constancy: the estimated random-walk innovation standard deviation of each coefficient. A value of zero means the coefficient is effectively constant.",
        "tab:constancy", "llll",
        fmt={"state_innovation_sd": "f3"}, size="\\footnotesize"))

    parts.append(tbl(
        "task_robustness_fragility.csv",
        ["test", "p_value", "verdict"],
        ["Test", "$p$-value", "Verdict"],
        "Fragility of the headline money-to-inflation result across the four inflation measures.",
        "tab:fragility", "lll",
        fmt={"p_value": "p"}))

    with open(os.path.join(OUT, "tables_auto.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("wrote", os.path.join(OUT, "tables_auto.tex"), "with", len(parts) - 1, "tables")


if __name__ == "__main__":
    main()
