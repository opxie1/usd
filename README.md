# The Long Shadow of Easy Money

Replication data and code for the working paper *The Long Shadow of Easy Money* (R. Gmeiner, University of South Dakota).

**Research question.** Has Federal Reserve action led to demand conditions that encourage monetary transmission of inflation made possible by earlier easy money? The thesis: expansionary policy (2008-2015, 2020-2021) created base money and lowered private borrowing costs; subsequent quantitative tightening, together with the level of demand, has drawn the latent inflationary pressure out of the monetary base via an expansion of bank credit (M2 rising while the monetary base is steady or falling).

Predecessor paper (VAR approach): Gmeiner, *The Fiscal Transmission of Inflation*, American Business Review. https://digitalcommons.newhaven.edu/cgi/viewcontent.cgi?article=2022&context=americanbusinessreview

## Repository layout

```
scripts/    data pull, QA, catalog, and figure code
data/raw/   one CSV per FRED series, native frequency (date,value)
data/processed/
            quarterly_panel.csv          all series + alternates + derived variables
            quarterly_panel_primary.csv  baseline series only
catalog/    variable_catalog.csv / .md   live FRED metadata for every series
figures/    the five summary figures from the outline
tables/     (econometric output, to come)
```

## Data

- **Source:** FRED (Federal Reserve Bank of St. Louis), pulled via the FRED API. Interest rates by sector follow Prof. Gmeiner's method — interest payments divided by debt — using NIPA interest series (BEA tables 1.10, 2.1, 3.2, 3.3, mirrored on FRED with full history and cross-validated against the BEA downloads in `data/raw/bea/`). Some Federal Reserve balance-sheet and Z.1 Financial Accounts series are mirrored on FRED; where a series is better taken from the Board's Data Download Program (Z.1), this is noted in the catalog.
- **Frequency:** quarterly (per Prof. Gmeiner). The aggregation rule (average for rates/prices, end-of-quarter for stocks) and all derived variables are documented in [`catalog/variable_catalog.md`](catalog/variable_catalog.md).
- **Coverage:** 1959Q1-2026Q2 where available; individual series coverage is in the catalog.

### Variable groups (Gmeiner's five categories)

- Money supply: M2 less monetary base (plus reserves)
- Inflation: CPI, PCE, PPI, GDP deflator (index levels and computed rates)
- Real output control: real GDP (plus alternates)
- Five interest rates: federal, state/local, business, consumer (implied = NIPA interest / debt) and mortgage (30y market rate, MORTGAGE30US, per Prof. Gmeiner)
- Five debt categories: federal (GFDEBTN), state/local (SLGSDODNS), mortgage (HHMSDODNS), business (BCNSDODNS), consumer (TOTALSL)
- Federal Reserve balance sheet: total assets, Treasuries, MBS
- Bank credit (thesis variables): total bank credit, loans and leases, C&I, real estate, consumer loans

### Known data issues (see catalog for detail)

1. The state/local implied rate runs high (~7-8%) because NIPA state/local interest includes public-pension actuarial interest (BEA Table 3.3 note 1); the federal implied rate carries the same pension component but is dominated by its large debt base. The business implied rate uses net (not gross) interest. See the catalog's open-data-issues section — these need a decision from Prof. Gmeiner.
2. Fed balance-sheet series begin 2002Q4, which caps any specification that uses them.
3. Z.1 debt levels lag about one quarter (latest 2025Q4), so federal/state-local/business implied rates end 2025Q4; the consumer implied rate reaches 2026Q1.

## Econometrics (first pass)

`scripts/task1_money_inflation_var.py` runs Task 1 (money supply -> inflation, controlling for real output): ADF/KPSS unit-root tests, trivariate VARs of (real GDP growth, growth of M2-less-base, inflation) for each of the four inflation measures, AIC lag selection capped at 8 lags, stability checks, Granger causality both directions, orthogonalized IRFs (Cholesky ordering: output, money, inflation), an h=12 FEVD share, and a rolling 60-quarter Granger causality test to trace how the money-inflation link changes before, during, and after COVID. Outputs land in `tables/task1_*.csv` and `figures/task1_*.png`. Full-sample and pre-COVID subsamples plus a short post-2020 subsample (25 observations; interpret with caution).

`scripts/task4_fed_transactions.py` runs Task 4 (role of Fed transactions in the money supply and interest rates), sample 2003Q1-2026Q1 because Fed securities holdings (WSHOSHO) begin 2002Q4. Six-variable VAR in growth rates and differences (Fed securities growth, monetary base growth, M2-less-base growth, change in fed funds, change in 10y Treasury, CPI inflation), AIC lags capped at 4 given the parameter count, Granger tests for the Fed-transactions channel, IRFs to a Fed securities shock, FEVD shares, then a Johansen trace test on the six log-level/rate series and a first-pass VECM (rank chosen by the trace test at 5 percent) whose loading and cointegration vectors are saved. Outputs in `tables/task4_*.csv` and `figures/task4_*.png`.

## Reproduce

Requires Python 3 with `pandas`, `numpy`, `matplotlib`, `statsmodels`.

```
python scripts/discover_nipa_interest.py  # validate NIPA interest series against BEA downloads
python scripts/fetch_fred.py              # pull data, build panels + catalog CSV
python scripts/make_catalog_md.py         # render catalog markdown
python scripts/make_plots.py              # render the six figures
python scripts/check_panel.py             # coverage + recent-values QA
python scripts/task1_money_inflation_var.py  # Task 1 VAR analysis
python scripts/task4_fed_transactions.py     # Task 4 Fed transactions VAR/VECM
```

The FRED API key is read from the `FRED_API_KEY` environment variable or from `config/fred_api_key.txt` (gitignored); it is not committed to the repository.
