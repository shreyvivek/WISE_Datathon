"""Demographic-blind matched disparity analysis.
Step 1 (blind): match every application of group G to the closest White application of the SAME lender using
financial features only (src.models.financial_twins distance). Demographics are not read until step 2.
Step 2 (reveal): compare denial rates between G and its matched White controls; bootstrap CI over G units.
Observed/adjusted disparity only - public HMDA lacks credit scores, so this is not evidence of discrimination."""
import numpy as np
import pandas as pd
from src.models.financial_twins import _matrix, TOL, MIN_SHARED, FEATS, quality


def blind_match_pairs(apps: pd.DataFrame, treated_ids: set, control_ids: set, keys=("lei",), tol=None) -> pd.DataFrame:
    """Financial-only 1-NN (with replacement) within lender from treated ids to control ids."""
    tol = tol or TOL
    rows = []
    apps = apps.assign(_t=apps.app_id.isin(list(treated_ids)), _c=apps.app_id.isin(list(control_ids)))
    for _, g in apps.groupby(list(keys)):
        T, C = g[g._t], g[g._c]
        if T.empty or C.empty:
            continue
        a, b = _matrix(T, tol), _matrix(C, tol)
        for st in range(0, len(a), 200):
            diff = np.abs(a[st:st + 200, None, :] - b[None, :, :]); v = ~np.isnan(diff)
            n = v.sum(2); ok = (n >= MIN_SHARED) & v[:, :, FEATS.index("loan_amount")]
            dist = np.where(ok, np.where(v, diff, 0).sum(2) / np.maximum(n, 1), np.inf)
            mx = np.where(v, diff, 0).max(2)
            j = dist.argmin(1)
            for i in range(len(dist)):
                if np.isfinite(dist[i, j[i]]):
                    rows.append((T.app_id.iloc[st + i], C.app_id.iloc[j[i]], dist[i, j[i]], mx[i, j[i]]))
    r = pd.DataFrame(rows, columns=["treated_id", "control_id", "dist", "max_diff"])
    r["quality"] = quality(r.dist.to_numpy(), r.max_diff.to_numpy())
    return r


def disparity(apps, audit, group, ref="White", n_boot=1000, seed=0, min_quality=("strong",), keys=("lei",), tol_mult=1.0):
    d = apps.merge(audit[["app_id", "race"]], on="app_id")   # reveal happens here, after matching
    den = d.set_index("app_id").outcome.eq("denied")
    tids, cids = set(d[d.race == group].app_id), set(d[d.race == ref].app_id)
    pairs = blind_match_pairs(apps, tids, cids, keys, {k: v * tol_mult for k, v in TOL.items()})
    good = pairs[pairs.quality.isin(min_quality)]
    y_t, y_c = den.loc[good.treated_id].to_numpy(float), den.loc[good.control_id].to_numpy(float)
    raw_t, raw_c = den.loc[sorted(tids)].mean(), den.loc[sorted(cids)].mean()
    rng = np.random.default_rng(seed)
    gaps = np.array([(y_t[i] - y_c[i]).mean() for i in (rng.integers(0, len(y_t), len(y_t)) for _ in range(n_boot))]) \
        if len(y_t) else np.array([np.nan])
    # raw gap CI: bootstrap each group's rows
    rt, rc = den.loc[sorted(tids)].to_numpy(float), den.loc[sorted(cids)].to_numpy(float)
    rg = np.array([rng.choice(rt, len(rt)).mean() - rng.choice(rc, len(rc)).mean() for _ in range(n_boot)])
    return {"group": group, "ref": ref, "n_group": len(tids), "n_ref": len(cids),
            "raw_rate_group": raw_t, "raw_rate_ref": raw_c, "raw_gap_pp": 100 * (raw_t - raw_c),
            "raw_ci": tuple(100 * np.percentile(rg, [2.5, 97.5])),
            "n_matched": len(good), "coverage": len(good) / max(len(tids), 1),
            "matched_rate_group": y_t.mean() if len(y_t) else np.nan, "matched_rate_ref": y_c.mean() if len(y_c) else np.nan,
            "matched_gap_pp": 100 * np.nanmean(y_t - y_c) if len(y_t) else np.nan,
            "matched_ci": tuple(100 * np.nanpercentile(gaps, [2.5, 97.5])),
            "small_sample_warning": len(good) < 200}
