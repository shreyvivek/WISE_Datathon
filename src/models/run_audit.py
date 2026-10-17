import pandas as pd
from src.models.prioritisation import build_queue
from src.fairness.matching_audit import disparity

apps = pd.read_parquet("data/processed/applications.parquet")
audit = pd.read_parquet("data/processed/audit_only.parquet")
q = build_queue(apps, pd.read_parquet("data/processed/twins_lender.parquet"))
q.to_parquet("data/processed/review_queue.parquet")
print(q.status.value_counts().to_string()); print(q.head(5)[["priority", "quality", "n_strong", "dist", "completeness"]])
rows = [disparity(apps, audit, g) for g in ["Black or African American", "Asian"]]
res = pd.DataFrame(rows)
for c in ("raw_ci", "matched_ci"):
    res[[f"{c}_lo", f"{c}_hi"]] = pd.DataFrame(res[c].tolist(), index=res.index).astype(float); res = res.drop(columns=c)
res.to_csv("data/processed/fairness_report.csv", index=False)
pd.set_option("display.width", 250); print(res.T.to_string())
