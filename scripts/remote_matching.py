"""Run the full constrained matching on this host and time it; print a digest to compare with other hosts."""
import hashlib, platform, resource, time
import pandas as pd
from src.api.main import load, P  # reuses csv.gz fallback
from src.models.financial_twins import find_twins
apps = load("applications")
print("arch", platform.machine(), "rows", len(apps))
for scope in ["lender", "lender_msa", "market"]:
    t = time.perf_counter(); r = find_twins(apps, scope); dt = time.perf_counter() - t
    d = r.sort_values(["denied_id", "rank"])[["denied_id", "twin_id", "quality"]].to_csv(index=False)
    print(f"{scope}: {dt:.2f}s pairs={len(r)} strong_best={(r[r['rank']==1].quality=='strong').sum()} digest={hashlib.md5(d.encode()).hexdigest()[:10]}")
print("max_rss_mb", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
