#!/usr/bin/env bash
# Usage: scripts/deploy_linuxone.sh <user@host> <path-to-key.pem>
# Copies code + processed data (no raw data, no secrets), installs deps on the s390x VM, starts the API.
set -euo pipefail
HOST=$1; KEY=$2; R=/home/$(echo "$HOST" | cut -d@ -f1)/secondlook
SSH="ssh -i $KEY -o StrictHostKeyChecking=accept-new $HOST"
$SSH "mkdir -p $R/data/processed"
rsync -az -e "ssh -i $KEY" --exclude '.venv' --exclude 'data' --exclude '.env' --exclude '*.pem' --exclude '__pycache__' ./ "$HOST:$R/"
rsync -az -e "ssh -i $KEY" data/processed/*.parquet data/processed/fairness_report.csv "$HOST:$R/data/processed/"
$SSH "cd $R && uname -m && nproc && free -m | head -2 && python3 -m venv .venv && .venv/bin/pip install -q -r requirements-api.txt && \
  nohup .venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 & sleep 5; curl -s localhost:8000/health"
