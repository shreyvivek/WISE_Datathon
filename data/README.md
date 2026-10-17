# Data

`raw/` and `processed/` are generated and not committed. Rebuild everything with `scripts/run_pipeline.sh`.

| Path | Contents | Produced by |
|---|---|---|
| `raw/hmda_2025_MD.csv` | HMDA 2025 loan application register, Maryland, actions 1 to 3 | `src/data/download.py` |
| `raw/shed/public2025.csv` | Federal Reserve SHED 2025 public-use file | `src/context/shed.py` |
| `processed/applications.parquet` | Cohort with financial matching features only | `src/data/preprocess.py` |
| `processed/audit_only.parquet` | Race, ethnicity, sex, age (never read by the matching code) | `src/data/preprocess.py` |
| `processed/denial_context.parquet` | Denial reasons and AUS identifiers (display only) | `src/data/preprocess.py` |
| `processed/twins_*.parquet`, `review_queue.parquet` | Matching results and review queue | `src.models.run_matching`, `run_audit` |
| `processed/*.json`, `fairness_*.csv`, `attrition.csv` | Evaluation, fairness, sensitivity and context results | `src.models.*`, `src.context.*` |

Method and cohort definition: `docs/dataset_methodology.md`.
