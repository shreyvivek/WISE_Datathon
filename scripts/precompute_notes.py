"""Pre-generate Granite notes for the top-N queue cases (Granite takes ~13 s/note on the shared VM). Usage: python scripts/precompute_notes.py http://localhost:8000 25"""
import sys, requests, time
url, n = sys.argv[1], int(sys.argv[2]); ok = 0
for r in requests.get(f"{url}/review-queue?limit={n}").json():
    t = time.time(); x = requests.post(f"{url}/generate-review-note", json={"app_id": r["app_id"]}, timeout=200).json()
    ok += x["generator"].startswith("granite"); print(r["app_id"], x["generator"], x["validation"], f"{time.time()-t:.1f}s", flush=True)
print(f"granite-validated {ok}/{n}")
