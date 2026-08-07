import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = os.path.join(ROOT, "tables")
OUT = os.path.join(ROOT, "paper", "tables_credit_inflation.tex")

MEAS = {"cpi": "CPI", "pce": "PCE", "ppi": "PPI", "gdpdef": "GDP deflator"}
SAMP = {
    "full_1959_2026": "Full (1959--2026)",
    "post_1981_break": "Post-1981",
    "pre_covid_1959_2019": "Pre-COVID",
    "full 1959-2026": "Full (1959--2026)",
    "post-1981": "Post-1981",
    "post-1981 pre-2008": "Post-1981, pre-2008",
    "pre-2008": "Pre-2008",
}
SEC = {"mortgage": "Mortgage", "consumer": "Consumer", "federal": "Federal"}


def stars(p):
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "$^{***}$"
    if p < 0.05:
        return "$^{**}$"
    if p < 0.10:
        return "$^{*}$"
    return ""


def cell(coef, p):
    if pd.isna(coef):
        return "---"
    return f"{coef:.3f}{stars(p)}"


def table_main():
    d = pd.read_csv(os.path.join(TAB, "task6_credit_inflation_ols.csv"))
    d = d[(d["lags"] == 4) & (d["controls"] == "base+output")]
    rows = []
    for m in MEAS:
        for s in ["full_1959_2026", "post_1981_break", "pre_covid_1959_2019"]:
            g = d[(d["measure"] == m) & (d["sample"] == s)]
            if g.empty:
                continue
            get = lambda r: g[g["regressor"] == r].iloc[0] if not g[g["regressor"] == r].empty else None
            n = int(g.iloc[0]["n_obs"])
            cells = []
            for r in ["mortgage", "consumer", "federal", "BASE MONEY"]:
                x = get(r)
                cells.append(cell(x["sum_coef"], x["joint_p"]) if x is not None else "---")
            j = get("ALL THREE (joint)")
            jp = f"{j['joint_p']:.3f}" if j is not None else "---"
            rows.append(f"{MEAS[m]} & {SAMP[s]} & {n} & " + " & ".join(cells) + f" & {jp} \\\\")
    body = "\n".join(rows)
    return f"""\\begin{{table}}[htbp]
\\centering
\\setlength{{\\belowcaptionskip}}{{8pt}}
\\footnotesize
\\setlength{{\\tabcolsep}}{{4pt}}
\\caption{{Sectoral borrowing and inflation. Each entry is the sum of four lagged coefficients from a regression of inflation on lagged borrowing growth in the three sectors, base money growth, real output growth, and four lags of inflation itself, estimated with Newey--West standard errors. The final column is the $p$-value for the joint exclusion of all three borrowing sectors. Significance from the joint test on each block: $^{{*}}$ ten percent, $^{{**}}$ five percent, $^{{***}}$ one percent.}}
\\label{{tab:creditinfl}}
\\begin{{tabular}}{{llrrrrrr}}
\\toprule
Measure & Sample & $N$ & Mortgage & Consumer & Federal & Base money & Joint $p$ \\\\
\\midrule
{body}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""


def table_policy():
    a = pd.read_csv(os.path.join(TAB, "task7_policy_controls.csv"))
    a = a[a["regressor"] == "consumer"]
    order = ["none", "base money", "funds rate", "funds rate + 10y", "base + funds rate"]
    head = ["None", "Base money", "Funds rate", "Funds $+$ 10y", "Base $+$ funds"]
    rows = []
    for m in ["cpi", "pce"]:
        for s in ["full 1959-2026", "post-1981", "post-1981 pre-2008", "pre-2008"]:
            g = a[(a["measure"] == m) & (a["sample"] == s)]
            if g.empty:
                continue
            cells = []
            for c in order:
                x = g[g["policy_control"] == c]
                cells.append(cell(x.iloc[0]["sum_coef"], x.iloc[0]["joint_p"]) if not x.empty else "---")
            rows.append(f"{MEAS[m]} & {SAMP[s]} & " + " & ".join(cells) + " \\\\")
    bodyA = "\n".join(rows)

    b = pd.read_csv(os.path.join(TAB, "task7_fed_responds_to_credit.csv"))
    rows = []
    for s in ["full 1959-2026", "post-1981", "post-1981 pre-2008", "pre-2008"]:
        for m in ["cpi", "pce"]:
            g = b[(b["sample"] == s) & (b["taylor_inflation"] == m)]
            if g.empty:
                continue
            n = int(g.iloc[0]["n_obs"])
            cells = []
            for r in ["mortgage", "consumer", "federal"]:
                x = g[g["credit"] == r]
                cells.append(cell(x.iloc[0]["sum_coef"], x.iloc[0]["joint_p"]) if not x.empty else "---")
            j = g[g["credit"] == "ALL THREE (joint)"]
            jp = f"{j.iloc[0]['joint_p']:.3f}" if not j.empty else "---"
            rows.append(f"{SAMP[s]} & {MEAS[m]} & {n} & " + " & ".join(cells) + f" & {jp} \\\\")
    bodyB = "\n".join(rows)

    return f"""\\begin{{table}}[htbp]
