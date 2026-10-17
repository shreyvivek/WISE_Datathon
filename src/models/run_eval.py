"""Evaluation layers 9.1 / 9.4. All numbers printed come from this run. Synthetic experiments are labelled."""
import time, json
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from src.models.financial_twins import find_twins, Params, TOL, FEATS, LOGF, baseline_global_knn
from src.models.prioritisation import build_queue

apps = pd.read_parquet("data/processed/applications.parquet")
out = {}
base_t = find_twins(apps, "lender"); base_q = build_queue(apps, base_t)

# 9.1 sensitivity to tolerance scale
sens = {}
for m in [0.5, 1.0, 1.5, 2.0]:
    p = Params(tol={k: v * m for k, v in TOL.items()}); t = find_twins(apps, "lender", p); q = build_queue(apps, t)
    both = base_q.priority.notna() & q.reindex(base_q.index).priority.notna()
    rho = spearmanr(base_q.priority[both], q.reindex(base_q.index).priority[both]).statistic if m != 1.0 else 1.0
    sens[m] = {"strong_share": float((q.quality == "strong").mean()), "queue_size": int(q.eligible.sum()), "spearman_vs_base": float(rho)}
out["tolerance_sensitivity"] = sens

# 9.1 feature balance: standardised mean difference denied vs best twin (smaller = better), constrained vs global kNN
def smd(pairs, d="denied_id", t="twin_id"):
    A = apps.set_index("app_id"); res = {}
    for f in FEATS:
        x = A.loc[pairs[d], f].to_numpy(float); y = A.loc[pairs[t], f].to_numpy(float)
        if f in LOGF: x, y = np.log(np.where(x > 0, x, np.nan)), np.log(np.where(y > 0, y, np.nan))
        sd = np.nanstd(np.concatenate([x, y])); res[f] = float(np.nanmean(x - y) / sd) if sd else 0.0
    return res
b1 = base_t[(base_t["rank"] == 1) & base_t.quality.eq("strong")]
bk = baseline_global_knn(apps); bk = bk[bk["rank"] == 1]
out["balance_smd"] = {"constrained_lender_strong": smd(b1), "baseline_global_knn": smd(bk)}
out["baseline_same_lender_share"] = float(bk.merge(apps[["app_id", "lei"]], left_on="denied_id", right_on="app_id")
    .merge(apps[["app_id", "lei"]], left_on="twin_id", right_on="app_id", suffixes=("_d", "_t")).pipe(lambda m: (m.lei_d == m.lei_t).mean()))

# 9.4 SYNTHETIC injection: perturb real approved apps (+-1-3%), relabel as denied, add to data, see queue rank
rng = np.random.default_rng(0)
src = apps[(apps.outcome == "approved") & (apps.completeness == 1)].sample(300, random_state=0).copy()
for f in ["income", "loan_amount", "property_value"]: src[f] *= rng.uniform(0.97, 1.03, len(src))
for f in ["dti", "ltv"]: src[f] += rng.uniform(-1, 1, len(src))
src["outcome"] = "denied"; src["app_id"] = "SYN" + src.app_id.str[:7]
aug = pd.concat([apps, src], ignore_index=True)
qa = build_queue(aug, find_twins(aug, "lender"))
real = qa[~qa.index.str.startswith("SYN")]; syn = qa[qa.index.str.startswith("SYN")]
pct = qa.priority.rank(pct=True, na_option="bottom")
out["synthetic_injection"] = {"n": len(syn), "share_in_queue": float(syn.eligible.mean()),
    "median_priority_syn": float(syn.priority.median()), "median_priority_real": float(real.priority.median()),
    "share_syn_above_real_median": float((syn.priority > real.priority.median()).mean())}

# 9.5 in-process latency of the analyse path (re-run on LinuxONE for the headline number)
from fastapi.testclient import TestClient
from src.api.main import app
c = TestClient(app); lei = base_q.lei.iloc[0]; ts = []
for _ in range(200):
    s = time.perf_counter(); c.post("/analyse-application", json={"lei": lei, "income": 90, "loan_amount": 280000, "dti": 35, "ltv": 79, "property_value": 355000}); ts.append((time.perf_counter() - s) * 1e3)
out["latency_inprocess_ms"] = {"median": float(np.median(ts)), "p95": float(np.percentile(ts, 95)), "n": 200}
json.dump(out, open("data/processed/eval_results.json", "w"), indent=1); print(json.dumps(out, indent=1))
