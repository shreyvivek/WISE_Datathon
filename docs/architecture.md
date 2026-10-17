# Architecture
HMDA CSV -> `src/data/preprocess.py` -> parquet (applications / audit_only / denial_context) -> matching + prioritisation + fairness (`src/models`, `src/fairness`)
-> FastAPI (`src/api/main.py`, runs on the LinuxONE VM) -> Streamlit (`dashboard/`, `SL_API_URL=http://<vm>:8000`).
Demographic endpoint `/fairness-report` is gated by `AUDIT_TOKEN`. Audit log: `audit_log.jsonl` (version, event, latency; no demographics or financials).
Status: API deployed and benchmarked on the LinuxONE VM (s390x); see model_evaluation.md. Dashboard verified locally, pointing at the VM via SSH tunnel `ssh -L 18000:localhost:8000` and `SL_API_URL=http://localhost:18000`. No Telum/NNPA claim is made; the workload is NumPy/pandas CPU code.
Deploy: `scripts/deploy_linuxone.sh user@host key.pem`; benchmark: `scripts/benchmark.py http://host:8000`.