\\centering
\\setlength{{\\belowcaptionskip}}{{8pt}}
\\footnotesize
\\setlength{{\\tabcolsep}}{{4pt}}
\\caption{{Monetary policy and the consumer borrowing result. Panel A re-estimates the consumer borrowing coefficient from Table~\\ref{{tab:creditinfl}} under five different measures of the policy stance, holding real output growth fixed throughout. Panel B reverses the question and regresses the change in the federal funds rate on lagged borrowing growth, inflation, real output growth, and its own lags, so a positive coefficient means the Federal Reserve raises rates after borrowing expands. Significance: $^{{*}}$ ten percent, $^{{**}}$ five percent, $^{{***}}$ one percent.}}
\\label{{tab:policyresp}}
\\textit{{Panel A. Consumer borrowing coefficient under alternative policy controls}}\\par\\vspace{{2pt}}
\\begin{{tabular}}{{ll{'r' * len(order)}}}
\\toprule
Measure & Sample & {' & '.join(head)} \\\\
\\midrule
{bodyA}
\\bottomrule
\\end{{tabular}}
\\par\\vspace{{10pt}}
\\textit{{Panel B. Does the Federal Reserve raise rates after borrowing grows?}}\\par\\vspace{{2pt}}
\\begin{{tabular}}{{llrrrrr}}
\\toprule
Sample & Inflation & $N$ & Mortgage & Consumer & Federal & Joint $p$ \\\\
\\midrule
{bodyB}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""


def table_break():
    c = pd.read_csv(os.path.join(TAB, "task7_break_interaction.csv"))
    rows = []
    for m in ["cpi", "pce"]:
        for s in ["mortgage", "consumer", "federal"]:
            g = c[(c["measure"] == m) & (c["credit"] == s)]
            if g.empty:
                continue
            r = g.iloc[0]
            rows.append(
                f"{MEAS[m]} & {SEC[s]} & {int(r['n_obs'])} & {r['coef_pre_1982']:.3f} & "
                f"{r['change_after_1982']:.3f}{stars(r['p_change_is_zero'])} & "
                f"{r['coef_post_1982']:.3f} & {r['p_change_is_zero']:.3f} \\\\"
            )
    body = "\n".join(rows)
    return f"""\\begin{{table}}[htbp]
\\centering
\\setlength{{\\belowcaptionskip}}{{8pt}}
\\small
\\caption{{Testing the early-1980s break directly. A single regression over the whole sample interacts each borrowing series with an indicator for quarters after 1981, so the change column is the estimated shift in the coefficient at the break and the final column tests whether that shift is zero. Significance: $^{{*}}$ ten percent, $^{{**}}$ five percent, $^{{***}}$ one percent.}}
\\label{{tab:creditbreak}}
\\begin{{tabular}}{{llrrrrr}}
\\toprule
Measure & Sector & $N$ & Before 1982 & Change & After 1982 & $p$ (change $=0$) \\\\
\\midrule
{body}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""


def main():
    parts = [table_main(), "", table_policy(), "", table_break()]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
