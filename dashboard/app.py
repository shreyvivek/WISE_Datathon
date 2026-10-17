import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import streamlit as st
st.set_page_config(page_title="SecondLook", layout="wide")
from dashboard.client import MODE
from dashboard.pages import overview, financial_twins, fairness, review_queue, lenders, sensitivity, context, evaluation
PAGES = {"Overview": overview, "Financial Twins": financial_twins, "Blind Review / Fairness": fairness,
         "Lender Comparison": lenders, "Model Sensitivity": sensitivity, "SHED & Census Context": context, "Evaluation": evaluation, "Second-Look Queue": review_queue}
st.sidebar.title("SecondLook"); st.sidebar.caption(f"Backend: {MODE}")
PAGES[st.sidebar.radio("Page", list(PAGES))].render()
