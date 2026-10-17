"""Does SecondLook's prioritisation surface known inconsistencies better than baselines?  *** SYNTHETIC EXPERIMENT ***
Known positives: 200 REAL approved applications are copied with small perturbations and relabelled 'denied' (an injected inconsistent decision:
a near-identical application from the same lender that was approved). They are ranked together with the 2,600 REAL denials.
Methods: random | baseline B (global nearest approved, no constraints) | baseline A (same-lender nearest approved, plain standardised Euclid) | SecondLook (constrained matching + review priority score).
Metrics: Precision@K and Recall@K for the injected cases. This is a sanity check, NOT validation on wrongful denials (no ground truth exists); real denials that also have
near-duplicate approved applications compete for the top ranks, which lowers precision by design."""
import json
import numpy as np, pandas as pd
from src.models.financial_twins import find_twins, baseline_global_knn, FEATS, LOGF
from src.models.prioritisation import build_queue

apps = pd.read_parquet("data/processed/applications.parquet")
KS = [50, 100, 200, 400]; N_SYN = 200
LEVELS = {"easy (1-3% perturbation)": (0.01, 0.03, 1.0), "harder (6-12% perturbation)": (0.06, 0.12, 3.0)}


def inject(seed, lo, hi, pts):
    rng = np.random.default_rng(seed)
    src = apps[(apps.outcome == "approved") & (apps.completeness == 1)].sample(N_SYN, random_state=seed).copy()
    for f in ["income", "loan_amount", "property_value"]:
        src[f] = src[f] * (1 + rng.choice([-1, 1], len(src)) * rng.uniform(lo, hi, len(src)))
    for f in ["dti", "ltv"]:
        src[f] = src[f] + rng.choice([-1, 1], len(src)) * rng.uniform(0.3 * pts, pts, len(src))
    src["outcome"] = "denied"; src["app_id"] = "SYN" + src.app_id.str[:7]
    return pd.concat([apps, src], ignore_index=True)


def zmat(df):
    X = df[FEATS].copy()
    for f in LOGF: X[f] = np.log(X[f].where(X[f] > 0))
    return X


def baseline_a(aug):
    """Same-lender nearest approved, plain standardised Euclid, complete cases only. Returns score (higher = more suspicious) per denied id."""
    X = zmat(aug); ok = X.notna().all(axis=1); Z = (X - X[ok].mean()) / X[ok].std()
    out = {}
    for lei, g in aug[ok].groupby("lei"):
        d, a = g[g.outcome == "denied"], g[g.outcome == "approved"]
        if d.empty or a.empty: continue
        D = np.linalg.norm(Z.loc[d.index].to_numpy()[:, None, :] - Z.loc[a.index].to_numpy()[None, :, :], axis=2).min(1)
        out.update(dict(zip(d.app_id, -D)))
    return out


def prec_rec(order, positives):
    r = {}
    for k in KS:
        hit = sum(1 for i in order[:k] if i in positives); r[k] = (hit / k, hit / len(positives))
    return r


rows = []
for level, (lo, hi, pts) in LEVELS.items():
    for seed in range(5):
        aug = inject(seed, lo, hi, pts); den_ids = aug[aug.outcome == "denied"].app_id.tolist(); pos = {i for i in den_ids if i.startswith("SYN")}
        rng = np.random.default_rng(100 + seed); orders = {"random": list(rng.permutation(den_ids))}
        q = build_queue(aug, find_twins(aug, "lender")); orders["SecondLook (constrained + priority score)"] = q.sort_values("rank").index.tolist()
        qq = q.reset_index().assign(_d=lambda d: d.dist.where(d.eligible, np.inf).fillna(np.inf)).sort_values(["_d", "n_candidates"], ascending=[True, False])
        orders["SecondLook variant: tightest constrained match first"] = qq.app_id.tolist()
        bb = baseline_global_knn(aug); bb = bb[bb["rank"] == 1].set_index("denied_id").dist
        orders["Baseline B: global nearest approved"] = sorted(den_ids, key=lambda i: (bb.get(i, np.inf), rng.random()))
        sa = baseline_a(aug); orders["Baseline A: same-lender nearest (Euclid)"] = sorted(den_ids, key=lambda i: (-sa.get(i, -np.inf), rng.random()))
        for m, o in orders.items():
            for k, (p, r) in prec_rec(o, pos).items(): rows.append({"level": level, "method": m, "seed": seed, "K": k, "precision": p, "recall": r})
df = pd.DataFrame(rows)
agg = df.groupby(["level", "method", "K"])[["precision", "recall"]].agg(["mean", "std"]).round(3)
res = {"label": "SYNTHETIC experiment: injected near-duplicate-of-approved 'denials' among real denials; sanity check, not validation on real wrongful denials",
       "n_injected": N_SYN, "n_real_denied": int((apps.outcome == "denied").sum()), "seeds": 5, "ks": KS, "results": {}}
for (lv, m, k), r in agg.iterrows():
    res["results"].setdefault(lv, {}).setdefault(m, {})[str(k)] = {"precision_mean": r[("precision", "mean")], "precision_sd": r[("precision", "std")],
                                                                    "recall_mean": r[("recall", "mean")], "recall_sd": r[("recall", "std")]}
q0 = build_queue(apps, find_twins(apps, "lender"))
ref = apps[apps.outcome == "denied"]; q_ref = build_queue(apps, find_twins(apps, "lender"))
res["ceiling_note"] = {"real_denials_with_best_dist_le_0.15": int((q_ref.dist <= 0.15).sum()),
    "meaning": "Real denials that already have a near-duplicate approved comparator compete with the injected cases and count as misses in injected-only precision, so P@K has a ceiling well below 1."}
res["triage"] = {"real_denials": int((apps.outcome == "denied").sum()), "queued": int(q0.eligible.sum()), "not_queued_insufficient_evidence": int((~q0.eligible).sum()),
                 "note": "Review time and real workload savings were NOT measured."}
json.dump(res, open("data/processed/ranking_eval.json", "w"), indent=1)
for lv in res["results"]:
    print("\n==", lv)
    for m, d in res["results"][lv].items(): print(f"  {m:46s}", "  ".join(f"P@{k}={d[str(k)]['precision_mean']:.2f} R@{k}={d[str(k)]['recall_mean']:.2f}" for k in (100, 200, 400)))
