# Evaluation

All figures are measured on the Maryland 2025 HMDA cohort (37,491 applications, 2,600 denied) and can be reproduced with `scripts/run_pipeline.sh`. Synthetic experiments are labelled as such. Public HMDA has no ground truth for wrongful denials, so no precision or recall for real wrongful denials is reported.

## 1. Matching quality
Same-lender scope, 2,600 denied applications:

| Best-match quality | Count |
|---|---|
| strong | 1,338 |
| moderate | 388 |
| weak | 825 |
| no candidate | 49 |

The review queue is strong plus moderate: 1,726 cases. The other 874 are labelled "Insufficient comparable evidence" (506 of them have debt-to-income above 60%, where almost no approved applications exist). An unconstrained global nearest-neighbour search finds a same-lender twin only 4.1% of the time.

**Sensitivity to tolerances** (all tolerances multiplied by m; `src/models/run_eval.py`):

| m | strong share of denied | queue size | Spearman rank correlation with m = 1 |
|---|---|---|---|
| 0.5 | 23.0% | 1,023 | 0.87 |
| 1.0 | 51.5% | 1,726 | 1.00 |
| 1.5 | 65.3% | 2,237 | 0.95 |
| 2.0 | 81.0% | 2,386 | 0.93 |

**Feature balance** (standardised mean difference, denied minus best twin):

| feature | constrained (strong) | global kNN |
|---|---|---|
| income | -0.001 | -0.021 |
| loan amount | +0.001 | -0.009 |
| DTI | +0.124 | +0.037 |
| LTV | +0.012 | +0.018 |
| property value | -0.003 | -0.013 |
| loan term | -0.010 | -0.001 |

DTI shows the largest residual imbalance for the constrained method, because DTI values of 50 and above are reported as brackets and replaced by midpoints.

## 2. Review queue against baselines (synthetic)
200 real approved applications are perturbed and relabelled "denied" (injected inconsistencies with known labels) and ranked together with the 2,600 real denials. Mean of 5 seeds; `python -m src.models.run_ranking_eval`.

**Easy: 1 to 3% perturbation**

| method | K=100 | K=200 | K=400 |
|---|---|---|---|
| Baseline A: same-lender nearest (Euclidean) | P 0.48 / R 0.24 | P 0.59 / R 0.59 | P 0.50 / R 1.00 |
| Baseline B: global nearest approved | P 0.00 / R 0.00 | P 0.00 / R 0.00 | P 0.04 / R 0.07 |
| SecondLook priority score | P 0.13 / R 0.07 | P 0.34 / R 0.34 | P 0.31 / R 0.62 |
| SecondLook, tightest match first | P 0.06 / R 0.03 | P 0.30 / R 0.30 | P 0.47 / R 0.93 |
| random | P 0.08 / R 0.04 | P 0.09 / R 0.09 | P 0.07 / R 0.15 |

**Harder: 6 to 12% perturbation**

| method | K=100 | K=200 | K=400 |
|---|---|---|---|
| Baseline A: same-lender nearest (Euclidean) | P 0.01 / R 0.00 | P 0.01 / R 0.01 | P 0.05 / R 0.10 |
| Baseline B: global nearest approved | P 0.00 / R 0.00 | P 0.00 / R 0.00 | P 0.00 / R 0.01 |
| SecondLook priority score | P 0.00 / R 0.00 | P 0.02 / R 0.02 | P 0.05 / R 0.10 |
| SecondLook, tightest match first | P 0.00 / R 0.00 | P 0.01 / R 0.01 | P 0.03 / R 0.07 |
| random | P 0.08 / R 0.04 | P 0.09 / R 0.09 | P 0.07 / R 0.15 |

