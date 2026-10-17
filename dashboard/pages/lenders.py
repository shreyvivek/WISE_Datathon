import pandas as pd, streamlit as st
from dashboard.client import call

def render():
    st.header("Lender Comparison")
    st.warning("Lenders differ legitimately in products, policies and risk tolerance. This is not a ranking of misconduct.")
    d = pd.DataFrame(call("GET", "/lenders", params={"min_apps": st.slider("Minimum applications", 50, 1000, 200)})[0])
    pick = st.multiselect("Lenders (LEI)", d.lei.tolist(), default=d.lei.tolist()[:5])
    d["coverage"] = (d.denied_with_comparator / d.denied.replace(0, float("nan"))).round(3)
    st.dataframe(d[d.lei.isin(pick)].rename(columns={"denial_rate": "denial rate", "denied_with_comparator": "denied w/ same-lender comparator",
                 "coverage": "comparable-case coverage"}), use_container_width=True, hide_index=True)
