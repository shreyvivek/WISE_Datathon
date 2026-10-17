"""Run all scopes, save twins, print coverage/quality + baseline comparison."""
import time
import pandas as pd
from src.models.financial_twins import find_twins, baseline_global_knn, FEATS

apps = pd.read_parquet("data/processed/applications.parquet")
den = apps[apps.outcome == "denied"]
res = {}
for scope in ["lender", "lender_msa", "market"]:
    t = time.time(); r = find_twins(apps, scope); dt = time.time() - t
    res[scope] = r; r.to_parquet(f"data/processed/twins_{scope}.parquet")
    b = r[r["rank"] == 1]
    cov = b.quality.value_counts().reindex(["strong", "moderate", "weak"], fill_value=0)
    n_strong3 = (r[r.quality == "strong"].groupby("denied_id").size() >= 1).sum()
    print(f"\n[{scope}] {dt:.1f}s  denied with any candidate: {b.denied_id.nunique()}/{len(den)}"
          f"  best-match quality: {cov.to_dict()}  median dist(best): {b.dist.median():.2f}")
base = baseline_global_knn(apps)
m = base[base["rank"] == 1].merge(apps[["app_id", "lei"]], left_on="denied_id", right_on="app_id") \
        .merge(apps[["app_id", "lei"]], left_on="twin_id", right_on="app_id", suffixes=("_d", "_t"))
print(f"\n[baseline B global kNN] denied matched: {len(m)}; share whose nearest approved twin is from the SAME lender: "
      f"{(m.lei_d == m.lei_t).mean():.1%}")
