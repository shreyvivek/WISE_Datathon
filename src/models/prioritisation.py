"""Transparent Review Priority Score (0-100). Measures how useful a case is for human comparison,
NOT the likelihood of an incorrect or unlawful denial. Components are stored so the UI can show them."""
import pandas as pd

W = {"match_strength": 40, "n_strong_comparators": 20, "same_lender": 20, "completeness": 20}


def build_queue(apps: pd.DataFrame, twins_lender: pd.DataFrame) -> pd.DataFrame:
    den = apps[apps.outcome == "denied"].set_index("app_id")
    t = twins_lender
    best = t[t["rank"] == 1].set_index("denied_id")
    n_strong = t[t.quality == "strong"].groupby("denied_id").size()
    q = den[["lei", "county_code", "completeness"]].join(best[["dist", "max_diff", "quality", "n_candidates"]])
    q["n_strong"] = n_strong.reindex(q.index).fillna(0).astype(int)
    q["eligible"] = q.quality.isin(["strong", "moderate"])
    q["c_match"] = W["match_strength"] * (1 - q.dist.clip(upper=1.25) / 1.25).fillna(0)
    q["c_count"] = W["n_strong_comparators"] * (q.n_strong / 3)
    q["c_lender"] = W["same_lender"] * q.eligible
    q["c_complete"] = W["completeness"] * q.completeness
    q["priority"] = (q.c_match + q.c_count + q.c_lender + q.c_complete).round(1)
    q.loc[~q.eligible, "priority"] = float("nan")
    q["status"] = q.eligible.map({True: "Pending review", False: "Insufficient comparable evidence"})
    # deterministic tie-break: more same-lender candidates, then completeness, then id (round-number loans tie at 100)
    q = q.reset_index().sort_values(["priority", "n_candidates", "completeness", "app_id"],
                                   ascending=[False, False, False, True], na_position="last").set_index("app_id")
    q["rank"] = range(1, len(q) + 1)
    return q
