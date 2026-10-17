"""SecondLook API. Run: uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Advisory only. Every request is timed; /metrics reports measured latencies (no claims beyond what is measured)."""
import json, os, platform, time, statistics, datetime
from pathlib import Path
import numpy as np
import pandas as pd
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from src.models.financial_twins import _matrix, TOL, FEATS, MIN_SHARED, quality
import subprocess
from src.explainability.reviewer_notes import make_note, facts_for, finalize, DENIAL

P = Path(os.environ.get("SL_DATA", "data/processed"))
VERSION = "secondlook-0.1"
AUDIT_TOKEN = os.environ.get("AUDIT_TOKEN")  # if set, demographic endpoints require X-Audit-Token
LOG = Path(os.environ.get("SL_LOG", "audit_log.jsonl"))

STR = {"app_id", "lei", "county_code", "census_tract", "msa", "outcome", "quality", "status", "denied_id", "twin_id", "scope",
       "denial_reason-1", "denial_reason-2", "denial_reason-3", "denial_reason-4", "aus-1", "aus-2", "aus-3", "aus-4", "aus-5"}

def load(name: str) -> pd.DataFrame:
    """parquet if pyarrow is available (dev), else gzipped CSV exported by scripts/export_csv.py (s390x apt has no pyarrow)."""
    try:
        return pd.read_parquet(P / f"{name}.parquet")
    except (ImportError, FileNotFoundError):
        df = pd.read_csv(P / f"{name}.csv.gz", dtype={c: str for c in STR}, keep_default_na=False, na_values=[""])
        for c in df.columns:
            if df[c].dtype == object and set(df[c].dropna().unique()) <= {"True", "False"}:
                df[c] = df[c].map({"True": True, "False": False})
        return df.set_index("app_id") if name == "review_queue" else df

t0 = time.perf_counter()
apps = load("applications")
twins = load("twins_lender")
queue = load("review_queue")
ctx = load("denial_context").set_index("app_id")
fair = pd.read_csv(P / "fairness_report.csv")
LOAD_S = time.perf_counter() - t0
approved = apps[apps.outcome == "approved"]
lat: list[float] = []
app = FastAPI(title="SecondLook", version=VERSION)

@app.middleware("http")
async def timer(request, call_next):
    s = time.perf_counter(); r = await call_next(request); ms = (time.perf_counter() - s) * 1e3
    if request.url.path != "/metrics":
        lat.append(ms)
    r.headers["X-Process-Ms"] = f"{ms:.2f}"; return r

def _log(ev: dict):  # no demographics or raw financials in logs
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": datetime.datetime.utcnow().isoformat(), "version": VERSION, **ev}) + "\n")

@app.get("/health")
def health():
    return {"status": "ok", "arch": platform.machine(), "python": platform.python_version(),
            "model_load_s": round(LOAD_S, 3), "version": VERSION}

@app.get("/metrics")
def metrics():
    import resource
    a = np.array(lat) if lat else np.array([np.nan])
    return {"n_requests": len(lat), "median_ms": float(np.median(a)), "p95_ms": float(np.percentile(a, 95)),
            "max_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 if platform.system() == "Linux" else 1048576),
            "model_load_s": LOAD_S}

@app.get("/summary")
def summary():
    den = apps[apps.outcome == "denied"]
    return {"applications": len(apps), "denied": len(den), "lenders": int(apps.lei.nunique()),
            "denied_with_strong_comparator": int((queue.quality == "strong").sum()),
            "review_queue_size": int(queue.eligible.sum()),
            "insufficient_evidence": int((~queue.eligible).sum()),
            "missing_share": apps[FEATS].isna().mean().round(4).to_dict(),
            "note": "Historical, publicly reported HMDA 2025 Maryland records. Advisory only."}

@app.get("/lenders")
def lenders(min_apps: int = 100):
    g = apps.groupby("lei").agg(applications=("app_id", "size"), denial_rate=("outcome", lambda s: (s == "denied").mean()))
    g["denied_with_comparator"] = queue[queue.eligible].groupby("lei").size()
    g["denied"] = queue.groupby("lei").size()
    g = g[g.applications >= min_apps].fillna(0).sort_values("applications", ascending=False)
    return g.reset_index().round(4).to_dict("records")

@app.get("/review-queue")
def review_queue(limit: int = 50, lei: str | None = None):
    q = queue[queue.eligible]
    if lei: q = q[q.lei == lei]
    q = q.head(limit).reset_index()
    return q[["app_id", "lei", "county_code", "n_candidates", "n_strong", "quality", "dist", "completeness", "priority"]] \
        .round(3).to_dict("records")

def _app_row(app_id):
    r = apps[apps.app_id == app_id]
    if r.empty: raise HTTPException(404, "unknown application id")
    return r.iloc[0]

