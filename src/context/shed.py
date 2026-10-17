"""Federal Reserve SHED 2025: weighted, SUPPLEMENTARY credit-access context. Never joined to HMDA applicants (different populations).
Base for A1_* items = respondents who applied for any credit in the past 12 months (A0 = Yes). Uses `weight` (scaled to sample size);
CIs are a respondent-level weighted bootstrap (approximate; the public file has no strata/PSU design variables)."""
import io, json, zipfile
from pathlib import Path
import numpy as np, pandas as pd
import requests

URL = "https://www.federalreserve.gov/consumerscommunities/files/SHED_public_use_data_2025_%28CSV%29.zip"
CSV = Path("data/raw/shed/public2025.csv")


def download() -> Path:
    """Fetch the public-use SHED 2025 CSV from the Federal Reserve (skipped if already present)."""
    if not CSV.exists():
        r = requests.get(URL, timeout=120); r.raise_for_status()
        CSV.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            CSV.write_bytes(z.read("public2025.csv"))
    return CSV


RACE = ["White", "Black", "Hispanic", "Asian", "Other"]
ITEMS = {"A1_a": "Turned down for credit (past 12 months)", "A1_b": "Approved for less credit than requested",
         "A1_c": "Put off applying because expected to be turned down"}


def wprop(y, w):
    return float(np.sum(w * y) / np.sum(w))


def boot_ci(y, w, n_boot=1000, seed=0):
    rng = np.random.default_rng(seed); n = len(y)
    s = [wprop(y[i], w[i]) for i in (rng.integers(0, n, n) for _ in range(n_boot))]
    return [float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))]


def build(path=CSV) -> dict:
    d = pd.read_csv(path, low_memory=False)
    yn = {"Yes": 1.0, "No": 0.0}
    for c in ["A0", *ITEMS]: d[c] = d[c].map(yn)  # labelled text in the public CSV
    app = d[d.A0 == 1].copy(); out = {"source": "Federal Reserve SHED 2025 (public use)", "weights": "weight (scaled to sample size)",
                                       "n_respondents": int(len(d)), "n_applied_for_credit": int(len(app)), "items": {}}
    for item, label in ITEMS.items():
        rows = []
        for name in ["All", *RACE]:
            g = app if name == "All" else app[app.race_5cat == name]
            g = g[g[item].isin([0, 1])]
            if len(g) == 0: continue
            y, w = g[item].to_numpy(float), g.weight.to_numpy(float)
            rows.append({"group": name, "n": int(len(g)), "weighted_share": wprop(y, w), "ci95": boot_ci(y, w),
                         "small_n_warning": bool(len(g) < 100)})
        out["items"][item] = {"label": label, "by_group": rows}
    out["caveat"] = ("Items cover all credit types (cards, auto, student, mortgage, other), not mortgages specifically. Survey of US adults (not mortgage applicants in Maryland); respondents cannot be linked to HMDA records. "
                     "Shown only as context for wider credit-access differences.")
    return out


if __name__ == "__main__":
    download(); r = build(); json.dump(r, open("data/processed/shed_context.json", "w"), indent=1)
    for k, v in r["items"].items():
        print(k, v["label"]); [print("  ", x["group"].ljust(9), f"n={x['n']:5d}", f"{x['weighted_share']:.1%}", [f"{c:.1%}" for c in x["ci95"]], "SMALL-N" if x["small_n_warning"] else "") for x in v["by_group"]]
