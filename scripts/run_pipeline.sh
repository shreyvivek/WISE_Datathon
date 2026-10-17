#!/usr/bin/env bash
# Rebuild every dataset, result file and evaluation from scratch (needs network access; a few minutes).
# Usage: scripts/run_pipeline.sh        (set PY to use a different interpreter)
set -euo pipefail
PY=${PY:-.venv/bin/python}
$PY src/data/download.py                     # HMDA 2025, Maryland -> data/raw
$PY src/data/preprocess.py                   # cohort + leak-safe tables -> data/processed
$PY -m src.models.run_matching               # financial-twin matching (3 scopes)
$PY -m src.models.run_audit                  # review queue + blind fairness audit
$PY -m src.models.run_eval                   # matching quality, tolerance sensitivity, latency
$PY -m src.models.run_ranking_eval           # ranking vs baselines (synthetic)
$PY -m src.models.run_fairness_sensitivity   # gap sensitivity + proxy check
$PY -m src.models.model_sensitivity logreg   # model sensitivity analysis
$PY -m src.models.model_sensitivity xgb
$PY -m src.context.shed                      # SHED 2025 context
$PY -m src.context.census                    # ACS 2024 county context
echo "done: results are in data/processed"
