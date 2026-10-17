# SecondLook — Same qualifications. Different decisions. Who notices?
IBM Z Datathon 2026. Advisory audit of historical HMDA decisions: finds denied applications with financially comparable approved ones, queues them for
human review, and reports demographic patterns only as observed disparities (never proof of discrimination).
## Run
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python src/data/download.py && .venv/bin/python src/data/preprocess.py
    .venv/bin/python -m src.models.run_matching && .venv/bin/python -m src.models.run_audit && .venv/bin/python -m src.models.run_eval
    .venv/bin/python -m pytest tests
    .venv/bin/streamlit run dashboard/app.py          # local; set SL_API_URL=http://<linuxone>:8000 for remote
    .venv/bin/uvicorn src.api.main:app --port 8000
Docs: `docs/`. Status: MVP works locally, Granite notes, Model Sensitivity Analysis, SHED and Census context are in, and the API is deployed on the LinuxONE VM; Granite notes, ablation model are pending.

## Data sources and licences
| Data | Source | Terms |
|---|---|---|
| HMDA 2025 LAR (Maryland) | FFIEC / CFPB Data Browser API | US public data |
| SHED 2025 public-use file | Federal Reserve Board | public use; used with survey weights, as context only |
| ACS 2024 5-year (county) | US Census Bureau, via Census Reporter (official API needs a key) | public data |

## Libraries (all open source)
pandas, NumPy, SciPy, scikit-learn, XGBoost (BSD/Apache-2.0); FastAPI, Uvicorn, Pydantic, Requests, HTTPX (MIT/BSD/Apache-2.0); Streamlit (Apache-2.0), Plotly (MIT); PyArrow (Apache-2.0);
pytest (MIT); llama.cpp / llama-cpp-python (MIT) in the IBM-provided LinuxONE container; IBM Granite 4.0-H 350M base (Apache-2.0), provided in that container.
All SecondLook code in `src/`, `dashboard/`, `scripts/`, `tests/` was written during the datathon; the IBM loan demo notebook was not reused.
Docs: `docs/architecture.md`, `docs/runbook.md`, `docs/demo_script.md`, `docs/model_evaluation.md`, `docs/dataset_methodology.md`. LinuxONE evidence: `docs/proof/linuxone_evidence.txt`.
