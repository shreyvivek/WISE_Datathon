"""Export processed parquet tables to gz CSV for hosts without pyarrow (e.g. s390x Ubuntu apt)."""
import pandas as pd
for n in ["applications", "twins_lender", "review_queue", "denial_context", "audit_only"]:
    d = pd.read_parquet(f"data/processed/{n}.parquet")
    (d.reset_index() if d.index.name else d).to_csv(f"data/processed/{n}.csv.gz", index=False)
