# Variable Catalog - The Long Shadow of Easy Money

All series retrieved from FRED (Federal Reserve Bank of St. Louis) via the FRED API.
Metadata below (title, units, frequency, coverage) is captured live from the API at fetch time, not transcribed by hand.

**Frequency:** native series resampled to quarterly per Prof. Gmeiner's instruction.

**Quarterly aggregation rule:**
- Price indices and interest rates: quarterly = average of the within-quarter observations (`agg_rule = avg`).
- Stocks (money, debt levels, Federal Reserve balance sheet): quarterly = last (end-of-quarter) observation, matching the point-in-time convention of the Z.1 Financial Accounts (`agg_rule = last`).
- Series already quarterly (GDP, GDP deflator, Z.1 debt) are placed in their quarter bucket unchanged.

**Quarter dating:** rows are labeled by quarter end (e.g., `2020-03-31` = 2020Q1).

**Derived variables in the panel:**
- `m2_less_base` = `m2` (M2SL) minus `monetary_base` (BOGMBASE); both in billions of dollars.
- `infl_<index>_qoq_ann` = 400 x (ln P_t - ln P_(t-1)); annualized quarterly inflation.
- `infl_<index>_yoy` = 100 x (P_t / P_(t-4) - 1); year-over-year inflation.

**Implied interest rates (per Prof. Gmeiner: interest payments divided by debt).** Computed as annual NIPA interest payment (SAAR, billions) divided by the end-of-quarter debt stock (converted to billions), times 100, giving an annualized weighted-average rate in percent:
- `rate_federal_implied` = `int_federal` (A091RC1Q027SBEA) / `debt_federal` (GFDEBTN)
- `rate_state_local_implied` = `int_state_local` (B111RC1Q027SBEA) / `debt_state_local` (SLGSDODNS)
- `rate_business_implied` = `int_business` (W272RC1Q027SBEA) / `debt_business_corporate` (BCNSDODNS)
- `rate_consumer_implied` = `int_personal` (B069RC1Q027SBEA) / `debt_consumer_credit` (TOTALSL)
- `rate_business_implied_nonfin` = `int_business` / `debt_business` (TBSDODNS); broader-business alternate.
- `rate_state_local_implied_expension` = (`int_state_local` - `int_state_local_pension`) / `debt_state_local`; the pension correction chosen by Prof. Gmeiner (option 1). `int_state_local_pension` is NIPA table 7.24 'Imputed interest on plans' claims on employers' (Y315RC1A027NBEA), the actuarial pension interest that BEA folds into state/local interest payments (Table 3.3 note 1). The series is annual, carried forward across the quarters of each year; it currently ends with the 2024 annual value, so the corrected rate ends 2024Q4 until BEA releases 2025. Validation: over 1990-2016 the corrected rate tracks the Bond Buyer GO 20-bond muni index with a mean absolute gap of 0.8 percentage points, against roughly 3.5 points uncorrected.
- Mortgage rate uses the market series `rate_mortgage_30y` (MORTGAGE30US) per Prof. Gmeiner, since long mortgage durations make a current rate more informative than a weighted average.

**status:** `primary` = series intended for the baseline specification; `alternate` = comparable series kept for robustness and selection, per Prof. Gmeiner's note that the best of several similar series will become clear during the econometrics.

## Open data issues

1. **State/local implied rate pension bias - RESOLVED (Gmeiner chose option a, net out the pension interest).** BEA Table 3.3 footnote 1: state/local 'interest payments' includes interest accrued on the actuarial liabilities of defined-benefit public pension plans, which pushed the uncorrected ratio to 7-8%. `rate_state_local_implied_expension` subtracts the table 7.24 pension-interest imputation (Y315RC1A027NBEA) and lands at 3-4%, in line with municipal yields. The uncorrected `rate_state_local_implied` is retained for reference. Remaining caveat: the pension series is annual (carried forward within each year) and ends with the 2024 release, so the corrected rate stops at 2024Q4 for now.
2. **Federal implied rate also contains pension interest** (BEA Table 3.2 footnote 4: federal-employee DB pension interest), but the very large debt base makes the relative effect small; the federal implied rate of about 3.2% is consistent with the average rate on total public debt.
3. **Business implied rate uses NET interest and miscellaneous payments** (domestic industries), not gross interest, and the interest concept spans domestic private industries while the debt base is nonfinancial corporate (`BCNSDODNS`). Treat it as a cost-of-funds index rather than a precise contractual rate; `rate_business_implied_nonfin` (over `TBSDODNS`) is provided as an alternate.
4. **Federal Reserve balance-sheet series begin 2002Q4** (weekly H.4.1). Any specification including Fed total assets / securities held is capped at a 2002Q4 start.
5. **Z.1 Financial Accounts (debt levels) lag about one quarter.** The latest debt point is 2025Q4, so the federal, state/local, and business implied rates end 2025Q4; the consumer implied rate extends to 2026Q1 because consumer credit (`TOTALSL`) is monthly.
6. **Several market rate series are not seasonally adjusted (NSA);** see the `SA` column. The TERMCB consumer rates are reported on a quarterly cadence (Feb/May/Aug/Nov).

