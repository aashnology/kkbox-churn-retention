"""
Sanity-check plot: draws retention curves for a handful of cohorts,
so you can SEE whether retention behaves believably (declining over
time) rather than just eyeballing rows of numbers in the terminal.

Run from your project root: python 03_check_retention_curve.py
Requires matplotlib - install with: pip install matplotlib
"""

import pandas as pd
import matplotlib.pyplot as plt

INPUT_PATH = "data/processed/weekly_cohort_retention.csv"

df = pd.read_csv(INPUT_PATH, parse_dates=["cohort_week"])

# Small cohorts (like that first one with only 4 users) are noisy and
# not very meaningful - a single cancellation swings them by 25%+.
MIN_COHORT_SIZE = 50

# A cohort that only has a few observed weeks (because it's recent and
# got truncated by the censoring cutoff) hasn't had a chance to reach
# a real renewal/churn decision point yet. Diagnostic checks (see
# 04_diagnose_active_flag.py) showed real churners' cancellations
# typically land within their first ~10-15 observed weeks - so
# requiring 20+ weeks was excluding the exact cohorts with churn
# signal in them. Lowered to 8 to keep enough runway to see a first
# renewal decision, without excluding the informative cohorts.
MIN_OBSERVED_WEEKS = 8

weeks_per_cohort = df.groupby("cohort_week")["weeks_since_signup"].max()
eligible_cohorts = weeks_per_cohort[weeks_per_cohort >= MIN_OBSERVED_WEEKS].index

big_cohorts = df[
    (df["cohort_size"] >= MIN_COHORT_SIZE) &
    (df["cohort_week"].isin(eligible_cohorts))
]

print(f"Cohorts with at least {MIN_COHORT_SIZE} users AND "
      f"{MIN_OBSERVED_WEEKS}+ observed weeks: "
      f"{big_cohorts['cohort_week'].nunique()} out of {df['cohort_week'].nunique()} total")

# Pick 6 cohorts spread across the time range, not just the first 6 -
# this gives a more honest picture of whether the pattern holds over time.
cohort_weeks = sorted(big_cohorts["cohort_week"].unique())
print(f"Aggregating across {len(cohort_weeks)} eligible cohorts "
      f"(total users: {big_cohorts.drop_duplicates('cohort_week')['cohort_size'].sum()})")

# THE MAIN CHECK: a single aggregate curve, weighted by how many users
# were actually active at each cohort/week, pooled across ALL eligible
# cohorts. This is far more statistically reliable than eyeballing a
# handful of small individual cohorts, which can look noisy or flat
# just from small-sample luck.
aggregate = (
    big_cohorts.groupby("weeks_since_signup")
    .apply(lambda g: 100 * g["active_users"].sum() / g["cohort_size"].sum())
    .reset_index(name="retention_pct")
)
# Only trust weeks that still have a reasonable number of cohorts
# contributing data (later weeks have fewer surviving cohorts to
# average over, since older cohorts run out of observed weeks first).
cohorts_per_week = big_cohorts.groupby("weeks_since_signup")["cohort_week"].nunique()
aggregate = aggregate[aggregate["weeks_since_signup"].map(cohorts_per_week) >= 3]

plt.figure(figsize=(10, 6))
plt.plot(aggregate["weeks_since_signup"], aggregate["retention_pct"],
          marker="o", markersize=4, linewidth=2, color="black",
          label="Aggregate (all eligible cohorts, weighted)")

# Still show a few of the biggest individual cohorts faintly in the
# background for context/comparison, but the aggregate line is the
# one to actually trust.
top_cohorts = (
    big_cohorts.drop_duplicates("cohort_week")
    .nlargest(4, "cohort_size")["cohort_week"]
)
for cw in top_cohorts:
    cohort_data = big_cohorts[big_cohorts["cohort_week"] == cw].sort_values("weeks_since_signup")
    label = f"{pd.Timestamp(cw).date()} (n={cohort_data['cohort_size'].iloc[0]})"
    plt.plot(cohort_data["weeks_since_signup"], cohort_data["retention_pct"],
              marker="o", markersize=2, alpha=0.4, linewidth=1, label=label)

plt.xlabel("Weeks since signup")
plt.ylabel("Retention %")
plt.title("Retention curves by cohort (sanity check)")
plt.legend(fontsize=8)
plt.grid(alpha=0.3)
plt.tight_layout()

output_path = "retention_sanity_check.png"
plt.savefig(output_path, dpi=150)
print(f"\nSaved chart to {output_path} - open it and take a look.")
print("What to check for:")
print("  - Lines should generally trend DOWNWARD as weeks_since_signup increases")
print("  - Some noise/plateaus are fine, but a steady decline overall is the signal you want")
print("  - If lines look flat at 100% the whole way, or jump around wildly, something's off")
