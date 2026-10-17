import pandas as pd, plotly.graph_objects as go, streamlit as st
from dashboard.client import call

def render():
    st.header("Blind Review / Fairness Audit")
    reveal = st.toggle("REVEAL DEMOGRAPHIC PATTERNS", value=False)
    st.markdown(f"**BLIND REVIEW — {'OFF (aggregates shown)' if reveal else 'ON'}**")
    if not reveal:
        st.write("Financially matched sets are built from income, loan amount, DTI, LTV, property value and term only, "
                 "within the same lender. Race, ethnicity, sex and age are not read by the matching code. "
                 "Toggle above to reveal aggregate outcomes by group; the matched sets do not change.")
        return
    try:
        r, _ = call("GET", "/fairness-report")
    except Exception as e:
        st.error(f"Demographic audit access restricted or unavailable: {e}"); return
    st.warning(r["caveat"]); df = pd.DataFrame(r["results"])
    for _, x in df.iterrows():
        st.subheader(f"{x.group} vs {x.ref}")
        fig = go.Figure()
        raw_ci, m_ci = (x.raw_ci_lo, x.raw_ci_hi), (x.matched_ci_lo, x.matched_ci_hi)
        fig.add_trace(go.Scatter(x=[x.raw_gap_pp, x.matched_gap_pp], y=["Raw", "Matched (blind, same lender)"], mode="markers",
                                 marker=dict(size=12), error_x=dict(type="data", symmetric=False,
                                 array=[raw_ci[1] - x.raw_gap_pp, m_ci[1] - x.matched_gap_pp],
                                 arrayminus=[x.raw_gap_pp - raw_ci[0], x.matched_gap_pp - m_ci[0]])))
        fig.add_vline(x=0, line_dash="dot"); fig.update_layout(height=220, xaxis_title="Denial-rate gap (percentage points, 95% CI)", margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
        st.write(f"Raw denial rate {x.raw_rate_group:.1%} vs {x.raw_rate_ref:.1%} (n={x.n_group:,} / {x.n_ref:,}). "
                 f"Matched: {x.matched_rate_group:.1%} vs {x.matched_rate_ref:.1%} on {x.n_matched:,} strong pairs "
                 f"(coverage {x.coverage:.0%} of the group).")
        if x.small_sample_warning: st.warning("Small matched sample — interpret with caution.")
    st.caption("Observed vs adjusted disparity. Credit scores are absent from public HMDA; a matched gap is not proof of discrimination.")