## Money Supply and Reserves

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `m2` | `M2SL` | M2 | Billions of Dollars | Monthly | SA | 1959-01-01 .. 2026-05-01 | last |
| primary | `monetary_base` | `BOGMBASE` | Monetary Base: Total | Billions of Dollars | Monthly | NSA | 1959-01-01 .. 2026-05-01 | last |
| alternate | `m2_real` | `M2REAL` | Real M2 Money Stock | Billions of 1982-84 Dollars | Monthly | SA | 1959-01-01 .. 2026-05-01 | last |
| alternate | `reserve_balances` | `WRESBAL` | Liabilities and Capital: Other Factors Draining Reserve Balances: Reserve Balances with Federal Reserve Banks: Week Average | Millions of U.S. Dollars | Weekly, Ending Wednesday | NSA | 2002-12-18 .. 2026-06-17 | last |
| alternate | `total_reserves` | `TRESEGUSM052N` | Total Reserves excluding Gold for United States | Millions of Dollars | Monthly | NSA | 1950-12-01 .. 2026-03-01 | last |

## Price Indices (for Inflation)

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `cpi` | `CPIAUCSL` | Consumer Price Index for All Urban Consumers: All Items in U.S. City Average | Index 1982-1984=100 | Monthly | SA | 1947-01-01 .. 2026-05-01 | avg |
| primary | `gdp_deflator` | `GDPDEF` | Gross Domestic Product: Implicit Price Deflator | Index 2017=100 | Quarterly | SA | 1947-01-01 .. 2026-01-01 | avg |
| primary | `pce_price` | `PCEPI` | Personal Consumption Expenditures: Chain-type Price Index | Index 2017=100 | Monthly | SA | 1959-01-01 .. 2026-05-01 | avg |
| primary | `ppi_allcommodities` | `PPIACO` | Producer Price Index by Commodity: All Commodities | Index 1982=100 | Monthly | NSA | 1913-01-01 .. 2026-05-01 | avg |
| alternate | `cpi_core` | `CPILFESL` | Consumer Price Index for All Urban Consumers: All Items Less Food and Energy in U.S. City Average | Index 1982-1984=100 | Monthly | SA | 1957-01-01 .. 2026-05-01 | avg |
| alternate | `pce_price_core` | `PCEPILFE` | Personal Consumption Expenditures Excluding Food and Energy (Chain-Type Price Index) | Index 2017=100 | Monthly | SA | 1959-01-01 .. 2026-05-01 | avg |
| alternate | `ppi_finaldemand` | `PPIFIS` | Producer Price Index by Commodity: Final Demand | Index Nov 2009=100 | Monthly | SA | 2009-11-01 .. 2026-05-01 | avg |

## Real Output (Controls)

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `real_gdp` | `GDPC1` | Real Gross Domestic Product | Billions of Chained 2017 Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | last |
| alternate | `nominal_gdp` | `GDP` | Gross Domestic Product | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | last |
| alternate | `potential_gdp` | `GDPPOT` | Real Potential Gross Domestic Product | Billions of Chained 2017 Dollars | Quarterly | NSA | 1949-01-01 .. 2036-10-01 | last |
| alternate | `real_pce` | `PCECC96` | Real Personal Consumption Expenditures | Billions of Chained 2017 Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | last |

## Interest Rate: Federal

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `rate_federal_10y` | `GS10` | Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis | Percent | Monthly | NSA | 1953-04-01 .. 2026-05-01 | avg |
| primary | `rate_fedfunds_policy` | `FEDFUNDS` | Federal Funds Effective Rate | Percent | Monthly | NSA | 1954-07-01 .. 2026-05-01 | avg |
| alternate | `rate_tbill_3m` | `TB3MS` | 3-Month Treasury Bill Secondary Market Rate, Discount Basis | Percent | Monthly | NSA | 1934-01-01 .. 2026-05-01 | avg |
| alternate | `rate_treasury_2y` | `GS2` | Market Yield on U.S. Treasury Securities at 2-Year Constant Maturity, Quoted on an Investment Basis | Percent | Monthly | NSA | 1976-06-01 .. 2026-05-01 | avg |

