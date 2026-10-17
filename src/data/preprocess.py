"""Build the comparable cohort and split it into three leak-safe tables.

Outputs (data/processed/):
  applications.parquet  - anonymised id, lender, structural fields, financial matching features, outcome
  audit_only.parquet    - id + race/ethnicity/sex/age. NEVER read by the matching code.
  denial_context.parquet- id + denial reasons + AUS ids. Shown to reviewers only, never used for matching.
  attrition.csv         - rows remaining after each cohort filter
"""
import hashlib
import sys
from pathlib import Path
import numpy as np
import pandas as pd

RAW = Path("data/raw/hmda_2025_MD.csv")
OUT = Path("data/processed")
SALT = "secondlook-2026"  # id salt; ids are not reversible to HMDA rows without the raw file + salt

DTI_BRACKETS = {"<20%": 15.0, "20%-<30%": 25.0, "30%-<36%": 33.0, "50%-60%": 55.0, ">60%": 65.0}


def parse_dti(s: pd.Series) -> pd.DataFrame:
    """Numeric DTI (bracket midpoints for bracketed values) + flags; unknown stays NaN, never 0."""
    num = pd.to_numeric(s, errors="coerce")
    mid = s.map(DTI_BRACKETS)
    return pd.DataFrame({
        "dti": num.fillna(mid),
        "dti_is_bracket": mid.notna(),
        "dti_missing": num.isna() & mid.isna(),
    })


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")  # 'Exempt' / 'NA' -> NaN


def main() -> None:
    df = pd.read_csv(RAW, dtype=str, low_memory=False)
    steps, rows = [("raw (MD 2025, actions 1-3)", df)], []
    filters = [
        ("action_taken in 1,2,3", lambda d: d.action_taken.isin(["1", "2", "3"])),
        ("conventional", lambda d: d.loan_type == "1"),
        ("home purchase", lambda d: d.loan_purpose == "1"),
        ("first lien", lambda d: d.lien_status == "1"),
        ("owner-occupied", lambda d: d.occupancy_type == "1"),
        ("single-family site-built", lambda d: d.derived_dwelling_category == "Single Family (1-4 Units):Site-Built"),
        ("not reverse / HELOC / business", lambda d: (d.reverse_mortgage == "2") & (d["open-end_line_of_credit"] == "2")
                                                       & (d.business_or_commercial_purpose == "2")),
    ]
    attr = [("raw", len(df))]
    for name, f in filters:
        df = df[f(df)]
        attr.append((name, len(df)))
    df = df.reset_index(drop=True)

    df["app_id"] = [hashlib.sha256(f"{SALT}{i}{l}".encode()).hexdigest()[:10] for i, l in enumerate(df.lei)]
    dti = parse_dti(df["debt_to_income_ratio"])
    apps = pd.DataFrame({
        "app_id": df.app_id, "lei": df.lei, "county_code": df.county_code,
        "census_tract": df.census_tract, "msa": df["derived_msa-md"],
        "outcome": np.where(df.action_taken == "3", "denied", "approved"),
        "action_taken": df.action_taken.astype(int),
        "income": num(df.income),                     # $ thousands
        "loan_amount": num(df.loan_amount),
        "ltv": num(df.loan_to_value_ratio),
        "property_value": num(df.property_value),
        "loan_term": num(df.loan_term),
    }).join(dti)
    apps.loc[apps.income <= 0, "income"] = np.nan     # 0 income is a reporting artefact, not a real value
    apps.loc[apps.ltv <= 0, "ltv"] = np.nan
    for c in ["income", "ltv", "property_value", "loan_term"]:
        apps[f"{c}_missing"] = apps[c].isna()
    feats = ["income", "loan_amount", "dti", "ltv", "property_value", "loan_term"]
    apps["n_feats"] = apps[feats].notna().sum(axis=1)
    apps["completeness"] = apps.n_feats / len(feats)

    audit = pd.DataFrame({"app_id": df.app_id, "race": df.derived_race, "ethnicity": df.derived_ethnicity,
                          "sex": df.derived_sex, "age": df.applicant_age})
    ctx = df[["app_id", "denial_reason-1", "denial_reason-2", "denial_reason-3", "denial_reason-4",
              "aus-1", "aus-2", "aus-3", "aus-4", "aus-5"]].copy()

    OUT.mkdir(parents=True, exist_ok=True)
    apps.to_parquet(OUT / "applications.parquet"); audit.to_parquet(OUT / "audit_only.parquet")
    ctx.to_parquet(OUT / "denial_context.parquet")
    pd.DataFrame(attr, columns=["step", "rows"]).to_csv(OUT / "attrition.csv", index=False)
    print(pd.DataFrame(attr, columns=["step", "rows"]).to_string(index=False))
    print(apps.outcome.value_counts().to_dict(), "lenders:", apps.lei.nunique())
    print("missing share:\n", apps[feats].isna().mean().round(3).to_string())
    print("completeness (denied vs approved):\n", apps.groupby("outcome").completeness.mean().round(3).to_string())


if __name__ == "__main__":
    main()
