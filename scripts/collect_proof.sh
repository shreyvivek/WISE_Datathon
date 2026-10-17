#!/usr/bin/env bash
# Collect LinuxONE evidence (no secrets, no demographics). Usage: scripts/collect_proof.sh [key] [user@host] > docs/proof/linuxone_evidence.txt
KEY=${1:-wise_key.pem}; HOST=${2:-linux1@148.100.109.157}
ssh -i "$KEY" -o BatchMode=yes "$HOST" '
echo "== collected $(date -u +%FT%TZ) on $(hostname)"; echo "== architecture / resources"; uname -a; nproc; free -m | head -2
echo "== CPU facilities (note: nnpa listed; SecondLook CPU code does not use it)"; lscpu | grep -iE "^Architecture|^Byte|^Model name"; grep -o "nnpa\|vxe2\|sie" /proc/cpuinfo | sort -u | tr "\n" " "; echo
echo "== services"; systemctl is-active secondlook-api secondlook-granite
echo "== API health / summary"; curl -s localhost:8000/health; echo; curl -s localhost:8000/summary | cut -c1-200; echo
echo "== API benchmark (300 sequential /analyse-application, simulated input)"; cd ~/secondlook && .venv/bin/python scripts/benchmark.py http://localhost:8000 300 | grep -E "median|p95|throughput|max_rss|model_load"
echo "== full matching on this host (digests equal arm64 results)"; .venv/bin/python -I -c "import sys;sys.path.insert(0,\".\");exec(open(\"scripts/remote_matching.py\").read())" 2>&1 | grep -v Warn
echo "== Granite server"; docker exec notebook curl -s localhost:8001/health; echo
echo "== zDNN / NNPA backend lines from llama.cpp (offload then disabled: measured no speed-up)"; docker exec notebook /opt/venv/bin/python -c "
from llama_cpp import Llama
Llama(model_path=\"/home/ibm-user/granite-4.0-h-350m-base-be.f16.gguf\", n_ctx=256, verbose=True)" 2>&1 | grep -iE "ggml_zdnn_init|zDNN model buffer|NNPA" | head -8
echo "== cached validated Granite notes"; python3 -c "import json;c=json.load(open(\"data/processed/notes_cache.json\"));print(len(c),\"cached notes; generators:\",sorted({v[\"generator\"] for v in c.values()}))"
'
