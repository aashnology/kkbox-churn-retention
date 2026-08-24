# Subscription Churn \& Cohort Retention — The KKBox Premium Problem

For subscription businesses like KKBox (a major Asian music streaming
service), retaining an existing user is cheaper than acquiring a new one.
This project analyzes real subscription data to understand **who churns,
when, and what it costs the business** — combining SQL cohort analysis,
survival modeling, and a Tableau retention heatmap to arrive at a concrete,
actionable business number.

## TL;DR

* **Strongest lever**: enabling auto-renew cuts a user's churn hazard by
\~74% (hazard ratio 0.26) — by far the single largest effect found.
* **Financial impact**: across \~40,000 confirmed churners in this sample,
total lost lifetime value is approximately **NT$25.05M**, averaging
**\~NT$626 per churned user**.
* **Retention heatmap**: [Link](https://public.tableau.com/views/KKBoxSubscriptionChurnRetentionAnalysis/Dashboard1?:language=en-GB&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

## The data

[KKBox Churn Prediction Challenge](https://www.kaggle.com/c/kkbox-churn-prediction-challenge)
(Kaggle, WSDM Cup 2018) — \~80,000 sampled users, stratified to 50% churn
for modeling purposes (real-world KKBox churn is \~6%).

One early, important finding: `transactions_v2.csv` alone only covers a
recent window, not full user history — the original `transactions.csv` was
needed and combined with it for accurate cohort assignment. Using v2 alone
silently distorted early analysis; see `01_sample_data.py` for the fix.

## Repo structure

```
01_sample_data.py             - samples the full KKBox dataset down to a working subset
02_weekly_cohorts.py          - SQL weekly cohort retention query (DuckDB), handles right-censoring
03_check_retention_curve.py   - sanity-check plots for the retention curve
04_diagnose_active_flag.py    - diagnostic: verifies churn detection against known churners
05_check_full_distribution.py - diagnostic: full unfiltered retention distribution check
01_eda.ipynb                  - exploratory data analysis
02_survival_model.ipynb       - Cox Proportional Hazards model + LTV calculation
retention_sanity_check.png    - retention curve sanity-check chart
```

## Methodology and findings

### 1\. Weekly cohort retention (SQL / DuckDB)

Users were grouped by signup week and tracked over time. A key challenge:
**right-censoring** — recent cohorts haven't had enough time to reach a
renewal decision, and the dataset itself has a fixed observation cutoff.
Early attempts that ignored this showed implausible retention curves
(sudden cliffs, or flat 100% for a full year); the fix was to explicitly
truncate any cohort-week combination that fell beyond the data's actual
observation window, rather than letting missing future data masquerade as
churn. See `02_weekly_cohorts.py` for the full reasoning.

### 2\. Exploratory data analysis

* **Age data**: \~46% of values were implausible (0, negative, or over 1000) — a known issue with this self-reported field. Cleaned before use.
* **Profile completeness vs. churn**: users who left gender blank churned
at 40.6%, vs. 60.2% for those who specified it — a real, substantial gap
worth further investigation (see notebook for detail).
* **`is_auto_renew`**: 88.1% churn when off vs. 32.4% when on — the
strongest raw signal in the dataset, later confirmed by the model.
* **`payment_method_id`**: churn ranged from 17.6% to 99.7% depending on
method — some payment methods are near-certain churn indicators.

### 3\. Cox Proportional Hazards survival model

Fit using `lifelines`, with `duration` = observed subscription span and
`event` = KKBox's own churn label. Full findings and hazard ratios are in
`02_survival_model.ipynb`.

**A genuine statistical finding worth calling out**: the raw EDA showed
gender-specified users churning *more*; the Cox model, once controlling
for auto-renew status and plan length, showed the opposite direction —
a classic confounding effect, resolved by moving to a multivariate model.

The proportional hazards assumption was violated for all covariates
(common at this sample size — see notebook). Binary covariates were
stratified as a robustness check; effect directions held consistent
across both the primary and stratified models.

### 4\. Customer Lifetime Value (LTV) lost

For each churned user, lost LTV = (average retained-user duration − their
actual duration) × their daily revenue rate. This yields **NT$25.05M**
total across the sample, or **\~NT$626 average per churned user** — a
conservative estimate, since the retained-user benchmark is itself
right-censored (real retention may run longer than observed).

## Limitations

* Churn rate is deliberately balanced (50%) for modeling, not
representative of KKBox's true \~6% rate — the *total* LTV figure is
sample-specific; the *per-user average* is more generalizable.
* Cox PH's proportional hazards assumption was violated; addressed via
stratification, documented rather than hidden.
* Age data is missing/unreliable for a large share of users.

## Tech stack

SQL (DuckDB) · Python (pandas, lifelines, matplotlib) · Tableau Public

