# SecondLook — 3-minute video: script, screen directions, IBM material, screenshots
Team WISE · IBM Z Datathon 2026 · hard limit **3:00** (compulsory). The guide asks the video to cover: **problem · data · solution · how it leverages IBM Z (tech stack, show the LinuxONE instance and the model).** This script does all four and ends well under 3:00 so you have room for clicks.

Narration lines are the lines starting with `>`. Speak at a normal pace (about 150 words per minute); the budget below is ~2:30 of speech plus ~25 s of clicking and terminal output. **Rehearse once with a timer and cut a sentence rather than rush.**

---
## 0. Set-up before you hit record (10 minutes)
| Step | Do this |
|---|---|
| 1 | Terminal A (tunnel, leave running): `ssh -i wise_key.pem -N -L 18000:localhost:8000 linux1@148.100.109.157` |
| 2 | Terminal B (dashboard): `cd ~/Desktop/WISE_Datathon && set -a; . ./.env; set +a; SL_API_URL=http://localhost:18000 .venv/bin/streamlit run dashboard/app.py` — sidebar must say **Backend: REMOTE http://localhost:18000** (never record with "LOCAL"). |
| 3 | Terminal C (IBM part, big font ~18pt, dark theme): `cd ~/Desktop/WISE_Datathon` and keep this ready: `STEPS="1 2 4 5" scripts/demo_ibm.sh` (press Enter to advance each step). |
| 4 | Browser: dashboard at 110–125% zoom, sidebar visible, one window only. Open the pages in the order of the script so each is one click. |
| 5 | Dry run: use case ID `b81daae6eb` (its Granite note is cached, so it appears instantly). Do **not** pick another ID; a fresh Granite note takes 13–63 s. |
| 6 | Close anything with personal info (mail, chat, other tabs). Turn on Do Not Disturb. Record at 1080p, mic close to mouth, test 10 s of audio first. |
| 7 | **Never show:** the `.env` file, `AUDIT_TOKEN`, the contents of `wise_key.pem`, the Jupyter token, your email. The terminal command line above that sources `.env` is fine as long as you do not `cat` it. |

Tip: record the screen and the voice in one take per segment, then stitch. Segment order below matches the final cut.

---
## 1. The script (target 2:55 on screen)

### 0:00–0:18 — Problem  ·  *screen: Overview page title + big numbers*
> Two applicants. Similar finances. Different decisions. Who checks why? Millions of mortgage decisions are published as public data. SecondLook finds denials that have near-identical approved applications, and sends them to a human reviewer.

*(33 words ≈ 13 s.)*

### 0:18–0:36 — Data and scale  ·  *screen: Overview page, point at the metrics*
> We use real 2025 mortgage records for Maryland: thirty-seven thousand comparable applications, twenty-six hundred denials. Seventeen hundred have a close approved comparator at the same lender. The rest say "insufficient evidence"; we never force a flag.

*(36 words ≈ 14 s.)*  Click: sidebar → **Financial Twins**, select `b81daae6eb`.

### 0:36–1:12 — The solution: Financial Twins  ·  *screen: Financial Twins page — left application, three twins, match quality, then scroll to reason review and the Granite note*
> Here is the top case. A denied application: income a hundred forty-one thousand, loan six hundred fifteen thousand, debt-to-income forty-six, loan-to-value ninety-five. Three approved applications from the same lender sit right next to it. The first reports identical values on all six fields; the others are within a few percent. The stated reason is collateral, yet loan-to-value is ninety-five for the applicant and the twins, and appraisal details are not public. So the public data cannot explain the difference.

*(79 words ≈ 32 s.)*  On screen: hover the match-quality label, the "Not distinguished by reported data" row, and the missing-information line.

### 1:12–1:32 — Generative AI + human in the loop  ·  *screen: click "Generate reviewer note" (cached), then "Ask": What differences could explain the denial? then "Save review decision": Escalate for further review; show the history row appear*
> IBM Granite, running on LinuxONE, writes the case summary, checked against the facts. The reviewer can ask follow-up questions, answered only from the evidence, and record a decision in an audit trail. SecondLook cannot approve or overturn anything.

*(38 words ≈ 15 s.)*

### 1:32–1:55 — Fairness, carefully  ·  *screen: Blind Review / Fairness → toggle "Reveal demographic patterns" → the two gap charts*
> Matching is blind: it never sees race, sex, ethnicity or age. Now we reveal. Black applicants are denied eight points more often overall. Matched on finances at the same lender, the gap is three points, interval two to four. Credit scores are missing, so this raises questions. It does not prove discrimination.

