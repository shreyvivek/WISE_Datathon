"""Constrained financial-twin discovery. Reads ONLY applications.parquet (no demographic columns).

Similarity definition (not a probability):
  For each feature f present in both applications, scaled difference d_f = |a_f - b_f| / tol_f
  (log-ratio for dollar amounts, absolute points for DTI/LTV/term). Match distance = mean(d_f) over shared
  features; max_diff = max(d_f). A pair needs >= MIN_SHARED shared features including loan_amount.
  Quality: strong (dist<=0.75 & max<=2), moderate (dist<=1.25 & max<=3), else weak.
  Distance 1.0 means "differs by one tolerance on average" - it says nothing about whether the loan should be approved.
"""
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

FEATS = ["income", "loan_amount", "dti", "ltv", "property_value", "loan_term"]
LOGF = {"income", "loan_amount", "property_value"}
TOL = {"income": 0.15, "loan_amount": 0.10, "dti": 5.0, "ltv": 5.0, "property_value": 0.10, "loan_term": 60.0}
MIN_SHARED = 4
SCOPES = {"lender": ["lei"], "lender_msa": ["lei", "msa"], "market": ["msa"]}  # + "global" baseline handled separately


@dataclass
class Params:
    tol: dict = field(default_factory=lambda: dict(TOL))
    min_shared: int = MIN_SHARED
    k: int = 3


def _matrix(df: pd.DataFrame, tol: dict) -> np.ndarray:
    cols = []
    for f in FEATS:
        v = df[f].to_numpy(float)
        cols.append(np.log(np.where(v > 0, v, np.nan)) / tol[f] if f in LOGF else v / tol[f])
    return np.stack(cols, axis=1)  # features already divided by tol, so |diff| is the scaled diff


def quality(dist, mx):
    return np.where((dist <= 0.75) & (mx <= 2), "strong", np.where((dist <= 1.25) & (mx <= 3), "moderate", "weak"))


def find_twins(apps: pd.DataFrame, scope: str = "lender", params: Params | None = None) -> pd.DataFrame:
    p = params or Params()
    keys = SCOPES[scope]
    den = apps[apps.outcome == "denied"]
    app = apps[apps.outcome == "approved"]
    out = []
    for gk, dg in den.groupby(keys, dropna=True):
        ag = app
        for k_, v in zip(keys, gk if isinstance(gk, tuple) else (gk,)):
            ag = ag[ag[k_] == v]
        if ag.empty:
            continue
        A, D = _matrix(ag, p.tol), _matrix(dg, p.tol)
        a_ids, d_ids = ag.app_id.to_numpy(), dg.app_id.to_numpy()
        for s in range(0, len(D), 200):
            diff = np.abs(D[s:s + 200, None, :] - A[None, :, :])          # (nd, na, F)
            valid = ~np.isnan(diff)
            nsh = valid.sum(2)
            ok = nsh >= p.min_shared
            ok &= valid[:, :, FEATS.index("loan_amount")]
            dsum = np.where(valid, diff, 0).sum(2)
            dist = np.where(ok, dsum / np.maximum(nsh, 1), np.inf)
            mx = np.where(valid, diff, 0).max(2)
            kk = min(p.k, dist.shape[1])
            idx = np.argpartition(dist, kk - 1, axis=1)[:, :kk]
            for i in range(dist.shape[0]):
                for j in idx[i][np.argsort(dist[i, idx[i]])]:
                    if np.isfinite(dist[i, j]):
                        out.append((d_ids[s + i], a_ids[j], dist[i, j], mx[i, j], nsh[i, j], len(ag)))
    r = pd.DataFrame(out, columns=["denied_id", "twin_id", "dist", "max_diff", "n_shared", "n_candidates"])
    if r.empty:
        return r
    r["quality"] = quality(r.dist.to_numpy(), r.max_diff.to_numpy())
    r["rank"] = r.groupby("denied_id").cumcount() + 1
    r["scope"] = scope
    return r


def baseline_global_knn(apps: pd.DataFrame, k: int = 3) -> pd.DataFrame:
    """Baseline B: unconstrained nearest neighbours on globally standardised numerics (complete cases only)."""
    from sklearn.neighbors import NearestNeighbors
    X = apps[FEATS].copy()
    for f in LOGF:
        X[f] = np.log(X[f].where(X[f] > 0))
    ok = X.notna().all(axis=1)
    Z = (X - X[ok].mean()) / X[ok].std()
    a, d = apps[ok & (apps.outcome == "approved")], apps[ok & (apps.outcome == "denied")]
    nn = NearestNeighbors(n_neighbors=k).fit(Z.loc[a.index])
    dist, idx = nn.kneighbors(Z.loc[d.index])
    rows = [(d.app_id.iloc[i], a.app_id.iloc[j], dist[i, r], r + 1) for i in range(len(d)) for r, j in enumerate(idx[i])]
    return pd.DataFrame(rows, columns=["denied_id", "twin_id", "dist", "rank"])


def best_per_denied(r: pd.DataFrame) -> pd.DataFrame:
    return r[r["rank"] == 1].set_index("denied_id")
