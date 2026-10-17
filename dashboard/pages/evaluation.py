import pandas as pd, streamlit as st
from dashboard.client import call


def render():
    st.header("Evaluation")
    ev, _ = call("GET", "/evaluation"); rk, mt = ev["ranking"], ev["matching"]
    st.subheader("1. Does the queue surface known inconsistencies? (SYNTHETIC experiment)")
    st.warning(rk["label"] + ". Real HMDA data has no ground truth for wrongful denials, so no precision/recall for real wrongful denials is claimed.")
    for lv, methods in rk["results"].items():
        st.markdown(f"**{lv}** — {rk['n_injected']} injected cases among {rk['n_real_denied']:,} real denials, mean of {rk['seeds']} seeds")
        rows = []
        for m, d in methods.items():
            r = {"Method": m}
            for k in rk["ks"]: r[f"P@{k}"] = round(d[str(k)]["precision_mean"], 2); r[f"R@{k}"] = round(d[str(k)]["recall_mean"], 2)
            rows.append(r)
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.info("Reading: an unconstrained global search (Baseline B) is useless here, and the lender constraint matters. A plain same-lender similarity ranking (Baseline A) is as good as or better than our "
            "composite score at recovering near-duplicate injected cases, so we do not claim better ranking. At the harder level no method beats random: such cases are not distinguishable from ordinary denials. "
            f"Also {rk['ceiling_note']['real_denials_with_best_dist_le_0.15']} real denials already have a near-identical approved comparator, which caps injected-only precision. "
            "SecondLook's added value is evidence quality: tolerances, missing-data handling, match-quality labels, 'insufficient evidence', reason-aware review and an audit trail.")
    st.subheader("2. Triage and matching quality (real data)")
    t = rk["triage"]; c = st.columns(3)
    c[0].metric("Real denials", f"{t['real_denials']:,}"); c[1].metric("Queued", f"{t['queued']:,}"); c[2].metric("Insufficient evidence", f"{t['not_queued_insufficient_evidence']:,}")
    st.caption(t["note"])
    sens = pd.DataFrame(mt["tolerance_sensitivity"]).T.rename_axis("tolerance x").reset_index()
    st.dataframe(sens.round(3), hide_index=True, width="stretch"); st.caption("Sensitivity of queue size and score ranking to matching tolerances (Spearman vs baseline tolerances).")
