import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from statsmodels.tsa.vector_ar.vecm import coint_johansen

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
TAB = os.path.join(ROOT, "tables")
FIG = os.path.join(ROOT, "figures")

RATES = {
    "rate_federal": "rate_federal_implied",
    "rate_state_local": "rate_state_local_implied_expension",
    "rate_mortgage": "rate_mortgage_30y",
    "rate_business": "rate_business_implied",
    "rate_consumer": "rate_consumer_implied",
}

ORDER = ["money_g", "rate_federal", "rate_state_local", "rate_mortgage", "rate_business", "rate_consumer"]

ORDERING_NOTE = "Cholesky ordering: money_g, federal, state_local, mortgage, business, consumer (money first, federal rate leads the rate block per the hypothesis)"

SAMPLES = {
    "full_1971_2024": (None, None),
    "pre_covid_1971_2019": (None, "2019-12-31"),
}


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    out = pd.DataFrame(index=df.index)
    out["money_g"] = 400.0 * (np.log(df["m2_less_base"]) - np.log(df["m2_less_base"].shift(1)))
    for short, col in RATES.items():
        out[short] = df[col]
    return out[ORDER].dropna()


def run_sample(d, sample_name, start, end):
    w = d.copy()
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
    joint_fed = res.test_causality([r for r in names if r.startswith("rate_") and r != "rate_federal"], ["rate_federal"], kind="f")
    joint_to_fed = res.test_causality("rate_federal", [r for r in names if r.startswith("rate_") and r != "rate_federal"], kind="f")
    meta = dict(sample=sample_name, n_obs=n, lag_aic=p, stable=bool(res.is_stable()),
                joint_federal_to_others_p=round(float(joint_fed.pvalue), 4),
                joint_others_to_federal_p=round(float(joint_to_fed.pvalue), 4))
    return mat, meta, res


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

    long_rows = []
    for sample_name, (start, end) in SAMPLES.items():
        mat, meta, res = run_sample(d, sample_name, start, end)
        mat.rename_axis("caused").to_csv(os.path.join(TAB, f"task23_granger_matrix_{sample_name}.csv"))
        long_rows.append(meta)
        if sample_name == "full_1971_2024":
            heatmap(mat, f"Granger causality p-values, rate system VAR({meta['lag_aic']}), {meta['n_obs']} obs, 1971-2024",
                    os.path.join(FIG, "task23_granger_heatmap.png"))
            irf = res.irf(12)
            fig = irf.plot(orth=True, impulse="rate_federal")
            fig.suptitle(f"Orthogonalized IRFs to a federal-rate shock (full sample)\n{ORDERING_NOTE}", fontsize=9)
            fig.tight_layout()
            fig.savefig(os.path.join(FIG, "task23_irf_federal_shock.png"), dpi=150)
            plt.close(fig)
            fig = irf.plot(orth=True, impulse="money_g")
            fig.suptitle(f"Orthogonalized IRFs to a money growth shock (full sample)\n{ORDERING_NOTE}", fontsize=9)
            fig.tight_layout()
            fig.savefig(os.path.join(FIG, "task23_irf_money_shock.png"), dpi=150)
            plt.close(fig)
        print(f"=== {sample_name}: VAR({meta['lag_aic']}), n={meta['n_obs']}, stable={meta['stable']} ===")
        print(mat.to_string())
        print(f"joint federal causes other rates: p={meta['joint_federal_to_others_p']}")
        print(f"joint other rates cause federal: p={meta['joint_others_to_federal_p']}")
        print()

    pd.DataFrame(long_rows).to_csv(os.path.join(TAB, "task23_var_meta.csv"), index=False)

    rates_only = d[[c for c in ORDER if c.startswith("rate_")]]
    jo_rows = []
    jo = coint_johansen(rates_only.values, 0, 4)
    for r in range(len(jo.lr1)):
        jo_rows.append(dict(system="five_rates", deterministic="constant", k_ar_diff=4, null_rank_at_most=r,
                            trace_stat=round(float(jo.lr1[r]), 2), cv_95=round(float(jo.cvt[r, 1]), 2),
                            reject_at_5pct=bool(jo.lr1[r] > jo.cvt[r, 1])))
    jo_df = pd.DataFrame(jo_rows)
    jo_df.to_csv(os.path.join(TAB, "task23_johansen_rates.csv"), index=False)
    print("=== JOHANSEN trace test, five rates, constant, k_ar_diff=4 ===")
    print(jo_df.to_string(index=False))
    print()
    print(ORDERING_NOTE)


if __name__ == "__main__":
    main()
