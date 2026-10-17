# Architecture
HMDA CSV -> `src/data/preprocess.py` -> parquet (applications / audit_only / denial_context) -> matching + prioritisation + fairness (`src/models`, `src/fairness`)
-> FastAPI (`src/api/main.py`, runs on the LinuxONE VM) -> Streamlit (`dashboard/`, `SL_API_URL=http://<vm>:8000`).
Demographic endpoint `/fairness-report` is gated by `AUDIT_TOKEN`. Audit log: `audit_log.jsonl` (version, event, latency; no demographics or financials).
Status: API deployed and benchmarked on the LinuxONE VM (s390x); see model_evaluation.md. Dashboard verified locally, pointing at the VM via SSH tunnel `ssh -L 18000:localhost:8000` and `SL_API_URL=http://localhost:18000`. No Telum/NNPA claim is made; the workload is NumPy/pandas CPU code.
Deploy: `scripts/deploy_linuxone.sh user@host key.pem`; benchmark: `scripts/benchmark.py http://host:8000`.
Granite: `src/explainability/granite_server.py` runs inside the provided LinuxONE JupyterLab container (llama.cpp + Granite 4.0-H 350M base GGUF) on port 8001 (container-local).
The host API calls it through `docker exec ... curl` (`SL_GRANITE_CMD`), validates the output, caches validated notes in `data/processed/notes_cache.json`, and falls back to templates.
Network: the VM exposes only ports 22 (SSH) and 38888 (the lab's Jupyter) to the internet; the host firewall (iptables INPUT policy ACCEPT) is not the blocker, so port 8000 is filtered upstream by the hosting environment
and cannot be opened from inside the VM. Access to the API/dashboard is via SSH tunnel: `ssh -i wise_key.pem -N -L 18000:localhost:8000 linux1@<host>` then `SL_API_URL=http://localhost:18000 streamlit run dashboard/app.py`.
Dashboard pages: Overview, Financial Twins (with Granite note button), Blind Review / Fairness, Lender Comparison, Model Sensitivity, SHED & Census Context, Second-Look Queue.
