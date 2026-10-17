# SecondLook

**Same qualifications. Different decisions. Who notices?**

Team WISE · IBM Z Datathon 2026 · Real-Time AI for Critical Decisions · AI for Good

SecondLook is an advisory audit tool for historical mortgage decisions. For each denied application in public HMDA data it finds approved applications from the same lender with closely comparable finances, queues the cases worth a human second look, and shows the evidence behind each one. Demographic patterns are examined only after the financial matching is done, and are reported as observed disparities, never as proof of discrimination. The tool never approves, denies or overturns a loan.

## What it does
- **Financial twins.** Constrained, demographic-blind matching on income, loan amount, debt-to-income, loan-to-value, property value and loan term, with a match-quality label and an explicit "insufficient comparable evidence" outcome.
- **Review queue.** A transparent priority score with its components, a reason-aware check of the stated denial reasons against the reported data, grounded answers to reviewer questions, and an append-only audit trail of advisory decisions.
- **Reviewer notes.** IBM Granite writes short case summaries from structured facts only; every note is validated, with a template fallback.
- **Fairness audit.** Raw and matched denial-rate gaps with bootstrap intervals, sensitivity to matching settings, a proxy check, and an exploratory model sensitivity analysis. Context from the Federal Reserve SHED survey and Census ACS.

## Demo
Demo video: https://drive.google.com/file/d/1Vd0Ypqad56WqJVWRt4pn1nwvkosohwOL/view?usp=sharing

## Results at a glance
Maryland, HMDA 2025, one comparable cohort: 37,491 applications, 2,600 denied, 447 lenders. Details and caveats are in [`docs/model_evaluation.md`](docs/model_evaluation.md).

| | |
|---|---|
| Denials with a strong same-lender approved twin | 1,338 (1,726 queued, 874 without enough evidence) |
| Black vs White denial-rate gap | 8.4 pp raw, 3.1 pp after financial matching (95% CI 2.0 to 4.1) |
| Asian vs White denial-rate gap | 3.8 pp raw, 1.1 pp after matching (95% CI -0.04 to 2.3) |
| Matching on IBM LinuxONE (s390x) | identical results to an arm64 laptop; about 4 ms per simulated application |
| Throughput on the VM | about 370 to 470 requests per second with 4 to 16 clients |

## Repository
```
src/data/          download, cohort filtering, leak-safe tables
src/models/        twin matching, prioritisation, evaluation, model sensitivity
src/fairness/      blind matched-disparity analysis
src/explainability/ reviewer notes, reason check, Granite server
src/context/       SHED and Census context
src/api/           FastAPI service
dashboard/         Streamlit dashboard
scripts/           pipeline, deployment services, benchmarks, evidence collection
tests/             automated tests
docs/              architecture, methodology, evaluation, deployment, proof, slides
```

## Quick start
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
scripts/run_pipeline.sh                        # download data and rebuild every result (a few minutes)
.venv/bin/python -m pytest -q tests
.venv/bin/uvicorn src.api.main:app --port 8000
.venv/bin/streamlit run dashboard/app.py       # set SL_API_URL to use a remote API
```
The demographic endpoints return 403 unless the `AUDIT_TOKEN` environment variable is set and sent in the `X-Audit-Token` header; the dashboard reads it from the environment.

## IBM LinuxONE
Matching, scoring, the fairness audit, XGBoost and Granite run on a LinuxONE Community Cloud VM, with Granite in the IBM-provided container. See [`docs/deployment.md`](docs/deployment.md) for setup, [`docs/architecture.md`](docs/architecture.md) for the design, and [`docs/proof/`](docs/proof) for measured evidence. The VM was not faster than a laptop for this workload, and no hardware acceleration is claimed.

## Documentation
[Architecture](docs/architecture.md) · [Dataset and methodology](docs/dataset_methodology.md) · [Evaluation](docs/model_evaluation.md) · [Deployment](docs/deployment.md) · [Slides](docs/slides/SecondLook_Slides.pdf)

## Reviewer dashboard (`ui_demo/`) — step by step
A single-page app (plain HTML/JS, no build, works offline). It shows **LIVE API** when connected to the backend, **DEMO DATA** otherwise.

**A. Quick look, no backend (bundled demo data)**
1. `python3 ui_demo/serve.py` — opens http://localhost:8080.

**B. Live data from the LinuxONE VM (what the demo video uses)**
1. Put `wise_key.pem` in the repo root: `chmod 600 wise_key.pem` (it is git-ignored).
2. Get the audit token once: `ssh -i wise_key.pem linux1@148.100.109.157 'cat ~/secondlook/.api.env'` (needed only for the Fairness page).
3. Terminal 1 — tunnel to the VM's API, leave it running:
   `ssh -i wise_key.pem -N -L 18000:localhost:8000 linux1@148.100.109.157`
4. Terminal 2 — dashboard, proxying every API call through the tunnel:
   `python3 ui_demo/serve.py --api http://localhost:18000 --token <AUDIT_TOKEN>`
