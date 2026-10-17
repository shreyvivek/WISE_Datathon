# Model evaluation (measured; reproduce with `python -m src.models.run_eval`)

## Matching coverage (lender scope, 2,600 denied)
- Strong best-match 1,338; moderate 388; weak 825; no candidate 49. Queue = strong+moderate = 1,726; 874 'Insufficient comparable evidence'.
- Unconstrained global kNN baseline: nearest approved twin is from the same lender only 4.1% of the time.

## Tolerance sensitivity (tolerances x m)
| m | strong share of denied | queue size | Spearman vs m=1 |
|---|---|---|---|
| 0.5 | 23.0% | 1023 | 0.87 |
| 1.0 | 51.5% | 1726 | 1.00 |
| 1.5 | 65.3% | 2237 | 0.95 |
| 2.0 | 81.0% | 2386 | 0.93 |

## Feature balance (standardised mean diff, denied minus best twin)
| feature | constrained (strong) | global kNN |
|---|---|---|
| income | -0.001 | -0.021 |
| loan_amount | +0.001 | -0.009 |
| dti | +0.124 | +0.037 |
| ltv | +0.012 | +0.018 |
| property_value | -0.003 | -0.013 |
| loan_term | -0.010 | -0.001 |
DTI shows the largest residual imbalance for the constrained method (bracket midpoints).

## SYNTHETIC injection test (not real data)
300 real approved applications perturbed by 1-3% and relabelled denied. 100% entered the queue; median priority 96.0 vs 82.3 for real denials; 98% rank above the real median. This shows the score responds to near-duplicate approved comparators, not that it finds wrongful denials (no ground truth exists).

## Latency (local macOS arm64, in-process, n=200) - NOT a LinuxONE number
median 3.21 ms, p95 3.87 ms. LinuxONE numbers: run `scripts/benchmark.py` against the deployed API.

## Fairness
See `data/processed/fairness_report.csv`. Not yet done: sensitivity of gaps to geography/lender restrictions, per-group coverage beyond the two groups, Model Sensitivity Analysis (optional).
## Historical-outcome prediction
Not implemented.

## IBM LinuxONE measurements (measured 2026-10-17; VM: s390x, 3 vCPU, 8 GB RAM shared with 3 Jupyter kernels, Python 3.12.3, apt numpy 1.26.4 / pandas 2.1.4 / sklearn 1.4.1)
- Full constrained matching on the VM (`scripts/remote_matching.py`, 37,491 apps): lender 0.83 s, lender+MSA 1.24 s, market 6.04 s; peak RSS ~804 MB.
  Same workload on a MacBook (arm64): 0.38 / 0.71 / 2.19 s. **The VM is slower here; no speed-up is claimed.**
- Result digests are identical on s390x and arm64 for all three scopes (reproducibility across architectures).
- API `/analyse-application` (SIMULATION), n=300 sequential requests, on the VM itself: median 3.4 ms, p95 4.1 ms, 278 req/s; server RSS 114 MB; data+model load 0.17 s.
- Same endpoint from a laptop over an SSH tunnel: median 787 ms, p95 1,046 ms (dominated by network/tunnel; server-side processing ~4 ms per /metrics).
- CPU flags list `nnpa`, but SecondLook is plain NumPy/pandas CPU code and does **not** use the NNPA/Telum accelerator. No acceleration claim.
- Deployment notes: PyPI has no s390x wheels for numpy/pandas/scikit-learn/pyarrow, so these came from Ubuntu apt (`python3-numpy python3-pandas python3-sklearn python3-scipy`); no apt pyarrow, so the API reads gzipped CSV exports (`scripts/export_csv.py`).

