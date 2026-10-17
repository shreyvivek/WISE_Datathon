# Dataset & methodology
**Data:** HMDA 2025 LAR, Maryland, action_taken 1/2/3 (177,171 rows; FFIEC Data Browser API). Raw file is not committed (`data/raw/`).
**Cohort (37,491):** conventional, home purchase, first lien, owner-occupied, single-family site-built, not reverse/HELOC/business
(attrition table: `data/processed/attrition.csv`). 34,891 approved (actions 1,2) / 2,600 denied; 447 lenders.
**Missing values:** 'Exempt'/'NA' -> NaN, never 0. DTI brackets -> midpoints (`dti_is_bracket` kept). income<=0 and ltv<=0 -> NaN. Rows are kept
if >=4 of 6 financial features are shared with a candidate (including loan amount).
**Leakage control:** three tables. `applications.parquet` (matching inputs only), `audit_only.parquet` (race/ethnicity/sex/age),
`denial_context.parquet` (denial reasons, AUS ids - display only). Test `test_matching_inputs_have_no_demographics` enforces this.
**Similarity:** per-feature scaled difference |a-b|/tol (log-ratio for income/loan/property value; tol 15%/10%/10%; DTI 5 pts, LTV 5 pts, term 60 mo).
Distance = mean over shared features. strong: dist<=0.75 & max<=2; moderate: dist<=1.25 & max<=3. Not a probability.
**Scopes:** lender (primary), lender+MSA, market (cross-lender), global kNN baseline.
**Disparity:** within-lender 1-NN (with replacement) from each group's applications to White applications, financial features only; only strong
pairs used; bootstrap 1,000 resamples of the group's pairs. Raw-gap CI bootstraps both groups. Observed/adjusted disparity only.
**Limitations:** no credit scores/assets/employment in public HMDA; historical decisions are not ground truth; matched controls reused; CIs ignore
matching uncertainty; race "Not Available"/Joint excluded from comparisons; location as a proxy for race is not yet evaluated; DTI bracket midpoints add noise;
exact-duplicate records (round-number loans) yield distance 0 and create ties at priority 100.

## Supplementary context data
**SHED 2025** (`src/context/shed.py`; Federal Reserve public-use CSV + codebook): weighted shares (variable `weight`, scaled to sample size) of adults who applied for credit in the past 12 months
and were turned down (A1_a), offered less credit (A1_b) or put off applying (A1_c), by race/ethnicity (`race_5cat`). Confidence intervals are an approximate respondent-level weighted bootstrap (the public file
lacks strata/PSU variables). Items cover ALL credit types, not mortgages; the mortgage-specific item A8_d was dropped because its respondent base is unclear. SHED respondents are never joined to HMDA applicants.
**Census ACS 2024 5-year** (`src/context/census.py`): county median household income (B19013_001E) and population (B01003_001E) for Maryland counties, joined to HMDA by county FIPS (24 counties with >=30 applications).
The official API (api.census.gov) now rejects keyless calls (redirect to `missing_key`), and no key was available, so the data came from Census Reporter (same release, id `acs2024_5yr`, 2020-2024).
Set `CENSUS_API_KEY` to use the official API instead (code path implemented, not exercised). County-level association (Spearman income vs denial rate = -0.45) is ecological and says nothing about individuals.
HMDA's own tract fields (tract income percentage, minority share) are available but not yet used in matching.