Reading:
1. The same-lender constraint is essential: an unconstrained search finds none of the injected cases.
2. A plain same-lender similarity ranking matches or beats the composite priority score at recovering near-duplicate cases, so no ranking-accuracy advantage over simple similarity is claimed. The composite score also rewards having several strong comparators, which 40% of the injected cases lack.
3. At the harder perturbation level no method beats random: such cases are not distinguishable from ordinary denials.
4. 195 real denials already have a near-identical approved comparator (distance 0.15 or less), so precision measured against injected cases alone has a ceiling well below 1.
5. The value of SecondLook is evidence quality and workflow: feature-specific tolerances, missing-data handling, match-quality labels, "insufficient comparable evidence", reason-aware checks, grounded questions and an audit trail. Review time and workload savings were not measured; only triage counts are reported (1,726 of 2,600 denials queued).

## 3. Fairness analysis
Matching is demographic-blind: each applicant is matched to the closest White applicant at the same lender using financial features only, and demographics are joined afterwards. Only strong matches are used. Intervals are bootstrap 95% (1,000 resamples). Results are observed disparities, not evidence of discrimination.

| Group vs White | Raw rates | Raw gap | Strongly matched (coverage) | Matched gap |
|---|---|---|---|---|
| Black | 13.1% vs 4.7% | 8.4 pp (7.4 to 9.3) | 4,148 of 6,031 (69%) | 3.1 pp (2.0 to 4.1) |
| Asian | 8.6% vs 4.7% | 3.8 pp (2.9 to 4.8) | 2,293 of 3,884 (59%) | 1.1 pp (-0.04 to 2.3) |

**Sensitivity of the matched gap** (`python -m src.models.run_fairness_sensitivity`):

| specification | Black gap (95% CI) | coverage | Asian gap (95% CI) | coverage |
|---|---|---|---|---|
| base: same lender, strong, tolerances x1 | 3.09 (2.1, 4.0) | 69% | 1.09 (0.0, 2.2) | 59% |
| plus moderate matches | 3.64 (2.8, 4.6) | 85% | 1.85 (0.8, 2.9) | 79% |
| tolerances x0.5 | 1.74 (0.2, 3.3) | 30% | 0.43 (-1.3, 2.3) | 24% |
| tolerances x2 | 4.89 (3.9, 5.9) | 91% | 2.38 (1.4, 3.5) | 87% |
| same lender and MSA | 2.89 (1.6, 4.0) | 46% | 1.05 (-0.2, 2.3) | 44% |
| market (MSA, cross-lender) | 3.11 (2.1, 4.1) | 93% | 1.35 (0.3, 2.3) | 93% |

The Black matched gap is positive in every specification (1.7 to 4.9 pp) but its size depends on matching strictness. The Asian gap is small and its interval touches or includes zero in several specifications. Stricter matching shrinks coverage sharply, so the rows describe different subpopulations. Intervals do not include uncertainty from the matching step.

**Proxy check** (5-fold logistic regression predicting Black vs White applicant): AUC 0.680 from financial features, 0.740 from county, 0.792 from both (0.5 means no signal). Finances and location both carry information about race, so blind matching does not remove all correlation with race.

## 4. Model sensitivity analysis
Exploratory. Historical decisions (denied or approved) are predicted for White, Black and Asian applicants (n = 30,254; 6.9% denied) with 5-fold out-of-fold predictions. Model A uses financial features, lender and county. Model B adds race, ethnicity, sex and age. `python -m src.models.model_sensitivity logreg|xgb`.

| model | AUC A | AUC B | White: actual / A / B | Black: actual / A / B | Asian: actual / A / B |
|---|---|---|---|---|---|
| logistic regression | 0.806 | 0.816 | 4.7% / 5.5% / 4.7% | 13.1% / 11.1% / 13.2% | 8.6% / 7.6% / 8.5% |
| XGBoost | 0.867 | 0.873 | 4.7% / 5.3% / 4.7% | 13.1% / 11.5% / 13.1% | 8.6% / 7.7% / 8.4% |

Without demographics the models under-predict denials for Black applicants and over-predict for White applicants; adding demographics removes that gap, and overall AUC changes by only 0.006 to 0.010. The public financial, lender and county fields therefore do not fully explain group differences in outcomes. This does not show that a lender used race: credit scores, assets and other underwriting inputs are absent and may correlate with race, and omitting race does not remove proxies. Historical decisions are not an approval standard, and Model B is for auditing only. XGBoost was trained inside the LinuxONE container (32 s for both models, 5 folds each).

