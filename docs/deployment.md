# Deployment on IBM LinuxONE

The API, the matching and scoring code, and the Granite note server run on a LinuxONE Community Cloud VM (s390x, Ubuntu 24.04, 3 vCPU, 8 GB RAM). Granite runs inside the IBM-provided JupyterLab container on the same VM. See `docs/architecture.md` for the design.

## One-time setup
1. **Packages.** PyPI has no s390x wheels for numpy, pandas or scikit-learn, so install them from Ubuntu, then add the web packages with pip:
   ```
   sudo apt-get install -y python3-numpy python3-pandas python3-sklearn python3-scipy
   python3 -m venv --without-pip --system-site-packages ~/secondlook/.venv
   curl -sS https://bootstrap.pypa.io/get-pip.py | ~/secondlook/.venv/bin/python
   ~/secondlook/.venv/bin/pip install fastapi uvicorn pydantic httpx requests
   ```
2. **Code and data.** Copy `src/` and `scripts/` to `~/secondlook/`. Ubuntu has no pyarrow package, so export the tables to gzipped CSV on your machine (`python scripts/export_csv.py`) and copy `data/processed/*.csv.gz` plus the result files (`fairness_report.csv`, `eval_results.json`, `ranking_eval.json`, `model_sensitivity_*.json`, `shed_context.json`, `census_context.json`) to `~/secondlook/data/processed/`.
3. **Access token** for the demographic endpoints: put `AUDIT_TOKEN=<random value>` in `~/secondlook/.api.env` (mode 600). Without the token those endpoints return 403.
4. **Granite server.** Copy `src/` and `scripts/kill_granite.py` into the container (`docker cp`) under `/home/ibm-user/secondlook/`; the server is `src/explainability/granite_server.py` and loads `granite-4.0-h-350m-base-be.f16.gguf` from `/home/ibm-user/`.
5. **Services.** Install and start both units:
   ```
   sudo cp scripts/secondlook-api.service scripts/secondlook-granite.service /etc/systemd/system/
   sudo systemctl daemon-reload && sudo systemctl enable --now secondlook-api secondlook-granite
   ```
6. **Cached notes.** `~/secondlook/.venv/bin/python scripts/precompute_notes.py http://localhost:8000 25` pre-generates validated Granite notes for the top queue cases (about 13 to 60 s each).

## Daily use
- **Check the services:** `ssh -i wise_key.pem linux1@<vm-ip> 'uname -m; systemctl is-active secondlook-api secondlook-granite; curl -s localhost:8000/health'`
- **Tunnel** (port 8000 is not reachable from the internet; only SSH is): `ssh -i wise_key.pem -N -L 18000:localhost:8000 linux1@<vm-ip>`
- **Dashboard against the VM:** `set -a; . ./.env; set +a; SL_API_URL=http://localhost:18000 .venv/bin/streamlit run dashboard/app.py` (put the same `AUDIT_TOKEN` in your local `.env`). The sidebar shows `Backend: REMOTE` when it is connected.
- **Restart:** `sudo systemctl restart secondlook-api secondlook-granite` on the VM, then wait about 20 s.
- **Walkthrough:** `scripts/linuxone_walkthrough.sh` steps through the instance, services, a live request, load and access control.
- **Evidence and benchmarks:** `scripts/collect_proof.sh > docs/proof/linuxone_evidence.txt`; `scripts/benchmark.py` and `scripts/benchmark_concurrent.py http://localhost:8000` run on the VM.

## Notes
- The API runs with 3 uvicorn workers; `/metrics` is therefore per worker process.
- Only ports 22 (SSH) and 38888 (the lab's Jupyter) are reachable from the internet. The VM firewall accepts all traffic, so port 8000 is filtered upstream and cannot be opened from inside the VM.
- Locally, `uvicorn src.api.main:app --port 8000` serves the same API from `data/processed` (parquet).