## Interest Rate: State and Local

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `rate_state_local_muni` | `MSLB20` | Bond Buyer Go 20-Bond Municipal Bond Index (DISCONTINUED) (DISCONTINUED) | Percent | Monthly | NSA | 1953-01-01 .. 2016-09-01 | avg |

## Interest Rate: Mortgage

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `rate_mortgage_30y` | `MORTGAGE30US` | 30-Year Fixed Rate Mortgage Average in the United States | Percent | Weekly, Ending Thursday | NSA | 1971-04-02 .. 2026-06-25 | avg |

## Interest Rate: Business

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `rate_business_baa` | `BAA` | Moody's Seasoned Baa Corporate Bond Yield | Percent | Monthly | NSA | 1919-01-01 .. 2026-05-01 | avg |
| alternate | `rate_business_aaa` | `AAA` | Moody's Seasoned Aaa Corporate Bond Yield | Percent | Monthly | NSA | 1919-01-01 .. 2026-05-01 | avg |
| alternate | `rate_business_prime` | `MPRIME` | Bank Prime Loan Rate | Percent | Monthly | NSA | 1949-01-01 .. 2026-05-01 | avg |

## Interest Rate: Consumer/Personal

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `rate_consumer_personal24m` | `TERMCBPER24NS` | Finance Rate on Personal Loans at Commercial Banks, 24 Month Loan | Percent | Monthly | NSA | 1972-02-01 .. 2026-02-01 | avg |
| alternate | `rate_consumer_auto48m` | `TERMCBAUTO48NS` | Finance Rate on Consumer Installment Loans at Commercial Banks, New Autos 48 Month Loan | Percent | Monthly | NSA | 1972-02-01 .. 2026-02-01 | avg |
| alternate | `rate_consumer_creditcard` | `TERMCBCCALLNS` | Commercial Bank Interest Rate on Credit Card Plans, All Accounts | Percent | Monthly | NSA | 1994-11-01 .. 2026-02-01 | avg |

## Debt: Federal

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `debt_federal` | `GFDEBTN` | Federal Debt: Total Public Debt | Millions of Dollars | Quarterly, End of Period | NSA | 1966-01-01 .. 2026-01-01 | last |
| alternate | `debt_federal_public` | `FYGFDPUN` | Federal Debt Held by the Public | Millions of Dollars | Quarterly, End of Period | NSA | 1970-01-01 .. 2026-01-01 | last |

## Debt: State and Local

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `debt_state_local` | `SLGSDODNS` | State and Local Governments; Debt Securities and Loans; Liability, Level | Millions of U.S. Dollars | Quarterly, End of Period | SA | 1945-10-01 .. 2026-01-01 | last |

## Debt: Mortgage

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `debt_mortgage_household` | `HHMSDODNS` | Households and Nonprofit Organizations; One-to-Four-Family Residential Mortgages; Liability, Level | Millions of U.S. Dollars | Quarterly, End of Period | SA | 1945-10-01 .. 2026-01-01 | last |
| alternate | `debt_mortgage_total` | `ASTMA` | All Sectors; Total Mortgages; Asset, Level | Millions of U.S. Dollars | Quarterly, End of Period | NSA | 1945-10-01 .. 2026-01-01 | last |

## Debt: Business

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `debt_business_corporate` | `BCNSDODNS` | Nonfinancial Corporate Business; Debt Securities and Loans; Liability, Level | Millions of U.S. Dollars | Quarterly, End of Period | SA | 1945-10-01 .. 2026-01-01 | last |
| alternate | `debt_business` | `TBSDODNS` | Nonfinancial Business; Debt Securities and Loans; Liability, Level | Millions of U.S. Dollars | Quarterly, End of Period | SA | 1945-10-01 .. 2026-01-01 | last |

## Debt: Consumer/Personal

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `debt_consumer_credit` | `TOTALSL` | Total Consumer Credit Owned and Securitized | Millions of U.S. Dollars | Monthly | SA | 1943-01-01 .. 2026-04-01 | last |
| alternate | `debt_household_total` | `CMDEBT` | Households and Nonprofit Organizations; Debt Securities and Loans; Liability, Level | Millions of U.S. Dollars | Quarterly, End of Period | SA | 1945-10-01 .. 2026-01-01 | last |

