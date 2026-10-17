"""Deterministic reviewer notes built only from structured results (no free generation, no invented facts)."""
from src.models.financial_twins import FEATS

LABEL = {"income": "income", "loan_amount": "loan amount", "dti": "debt-to-income ratio",
         "ltv": "loan-to-value ratio", "property_value": "property value", "loan_term": "loan term"}
DENIAL = {"1": "debt-to-income ratio", "2": "employment history", "3": "credit history", "4": "collateral", "5": "insufficient cash",
          "6": "unverifiable information", "7": "incomplete credit application", "8": "mortgage insurance denied", "9": "other"}
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


# ---- Granite (base model, raw completion) support -------------------------------------------------------------
import json
import re

FORBIDDEN = ("discriminat", "racis", "illegal", "unlawful", "wrongful", "wrongly", "biased", "violat", "fraud", "should have been approved")
FEWSHOT = [
    ({"outcome_under_review": "denied", "same_lender": True, "comparable_approved_in_lender": 212, "strong_matches": 3,
      "best_match_quality": "strong", "avg_scaled_distance": 0.31, "fields_compared": ["income", "loan amount", "debt-to-income", "loan-to-value"],
      "fields_not_reported": [], "stated_denial_reasons": ["credit history"]},
     "This denied application was queued because 3 approved applications from the same lender, out of 212 candidates, report closely similar income, loan amount, debt-to-income and loan-to-value. The stated denial reason was credit history."),
    ({"outcome_under_review": "denied", "same_lender": True, "comparable_approved_in_lender": 48, "strong_matches": 1,
      "best_match_quality": "moderate", "avg_scaled_distance": 0.96, "fields_compared": ["income", "loan amount", "loan-to-value"],
      "fields_not_reported": ["debt-to-income"], "stated_denial_reasons": []},
     "This denied application was queued because 1 approved application from the same lender, out of 48 candidates, reports moderately similar income, loan amount and loan-to-value. Debt-to-income was not reported for this application, which limits the comparison."),
]


def facts_for(rec: dict) -> dict:
    compared = [LABEL[f] for f in FEATS if LABEL[f] not in [LABEL.get(m, m) for m in rec.get("missing", [])]]
    return {"outcome_under_review": "denied", "same_lender": bool(rec["same_lender"]), "comparable_approved_in_lender": int(rec["n_candidates"]),
            "strong_matches": int(rec["n_strong"]), "best_match_quality": rec["quality"], "avg_scaled_distance": round(float(rec["dist"]), 2),
            "fields_compared": compared, "fields_not_reported": [LABEL.get(m, m) for m in rec.get("missing", [])],
            "stated_denial_reasons": [r for r in rec.get("denial_reasons", [])]}


def build_prompt(facts: dict) -> str:
    head = "Write a short, neutral note explaining why a denied mortgage application was queued for human review, using only the facts given.\n\n"
    shots = "".join(f"FACTS: {json.dumps(f)}\nNOTE: {n}\n\n" for f, n in FEWSHOT)
    return head + shots + f"FACTS: {json.dumps(facts)}\nNOTE:"


def validate_llm(text: str, facts: dict) -> tuple[bool, str]:
    """Reject anything not grounded in the facts: invented numbers, accusatory language, or odd length."""
    t = text.strip()
    if not 40 <= len(t) <= 700 or not t.endswith("."):
        return False, "length/format"
    low = t.lower()
    if any(w in low for w in FORBIDDEN):
        return False, "forbidden wording"
    allowed = set(re.findall(r"\d+(?:\.\d+)?", json.dumps(facts)))
    extra = set(re.findall(r"\d+(?:\.\d+)?", t)) - allowed
    if extra:
        return False, f"numbers not in facts: {sorted(extra)}"
    return True, "ok"


def finalize(llm_text: str | None, rec: dict) -> dict:
    """Granite text if it validates, else deterministic template; fixed disclaimer is always appended."""
    facts = facts_for(rec)
    if llm_text:
        ok, why = validate_llm(llm_text, facts)
        if ok:
            text = llm_text.strip()
            if rec.get("missing") and "not reported" not in text.lower():  # missing information must always be stated
                text += " Not reported for this application: " + ", ".join(LABEL.get(m, m) for m in rec["missing"]) + "."
            return {"generator": "granite-4.0-h-350m-base", "validation": why, "note": text + " " + DISCLAIMER}
        return {"generator": "deterministic-template", "validation": f"granite output rejected: {why}", "note": make_note(rec)}
    return {"generator": "deterministic-template", "validation": "granite unavailable", "note": make_note(rec)}
