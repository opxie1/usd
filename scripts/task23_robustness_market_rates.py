import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")
FIG = os.path.join(ROOT, "figures")

MARKET_RATES = {
    "rate_federal": "rate_federal_10y",
    "rate_mortgage": "rate_mortgage_30y",
    "rate_business": "rate_business_baa",
    "rate_consumer": "rate_consumer_personal24m",
}
MUNI = ("rate_state_local", "rate_state_local_muni")

SAMPLES = {
    "market4_full_1972_2026": (list(MARKET_RATES), None, None),
    "market4_pre_covid_1972_2019": (list(MARKET_RATES), None, "2019-12-31"),
    "market5_with_muni_1972_2016": (list(MARKET_RATES) + [MUNI[0]], None, "2016-09-30"),
}


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    out = pd.DataFrame(index=df.index)
    out["money_g"] = 400.0 * (np.log(df["m2_less_base"]) - np.log(df["m2_less_base"].shift(1)))
    for short, col in MARKET_RATES.items():
        out[short] = df[col]
    out[MUNI[0]] = df[MUNI[1]]
    return out


def run_sample(d, sample_name, rate_cols, start, end):
    cols = ["money_g"] + rate_cols
    w = d[cols].dropna()
    if start:
        w = w.loc[w.index >= start]
    if end:
        w = w.loc[w.index <= end]
    n = len(w)
    model = VAR(w)
    sel = model.select_order(maxlags=8)
    p = max(int(sel.selected_orders["aic"]), 1)
    res = model.fit(p)
    names = list(res.names)
    mat = pd.DataFrame(index=names, columns=names, dtype=float)
    for caused in names:
        for causing in names:
            if caused == causing:
                continue
            g = res.test_causality(caused, [causing], kind="f")
            mat.loc[caused, causing] = round(float(g.pvalue), 4)
    others = [r for r in names if r.startswith("rate_") and r != "rate_federal"]
    joint_fed = res.test_causality(others, ["rate_federal"], kind="f")
    joint_to_fed = res.test_causality("rate_federal", others, kind="f")
    meta = dict(sample=sample_name, n_obs=n, lag_aic=p, stable=bool(res.is_stable()),
                joint_federal_to_others_p=round(float(joint_fed.pvalue), 4),
                joint_others_to_federal_p=round(float(joint_to_fed.pvalue), 4))
    return mat, meta


def heatmap(mat, title, path):
    fig, ax = plt.subplots(figsize=(8.5, 7))
    vals = mat.values.astype(float)
    masked = np.ma.masked_invalid(vals)
    im = ax.imshow(masked, cmap="RdYlGn", vmin=0, vmax=0.2)
    ax.set_xticks(range(len(mat.columns)), mat.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(mat.index)), mat.index)
    ax.set_xlabel("causing (column Granger-causes row)")
    ax.set_ylabel("caused")
    for i in range(len(mat.index)):
        for j in range(len(mat.columns)):
            if i != j and not np.isnan(vals[i, j]):
                ax.text(j, i, f"{vals[i, j]:.3f}", ha="center", va="center", fontsize=8,
                        color="black", fontweight="bold" if vals[i, j] < 0.05 else "normal")
    fig.colorbar(im, ax=ax, label="Granger p-value (red = significant)")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    d = load()
    metas = []
    for sample_name, (rate_cols, start, end) in SAMPLES.items():
        mat, meta = run_sample(d, sample_name, rate_cols, start, end)
        mat.rename_axis("caused").to_csv(os.path.join(TAB, f"task23_market_granger_{sample_name}.csv"))
        metas.append(meta)
        if sample_name == "market4_full_1972_2026":
            heatmap(mat, f"Granger p-values, MARKET rates VAR({meta['lag_aic']}), {meta['n_obs']} obs",
                    os.path.join(FIG, "task23_market_granger_heatmap.png"))
        print(f"=== {sample_name}: VAR({meta['lag_aic']}), n={meta['n_obs']}, stable={meta['stable']} ===")
        print(mat.to_string())
        print(f"joint federal causes other rates: p={meta['joint_federal_to_others_p']}")
        print(f"joint other rates cause federal: p={meta['joint_others_to_federal_p']}")
        print()
    pd.DataFrame(metas).to_csv(os.path.join(TAB, "task23_market_var_meta.csv"), index=False)


if __name__ == "__main__":
    main()