## Federal Reserve Balance Sheet

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `fed_mbs` | `WSHOMCB` | Assets: Securities Held Outright: Mortgage-Backed Securities: Wednesday Level | Millions of U.S. Dollars | Weekly, As of Wednesday | NSA | 2002-12-18 .. 2026-06-17 | last |
| primary | `fed_total_assets` | `WALCL` | Assets: Total Assets: Total Assets (Less Eliminations from Consolidation): Wednesday Level | Millions of U.S. Dollars | Weekly, As of Wednesday | NSA | 2002-12-18 .. 2026-06-17 | last |
| primary | `fed_treasuries` | `TREAST` | Assets: Securities Held Outright: U.S. Treasury Securities: All: Wednesday Level | Millions of U.S. Dollars | Weekly, As of Wednesday | NSA | 2002-12-18 .. 2026-06-17 | last |
| alternate | `fed_securities_total` | `WSHOSHO` | Assets: Securities Held Outright: Securities Held Outright: Wednesday Level | Millions of U.S. Dollars | Weekly, As of Wednesday | NSA | 2002-12-18 .. 2026-06-17 | last |

## Bank Credit (Thesis Variables)

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `bank_credit_total` | `TOTBKCR` | Bank Credit, All Commercial Banks | Billions of U.S. Dollars | Weekly, Ending Wednesday | SA | 1973-01-03 .. 2026-06-10 | last |
| alternate | `bank_ci_loans` | `BUSLOANS` | Commercial and Industrial Loans, All Commercial Banks | Billions of U.S. Dollars | Monthly | SA | 1947-01-01 .. 2026-05-01 | last |
| alternate | `bank_consumer_loans` | `CONSUMER` | Consumer Loans, All Commercial Banks | Billions of U.S. Dollars | Monthly | SA | 1947-01-01 .. 2026-05-01 | last |
| alternate | `bank_loans_leases` | `TOTLL` | Loans and Leases in Bank Credit, All Commercial Banks | Billions of U.S. Dollars | Weekly, Ending Wednesday | SA | 1973-01-03 .. 2026-06-10 | last |
| alternate | `bank_realestate_loans` | `REALLN` | Real Estate Loans, All Commercial Banks | Billions of U.S. Dollars | Monthly | SA | 1947-01-01 .. 2026-05-01 | last |

## NIPA Interest Payments (for implied rates)

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `int_business` | `W272RC1Q027SBEA` | Gross domestic income: Net operating surplus: Private enterprises: Net interest and miscellaneous payments, domestic industries | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | avg |
| primary | `int_federal` | `A091RC1Q027SBEA` | Federal government current expenditures: Interest payments | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | avg |
| primary | `int_personal` | `B069RC1Q027SBEA` | Personal interest payments | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | avg |
| primary | `int_state_local` | `B111RC1Q027SBEA` | State and local government current receipts: Interest payments | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | avg |
| primary | `int_state_local_pension` | `Y315RC1A027NBEA` | State and Local Government Defined Benefit Pension Plans: Current receipts, accrual basis: Income receipts on assets: Interest: Imputed interest on plans' claims on employers | Billions of Dollars | Annual | NSA | 1929-01-01 .. 2024-01-01 | ffill |

## GDP Components, Nominal (Task 5)

| status | name (panel column) | FRED ID | title | units | freq | SA | coverage | agg |
|---|---|---|---|---|---|---|---|---|
| primary | `government_nominal` | `GCE` | Government Consumption Expenditures and Gross Investment | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | last |
| primary | `investment_nominal` | `GPDI` | Gross Private Domestic Investment | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | last |
| primary | `netexports_nominal` | `NETEXP` | Net Exports of Goods and Services | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | last |
| primary | `pce_nominal` | `PCEC` | Personal Consumption Expenditures | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | last |
| alternate | `pce_durables` | `PCDG` | Personal Consumption Expenditures: Durable Goods | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | last |
| alternate | `pce_nondurables` | `PCND` | Personal Consumption Expenditures: Nondurable Goods | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | last |
| alternate | `pce_services` | `PCESV` | Personal Consumption Expenditures: Services | Billions of Dollars | Quarterly | SAAR | 1947-01-01 .. 2026-01-01 | last |
