# Submission text (paste into the Hack2Skill form)
**Project title:** WISE_IBM Z Datathon 2026 Project  *(format required by the guide: [Team Name_IBM Z Datathon 2026 Project]; project name: SecondLook)*

**Theme:** Real-Time AI for Critical Decisions (AI for Good)

**Short description (about 100 words):**
SecondLook – "Same qualifications. Different decisions. Who notices?" – audits historical mortgage decisions in public HMDA data (Maryland, 2025; 37,491 comparable applications). For each denied application it finds approved applications from the same lender with closely similar reported finances, and ranks the cases worth a human second look. Matching is demographic-blind; aggregate demographic disparities are revealed only afterwards, with sample sizes and confidence intervals, and always as observed disparities – never as proof of discrimination. Matching, scoring, an XGBoost model-sensitivity analysis and IBM Granite reviewer notes all run on IBM LinuxONE (s390x). It is advisory only and changes no loan decision.

**Problem & data:** Applicants with similar finances can get different outcomes; public data allows independent review. Data: HMDA 2025 LAR (FFIEC), Federal Reserve SHED 2025 (context), ACS 2024 5-year county data (context).

**How it uses IBM Z / LinuxONE:** Whole pipeline deployed on a LinuxONE VM (s390x, 3 vCPU): constrained matching (results bit-identical to an arm64 laptop), FastAPI service with 3 workers under systemd and token-gated demographic endpoints, XGBoost trained on s390x, Granite 4.0-H 350M served with llama.cpp inside the provided container (zDNN backend initialised; offload measured no faster, so no acceleration is claimed). Measured: ~4 ms median per simulated-application analysis, ~440-470 req/s with 4-16 concurrent clients. All numbers in docs/model_evaluation.md.

**Tech stack:** Python, pandas, NumPy, SciPy, scikit-learn, XGBoost, FastAPI, Uvicorn, Streamlit, Plotly, llama.cpp, IBM Granite 4.0, systemd, Mermaid.

**Repository:** https://github.com/shreyvivek/WISE_Datathon  (public)
**Open-source links:** README, table "Libraries and open-source resources used".
**Flowchart (optional):** docs/architecture.md (Mermaid diagram). **Prototype (optional):** Streamlit dashboard, see docs/runbook.md.
**Limitations (state them):** public HMDA has no credit scores; historical decisions are not ground truth; matched gaps depend on matching strictness; the LinuxONE VM was not faster than a laptop for this workload.