5. Open http://localhost:8080/?reset#overview and check the sidebar badge says **LIVE API**.
   (`?reset` clears locally saved demo decisions and selects case `b81daae6eb`.)

**C. Same machine as the API** (laptop with `data/processed/`, or on the VM): `uvicorn src.api.main:app --port 8000` then open http://localhost:8000/ui.

**Pages:** Overview → Queue (▾ on a row: *View in detail* / *Compare twins*) → Compare (denied vs. any ranked approved comparator, gap bars in tolerance units) → Case detail (stated reasons vs data, Granite note, grounded Q&A, advisory decision + audit trail) → Simulate (live `/analyse-application`) → Fairness (raw vs matched gap, matching-setting dropdown, reviewer consistency, model sensitivity) → System.
Decisions saved in live mode go to the VM's append-only review log. Demo script: `docs/demo_walkthrough.md`.

## Data sources
| Data | Source | Use |
|---|---|---|
| HMDA 2025 loan application register (Maryland) | FFIEC Data Browser API | primary analysis |
| SHED 2025 public-use file | Federal Reserve Board | weighted context only; never joined to HMDA applicants |
| ACS 2024 5-year, county level | US Census Bureau, via Census Reporter (the official API requires a key; set `CENSUS_API_KEY` to use it) | county context |

## Open-source libraries
| Library | Link | Licence |
|---|---|---|
| pandas, NumPy, SciPy | https://pandas.pydata.org , https://numpy.org , https://scipy.org | BSD-3 |
| scikit-learn | https://scikit-learn.org | BSD-3 |
| XGBoost | https://github.com/dmlc/xgboost | Apache-2.0 |
| FastAPI, Pydantic | https://fastapi.tiangolo.com , https://docs.pydantic.dev | MIT |
| Uvicorn | https://www.uvicorn.org | BSD-3 |
| Requests, HTTPX | https://requests.readthedocs.io , https://www.python-httpx.org | Apache-2.0, BSD-3 |
| Streamlit | https://streamlit.io | Apache-2.0 |
| Plotly | https://plotly.com/python | MIT |
| PyArrow | https://arrow.apache.org | Apache-2.0 |
| pytest | https://pytest.org | MIT |
| llama.cpp, llama-cpp-python (in the IBM-provided container) | https://github.com/ggml-org/llama.cpp , https://github.com/abetlen/llama-cpp-python | MIT |
| IBM Granite 4.0-H 350M base (in the IBM-provided container) | https://huggingface.co/ibm-granite | Apache-2.0 |
| Mermaid (diagrams in the docs) | https://mermaid.js.org | MIT |

## Limitations
Public HMDA has no credit scores, assets or employment history, and historical decisions are not an approval standard. A matched gap is an observed disparity that depends on matching settings; it is not evidence that any lender acted unlawfully. See the limitations in [`docs/model_evaluation.md`](docs/model_evaluation.md).
