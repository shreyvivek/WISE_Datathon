"""MODEL SENSITIVITY ANALYSIS (exploratory; NOT proof of causation and NOT a credit model).
Model A: predict the HISTORICAL decision from financial features + lender + county (no demographics).
Model B: Model A + race/ethnicity/sex/age (audit only).
Compares performance and predicted denial rates by group. Historical decisions are not ground truth; omitting race does not remove proxies;
a change in predictions when race is added does not show the lender used race.
Runs on the LinuxONE container (xgboost 3.4.1) when --xgb is given."""
import json, sys, time
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, precision_score, recall_score
from sklearn.calibration import calibration_curve

FIN = ["income", "loan_amount", "dti", "ltv", "property_value", "loan_term"]
GROUPS = ["White", "Black or African American", "Asian"]


def load(name):
    try:
        return pd.read_parquet(f"data/processed/{name}.parquet")
    except ImportError:  # no pyarrow (LinuxONE container): gz CSV from scripts/export_csv.py
        return pd.read_csv(f"data/processed/{name}.csv.gz", dtype=str if name == "audit_only" else {"app_id": str, "lei": str, "county_code": str, "outcome": str, "census_tract": str, "msa": str}, keep_default_na=False, na_values=[""])


def design(d: pd.DataFrame, demo: bool) -> pd.DataFrame:
    X = d[FIN].copy()
    for f in ["income", "loan_amount", "property_value"]:
        X[f] = np.log(X[f].where(X[f] > 0))
    X["income_na"] = X.income.isna().astype(int); X["dti_na"] = X.dti.isna().astype(int); X["ltv_na"] = X.ltv.isna().astype(int)
    X = X.fillna(X.median())
    X = (X - X.mean()) / X.std().replace(0, 1)
    cat = ["lei", "county_code"] + (["race", "ethnicity", "sex", "age"] if demo else [])
    # lender dummies restricted to lenders with >=50 applications to keep the model stable
    D = d[cat].copy(); D["lei"] = D.lei.where(D.lei.map(D.lei.value_counts()) >= 50, "other")
    Z = pd.concat([X, pd.get_dummies(D, dtype=float)], axis=1)
    Z.columns = [c.replace("<", "lt").replace(">", "gt").replace("[", "(").replace("]", ")") for c in Z.columns]  # xgboost name rules
    return Z


def make_model(kind):
    if kind == "xgb":
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.08, subsample=0.8, colsample_bytree=0.8, n_jobs=3, eval_metric="logloss")
    return LogisticRegression(max_iter=500, C=0.5)


def oof_predict(X, y, kind, seed=0):
    p = np.zeros(len(y))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(X, y):
        m = make_model(kind).fit(X.iloc[tr], y.iloc[tr]); p[te] = m.predict_proba(X.iloc[te])[:, 1]
    return p


def main(kind="logreg"):
    apps, audit = load("applications"), load("audit_only")
    d = apps.merge(audit, on="app_id"); d = d[d.race.isin(GROUPS)].reset_index(drop=True)
    y = (d.outcome == "denied").astype(int); t = time.perf_counter()
    pa, pb = oof_predict(design(d, False), y, kind), oof_predict(design(d, True), y, kind); secs = time.perf_counter() - t
    thr = np.quantile(pa, 1 - y.mean())  # threshold giving the same overall predicted-denial share as the base rate
    out = {"model": kind, "n": len(d), "base_denial_rate": float(y.mean()), "train_eval_seconds": round(secs, 1),
           "overall": {m: {"roc_auc": float(roc_auc_score(y, p)), "precision@base_rate": float(precision_score(y, p >= np.quantile(p, 1 - y.mean()))),
                           "recall@base_rate": float(recall_score(y, p >= np.quantile(p, 1 - y.mean())))} for m, p in [("A_no_demographics", pa), ("B_with_demographics", pb)]},
           "calibration_A": [list(map(float, c)) for c in calibration_curve(y, pa, n_bins=5, strategy="quantile")],
           "by_group": {}}
    for g in GROUPS:
        m = (d.race == g).to_numpy()
        out["by_group"][g] = {"n": int(m.sum()), "actual_denial_rate": float(y[m].mean()), "mean_pred_A": float(pa[m].mean()), "mean_pred_B": float(pb[m].mean()),
                              "auc_A": float(roc_auc_score(y[m], pa[m])), "auc_B": float(roc_auc_score(y[m], pb[m])),
                              "mean_abs_pred_shift": float(np.abs(pb[m] - pa[m]).mean()), "mean_signed_shift_B_minus_A": float((pb[m] - pa[m]).mean())}
    out["note"] = "Exploratory model sensitivity analysis on historical decisions; not evidence that any lender used race."
    json.dump(out, open(f"data/processed/model_sensitivity_{kind}.json", "w"), indent=1); print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "logreg")
