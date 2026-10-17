"""Throughput/latency under concurrent clients: python scripts/benchmark_concurrent.py http://host:8000 [requests_per_level]
Uses the simulated-application endpoint (read-only). Client runs on the same host unless pointed elsewhere."""
import sys, time, statistics, json
from concurrent.futures import ThreadPoolExecutor
import requests

url, n = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 400
q = requests.get(f"{url}/review-queue?limit=1").json()[0]
body = {"lei": q["lei"], "income": 90, "loan_amount": 280000, "dti": 35, "ltv": 79, "property_value": 355000}
s = requests  # new connection per request (a keep-alive Session showed a ~50 ms delayed-ACK artifact with multi-worker uvicorn)

def one(_):
    t = time.perf_counter(); r = s.post(f"{url}/analyse-application", json=body); r.raise_for_status(); return (time.perf_counter() - t) * 1e3

res = {}
for workers in (1, 2, 4, 8, 16):
    t0 = time.perf_counter()
    with ThreadPoolExecutor(workers) as ex: lat = sorted(ex.map(one, range(n)))
    wall = time.perf_counter() - t0
    res[workers] = {"requests": n, "rps": round(n / wall, 1), "median_ms": round(statistics.median(lat), 1), "p95_ms": round(lat[int(.95 * n)], 1), "max_ms": round(lat[-1], 1)}
print(json.dumps({"endpoint": "/analyse-application (SIMULATION)", "levels": res}, indent=1))
