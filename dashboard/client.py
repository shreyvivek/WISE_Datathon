"""API client: remote SecondLook service if SL_API_URL is set, else in-process (labelled LOCAL)."""
import os
import requests

URL = os.environ.get("SL_API_URL")
TOKEN = os.environ.get("AUDIT_TOKEN")
if not URL:
    from fastapi.testclient import TestClient
    from src.api.main import app
    _c = TestClient(app)

MODE = f"REMOTE {URL}" if URL else "LOCAL (in-process, not LinuxONE)"
DENIAL = {"1": "Debt-to-income ratio", "2": "Employment history", "3": "Credit history", "4": "Collateral",
          "5": "Insufficient cash", "6": "Unverifiable information", "7": "Credit application incomplete",
          "8": "Mortgage insurance denied", "9": "Other"}

def call(method, path, **kw):
    hdr = {"X-Audit-Token": TOKEN} if TOKEN else {}
    r = requests.request(method, URL + path, headers=hdr, timeout=30, **kw) if URL else _c.request(method, path, headers=hdr, **kw)
    r.raise_for_status()
    return r.json(), float(r.headers.get("X-Process-Ms", "nan"))
