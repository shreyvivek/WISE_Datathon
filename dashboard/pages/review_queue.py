import pandas as pd, streamlit as st
from dashboard.client import call

def render():
    st.header("Second-Look Queue")
    n = st.slider("Rows", 10, 500, 100)
    q = pd.DataFrame(call("GET", "/review-queue", params={"limit": n})[0])
    q["lei"] = q.lei.str[:8] + "…"; q["Loan category"] = "Conventional / purchase / 1st lien"
    st.session_state.setdefault("status", {})
    q["Review status"] = q.app_id.map(lambda i: st.session_state["status"].get(i, "Pending"))
    st.dataframe(q.rename(columns={"app_id": "Record", "lei": "Lender", "n_strong": "Strong comparators", "quality": "Match quality",
                                   "completeness": "Completeness", "priority": "Priority"})
                 [["Record", "Lender", "Loan category", "Strong comparators", "Match quality", "Completeness", "Priority", "Review status"]],
                 use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    rec = c1.selectbox("Record", q.app_id)
    opt = c2.selectbox("Mark as", ["Needs additional information", "Reviewed — no conclusion", "Escalate for further review"])
    if st.button("Save status"): st.session_state["status"][rec] = opt; st.rerun()
    st.caption("Advisory only. No loan decision is changed by this tool.")