@app.get("/application/{app_id}")
def application(app_id: str):
    r = _app_row(app_id); out = {k: (None if pd.isna(v) else v) for k, v in r[["app_id", "lei", "outcome", *FEATS, "completeness"]].items()}
    if app_id in ctx.index:
        out["denial_reasons"] = [x for x in ctx.loc[app_id, [f"denial_reason-{i}" for i in range(1, 5)]] if isinstance(x, str) and x not in ("", "10")]
    if app_id in queue.index:
        out["priority_components"] = queue.loc[app_id, ["c_match", "c_count", "c_lender", "c_complete", "priority", "status"]].to_dict()
    return json.loads(json.dumps(out, default=lambda o: o.item() if hasattr(o, "item") else str(o)))

@app.get("/application/{app_id}/twins")
def app_twins(app_id: str):
    t = twins[twins.denied_id == app_id].merge(apps, left_on="twin_id", right_on="app_id")
    if t.empty: raise HTTPException(404, "no twins for this id")
    return json.loads(t[["twin_id", "rank", "dist", "max_diff", "quality", *FEATS]].to_json(orient="records"))

@app.get("/fairness-report")
def fairness_report(x_audit_token: str | None = Header(None)):
    if AUDIT_TOKEN and x_audit_token != AUDIT_TOKEN: raise HTTPException(403, "demographic audit access restricted")
    return {"method": "blind within-lender financial matching, then reveal; observed/adjusted disparity only",
            "caveat": "Public HMDA lacks credit scores; a matched gap is not proof of discrimination.",
            "results": json.loads(fair.to_json(orient="records"))}

class Sim(BaseModel):
    lei: str; income: float | None = None; loan_amount: float; dti: float | None = None
    ltv: float | None = None; property_value: float | None = None; loan_term: float | None = 360

@app.post("/analyse-application")
def analyse(a: Sim):
    s = time.perf_counter()
    cand = approved[approved.lei == a.lei]
    if cand.empty: raise HTTPException(404, "lender has no approved applications in dataset")
    row = pd.DataFrame([a.model_dump()]); X, C = _matrix(row, TOL)[0], _matrix(cand, TOL)
    diff = np.abs(C - X); v = ~np.isnan(diff); n = v.sum(1)
    dist = np.where(n >= MIN_SHARED, np.where(v, diff, 0).sum(1) / np.maximum(n, 1), np.inf); mx = np.where(v, diff, 0).max(1)
    idx = np.argsort(dist)[:3]; q = quality(dist[idx], mx[idx])
    ms = (time.perf_counter() - s) * 1e3; _log({"event": "analyse", "ms": ms})
    return {"SIMULATION": True, "compute_ms": round(ms, 3), "n_candidates": len(cand),
            "twins": [{"twin_id": cand.app_id.iloc[i], "dist": float(dist[i]), "quality": str(qq),
                       **{f: (None if pd.isna(cand[f].iloc[i]) else float(cand[f].iloc[i])) for f in FEATS}} for i, qq in zip(idx, q) if np.isfinite(dist[i])],
            "disclaimer": "Simulated input; similarity is not an approval probability."}

class NoteReq(BaseModel):
    app_id: str
    use_granite: bool = True

CACHE = P / "notes_cache.json"
GRANITE_CMD = os.environ.get("SL_GRANITE_CMD", "docker exec -i notebook curl -s --max-time 120 -X POST --data-binary @- localhost:8001/note")

def _cache():
    try: return json.loads(CACHE.read_text())
    except Exception: return {}

def _granite(facts: dict):
    try:
        r = subprocess.run(GRANITE_CMD, shell=True, input=json.dumps({"facts": facts}), capture_output=True, text=True, timeout=150)
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout else None
    except Exception:
        return None

@app.post("/generate-review-note")
def note(req: NoteReq):
    if req.app_id not in queue.index: raise HTTPException(404, "not in queue")
    c = _cache()
    if req.app_id in c and req.use_granite: return {"app_id": req.app_id, "cached": True, **c[req.app_id]}
    q = queue.loc[req.app_id]; r = apps[apps.app_id == req.app_id].iloc[0]
    reasons = application(req.app_id).get("denial_reasons", [])
    rec = {"quality": q.quality, "n_strong": int(q.n_strong), "n_candidates": int(q.n_candidates), "dist": float(q.dist),
           "same_lender": True, "missing": [f for f in FEATS if pd.isna(r[f])], "denial_reasons": [DENIAL.get(x, f"code {x}") for x in reasons]}
    g = _granite(facts_for(rec)) if req.use_granite else None
    out = finalize(g["text"] if g else None, rec)
    if g: out.update(granite_gen_ms=g["gen_ms"], granite_tokens=g["n_tokens"])
    _log({"event": "note", "app_id": req.app_id, "generator": out["generator"], "validation": out["validation"]})
    if out["generator"].startswith("granite"):
        c[req.app_id] = out; CACHE.write_text(json.dumps(c))
    return {"app_id": req.app_id, "cached": False, **out}
