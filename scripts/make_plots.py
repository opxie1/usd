import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
FIG = os.path.join(ROOT, "figures")


def load():
    df = pd.read_csv(os.path.join(PROC, "quarterly_panel.csv"), parse_dates=["quarter_end"])
    return df.set_index("quarter_end")


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), dpi=150)
    plt.close(fig)


def fig_money(df):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(df.index, df["m2"] / 1000.0, label="M2", linewidth=1.4)
    ax.plot(df.index, df["monetary_base"] / 1000.0, label="Monetary base", linewidth=1.4)
    ax.plot(df.index, df["m2_less_base"] / 1000.0, label="M2 less monetary base", linewidth=2.0, color="black")
    ax.set_title("Money Supply: M2, Monetary Base, and M2 less Monetary Base")
    ax.set_ylabel("Trillions of dollars")
    ax.set_xlabel("Quarter")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save(fig, "fig1_money_supply.png")


def fig_inflation(df):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    series = [
        ("infl_cpi_yoy", "CPI"),
        ("infl_pce_price_yoy", "PCE"),
        ("infl_ppi_allcommodities_yoy", "PPI (all commodities)"),
        ("infl_gdp_deflator_yoy", "GDP deflator"),
    ]
    for col, lab in series:
        if col in df:
            ax.plot(df.index, df[col], label=lab, linewidth=1.3)
    ax.axhline(2.0, color="gray", linestyle="--", linewidth=1.0, label="2% target")
    ax.set_title("Inflation Rates (year-over-year)")
    ax.set_ylabel("Percent")
    ax.set_xlabel("Quarter")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save(fig, "fig2_inflation.png")


def fig_debt(df):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    cats = [
        ("debt_federal", "Federal"),
        ("debt_state_local", "State and local"),
        ("debt_mortgage_total", "Mortgage (total)"),
        ("debt_business", "Business (nonfinancial)"),
        ("debt_consumer_credit", "Consumer credit"),
    ]
    present = [(c, l) for c, l in cats if c in df]
    for col, lab in present:
        ax.plot(df.index, df[col] / 1e6, label=lab, linewidth=1.3)
    total = sum(df[c] for c, _ in present)
    ax.plot(df.index, total / 1e6, label="Sum of five categories", linewidth=2.0, color="black", linestyle=":")
    ax.set_title("Debt Levels by Category")
    ax.set_ylabel("Trillions of dollars")
    ax.set_xlabel("Quarter")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save(fig, "fig3_debt.png")


def fig_rates(df):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    rates = [
        ("rate_federal_10y", "Federal (10y Treasury)"),
        ("rate_state_local_muni", "State and local (muni, ends 2016)"),
        ("rate_mortgage_30y", "Mortgage (30y)"),
        ("rate_business_baa", "Business (Baa corporate)"),
        ("rate_consumer_personal24m", "Consumer (personal 24m)"),
    ]
    for col, lab in rates:
        if col in df:
            ax.plot(df.index, df[col], label=lab, linewidth=1.3)
    ax.set_title("Interest Rates by Category")
    ax.set_ylabel("Percent")
    ax.set_xlabel("Quarter")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save(fig, "fig4_interest_rates.png")


def fig_fed(df):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    items = [
        ("fed_total_assets", "Total assets"),
        ("fed_treasuries", "Treasury securities"),
        ("fed_mbs", "Mortgage-backed securities"),
    ]
    sub = df[df["fed_total_assets"].notna()] if "fed_total_assets" in df else df
    for col, lab in items:
        if col in df:
            ax.plot(sub.index, sub[col] / 1e6, label=lab, linewidth=1.4)
    ax.set_title("Federal Reserve Balance Sheet (securities held and total assets)")
    ax.set_ylabel("Trillions of dollars")
    ax.set_xlabel("Quarter")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save(fig, "fig5_fed_balance_sheet.png")


def main():
    df = load()
    fig_money(df)
    fig_inflation(df)
    fig_debt(df)
    fig_rates(df)
    fig_fed(df)
    print("wrote 5 figures to", FIG)


if __name__ == "__main__":
    main()