*(52 words ≈ 21 s.)*  Numbers on screen: raw 8.4 pp → matched 3.1 pp (CI 2.0–4.1); Asian 1.1 pp.

### 1:55–2:45 — IBM LinuxONE: the instance, the stack, the model  ·  *screen: switch to Terminal C, run `STEPS="1 2 4 5" scripts/demo_ibm.sh`, press Enter at each step while talking*
> Everything runs on IBM LinuxONE. This is the instance: s390x, big-endian, three vCPUs. The API runs as a service next to the IBM-provided container, where Granite 4 runs on llama dot cpp. Now a live, simulated incoming application: matching against nineteen hundred approved applications takes about four milliseconds. Under concurrent load it serves over four hundred requests a second. Demographics sit behind a token, and results are identical to my laptop. To be straight: it is not faster than a laptop here. The point is one controlled platform for a sensitive workflow, with predictive and generative AI together.

*(98 words ≈ 39 s.)*  See section 2 for what each step shows.

### 2:45–2:58 — Close  ·  *screen: Evaluation page (honest synthetic test) fading to the title, or the architecture diagram*
> SecondLook doesn't decide who deserves a mortgage. It helps ensure that decisions worth questioning don't disappear into millions of records.

*(20 words ≈ 8 s.)*  Optional 3 s before this line, from the Evaluation page: "And we tested it honestly: plain similarity ranking does as well, so our value is evidence quality and workflow."

**Total narration ≈ 356 words ≈ 142 s of speech**, leaving ~25 s for clicks and terminal output inside 3:00.

---
## 2. What to show of IBM *inside the video* (the graders' criterion 3)
`STEPS="1 2 4 5" scripts/demo_ibm.sh` prints, in order (≈ 25 s of output):

| Step | Command output on screen | What you say / what it proves |
|---|---|---|
| 1 | `s390x`, `Architecture: s390x`, `Byte Order: Big Endian`, `vCPUs: 3`, memory | **"This is the IBM LinuxONE instance."** Real hardware identity. |
| 2 | container `notebook` (image `.../l1cc/jupyterlab-image-s390x`), `secondlook-api: active`, `secondlook-granite: active` | **Containerization + services.** Granite runs in the IBM-provided container. |
| 4 | `SIMULATION: True`, `candidates: 1915`, `server compute ms: ~4`, three twins | **Real-time inference on LinuxONE.** The word SIMULATION must be on screen (it is an invented incoming application). |
| 5 | `median_ms ~3.9`, `throughput ~250 rps`, clients 1/4/16 up to ~470 rps | **Measured performance**, not claimed. |

Also visible in the dashboard: sidebar **Backend: REMOTE** (the UI is calling the VM), Granite note caption "granite-4.0-h-350m-base · validation ok · cached", the Model Sensitivity page title "XGBoost (LinuxONE)".
If time allows (+8 s): `STEPS="6" scripts/demo_ibm.sh` shows the model server and the zDNN initialisation lines. **Say only:** "the zDNN backend initialises, but offloading was measured no faster for this model, so we make no acceleration claim." Never say Telum accelerated anything.
**Tech-stack slide (optional, 5 s, no extra narration needed):** `docs/architecture.md` rendered on GitHub (the two Mermaid flowcharts).

---
## 3. Screenshot set for the submission (evidence for the rubric)
Save to `docs/proof/screenshots/` with the filenames below. Terminal screenshots: dark theme, font 16–18pt, whole command visible. **Crop out tokens, keys, email.**

