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
Docs: `docs/`. Status: MVP works locally and the API is deployed on the LinuxONE VM; Granite notes, ablation model are pending.
