"""Sensitivity of matched gaps to matching restrictions + proxy check. Observed disparity only."""
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import roc_auc_score
from src.fairness.matching_audit import disparity

apps = pd.read_parquet("data/processed/applications.parquet"); audit = pd.read_parquet("data/processed/audit_only.parquet")
specs = [("base: lender, strong, x1", {}), ("lender+moderate", {"min_quality": ("strong", "moderate")}),
         ("tolerances x0.5", {"tol_mult": 0.5}), ("tolerances x2", {"tol_mult": 2.0}),
         ("lender+MSA", {"keys": ("lei", "msa")}), ("market (MSA, cross-lender)", {"keys": ("msa",)})]
rows = []
for g in ["Black or African American", "Asian"]:
    for name, kw in specs:
        r = disparity(apps, audit, g, n_boot=500, **kw)
        rows.append({"group": g[:5], "spec": name, "n_matched": r["n_matched"], "coverage": round(r["coverage"], 2),
                     "matched_gap_pp": round(r["matched_gap_pp"], 2), "ci": f"({r['matched_ci'][0]:.1f}, {r['matched_ci'][1]:.1f})"})
res = pd.DataFrame(rows); res.to_csv("data/processed/fairness_sensitivity.csv", index=False); print(res.to_string(index=False))

# proxy check: can location + financial features predict race (Black vs White)? AUC well above 0.5 => location/finance partly proxy race
d = apps.merge(audit[["app_id", "race"]], on="app_id"); d = d[d.race.isin(["White", "Black or African American"])]
y = (d.race != "White").astype(int)
def auc(X): return roc_auc_score(y, cross_val_predict(LogisticRegression(max_iter=300), X, y, cv=5, method="predict_proba")[:, 1])
fin = d[["income", "loan_amount", "dti", "ltv", "property_value", "loan_term"]]; fin = ((fin - fin.mean()) / fin.std()).fillna(0)
geo = pd.get_dummies(d.county_code)
print(f"\nproxy AUC (predict Black vs White): financial only {auc(fin):.3f} | county only {auc(geo.astype(float)):.3f} | both {auc(pd.concat([fin, geo], axis=1).astype(float)):.3f}")
