"""Reason-aware review: compare a denial's STATED reasons with the matched approved comparators on the fields HMDA reports.
Deterministic and evidence-bound. It never decides a denial was unfair: it says whether the reported data distinguishes the case
from its approved comparators, or whether the reason cannot be assessed with public data. Reasons are context only, never used for matching."""
import statistics
from src.explainability.reviewer_notes import DENIAL, DISCLAIMER, LABEL, make_note

NOT_ASSESSABLE = {"2": "employment history is not in public HMDA", "3": "credit history / credit score is not in public HMDA",
                  "6": "document verification outcomes are not in public HMDA", "7": "application completeness is not in public HMDA",
                  "8": "mortgage-insurance decisions are not in public HMDA", "9": "'other' is not specified in public HMDA"}
EVIDENCE = {"1": "Verified income and debt documentation and the lender's debt-to-income calculation",
            "2": "Employment verification and history", "3": "Credit report/score and the guideline threshold the lender applied",
            "4": "Appraisal and collateral valuation", "5": "Asset and cash-to-close verification",
            "6": "The documents that could not be verified and the verification notes",
            "7": "Which application items were missing and whether the applicant was notified",
            "8": "The mortgage insurer's decision record", "9": "The detail behind 'other' in the adverse-action notice"}
GENERIC_EVIDENCE = ["The lender's written underwriting guideline for this loan product", "Any automated-underwriting recommendation received for this application"]
THRESH = 3.0  # points of DTI / LTV that count as a visible difference (feature tolerance is 5)


def _med(twins, f):
    v = [t[f] for t in twins if t.get(f) is not None]
    return statistics.median(v) if v else None


def _cmp(app, twins, f, name):
    a, m = app.get(f), _med(twins, f)
    if a is None or m is None:
        return "Cannot assess (field not reported)", f"{name} not reported for the application or its comparators"
    d = a - m
    txt = f"applicant {name} {a:g} vs comparators' median {m:g} ({d:+.1f})"
    if app.get("dti_is_bracket") and f == "dti": txt += "; DTI was reported as a bracket, midpoint used"
    if d >= THRESH: return "Consistent with reported data", txt
    if d <= -THRESH: return "Not supported by reported data", txt + " - applicant is lower, not higher"
    return "Not distinguished by reported data", txt + " - similar to approved comparators"


def reason_review(app: dict, twins: list, reason_codes: list) -> dict:
    items = []
    for c in reason_codes or []:
        if c in ("1", "4", "5"):
            f, name = ("dti", "debt-to-income") if c == "1" else ("ltv", "loan-to-value")
            status, detail = _cmp(app, twins, f, name)
            if c == "5": detail += "; assets/cash are not reported, LTV is only a weak proxy"; status = "Partially assessable: " + status
            if c == "4": detail += "; appraisal details are not reported"
            items.append({"reason": DENIAL.get(c, c), "code": c, "status": status, "detail": detail})
        elif c == "10":
            continue
        else:
            items.append({"reason": DENIAL.get(c, c), "code": c, "status": "Not assessable with public data", "detail": NOT_ASSESSABLE.get(c, "not in public HMDA")})
    evid = [EVIDENCE[c] for c in (reason_codes or []) if c in EVIDENCE] + GENERIC_EVIDENCE
    n_ass = sum(1 for i in items if not i["status"].startswith(("Not assessable", "Cannot")))
    n_dist = sum(1 for i in items if i["status"].startswith(("Consistent", "Partially assessable: Consistent")))
    if not items: summary = "No stated denial reason was reported for this application."
    else:
        summary = (f"{len(items)} stated reason(s); {n_ass} can be checked against public fields; reported data distinguishes the applicant from approved comparators "
                   f"on {n_dist} of them. This is an evidence check, not a finding about the decision.")
    return {"items": items, "summary": summary, "evidence_to_request": list(dict.fromkeys(evid))}


QUESTIONS = {"why_flagged": "Why was this application flagged?", "what_could_explain": "What differences could explain the denial?",
             "missing_info": "What missing information limits the comparison?", "evidence_to_request": "What evidence should a reviewer request?",
             "reason_consistency": "Are the stated denial reasons consistent with the reported data?"}


def answer(qid: str, case: dict) -> str:
    """Grounded answers assembled from structured results only (no free-form generation)."""
    rr, rec = case["reason_review"], case["note_rec"]
    if qid == "why_flagged": return make_note(rec)
    if qid == "reason_consistency":
        return rr["summary"] + " " + " ".join(f"[{i['reason']}: {i['status']} - {i['detail']}]" for i in rr["items"])
    if qid == "evidence_to_request": return "Suggested evidence to request: " + "; ".join(rr["evidence_to_request"]) + "."
    if qid == "missing_info":
        miss = ", ".join(LABEL.get(m, m) for m in rec["missing"]) or "none of the six matching fields"
        return (f"Not reported for this application: {miss}. Public HMDA also omits credit scores, assets, employment history, documentation completeness, "
                f"and the lender's policy overlays. {DISCLAIMER}")
    if qid == "what_could_explain":
        diffs = [f"{i['reason']}: {i['detail']}" for i in rr["items"] if i["status"].startswith(("Consistent", "Partially assessable: Consistent"))]
        s = ("Differences visible in reported data: " + "; ".join(diffs) + ". ") if diffs else "The reported financial fields do not visibly distinguish this application from its approved comparators. "
        return s + "Factors that could legitimately explain a different outcome but are absent from public data: credit score, assets/cash to close, employment history, document verification, property appraisal, and lender policy overlays. " + DISCLAIMER
    raise KeyError(qid)