## Fairness sensitivity (matched denial-rate gap vs White, percentage points; `python -m src.models.run_fairness_sensitivity`)
| spec | Black gap (95% CI) | coverage | Asian gap (95% CI) | coverage |
|---|---|---|---|---|
| base: same lender, strong, tol x1 | 3.09 (2.1, 4.0) | 69% | 1.09 (0.0, 2.2) | 59% |
| + moderate matches | 3.64 (2.8, 4.6) | 85% | 1.85 (0.8, 2.9) | 79% |
| tolerances x0.5 | 1.74 (0.2, 3.3) | 30% | 0.43 (-1.3, 2.3) | 24% |
| tolerances x2 | 4.89 (3.9, 5.9) | 91% | 2.38 (1.4, 3.5) | 87% |
| same lender + MSA | 2.89 (1.6, 4.0) | 46% | 1.05 (-0.2, 2.3) | 44% |
| market (MSA, cross-lender) | 3.11 (2.1, 4.1) | 93% | 1.35 (0.3, 2.3) | 93% |
Reading: the Black-vs-White matched gap stays positive in every specification (1.7-4.9 pp) but its size depends on matching strictness; the Asian-vs-White gap is
small and its interval touches or includes zero in several specifications. Stricter matching shrinks coverage sharply, so the estimates are for different subpopulations.
Intervals ignore matching uncertainty. These are observed disparities, not evidence of discrimination.

## Proxy check (5-fold CV logistic regression predicting Black vs White applicant)
AUC: financial features only 0.680; county only 0.740; both 0.792 (0.5 = no signal). Financial characteristics and location both carry information about race,
so "blind" matching does not remove all correlation with race; this is a limitation of any public-HMDA matching, and a reason the gap is an observed (not causal) quantity.

## Model Sensitivity Analysis (exploratory; `python -m src.models.model_sensitivity logreg|xgb`)
Predict the HISTORICAL decision (denied vs approved) for White/Black/Asian applicants (n=30,254; 6.9% denied) with 5-fold out-of-fold predictions.
Model A = financial features + lender + county, no demographics. Model B = A + race, ethnicity, sex, age. XGBoost ran inside the LinuxONE container (s390x, 32 s for both models x 5 folds, shared CPU).
| model | AUC A | AUC B | White actual / predA / predB | Black actual / predA / predB | Asian actual / predA / predB |
|---|---|---|---|---|---|
| logistic regression | 0.806 | 0.816 | 4.7% / 5.5% / 4.7% | 13.1% / 11.1% / 13.2% | 8.6% / 7.6% / 8.5% |
| XGBoost | 0.867 | 0.873 | 4.7% / 5.3% / 4.7% | 13.1% / 11.5% / 13.1% | 8.6% / 7.7% / 8.4% |
Reading: without demographics the models under-predict denials for Black applicants and over-predict for White applicants; adding demographics removes that gap (by construction, since group
base rates are then learnable). Overall AUC barely changes (+0.006 to +0.010). This means the group differences in outcomes are not fully explained by the public financial/lender/county
fields. It does NOT show that a lender used race: credit scores, assets and other underwriting inputs are absent and may correlate with race; and omitting race does not remove proxies (see proxy check).
Historical decisions are not an approval standard; Model B is for auditing only. Calibration bins for Model A are in the JSON outputs. Precision/recall are reported at the threshold giving the base-rate share of predicted denials.

## Granite reviewer notes (IBM Granite 4.0-H 350M *base*, f16 GGUF, llama.cpp in the provided LinuxONE container)
- Flow: structured facts JSON -> 2-shot raw-completion prompt -> Granite -> **validator** (rejects invented numbers, accusatory wording, bad length) -> deterministic template fallback; the missing-information sentence and the fixed disclaimer are always appended by code, never by the model.
- 25 of 25 pre-generated notes for the top queue cases passed validation on the first pass (cached on the VM); plus 4 further live API tests, all validated. `tests/test_core.py::test_granite_output_is_validated` covers rejection cases.
- Latency (shared 3-vCPU VM): ~13 s for a 44-token note measured in isolation; 17-63 s through the API (shared VM, other work running; one uncached request took 63 s). Not real-time, so notes for the top-25 queue cases are pre-generated and cached; live matching (~4 ms) is the real-time path.
- zDNN/NNPA: the llama.cpp log shows the zDNN backend initialised on the NNPA device (501 MiB of weights placed on it). Measured effect: with offload on (n_gpu_layers=-1) a 2-shot note took ~18 s vs ~13 s with offload off, and ~13 s vs ~14 s with a 1-shot prompt. **No speed-up was observed for this model, so the server runs with offload off and we make no acceleration claim.** Single shared VM, 2 repetitions each; treat as indicative.
- A 350M base model is weak at instruction following; it works here only because the prompt is tightly constrained and every output is validated.
