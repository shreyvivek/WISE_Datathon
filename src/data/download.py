"""Download HMDA 2025 LAR (Maryland, actions 1-3) from the FFIEC Data Browser API."""
import sys
from pathlib import Path
import requests

URL = "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv"
PARAMS = {"states": "MD", "years": "2025", "actions_taken": "1,2,3"}


def download(out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(URL, params=PARAMS, stream=True, timeout=600) as r:
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        if "csv" not in ctype and "octet" not in ctype and "text" not in ctype:
            raise RuntimeError(f"Unexpected content-type: {ctype}")
        with open(out, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/hmda_2025_MD.csv")
    print(download(dest), dest.stat().st_size, "bytes")
