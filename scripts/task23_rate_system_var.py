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

RATES = {
    "d_rate_federal": "rate_federal_implied",
    "d_rate_state_local": "rate_state_local_implied_expension",
    "d_rate_mortgage": "rate_mortgage_30y",
    "d_rate_business": "rate_business_implied",
    "d_rate_consumer": "rate_consumer_implied",
}
ORDER = ["money_g"] + list(RATES)
FED = "d_rate_federal"
ORDERING_NOTE = "Differenced implied rates (the levels are not cointegrated; see task23_diff_and_johansen.py). Market rates ARE cointegrated and are modeled with a VECM in that script. Cholesky ordering: money first, then federal, state_local, mortgage, business, consumer."
SAMPLES = {"full": (None, None), "pre_covid": (None, "2019-12-31")}


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"]).set_index("quarter_end")
    out = pd.DataFrame(index=df.index)
    out["money_g"] = 400.0 * (np.log(df["m2_less_base"]) - np.log(df["m2_less_base"].shift(1)))
    for short, col in RATES.items():
        out[short] = df[col].diff()
    return out[ORDER].dropna()


def whiteness(res):
    try:
        return round(float(res.test_whiteness(nlags=res.k_ar + 6, adjusted=True).pvalue), 4)
    except Exception:
        return float("nan")


def run_sample(d, start, end):
    w = d.copy()
    if start:
        w = w.loc[w.index >= start]
    if end:
        w = w.loc[w.index <= end]
    res = VAR(w).fit(maxlags=8, ic="aic")
    names = list(res.names)
    mat = pd.DataFrame(index=names, columns=names, dtype=float)
    for caused in names:
        for causing in names:
            if caused != causing:
                mat.loc[caused, causing] = round(float(res.test_causality(caused, [causing], kind="f").pvalue), 4)
    others = [r for r in names if r.startswith("d_rate_") and r != FED]
    meta = dict(n_obs=len(w), lag_aic=res.k_ar, stable=bool(res.is_stable()),
                min_root_modulus=round(float(np.min(np.abs(res.roots))), 4),
                resid_whiteness_p=whiteness(res),
                joint_federal_to_others_p=round(float(res.test_causality(others, [FED], kind="f").pvalue), 4),
                joint_others_to_federal_p=round(float(res.test_causality(FED, others, kind="f").pvalue), 4))
    return mat, meta, res


def heatmap(mat, title, path):
    fig, ax = plt.subplots(figsize=(8.5, 7))
    vals = mat.values.astype(float)
    im = ax.imshow(np.ma.masked_invalid(vals), cmap="RdYlGn", vmin=0, vmax=0.2)
    disp = {"money_g": "Money", "d_rate_federal": "Federal", "d_rate_state_local": "State/local",
            "d_rate_mortgage": "Mortgage", "d_rate_business": "Business", "d_rate_consumer": "Consumer"}
    labs = [disp.get(c, c) for c in mat.columns]
    ax.set_xticks(range(len(mat.columns)), labs, rotation=45, ha="right")
    ax.set_yticks(range(len(mat.index)), labs)
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
    for name, (start, end) in SAMPLES.items():
        mat, meta, res = run_sample(d, start, end)
        meta = dict(sample=name, **meta)
        metas.append(meta)
        mat.rename_axis("caused").to_csv(os.path.join(TAB, f"task23_granger_matrix_{name}.csv"))
        if name == "full":
            heatmap(mat, f"Granger p-values, differenced implied-rate VAR({meta['lag_aic']}), {meta['n_obs']} obs",
                    os.path.join(FIG, "task23_granger_heatmap.png"))
            irf = res.irf(12)
            for imp, fname in [("money_g", "task23_irf_money_shock.png"), (FED, "task23_irf_federal_shock.png")]:
                fig = irf.plot(orth=True, impulse=imp)
                fig.suptitle(f"Orthogonalized IRFs to a {imp} shock (differenced implied rates)\n{ORDERING_NOTE}", fontsize=8)
                fig.tight_layout()
                fig.savefig(os.path.join(FIG, fname), dpi=150)
                plt.close(fig)
        print(f"=== {name}: differenced implied-rate VAR({meta['lag_aic']}), n={meta['n_obs']}, stable={meta['stable']}, min|root|={meta['min_root_modulus']} ===")
        print(mat.to_string())
        print(f"joint federal -> others p={meta['joint_federal_to_others_p']}; joint others -> federal p={meta['joint_others_to_federal_p']}; resid whiteness p={meta['resid_whiteness_p']}")
        print()

    pd.DataFrame(metas).to_csv(os.path.join(TAB, "task23_var_meta.csv"), index=False)
    print(ORDERING_NOTE)


if __name__ == "__main__":
    main()
