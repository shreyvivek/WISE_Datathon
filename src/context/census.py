"""ACS 2024 5-year county context for Maryland (median household income, population), joined to HMDA at county level.
Source order: official Census API if CENSUS_API_KEY is set (the API now rejects keyless calls), else Census Reporter
(api.censusreporter.org, same ACS 2024 5-year release 'acs2024_5yr'). Aggregate neighbourhood context only; no individual linkage."""
import json, os
import pandas as pd, requests

TABLES = {"B19013_001E": "median_household_income", "B01003_001E": "population"}


def fetch() -> tuple[pd.DataFrame, str]:
    key = os.environ.get("CENSUS_API_KEY")
    if key:
        r = requests.get("https://api.census.gov/data/2024/acs/acs5", params={"get": "NAME,B19013_001E,B01003_001E", "for": "county:*", "in": "state:24", "key": key}, timeout=60)
        r.raise_for_status(); rows = r.json(); df = pd.DataFrame(rows[1:], columns=rows[0])
        df["county_code"] = df.state + df.county
        return df.rename(columns=TABLES).astype({"median_household_income": float, "population": float})[["county_code", "NAME", "median_household_income", "population"]], "Census API (acs/acs5 2024)"
    r = requests.get("https://api.censusreporter.org/1.0/data/show/latest?table_ids=B19013,B01003&geo_ids=050|04000US24",  # '|' must stay unencoded
                     headers={"User-Agent": "SecondLook-datathon/0.1"}, timeout=60)
    r.raise_for_status(); j = r.json()
    assert j["release"]["id"] == "acs2024_5yr", j["release"]
    rows = []
    for geoid, t in j["data"].items():
        rows.append({"county_code": geoid[-5:], "NAME": j["geography"][geoid]["name"],
                     "median_household_income": t["B19013"]["estimate"]["B19013001"], "population": t["B01003"]["estimate"]["B01003001"]})
    return pd.DataFrame(rows), "Census Reporter (ACS 2024 5-year, 2020-2024)"


def build() -> dict:
    acs, source = fetch()
    apps = pd.read_parquet("data/processed/applications.parquet")
    g = apps.groupby("county_code").agg(applications=("app_id", "size"), denial_rate=("outcome", lambda s: (s == "denied").mean())).reset_index()
    q = pd.read_parquet("data/processed/review_queue.parquet")
    cov = q.groupby("county_code").eligible.mean().rename("queue_share_of_denials").reset_index()
    m = acs.merge(g, on="county_code", how="inner").merge(cov, on="county_code", how="left")
    m = m[m.applications >= 30].sort_values("median_household_income")
    corr = float(m[["median_household_income", "denial_rate"]].corr(method="spearman").iloc[0, 1])
    return {"source": source, "n_counties": int(len(m)), "spearman_income_vs_denial_rate": corr,
            "caveat": "County-level (ecological) association across counties; says nothing about individual applicants. Counties with <30 applications omitted.",
            "counties": json.loads(m.round(4).to_json(orient="records"))}


if __name__ == "__main__":
    r = build(); json.dump(r, open("data/processed/census_context.json", "w"), indent=1)
    print(r["source"], r["n_counties"], "counties; Spearman(income, denial rate) =", round(r["spearman_income_vs_denial_rate"], 2))
    for c in r["counties"][:3] + r["counties"][-3:]: print(c)
