# Submission checklist (from the Participant Guidebook)
**Deadline:** Day 2 ends **Oct 18, 10:00 AM local** (closing ceremony 10:30). Submit at https://hack2skill.com/event/datathon-2026.
- [x] **Project title contains the team name** - `WISE_IBM Z Datathon 2026 Project` (text in `docs/submission_text.md`).
- [ ] **Video, max 3:00 (compulsory)** covering: problem statement, data supporting the problem, solution, and how it leverages IBM Z (tech stack, **show the LinuxONE instance and model**). Follow `docs/demo_script.md`, use `docs/runbook.md`.
- [x] **Code**: https://github.com/shreyvivek/WISE_Datathon - verified public (anonymous access returns 200).
- [ ] **Open-source links** (rule 5): in README "Libraries and open-source resources" table.
- [ ] Optional: flowchart (`docs/architecture.md`, Mermaid) and prototype (dashboard; runbook).
- [ ] **Screenshots as platform evidence** (judging criterion 3 asks for containerization, security, scalability, compute): `uname -m` s390x + `systemctl status secondlook-*`; `docker ps` showing the lab container running Granite; `docs/proof/linuxone_evidence.txt`; concurrency table; zDNN init log lines; token-gated 403 vs 200.
- [x] **Mandatory labs**: all four notebooks are executed on the VM with 0 errors (`docs/proof/labs_completed.md`). Take a screenshot of the executed Loan_Approval_Demo in JupyterLab as visual proof.
- [ ] Event code in project description, if the platform asks (guide lists it as TBD).
- [ ] Originality: all code written 17-18 Oct 2026 (git history shows first commit 2026-10-17); no code reused from the IBM demo.
- [ ] Rule 7 framing: project audits lending *processes*; it does not bash any group or take a political position; fairness results are stated as observed disparities with caveats.
