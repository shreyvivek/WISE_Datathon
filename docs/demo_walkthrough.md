# SecondLook — recorded demo script
Flow: **slides (Shrey) → terminal (Shrey) → dashboard (Ishita) → close (Shrey)**.
**Bold = action.** "Quotes" = spoken. Timings are for the raw take; the dashboard section is recorded at natural pace and sped up in the edit.

## Setup (Ishita, before recording)
Two terminal windows in `~/WISE_Datathon`:
```
ssh -i wise_key.pem -N -L 18000:localhost:8000 linux1@148.100.109.157
python3 ui_demo/serve.py --api http://localhost:18000 --token <AUDIT_TOKEN from ~/secondlook/.api.env on the VM>
```
Open `http://localhost:8080/?reset#overview`, Cmd+R, confirm the sidebar badge says **LIVE API**. Browser full screen.
Case `b81daae6eb` is the first row everywhere. Twin #1 is identical (distance 0.00). Stated reason: collateral.
Decisions saved in live mode are permanent — click Escalate only on the keeper take.

---

## PART 1 — SLIDES (Shrey)

**Slide 2** (0:00–0:16)
"So, imagine two people apply for a mortgage. Same income, same loan, same debts. One gets approved, the other gets denied, and almost nobody checks why. That's what SecondLook is for: an independent second look."

**Slide 3** (0:16–0:36)
"We used real public mortgage data from Maryland: about thirty-seven thousand applications, twenty-six hundred of them denials. For roughly seventeen hundred, we found an almost identical approved application at the same bank. For the rest, we just say there's not enough evidence."

**Slide 4** (0:36–0:54)
"It's pretty simple. We match only on finances: income, loan amount, debt, that kind of thing. Then IBM Granite explains the case, and a human reviewer makes the call. And the matching is blind, it never sees race or gender."

**Slide 5** (0:54–1:16)
"Now the sensitive part. Overall, Black applicants are denied about eight points more often. When we match on finances, at the same bank, it drops to about three. So finances explain a lot, but not everything, and since credit scores aren't public, it's a question to investigate, not proof."

**Slide 7** (1:16–1:23)
"And all of this runs on IBM LinuxONE, so let me show you the machine."

## PART 2 — TERMINAL (Shrey)

**Run `STEPS="1 2 4" scripts/demo_ibm.sh`** (1:23–1:55)
"So this is the actual instance: s390x, three virtual CPUs. The API and Granite run here as services, inside the IBM container. I'll send a live, simulated application, and it searches about nineteen hundred approved ones in roughly four milliseconds. Under load it handles over four hundred requests a second, and the results match my laptop. It's not faster than a laptop, though. The point is one controlled platform."

**Hand-off line (Shrey):** "And that same API is what the reviewer's dashboard talks to. Ishita."

## PART 3 — DASHBOARD (Ishita) · target 2:00 at natural pace

**Browser, Overview. Point at LIVE API badge.**
"This is the dashboard, talking to that machine live."

**Sweep the tiles.**
"Thirty-seven thousand applications. Twenty-six hundred denied. Seventeen twenty-six queued — a near-identical approval exists at the same bank. Eight seventy-four not queued: not enough evidence."

**Click Queue.**
"The reviewer's queue, ranked by match strength. Filter by lender, match, or status."

**▾ on `b81daae6eb` → Compare twins.**
"Top case. Denied."

**Point at the three cards.**
"Three approved twins, same bank."

**Point at the table.**
"The first is identical on all six fields. Zero gap."

**Click #2, #3.**
"Two and three — still inside every tolerance."

**Click View in detail.**
"So why?"

**Point at Stated reasons vs data.**
"Stated reason: collateral. But loan-to-value is 95 for the applicant and the twins. Public data can't explain it."

**Click Generate.**
"Granite writes the summary on LinuxONE. Facts only — no dollars, no demographics — every sentence checked."

**Click "What differences could explain the denial?"**
"Ask it why. It answers only from the evidence."

**Click Escalate → Save. Point at the trail.**
"The reviewer decides: escalate. Logged. The system can't approve or overturn anything."

**Click Simulate → Find twins.**
"New application, live match against the bank's approvals — four milliseconds, on the mainframe."

**Click Fairness. Let it animate.**
"Matching never sees race. Afterwards: raw gap for Black applicants, eight point four points. After matching, three point one."

**Open Matching dropdown, pick ×2, back to ×1.**
"Positive in every setting. A disparity to investigate — not proof."

**Point at Model sensitivity.**
"Without demographics the model under-predicts Black denials. Public fields don't explain the gap."

**Click System.**
"Everything on one LinuxONE VM. Four hundred sixty requests a second. Not faster than a laptop — one controlled platform."

**Hand back:** "Shrey."

## PART 4 — CLOSE (Shrey)

**Slide 8** (last ~13 s)
"So, SecondLook doesn't decide who deserves a mortgage. It just makes sure decisions worth questioning don't get lost in millions of records."

---

## Recovery
- Wrong case → sidebar **Queue**, first row ▾ → Compare twins.
- Badge says DEMO DATA → tunnel dropped; restart window 1, reload.
- Granite "Generate" slow → it's cached for b81d on the VM; if it still spins, say the line and move on, it will appear.
- Already escalated in a rehearsal → the trail shows it; just say "it's already been escalated once" or skip the Save click.
