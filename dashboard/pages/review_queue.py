import pandas as pd, streamlit as st
from dashboard.client import call


def render():
    st.header("Second-Look Queue")
    n = st.slider("Rows", 10, 500, 100)
    q = pd.DataFrame(call("GET", "/review-queue", params={"limit": n})[0])
    q["lei"] = q.lei.str[:8] + "…"; q["Loan category"] = "Conventional / purchase / 1st lien"
    st.dataframe(q.rename(columns={"app_id": "Record", "lei": "Lender", "n_strong": "Strong comparators", "quality": "Match quality",
                                   "completeness": "Completeness", "priority": "Priority", "review_status": "Review status"})
                 [["Record", "Lender", "Loan category", "Strong comparators", "Match quality", "Completeness", "Priority", "Review status"]],
                 width="stretch", hide_index=True)
    c1, c2, c3 = st.columns(3)
    rec = c1.selectbox("Record", q.app_id); reviewer = c3.text_input("Reviewer", value="reviewer-1")
    opt = c2.selectbox("Mark as", ["Needs additional information", "Reviewed — no conclusion", "Escalate for further review"])
    if st.button("Save status"):
        call("POST", "/review-decision", json={"app_id": rec, "decision": opt, "reviewer": reviewer}); st.rerun()
    st.subheader("Audit trail (latest first)")
    log, _ = call("GET", "/review-log", params={"limit": 50})
    if log: st.dataframe(pd.DataFrame(log)[["ts", "app_id", "reviewer", "decision", "comment", "model_version", "match_quality", "note_generator"]], hide_index=True, width="stretch")
    else: st.caption("No decisions recorded yet.")
    st.caption("Advisory only. No loan decision is changed by this tool. Decisions are appended to an audit log with model version and match quality.")
