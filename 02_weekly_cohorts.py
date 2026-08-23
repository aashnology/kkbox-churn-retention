"""
Step 2 (v2): Build weekly retention cohorts using SQL (via DuckDB).
"""

import duckdb

TRANSACTIONS_PATH = "data/processed/transactions_sample.csv"
OUTPUT_PATH = "data/processed/weekly_cohort_retention.csv"
MAX_WEEKS = 52  

con = duckdb.connect()

query = f"""

WITH transactions_clean AS (
    SELECT
        msno,
        strptime(CAST(transaction_date AS VARCHAR), '%Y%m%d') AS txn_date,
        strptime(CAST(membership_expire_date AS VARCHAR), '%Y%m%d') AS expire_date,
        is_cancel
    FROM read_csv_auto('{TRANSACTIONS_PATH}')
    -- a cancelled transaction doesn't extend coverage, so drop those here
    WHERE is_cancel = 0
),

    SELECT
        msno,
        date_trunc('week', MIN(txn_date)) AS cohort_week
    FROM transactions_clean
    GROUP BY msno
),

week_offsets AS (
    SELECT UNNEST(generate_series(0, {MAX_WEEKS})) AS weeks_since_signup
),

user_week_grid AS (
    SELECT
        c.msno,
        c.cohort_week,
        w.weeks_since_signup,
        c.cohort_week + (w.weeks_since_signup * INTERVAL 7 DAY) AS week_date
    FROM user_cohorts c
    CROSS JOIN week_offsets w
),

activity_flagged AS (
    SELECT
        g.cohort_week,
        g.weeks_since_signup,
        g.msno,
        EXISTS (
            SELECT 1 FROM transactions_clean t
            WHERE t.msno = g.msno
              AND g.week_date < t.expire_date
              AND (g.week_date + INTERVAL 7 DAY) > t.txn_date
        ) AS is_active
    FROM user_week_grid g
),

    SELECT
        cohort_week,
        weeks_since_signup,
        SUM(CASE WHEN is_active THEN 1 ELSE 0 END) AS active_users
    FROM activity_flagged
    GROUP BY cohort_week, weeks_since_signup
),

cohort_sizes AS (
    SELECT cohort_week, COUNT(DISTINCT msno) AS cohort_size
    FROM user_cohorts
    GROUP BY cohort_week
),

max_observed_date AS (
    SELECT MAX(txn_date) AS cutoff FROM transactions_clean
)

SELECT
    w.cohort_week,
    w.weeks_since_signup,
    w.active_users,
    s.cohort_size,
    ROUND(100.0 * w.active_users / s.cohort_size, 1) AS retention_pct
FROM weekly_activity w
JOIN cohort_sizes s ON w.cohort_week = s.cohort_week
CROSS JOIN max_observed_date m

WHERE (w.cohort_week + (w.weeks_since_signup * INTERVAL 7 DAY) + INTERVAL 7 DAY) <= m.cutoff
ORDER BY w.cohort_week, w.weeks_since_signup
"""

print("Running weekly cohort SQL query (this may take a minute or two - ")
print("it's now checking coverage windows, which is more work than before)...")
result = con.execute(query).df()

cutoff = con.execute(
    f"SELECT MAX(strptime(CAST(transaction_date AS VARCHAR), '%Y%m%d')) AS cutoff "
    f"FROM read_csv_auto('{TRANSACTIONS_PATH}')"
).fetchone()[0]
print(f"\nObservation cutoff used (latest transaction_date in the data): {cutoff}")
print("^ sanity check this looks like a real, recent-ish date - not decades in the future.")

print(f"\nProduced {len(result)} cohort-week rows (after dropping censored/unobservable cells).")
print(f"Cohorts span from {result['cohort_week'].min()} to {result['cohort_week'].max()}")
print("\nFirst 15 rows (retention_pct should now trend downward smoothly):")
print(result.head(15))

result.to_csv(OUTPUT_PATH, index=False)
print(f"\nSaved to {OUTPUT_PATH}")
