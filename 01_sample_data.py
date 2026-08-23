"""
Step 1: Sample down the KKBox dataset to a manageable size.
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")          
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_SIZE = 80_000   
RANDOM_SEED = 42

def load_full_transactions():
    """
    IMPORTANT: transactions_v2.csv alone only covers a recent window
    (roughly the competition's second-round refresh period). The
    original transactions.csv holds the full multi-year history back
    to ~2015. Using v2 alone makes most users look like they first
    appeared very recently, which badly distorts cohort assignment.
    We combine both and drop exact-duplicate rows.
    """
    print("Loading transactions.csv (original, full history)...")
    old = pd.read_csv(RAW_DIR / "transactions.csv")
    print(f"  {len(old):,} rows")

    print("Loading transactions_v2.csv (refresh window)...")
    new = pd.read_csv(RAW_DIR / "transactions_v2.csv")
    print(f"  {len(new):,} rows")

    combined = pd.concat([old, new], ignore_index=True).drop_duplicates()
    print(f"Combined + deduplicated: {len(combined):,} rows")
    return combined

def main():
    print("Loading train_v2.csv (labels)...")
    train = pd.read_csv(RAW_DIR / "train_v2.csv")
    print(f"Full label set: {len(train):,} users")
    print(f"Churn rate in full set: {train['is_churn'].mean():.4f}")

    churned = train[train["is_churn"] == 1]
    retained = train[train["is_churn"] == 0]

    n_churned = min(len(churned), SAMPLE_SIZE // 2)
    n_retained = SAMPLE_SIZE - n_churned

    sample_train = pd.concat([
        churned.sample(n=n_churned, random_state=RANDOM_SEED),
        retained.sample(n=n_retained, random_state=RANDOM_SEED),
    ]).sample(frac=1, random_state=RANDOM_SEED)  # shuffle

    sample_users = set(sample_train["msno"])
    print(f"\nSampled {len(sample_train):,} users "
          f"({sample_train['is_churn'].mean():.4f} churn rate)")

    sample_train.to_csv(OUT_DIR / "train_sample.csv", index=False)

    print("\nFiltering transactions (combined old + v2)...")
    full_transactions = load_full_transactions()
    filtered_txns = full_transactions[full_transactions["msno"].isin(sample_users)]
    filtered_txns.to_csv(OUT_DIR / "transactions_sample.csv", index=False)
    print(f"  {len(full_transactions):,} rows -> {len(filtered_txns):,} rows")

    print("\nFiltering members_v3.csv...")
    members_df = pd.read_csv(RAW_DIR / "members_v3.csv")
    filtered_members = members_df[members_df["msno"].isin(sample_users)]
    filtered_members.to_csv(OUT_DIR / "members_sample.csv", index=False)
    print(f"  {len(members_df):,} rows -> {len(filtered_members):,} rows")

    print("\nFiltering user_logs_v2.csv (chunked, this is the big one)...")
    chunks = []
    chunk_iter = pd.read_csv(
        RAW_DIR / "user_logs_v2.csv",
        chunksize=2_000_000,
    )
    total_rows = 0
    for i, chunk in enumerate(chunk_iter):
        total_rows += len(chunk)
        filtered_chunk = chunk[chunk["msno"].isin(sample_users)]
        chunks.append(filtered_chunk)
        print(f"  processed chunk {i+1} (cumulative raw rows: {total_rows:,})")

    user_logs_sample = pd.concat(chunks, ignore_index=True)
    user_logs_sample.to_csv(OUT_DIR / "user_logs_sample.csv", index=False)
    print(f"  user_logs: {total_rows:,} rows -> {len(user_logs_sample):,} rows")

    print("\nDone. Sampled files are in data/processed/:")
    for f in OUT_DIR.glob("*.csv"):
        print(f"  {f.name}")

if __name__ == "__main__":
    main()
