import pandas as pd, streamlit as st
from dashboard.client import call, DENIAL

ROWS = [("income", "Income ($K)"), ("loan_amount", "Loan amount ($)"), ("dti", "DTI (%)"), ("ltv", "LTV (%)"),
        ("property_value", "Property value ($)"), ("loan_term", "Term (months)")]

def render():
    st.header("Financial Twins")
    q, _ = call("GET", "/review-queue", params={"limit": 200})
    sel = st.selectbox("Denied application (ranked by review priority)", [r["app_id"] for r in q])
    a, _ = call("GET", f"/application/{sel}"); t, ms = call("GET", f"/application/{sel}/twins")
    st.subheader("Application under review — DENIED")
    cols = {"Application": {l: a.get(k) for k, l in ROWS}}
    for i, tw in enumerate(t[:3], 1):
        cols[f"Twin {i} ({tw['quality']}, d={tw['dist']:.2f})"] = {l: tw.get(k) for k, l in ROWS}
    df = pd.DataFrame(cols); df.loc["Outcome"] = ["Denied"] + ["Approved"] * (len(df.columns) - 1)
    st.dataframe(df.astype(object).fillna("not reported"), use_container_width=True)
    c1, c2 = st.columns(2)
    c1.metric("Best match quality", t[0]["quality"].upper() if t else "n/a")
    c2.metric("Largest single-feature gap (tolerances)", f"{t[0]['max_diff']:.1f}" if t else "n/a")
    miss = [l for k, l in ROWS if a.get(k) is None]
    if miss: st.warning("Missing for this application: " + ", ".join(miss))
    rs = [DENIAL.get(x, x) for x in a.get("denial_reasons", [])]
    st.write("Stated denial reason(s) (context only; not used for matching): " + (", ".join(rs) or "none reported"))
    comp = a.get("priority_components")
    if comp: st.write("Priority breakdown:", {k: comp[k] for k in ("c_match", "c_count", "c_lender", "c_complete", "priority")})
    if st.button("Generate reviewer note"):
        st.write(call("POST", "/generate-review-note", json={"app_id": sel})[0]["note"])
    st.caption("Distance = mean of per-feature differences in units of tolerance. It is not an approval probability.")
    with st.expander("Simulated incoming application (SIMULATION)"):
        lei = a["lei"]; inc = st.number_input("Income ($K)", 90.0); la = st.number_input("Loan amount", 280000.0)
        dti = st.number_input("DTI", 35.0); ltv = st.number_input("LTV", 79.0); pv = st.number_input("Property value", 355000.0)
        if st.button("Analyse (simulation)"):
            r, ms2 = call("POST", "/analyse-application", json={"lei": lei, "income": inc, "loan_amount": la, "dti": dti, "ltv": ltv, "property_value": pv})
            st.json(r); st.caption(f"Server compute {r['compute_ms']} ms; round-trip processing {ms2:.1f} ms")
