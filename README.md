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

- **Source:** FRED (Federal Reserve Bank of St. Louis), pulled via the FRED API. Some Federal Reserve balance-sheet and Z.1 Financial Accounts series are mirrored on FRED; where a series is better taken from the Board's Data Download Program (Z.1), this is noted in the catalog.
- **Frequency:** quarterly (per Prof. Gmeiner). The aggregation rule (average for rates/prices, end-of-quarter for stocks) and all derived variables are documented in [`catalog/variable_catalog.md`](catalog/variable_catalog.md).
- **Coverage:** 1959Q1-2026Q2 where available; individual series coverage is in the catalog.

### Variable groups (Gmeiner's five categories)

- Money supply: M2 less monetary base (plus reserves)
- Inflation: CPI, PCE, PPI, GDP deflator (index levels and computed rates)
- Real output control: real GDP (plus alternates)
- Five interest rates: federal, state/local, mortgage, business, consumer/personal
- Five debt categories: federal, state/local, mortgage, business, consumer/personal
- Federal Reserve balance sheet: total assets, Treasuries, MBS
- Bank credit (thesis variables): total bank credit, loans and leases, C&I, real estate, consumer loans

### Known data issues (see catalog for detail)

1. The standard municipal yield (`MSLB20`) was discontinued in 2016Q3; there is no current municipal rate on FRED. Needs a sourcing decision.
2. Fed balance-sheet series begin 2002Q4, which caps any specification that uses them.
3. Z.1 debt levels lag about one quarter.

## Reproduce

Requires Python 3 with `pandas`, `numpy`, `matplotlib`.

```
python scripts/fetch_fred.py        # pull data, build panels + catalog CSV
python scripts/make_catalog_md.py   # render catalog markdown
python scripts/make_plots.py        # render the five figures
python scripts/check_panel.py       # coverage + recent-values QA
```

The FRED API key is currently set inline in the fetch script; it can be moved to an environment variable before any public release.
