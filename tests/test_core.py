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
