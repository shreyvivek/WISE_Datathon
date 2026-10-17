import pandas as pd, plotly.graph_objects as go, streamlit as st
from dashboard.client import call


def render():
    st.header("Model Sensitivity Analysis")
    st.warning("Exploratory. Models predict HISTORICAL decisions, which are not a correct standard. A change in predictions when demographics are added does not show "
               "that a lender used race, and removing race does not remove correlated proxies (location and finances partly predict race). Audit use only.")
    try:
        r, _ = call("GET", "/model-sensitivity")
    except Exception as e:
        st.error(f"Demographic audit access restricted or unavailable: {e}"); return
    rows = []
    for name, m in r["models"].items():
        o = m["overall"]
        rows.append({"Model": {"logreg": "Logistic regression", "xgb": "XGBoost (LinuxONE)"}[name], "n": m["n"],
                     "AUC without demographics": round(o["A_no_demographics"]["roc_auc"], 3), "AUC with demographics": round(o["B_with_demographics"]["roc_auc"], 3),
                     "fit+eval seconds": m["train_eval_seconds"]})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    pick = st.radio("Model", list(r["models"]), horizontal=True, format_func=lambda k: {"logreg": "Logistic regression", "xgb": "XGBoost"}[k])
    bg = r["models"][pick]["by_group"]; groups = list(bg)
    fig = go.Figure()
    for lab, key in [("Actual denial rate", "actual_denial_rate"), ("Predicted — no demographics", "mean_pred_A"), ("Predicted — with demographics", "mean_pred_B")]:
        fig.add_trace(go.Bar(name=lab, x=[g.replace(" or African American", "") for g in groups], y=[100 * bg[g][key] for g in groups]))
    fig.update_layout(barmode="group", yaxis_title="Denial rate (%)", height=360, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")
    st.write("Without demographics the model under-predicts denials for the group with the higher actual rate and over-predicts for the lower one; adding demographics closes that gap. "
             "The public financial, lender and county fields therefore do not fully explain group differences in outcomes. Credit scores and other underwriting inputs are absent, "
             "so this is a question for review, not a finding about any lender.")
    st.dataframe(pd.DataFrame(bg).T.round(3), width="stretch")
