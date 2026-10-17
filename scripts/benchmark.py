"""Measure API latency/throughput against a running service: python scripts/benchmark.py http://host:8000 [n]"""
import sys, time, statistics, requests, json
url, n = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 300
q = requests.get(f"{url}/review-queue?limit=1").json()[0]
body = {"lei": q["lei"], "income": 90, "loan_amount": 280000, "dti": 35, "ltv": 79, "property_value": 355000}
ts = []; t0 = time.perf_counter()
for _ in range(n):
    s = time.perf_counter(); requests.post(f"{url}/analyse-application", json=body).raise_for_status(); ts.append((time.perf_counter() - s) * 1e3)
tot = time.perf_counter() - t0; ts.sort()
print(json.dumps({"n": n, "median_ms": statistics.median(ts), "p95_ms": ts[int(.95 * n)], "throughput_rps": n / tot,
                  "server": requests.get(f"{url}/health").json(), "metrics": requests.get(f"{url}/metrics").json()}, indent=1))
