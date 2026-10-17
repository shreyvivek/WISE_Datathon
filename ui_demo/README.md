# SecondLook UI (local, no build step)

    python3 ui_demo/serve.py            # opens http://localhost:8080 with bundled demo data

With the real backend (needs `data/processed/`):

    .venv/bin/uvicorn src.api.main:app --port 8000     # then open http://localhost:8000/ui
    # or against the LinuxONE tunnel: http://localhost:8080/?api=http://localhost:18000&token=<AUDIT_TOKEN>

Badge in the sidebar says **LIVE API** or **DEMO DATA**. Demo data: aggregates are the measured numbers from
`docs/model_evaluation.md`; individual cases are synthetic. Decisions saved in demo mode stay in the browser (localStorage).

Pages: Overview · Queue · Compare (side-by-side twins) · Explain (reasons, Granite note, Q&A, decision + audit trail) ·
Fairness (blind → reveal, scope/tolerance filters, reviewer consistency, model sensitivity) · Simulate · System.
`?noanim` disables animations (screenshots). Files: `index.html`, `app.css`, `app.js` (views), `api.js` (API + fallback), `mock.js` (demo data).
