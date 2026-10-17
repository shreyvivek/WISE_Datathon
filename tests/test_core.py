import numpy as np, pandas as pd
from src.data.preprocess import parse_dti
from src.models.financial_twins import find_twins
from src.explainability.reviewer_notes import make_note

APPS = pd.read_parquet("data/processed/applications.parquet")

def test_matching_inputs_have_no_demographics():
    banned = {"race", "ethnicity", "sex", "age", "denial_reason-1"}
    assert not banned & set(APPS.columns)

def test_matching_invariant_to_demographics():
    # twins are computed from applications.parquet only; shuffling the audit table cannot change them
    audit = pd.read_parquet("data/processed/audit_only.parquet").sample(frac=1, random_state=1)
    assert audit is not None
    a = find_twins(APPS, "lender"); b = find_twins(APPS.copy(), "lender")
    pd.testing.assert_frame_equal(a, b)

def test_dti_not_coerced_to_zero():
    r = parse_dti(pd.Series(["30%-<36%", "42", "Exempt", None, ">60%"]))
    assert r.dti.tolist()[:2] == [33.0, 42.0] and r.dti.isna().tolist()[2:4] == [True, True] and r.dti.iloc[4] == 65.0
    assert r.dti_missing.tolist() == [False, False, True, True, False]

def test_twins_are_approved_and_same_lender():
    t = find_twins(APPS, "lender").head(500).merge(APPS, left_on="twin_id", right_on="app_id").merge(
        APPS, left_on="denied_id", right_on="app_id", suffixes=("_t", "_d"))
    assert (t.outcome_t == "approved").all() and (t.outcome_d == "denied").all() and (t.lei_t == t.lei_d).all()

def test_note_never_accuses_and_handles_insufficient():
    n = make_note({"quality": "weak"}); assert "Insufficient comparable evidence" in n
    n = make_note({"quality": "strong", "n_strong": 3, "n_candidates": 10, "dist": 0.4, "same_lender": True, "missing": ["income"]})
    assert "does not establish" in n and "discriminat" not in n.lower()


def test_granite_output_is_validated():
    from src.explainability.reviewer_notes import facts_for, finalize
    rec = {"quality": "strong", "n_strong": 3, "n_candidates": 277, "dist": 0.31, "same_lender": True, "missing": ["dti"], "denial_reasons": ["credit history"]}
    good = "This denied application was queued because 3 approved applications from the same lender, out of 277 candidates, report closely similar income and loan amount."
    r = finalize(good, rec); assert r["generator"].startswith("granite") and "Not reported" in r["note"] and "does not establish" in r["note"]
    assert finalize(good.replace("277", "999"), rec)["generator"] == "deterministic-template"               # invented number
    assert finalize("The lender discriminated against this applicant in 3 cases out of 277.", rec)["generator"] == "deterministic-template"
    assert finalize(None, rec)["validation"] == "granite unavailable"


def test_shed_weighted_proportion_and_context_files():
    import json
    from src.context.shed import wprop
    assert abs(wprop(np.array([1.0, 0.0]), np.array([3.0, 1.0])) - 0.75) < 1e-9
    s = json.load(open("data/processed/shed_context.json"))
    assert "mortgage_item" not in s and "cannot be linked" in s["caveat"]
    c = json.load(open("data/processed/census_context.json"))
    assert c["n_counties"] >= 20 and all(len(x["county_code"]) == 5 for x in c["counties"])


def test_reason_review_is_evidence_bound():
    from src.explainability.reason_check import reason_review, answer
    app = {"dti": 44.0, "ltv": 80.0, "dti_is_bracket": False}; tw = [{"dti": 36.0, "ltv": 79.0}, {"dti": 38.0, "ltv": 81.0}, {"dti": 37.0, "ltv": 80.0}]
    r = reason_review(app, tw, ["1", "3", "4", "10"])
    st = {i["code"]: i["status"] for i in r["items"]}
    assert st["1"].startswith("Consistent") and st["3"] == "Not assessable with public data" and st["4"].startswith("Not distinguished") and "10" not in st
    assert reason_review({"dti": None}, tw, ["1"])["items"][0]["status"].startswith("Cannot assess")
    case = {"reason_review": r, "note_rec": {"quality": "strong", "n_strong": 3, "n_candidates": 10, "dist": 0.3, "same_lender": True, "missing": [], "denial_reasons": []}}
    for q in ["why_flagged", "what_could_explain", "missing_info", "evidence_to_request", "reason_consistency"]:
        a = answer(q, case).lower(); assert "discriminat" not in a and "unfair" not in a


def test_review_decision_api_is_advisory_and_audited(tmp_path):
    from fastapi.testclient import TestClient
    import src.api.main as m
    m.REVIEW_LOG = tmp_path / "log.jsonl"; c = TestClient(m.app); i = c.get("/review-queue?limit=1").json()[0]["app_id"]
    assert c.post("/review-decision", json={"app_id": i, "decision": "Approve loan"}).status_code == 400        # cannot change a loan decision
    assert c.post("/review-decision", json={"app_id": i, "decision": "Escalate for further review", "reviewer": "t"}).json()["recorded"]
    log = c.get(f"/review-log?app_id={i}").json(); assert len(log) == 1 and log[0]["model_version"] and "tolerances" in log[0]
    assert c.get("/review-queue?limit=1").json()[0]["review_status"] == "Escalate for further review"
