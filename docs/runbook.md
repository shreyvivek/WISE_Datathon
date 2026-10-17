# Demo-day runbook
**Prereqs (laptop):** repo cloned, `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, `wise_key.pem` and `.env` (contains `AUDIT_TOKEN`) present, `chmod 600 wise_key.pem`.

1. **Check the VM** (should print `s390x`, `active`, `active`):
   `ssh -i wise_key.pem linux1@148.100.109.157 'uname -m; systemctl is-active secondlook-api secondlook-granite; curl -s localhost:8000/health'`
2. **Open the tunnel** (leave running): `ssh -i wise_key.pem -N -L 18000:localhost:8000 linux1@148.100.109.157`
3. **Start the dashboard:** `set -a; . ./.env; set +a; SL_API_URL=http://localhost:18000 .venv/bin/streamlit run dashboard/app.py` - sidebar must say `Backend: REMOTE ...`.
4. **Evidence on demand:** `scripts/collect_proof.sh > docs/proof/linuxone_evidence.txt` (benchmark, matching run on the VM, Granite/zDNN log lines, cached-note count). Saved copy: `docs/proof/linuxone_evidence.txt`.
5. **Live latency demo:** `ssh ... '~/secondlook/.venv/bin/python ~/secondlook/scripts/benchmark.py http://localhost:8000 300'`.

**Use these cases in the demo (Granite notes are cached, instant):** `b81daae6eb`, `c6b4fbcc48`, `4ac65e168a`, `e9929da378`, `a27da7e482`. A fresh Granite note takes ~13-63 s.
**If something breaks:** `sudo systemctl restart secondlook-api secondlook-granite` on the VM (wait ~20 s). If the VM is unreachable, run locally (`unset SL_API_URL`; sidebar then says LOCAL, not LinuxONE) and say so, or play the fallback recording.
**Do not say:** that LinuxONE was faster, that Telum/NNPA accelerated anything, that a gap proves discrimination, or that Granite output is unchecked.