## 5. Granite reviewer notes
IBM Granite 4.0-H 350M base (f16 GGUF) served by llama.cpp in the IBM-provided LinuxONE container.
- **Pipeline:** structured facts (counts, match quality, field names, stated reason names; no dollar amounts, no demographics) go into a 2-shot completion prompt. The output is checked by a validator that rejects invented numbers, accusatory wording and bad length, with a deterministic template as fallback. Missing-information statements and the fixed disclaimer are always added by code.
- **Validation:** 26 notes (the top 25 queue cases plus one more) passed validation on the first pass and are cached. `tests/test_core.py::test_granite_output_is_validated` covers rejection cases.
- **Latency:** about 13 s for a 44-token note in isolation and 17 to 63 s through the API on the shared VM, so notes for top cases are pre-generated. Live matching (about 4 ms) is the real-time path.
- **zDNN:** the llama.cpp log shows the zDNN backend initialised on the NNPA device (501 MiB of weights placed on it). With offload on, a 2-shot note took about 18 s against about 13 s with offload off, and about 13 s against 14 s for a 1-shot prompt (2 repetitions each, shared VM). No speed-up was observed, so the server runs with offload off and no acceleration is claimed.

## 6. IBM LinuxONE measurements
Environment: s390x, 3 vCPU, 8 GB RAM shared with the lab's JupyterLab container, Ubuntu 24.04, Python 3.12.3, numpy 1.26.4, pandas 2.1.4, scikit-learn 1.4.1 (Ubuntu packages). Raw output: `docs/proof/linuxone_evidence.txt`; collect again with `scripts/collect_proof.sh`.

- **Matching, 37,491 applications** (`scripts/remote_matching.py`): same-lender 0.65 to 0.83 s, lender and MSA 1.2 s, market (cross-lender) 4.9 to 6.0 s, peak RSS about 810 MB. The same run on an arm64 laptop took 0.37, 0.70 and 2.19 s. **The VM is not faster than the laptop for this workload.**
- **Reproducibility:** result digests are identical on s390x and arm64 for all three scopes.
- **API latency** (`/analyse-application`, simulated input, 300 sequential requests on the VM): median 3.1 to 4.4 ms, p95 4 to 11 ms across runs, about 180 to 280 requests per second, about 114 MB per worker, data load 0.15 s. From a laptop over the SSH tunnel the median is about 790 ms, dominated by the network.
- **Concurrency** (3 uvicorn workers, load generator on the same 3 vCPUs, 400 requests per level):

| clients | requests/s | median ms | p95 ms |
|---|---|---|---|
| 1 | 235 | 4.0 | 5.7 |
| 2 | 343 | 4.9 | 9.6 |
| 4 | 438 | 7.9 | 17.7 |
| 8 | 460 | 14.0 | 41.1 |
| 16 | 435 | 32.3 | 76.9 |

  Across repeated runs the throughput at 4 to 16 clients ranged from 371 to 473 requests per second. With a single worker the endpoint plateaued near 240 requests per second regardless of client count, so three workers gave about 1.9 times the peak throughput.
- **Accelerator:** the CPU flags list `nnpa`, but the NumPy and pandas code does not use it, and the Granite offload test above showed no benefit.
- **Packaging:** PyPI has no s390x wheels for numpy, pandas, scikit-learn or pyarrow, so these come from Ubuntu packages. There is no pyarrow package, so the VM reads gzipped CSV exports (`scripts/export_csv.py`). See `docs/deployment.md`.

## 7. Limitations
- Public HMDA has no credit scores, assets or employment history; historical decisions are not an approval standard.
- Matched gaps depend on matching strictness, and the intervals exclude matching uncertainty; matched controls are reused.
- DTI brackets are replaced by midpoints; exact-duplicate records produce distance 0 and ties at the top of the priority ranking.
- The ranking evaluation is synthetic and shows no accuracy advantage over simple same-lender similarity.
- Review time and workload savings were not measured.