| # | File name | What to capture (exact command / place) | Rubric criterion it supports |
|---|---|---|---|
| 1 | `01_linuxone_identity.png` | `STEPS="1" scripts/demo_ibm.sh --auto` — `s390x`, Big Endian, 3 vCPUs, memory | IBM platform used |
| 2 | `02_linuxone_dashboard.png` | Your **LinuxONE Community Cloud "registered user server dashboard"** page showing your VM (open it in the browser; link is in your registration email / the guide's "Important Links") | Instance is real and yours |
| 3 | `03_containers_services.png` | `STEPS="2" scripts/demo_ibm.sh --auto` — container + both services `active` | Containerization |
| 4 | `04_systemd_status.png` | `ssh -i wise_key.pem linux1@148.100.109.157 'systemctl status secondlook-api --no-pager \| head -15'` — shows "active (running)", 3 worker processes | Reliability / scalability |
| 5 | `05_resources.png` | `ssh ... 'free -m; docker stats --no-stream; ps -eo pid,rss,args \| grep "[m]ultiprocessing" \| cut -c1-70'` | Compute resources used (memory, workers) |
| 6 | `06_jupyterlab_labs.png` | JupyterLab on the VM (`http://148.100.109.157:38888`, use your own token) with the 4 notebooks listed | Mandatory labs done |
| 7 | `07_loan_demo_executed.png` | JupyterLab → `Loan_Approval_Demo.ipynb`, scroll to executed outputs (Granite + XGBoost) | Predictive + Generative AI lab done |
| 8 | `08_granite_zdnn.png` | `STEPS="6" scripts/demo_ibm.sh --auto` — Granite health + `zDNN model buffer` / `NNPA` lines | Granite on LinuxONE; zDNN backend (state honestly: no speed-up) |
| 9 | `09_api_docs.png` | With tunnel up: browser `http://localhost:18000/docs` (FastAPI Swagger page listing all endpoints) | Technical architecture (API) |
| 10 | `10_live_request.png` | `STEPS="3 4" scripts/demo_ibm.sh --auto` — health + SIMULATION request with ~4 ms | Real-time AI on LinuxONE |
| 11 | `11_benchmark.png` | `STEPS="5" scripts/demo_ibm.sh --auto` — median/p95/throughput and clients 1/4/16 | Scalability, measured |
| 12 | `12_reproducible_matching.png` | `ssh ... 'cd ~/secondlook && .venv/bin/python -I -c "import sys;sys.path.insert(0,\".\");exec(open(\"scripts/remote_matching.py\").read())"'` — shows the three digests (`3c61072b7f`, `336b6e4fb6`, `ee656dbcf1`); next to it, your laptop's `docs/proof/linuxone_evidence.txt` | Same results on s390x and arm64 |
| 13 | `13_security_gate.png` | `STEPS="7" scripts/demo_ibm.sh --auto` (403 without token); then the same call with the token **hidden** returning 200 — or just crop the 403 | Security |
| 14 | `14_xgboost_on_linuxone.png` | `ssh ... 'ls -la ~/secondlook/data/processed/model_sensitivity_xgb.json'` plus the dashboard **Model Sensitivity** page | Predictive ML (XGBoost) on LinuxONE (trained inside the container, 32 s) |
| 15 | `15_dashboard_overview_remote.png` | Dashboard **Overview**, sidebar showing **Backend: REMOTE** | End-to-end on LinuxONE |
| 16 | `16_financial_twins.png` | **Financial Twins**, case `b81daae6eb`: twins table + match quality + reason review | Solution |
| 17 | `17_granite_note.png` | Same page after "Generate reviewer note" showing the caption (granite · validation ok · cached) | Generative AI |
| 18 | `18_ask_and_audit.png` | "Ask" answer + saved decision row in the history table | Human-in-the-loop |
| 19 | `19_fairness_reveal.png` | **Blind Review / Fairness**, toggle ON, with both charts and the caveat banner | Responsible AI |
| 20 | `20_evaluation.png` | **Evaluation** page including the honest-reading box | Technical rigor |
| 21 | `21_github_repo.png` | https://github.com/shreyvivek/WISE_Datathon README top (shows Team WISE, public) | Code link |
| 22 | `22_architecture_diagram.png` | `docs/architecture.md` rendered on GitHub (both flowcharts) | Optional flowchart |

Minimum if short on time: **1, 2, 3, 6, 7, 10, 11, 12, 13, 15, 16, 21** (12 shots, ~15 minutes).

---
## 4. After recording
1. Check the length is **under 3:00** (not "about 3:00").
2. Watch once with sound off: SIMULATION, "Backend: REMOTE", s390x and the fairness caveat must be readable.
3. Upload how the Hack2Skill form asks (file or link; if a link, make it public/unlisted and test it in a private window). Keep a local backup copy.
4. Submit title: `WISE_IBM Z Datathon 2026 Project`; description: `docs/submission_text.md`; repo: https://github.com/shreyvivek/WISE_Datathon. Checklist: `docs/submission_checklist.md`.
5. **If the VM or tunnel fails mid-recording:** `sudo systemctl restart secondlook-api secondlook-granite` on the VM and wait 20 s (see `docs/runbook.md`); do not record with the LOCAL backend, and do not claim LinuxONE for anything shown running locally.
