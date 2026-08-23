"""
Diagnostic: pick a few users we KNOW are labeled as churned (is_churn=1
in train_sample.csv), and print their raw transaction history directly.
This lets us visually confirm whether the data actually shows their
coverage ending somewhere - or whether something in our SQL logic is
wrongly treating them as perpetually active.

Run from your project root: python 04_diagnose_active_flag.py
"""

import pandas as pd

train = pd.read_csv("data/processed/train_sample.csv")
txns = pd.read_csv("data/processed/transactions_sample.csv")

churners = train[train["is_churn"] == 1]["msno"]
print(f"Total labeled churners in sample: {len(churners)}")

# Build this set ONCE - reusing it 40,000 times is instant.
# Rebuilding it inside a loop condition (a common beginner trap) would
# mean recomputing the whole set on every iteration - accidentally
# O(n^2) and slow enough to look like a hang.
txn_user_ids = set(txns["msno"])

# Pick 3 churners who actually have transaction history in our sample
sample_churners = [m for m in churners if m in txn_user_ids][:3]
print(f"Inspecting {len(sample_churners)} churners with transaction history:\n")

for msno in sample_churners:
    user_txns = txns[txns["msno"] == msno].sort_values("transaction_date")
    print(f"--- User {msno[:12]}... ---")
    print(user_txns[["transaction_date", "membership_expire_date", "is_cancel", "is_auto_renew"]].to_string(index=False))
    print(f"Number of transactions: {len(user_txns)}")
    print(f"Last transaction date: {user_txns['transaction_date'].max()}")
    print(f"Last membership_expire_date: {user_txns['membership_expire_date'].max()}")
    print()

# Also: overall check across ALL users (not just 3) - what fraction of
# labeled churners have NO is_cancel=1 row at all in their history?
# If most churners never show is_cancel=1, that tells us churn in this
# dataset is often "silent" (they just stop renewing, no explicit
# cancellation flag) - which matters for how we detect "inactive."
churners_with_data = [m for m in churners if m in txn_user_ids]
has_explicit_cancel = txns[txns["msno"].isin(churners_with_data) & (txns["is_cancel"] == 1)]["msno"].nunique()
print(f"Of {len(churners_with_data)} churners with transaction data, "
      f"{has_explicit_cancel} have at least one is_cancel=1 row "
      f"({100*has_explicit_cancel/len(churners_with_data):.1f}%)")
