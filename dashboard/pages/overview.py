import pandas as pd, streamlit as st
from dashboard.client import call

def render():
    st.title("SecondLook"); st.caption("Same qualifications. Different decisions. Who notices?")
    s, ms = call("GET", "/summary")
    st.info(s["note"] + " Differences shown here flag cases for human review; they do not establish errors or discrimination.")
    c = st.columns(5)
    for col, (k, v) in zip(c, [("Applications", s["applications"]), ("Denied", s["denied"]),
                               ("Denied w/ strong comparator", s["denied_with_strong_comparator"]),
                               ("Lenders", s["lenders"]), ("Review queue", s["review_queue_size"])]):
        col.metric(k, f"{v:,}")
    st.subheader("Data completeness (share missing)")
    st.dataframe(pd.Series(s["missing_share"], name="missing").map("{:.1%}".format), width=300)
    st.caption(f"{s['insufficient_evidence']:,} denials have insufficient comparable evidence and are not queued. API {ms:.1f} ms.")
