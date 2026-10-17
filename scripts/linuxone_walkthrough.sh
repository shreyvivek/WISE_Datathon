#!/usr/bin/env bash
# Step-by-step terminal walkthrough of the LinuxONE deployment: machine, services, live request, load, Granite, access control.
# Press Enter to run each step, or pass --auto to run without pauses.
# Usage: scripts/linuxone_walkthrough.sh [--auto]
#        STEPS="1 2 4 5" scripts/linuxone_walkthrough.sh     (run only some steps)
# Needs wise_key.pem in the repo root; prints no secrets.
KEY=${KEY:-wise_key.pem}; HOST=${HOST:-linux1@148.100.109.157}; AUTO=$1
RUN=1
CP="-o ControlMaster=auto -o ControlPath=/tmp/sl-ssh-%r@%h -o ControlPersist=120"  # one SSH connection reused by every step (faster)
R() { [ "$RUN" = 1 ] || return 0; ssh $CP -i "$KEY" -o BatchMode=yes -o LogLevel=ERROR "$HOST" "$1"; }
COUNT=0
step() { n=${1%%.*}; if [ -n "$STEPS" ] && [[ " $STEPS " != *" $n "* ]]; then RUN=0; return; fi; RUN=1; COUNT=$((COUNT+1)); printf '\n\033[1m== Step %s: %s\033[0m\n' "$COUNT" "${1#*. }"; [ "$AUTO" = "--auto" ] || read -r -p "   (Enter to run) " _; }
step "1. The machine: IBM LinuxONE, s390x, big-endian"
R 'uname -m; lscpu | grep -E "^Architecture|^Byte Order"; echo "vCPUs: $(nproc)"; free -m | sed -n 1,2p'
step "2. The platform: containers + services (Granite runs in the IBM-provided container)"
R 'docker ps --format "container: {{.Names}}  image: {{.Image}}" | cut -c1-110; for s in secondlook-api secondlook-granite; do echo "$s: $(systemctl is-active $s)"; done'
step "3. The API on LinuxONE"
R 'curl -s localhost:8000/health; echo; curl -s localhost:8000/summary | python3 -c "import sys,json;d=json.load(sys.stdin);print(\"applications:\",d[\"applications\"],\"| denied:\",d[\"denied\"],\"| queued:\",d[\"review_queue_size\"])"'
step "4. A live request (SIMULATED incoming application) - matching runs on this machine"
R 'curl -s -w "\nround trip on the VM: %{time_total}s\n" -X POST localhost:8000/analyse-application -H "content-type: application/json" -d "{\"lei\":\"549300FGXN1K3HLB1R50\",\"income\":141,\"loan_amount\":615000,\"dti\":46,\"ltv\":95,\"property_value\":645000}" | python3 -c "
import sys,json
t=sys.stdin.read().rsplit(chr(10),2); d=json.loads(t[0]); print(\"SIMULATION:\",d[\"SIMULATION\"],\"| candidates:\",d[\"n_candidates\"],\"| server compute ms:\",d[\"compute_ms\"])
[print(\"  twin\",i+1,x[\"quality\"],\"dist\",round(x[\"dist\"],2),\"income\",x[\"income\"],\"loan\",x[\"loan_amount\"]) for i,x in enumerate(d[\"twins\"])]; print(t[1])"'
step "5. Measured performance (300 requests, then concurrent clients)"
R 'cd ~/secondlook && .venv/bin/python scripts/benchmark.py http://localhost:8000 300 | python3 -c "import sys,json;d=json.load(sys.stdin);print(\"one client:  median %.1f ms | p95 %.1f ms | %.0f requests/s\"%(d[\"median_ms\"],d[\"p95_ms\"],d[\"throughput_rps\"]))"; .venv/bin/python scripts/benchmark_concurrent.py http://localhost:8000 300 | python3 -c "import sys,json; [print(\"%2s clients:  median %3.0f ms | p95 %3.0f ms | %3.0f requests/s\"%(k,v[\"median_ms\"],v[\"p95_ms\"],v[\"rps\"])) for k,v in json.load(sys.stdin)[\"levels\"].items() if k in (\"4\",\"16\")]"'
step "6. IBM Granite 4.0 (generative AI) served by llama.cpp inside the container"
R 'docker exec notebook curl -s localhost:8001/health; echo; docker exec notebook /opt/venv/bin/python -c "
from llama_cpp import Llama
Llama(model_path=\"/home/ibm-user/granite-4.0-h-350m-base-be.f16.gguf\", n_ctx=256, verbose=True)" 2>&1 | grep -E "zDNN model buffer|NNPA name|found 1 device" | head -3'
step "7. Security: demographic audit endpoint is token-gated"
R 'curl -s -o /dev/null -w "fairness-report WITHOUT token -> HTTP %{http_code}\n" localhost:8000/fairness-report; echo "SecondLook API/Granite are not exposed to the internet; reached through an SSH tunnel"'
exit 0
