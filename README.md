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

1. The raw state/local implied rate runs high (~7-8%) because NIPA state/local interest includes public-pension actuarial interest (BEA Table 3.3 note 1). Resolved per Prof. Gmeiner: `rate_state_local_implied_expension` nets out the table 7.24 pension-interest imputation (Y315RC1A027NBEA, annual, carried forward within year) and lands at 3-4%, validated against the Bond Buyer muni index over 1990-2016 (mean absolute gap 0.8pp). The federal implied rate carries the same pension component but is dominated by its large debt base. The business implied rate uses net (not gross) interest.
2. Fed balance-sheet series begin 2002Q4, which caps any specification that uses them.
3. Z.1 debt levels lag about one quarter (latest 2025Q4), so federal/state-local/business implied rates end 2025Q4; the consumer implied rate reaches 2026Q1.

## Econometrics (first pass)

`scripts/task1_money_inflation_var.py` runs Task 1 (money supply -> inflation, controlling for real output): ADF/KPSS unit-root tests, trivariate VARs of (real GDP growth, growth of M2-less-base, inflation) for each of the four inflation measures, AIC lag selection capped at 8 lags, stability checks, Granger causality both directions, orthogonalized IRFs (Cholesky ordering: output, money, inflation), an h=12 FEVD share, and a rolling 60-quarter Granger causality test to trace how the money-inflation link changes before, during, and after COVID. Outputs land in `tables/task1_*.csv` and `figures/task1_*.png`. Full-sample and pre-COVID subsamples plus a short post-2020 subsample (25 observations; interpret with caution).

`scripts/task23_rate_system_var.py` runs Tasks 2 and 3 (which rates respond to the money supply; which rates drive others). Six-variable VAR in levels of the five sector rates (federal, state/local ex-pension, mortgage, business, consumer) plus M2-less-base growth, 1971Q2-2024Q4 (the corrected state/local rate currently ends 2024Q4 because the pension series is annual). AIC lag selection capped at 8, stability confirmed, full pairwise Granger matrix plus joint tests of the federal-rate hierarchy, IRFs to federal-rate and money shocks, and a Johansen trace test across the five rates. Outputs in `tables/task23_*.csv`, `figures/task23_*.png`. Interpretation caveats: four of the five rates are backward-looking weighted averages (interest paid over debt), so the lone market rate (mortgage) naturally leads them; the state/local rate inherits annual steps from the pension correction.

`scripts/task5_loanable_funds_tvc.py` runs the empirical half of Task 5 (source of higher demand for loanable funds). It produces nominal GDP component shares (consumption, investment, government, net exports), a period-average table comparing 2010-2019, 2020-2021, and 2022-onward (growth of real GDP, real consumption, M2-less-base, sector-by-sector debt, and the CPI), and a time-varying coefficient regression of private borrowing growth (household mortgages + nonfinancial business + consumer credit) on one-quarter-lagged regressors (change in the 30y mortgage rate, real consumption growth, federal debt growth). Coefficients follow random walks estimated by maximum likelihood with the Kalman smoother; a rolling 40-quarter OLS provides a check. Regressors are lagged to limit same-quarter simultaneity. Outputs in `tables/task5_*.csv` and `figures/task5_*.png`. The literature-review half of Task 5 is in [`docs/task5_literature_review.md`](docs/task5_literature_review.md): fourteen verified sources across excess savings, fiscal transfers and fiscal-theory accounts of the inflation, the money-inflation regime literature, the supply-side counterpoint, current household borrowing, and crowding out, each with a note on how it bears on this paper's results.

