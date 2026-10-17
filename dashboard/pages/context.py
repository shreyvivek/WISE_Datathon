import pandas as pd, plotly.express as px, plotly.graph_objects as go, streamlit as st
from dashboard.client import call


def render():
    st.header("Context: Federal Reserve SHED and Census ACS")
    st.info("Supplementary context only. SHED respondents are not HMDA applicants and are never joined to them. Census data is county-level.")
    shed, _ = call("GET", "/context/shed")
    st.subheader("SHED 2025 — credit access among adults who applied for credit (all credit types, weighted)")
    st.caption(shed["caveat"])
    item = st.selectbox("Measure", list(shed["items"]), format_func=lambda k: shed["items"][k]["label"])
    rows = pd.DataFrame(shed["items"][item]["by_group"])
    fig = go.Figure(go.Bar(x=rows.group, y=100 * rows.weighted_share, error_y=dict(type="data", symmetric=False,
                    array=[100 * (c[1] - s) for c, s in zip(rows.ci95, rows.weighted_share)], arrayminus=[100 * (s - c[0]) for c, s in zip(rows.ci95, rows.weighted_share)])))
    fig.update_layout(yaxis_title="% of applicants (95% bootstrap CI)", height=340, margin=dict(t=10)); st.plotly_chart(fig, width="stretch")
    st.dataframe(rows.assign(ci95=rows.ci95.map(lambda c: f"{100*c[0]:.1f}–{100*c[1]:.1f}%"), weighted_share=(100 * rows.weighted_share).round(1)), hide_index=True, width="stretch")
    st.divider()
    cen, _ = call("GET", "/context/census"); c = pd.DataFrame(cen["counties"])
    st.subheader("Maryland counties — ACS 2024 5-year median household income vs HMDA denial rate")
    st.caption(f"{cen['source']}. {cen['caveat']} Spearman correlation across {cen['n_counties']} counties: {cen['spearman_income_vs_denial_rate']:.2f}.")
    fig = px.scatter(c, x="median_household_income", y=100 * c.denial_rate, size="applications", hover_name="NAME",
                     labels={"y": "Denial rate (%)", "median_household_income": "Median household income ($)"})
    fig.update_layout(height=380, margin=dict(t=10)); st.plotly_chart(fig, width="stretch")
    st.dataframe(c[["NAME", "median_household_income", "population", "applications", "denial_rate", "queue_share_of_denials"]].round(3), hide_index=True, width="stretch")
