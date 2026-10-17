# Reviewer dashboard

A single-page app in plain HTML and JavaScript, with bundled fonts and no build step. Pages: Overview, Queue, Compare (denied application against ranked approved comparators), Case detail (stated reasons against the reported data, Granite note, grounded questions, advisory decision with audit trail), Simulate, Fairness (blind, then reveal), and System.

The sidebar badge shows **LIVE API** when the SecondLook API is reachable and **DEMO DATA** otherwise. Demo data uses the measured aggregates from `docs/model_evaluation.md`; individual cases are synthetic, and decisions saved in that mode stay in the browser.

## Run it
**Sample data, no backend**
```
python3 ui_demo/serve.py                 # http://localhost:8080
```

**Against the LinuxONE VM** (SSH tunnel; commands and the access token are described in `docs/deployment.md`)
```
ssh -i wise_key.pem -N -L 18000:localhost:8000 linux1@<vm-ip>      # leave running
set -a; . ./.env; set +a                                           # exports AUDIT_TOKEN
python3 ui_demo/serve.py --api http://localhost:18000              # http://localhost:8080
```

**Same machine as the API**
```
.venv/bin/uvicorn src.api.main:app --port 8000                     # dashboard at http://localhost:8000/ui
```

`AUDIT_TOKEN` is only needed for the Fairness page and is read from the environment. In live mode, decisions are written to the API's append-only review log. Files: `index.html`, `app.css`, `app.js` (views), `api.js` (API calls and fallback), `mock.js` (sample data), `serve.py` (static server and API proxy).