`scripts/task23_robustness_market_rates.py` reruns the Tasks 2-3 system with market rates (10y Treasury, 30y mortgage, Baa corporate, 24m personal loan, and the Bond Buyer muni index in its pre-2016 window) in place of the implied weighted averages. The market-rate system delivers a clean one-way hierarchy: the federal rate jointly Granger-causes the other rates (p near 0 in full and pre-COVID samples) while the other rates jointly do not cause the federal rate (p = 0.75 full sample), and the mortgage rate's apparent dominance in the implied-rate system disappears, confirming it was an artifact of backward-looking weighted averages lagging a market rate. Money growth does not directly move market rates; the federal and business rates lead money growth instead. Outputs in `tables/task23_market_*.csv` and `figures/task23_market_granger_heatmap.png`.

`scripts/task23_toda_yamamoto.py` repeats the market-rate causality tests with the Toda-Yamamoto lag-augmented procedure (levels VAR with one extra lag, Wald tests on the first p lags only), which stays valid when the rates carry unit roots. Results match the standard tests: the federal rate causes the other rates, the other rates jointly do not cause the federal rate (p = 0.71), and the federal and business rates lead money growth. Outputs in `tables/task23_toda_yamamoto_*.csv`.

`scripts/validate_shapiro_demand.py` checks our money-driven story against Shapiro's supply/demand decomposition of PCE inflation (data in `data/raw/shapiro/`, from the San Francisco Fed). Money growth (M2-less-base, year over year) leads both components at long lags, with the demand-side correlation peaking around three years; bivariate Granger tests are stronger for the supply component than the demand component. The decomposition does not isolate monetary episodes as demand-driven, so the paper should cite it as an alternative lens rather than a validation, and we document that here. Outputs in `tables/shapiro_validation_*.csv` and `figures/shapiro_validation.png`.

`scripts/task4_vecm_spec_compare.py` estimates the Task 4 VECM under both deterministic specifications (constant only, rank 2 from the trace test; constant plus trend, rank 4) and saves log-likelihoods, loadings, and cointegrating vectors side by side in `tables/task4_vecm_specs_*.csv` so the specification choice can be made on economic grounds.

`scripts/task4_fed_transactions.py` runs Task 4 (role of Fed transactions in the money supply and interest rates), sample 2003Q1-2026Q1 because Fed securities holdings (WSHOSHO) begin 2002Q4. Six-variable VAR in growth rates and differences (Fed securities growth, monetary base growth, M2-less-base growth, change in fed funds, change in 10y Treasury, CPI inflation), AIC lags capped at 4 given the parameter count, Granger tests for the Fed-transactions channel, IRFs to a Fed securities shock, FEVD shares, then a Johansen trace test on the six log-level/rate series and a first-pass VECM (rank chosen by the trace test at 5 percent) whose loading and cointegration vectors are saved. Outputs in `tables/task4_*.csv` and `figures/task4_*.png`.

## Reproduce

Requires Python 3 with `pandas`, `numpy`, `matplotlib`, `statsmodels`.

```
python scripts/discover_nipa_interest.py  # validate NIPA interest series against BEA downloads
python scripts/fetch_fred.py              # pull data, build panels + catalog CSV
python scripts/make_catalog_md.py         # render catalog markdown
python scripts/make_plots.py              # render the six figures
python scripts/check_panel.py             # coverage + recent-values QA
python scripts/discover_pension_interest.py  # locate/validate the pension-interest correction series
python scripts/task1_money_inflation_var.py  # Task 1 VAR analysis
python scripts/task23_rate_system_var.py     # Tasks 2-3 rate system VAR
python scripts/task23_robustness_market_rates.py  # Tasks 2-3 market-rate robustness
python scripts/task23_toda_yamamoto.py       # Tasks 2-3 Toda-Yamamoto robustness
python scripts/validate_shapiro_demand.py    # money growth vs Shapiro components
python scripts/task4_vecm_spec_compare.py    # Task 4 VECM deterministic specs
python scripts/task4_fed_transactions.py     # Task 4 Fed transactions VAR/VECM
python scripts/task5_loanable_funds_tvc.py   # Task 5 loanable-funds demand TVC
```

The FRED API key is read from the `FRED_API_KEY` environment variable or from `config/fred_api_key.txt` (gitignored); it is not committed to the repository.
