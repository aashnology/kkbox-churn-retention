"""
Ground-truth check: look at the FULL, unfiltered weekly_cohort_retention.csv
directly - no cohort-size or observed-weeks filters - and find out exactly
where retention actually drops below 100%, if anywhere.

Run from your project root: python 05_check_full_distribution.py
"""

import pandas as pd

df = pd.read_csv("data/processed/weekly_cohort_retention.csv", parse_dates=["cohort_week"])

print(f"Total rows: {len(df)}")
print(f"\nretention_pct summary:")
print(df["retention_pct"].describe())

below_100 = df[df["retention_pct"] < 100]
print(f"\nRows with retention_pct < 100: {len(below_100)} out of {len(df)} "
      f"({100*len(below_100)/len(df):.1f}%)")

if len(below_100) > 0:
    print(f"\nCohorts that show ANY decline: {below_100['cohort_week'].nunique()} "
          f"out of {df['cohort_week'].nunique()} total cohorts")
    print("\n10 lowest retention_pct rows found in the whole dataset:")
    print(below_100.nsmallest(10, "retention_pct")[
        ["cohort_week", "weeks_since_signup", "active_users", "cohort_size", "retention_pct"]
    ].to_string(index=False))
else:
    print("\nNo decline found ANYWHERE in the dataset - this would mean the")
    print("issue is upstream in 02_weekly_cohorts.py, not a filtering/selection")
    print("problem. Share this output and we'll look at the SQL logic itself.")
