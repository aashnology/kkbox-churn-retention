# Subscription Churn & Cohort Retention — The KKBox Premium Problem

**Status: Work in progress.** Data pipeline, SQL cohort analysis, and the
Tableau retention heatmap are complete. Survival modeling (Cox Proportional
Hazards) and the LTV-lost calculation are still in progress.

## The business problem

For subscription businesses like KKBox (a major Asian music streaming
service), retaining an existing user is cheaper than acquiring a new one.
This project analyzes real subscription data to understand **who churns,
when, and what it costs the business** — with the goal of identifying
patterns that could inform targeted retention offers.

## What's done so far

- **Data pipeline**: sampled ~80,000 users from the full KKBox dataset
  (Kaggle's WSDM Cup 2018 Churn Prediction Challenge), combining the
  original `transactions.csv` with the `transactions_v2.csv` refresh for
  complete historical coverage.
- **Weekly cohort retention analysis (SQL / DuckDB)**: grouped users by
  signup week and tracked retention over time, correctly handling
  **right-censoring** — i.e., not treating "we ran out of observable data"
  as "the user churned." See `02_weekly_cohorts.py` for the full query
  and reasoning.
- **Retention heatmap (Tableau)**: [link to Tableau Public dashboard —
  add once you have the exact URL]

### A finding worth calling out

Early attempts at this analysis showed cohorts with implausible,
choppy retention curves. Debugging traced this to two real issues:
1. **Right-censoring** — recent cohorts hadn't had enough time to reach
   a renewal decision point yet, so they looked artificially "100%
   retained."
2. **Incomplete transaction history** — `transactions_v2.csv` alone only
   covers a recent window; the original `transactions.csv` was needed
   for full multi-year history per user.

Both are documented in the diagnostic scripts (`04_diagnose_active_flag.py`,
`05_check_full_distribution.py`), which were used to verify the fix
against known churners rather than assuming the numbers were right.

## Still in progress

- Cox Proportional Hazards survival model (`lifelines`) to predict
  30-day cancellation risk and identify which features drive churn
- Customer Lifetime Value (LTV) lost from the churned segment
- Exploratory data analysis notebook

## Tech stack

SQL (DuckDB) · Python (pandas, lifelines) · Tableau Public

## Repo structure

```
01_sample_data.py            - samples the full KKBox dataset down to a working subset
02_weekly_cohorts.py         - SQL weekly cohort retention query (DuckDB)
03_check_retention_curve.py  - sanity-check plots for the retention curve
04_diagnose_active_flag.py   - diagnostic: verifies churn detection against known churners
05_check_full_distribution.py - diagnostic: full unfiltered retention distribution check
data/processed/               - sampled, processed CSVs (raw data is gitignored)
```

## Data source

[KKBox Churn Prediction Challenge](https://www.kaggle.com/c/kkbox-churn-prediction-challenge)
(Kaggle, WSDM Cup 2018)
