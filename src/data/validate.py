"""Profile the raw HMDA CSV: shape, columns, outcomes, missingness, cohort filter attrition."""
import sys
import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/hmda_2025_MD.csv"
df = pd.read_csv(path, dtype=str, low_memory=False)
print("rows, cols:", df.shape)
print("columns:", list(df.columns))
print("\naction_taken:\n", df["action_taken"].value_counts(dropna=False))
for c in ["loan_type", "loan_purpose", "lien_status", "occupancy_type", "derived_dwelling_category",
          "derived_loan_product_type", "reverse_mortgage", "open-end_line_of_credit", "business_or_commercial_purpose"]:
    print(f"\n{c}:\n", df[c].value_counts(dropna=False).head(8))
for c in ["income", "loan_amount", "debt_to_income_ratio", "loan_to_value_ratio", "property_value", "loan_term"]:
    print(f"\n{c} missing/NA/Exempt:", df[c].isna().mean().round(3), (df[c] == "Exempt").mean().round(3))
    print(df[c].value_counts(dropna=False).head(6).to_dict())
print("\nraces:\n", df["derived_race"].value_counts(dropna=False))
print("lenders:", df["lei"].nunique())

m = df
steps = [("action_taken in 1,2,3", m.action_taken.isin(["1", "2", "3"])),
         ("conventional (loan_type=1)", m.loan_type == "1"),
         ("home purchase (loan_purpose=1)", m.loan_purpose == "1"),
         ("first lien (lien_status=1)", m.lien_status == "1"),
         ("owner-occupied (occupancy_type=1)", m.occupancy_type == "1"),
         ("single family site-built", m.derived_dwelling_category.fillna("").str.startswith("Single Family")
              & m.derived_dwelling_category.fillna("").str.contains("Site-Built"))]
print("\nCohort attrition:")
for name, mask in steps:
    m = m[mask.loc[m.index]]
    print(f"  {name:40s} -> {len(m):,}")
print("denied:", (m.action_taken == "3").sum(), " lenders:", m.lei.nunique())
