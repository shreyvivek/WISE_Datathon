"""Deterministic reviewer notes built only from structured results (no free generation, no invented facts)."""
from src.models.financial_twins import FEATS

LABEL = {"income": "income", "loan_amount": "loan amount", "dti": "debt-to-income ratio",
         "ltv": "loan-to-value ratio", "property_value": "property value", "loan_term": "loan term"}
DISCLAIMER = ("Public HMDA records omit credit scores, employment history and other underwriting inputs, so an observed "
              "difference in outcome does not establish that the decision was incorrect or improper.")


def make_note(rec: dict) -> str:
    """rec: {quality, n_strong, n_candidates, dist, same_lender, missing: [feature,...], denial_reasons: [str,...]}"""
    if rec["quality"] not in ("strong", "moderate"):
        return ("Insufficient comparable evidence: no approved application from the same lender is sufficiently close "
                "on the reported financial characteristics. This case is not prioritised. " + DISCLAIMER)
    scope = "the same lender" if rec["same_lender"] else "other lenders"
    s = (f"Selected for additional review because {rec['n_strong']} approved application(s) from {scope} "
         f"(out of {rec['n_candidates']} candidates) have closely comparable reported income, loan amount, "
         f"debt-to-income and loan-to-value characteristics (best match quality: {rec['quality']}, "
         f"average scaled distance {rec['dist']:.2f}) but received a different outcome. ")
    if rec.get("missing"):
        s += "Not reported for this application: " + ", ".join(LABEL.get(m, m) for m in rec["missing"]) + ". "
    if rec.get("denial_reasons"):
        s += "Stated denial reason(s): " + "; ".join(rec["denial_reasons"]) + ". "
    return s + DISCLAIMER
