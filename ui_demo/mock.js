/* Demo data used when the SecondLook API is not reachable (e.g. data/processed is empty).
   Aggregate numbers are the measured ones from docs/model_evaluation.md; individual cases are synthetic. */
window.MOCK = (() => {
  let s = 20261017; const rnd = () => { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; };
  const pick = a => a[Math.floor(rnd() * a.length)];
  const hex = n => { let o = ""; for (let i = 0; i < n; i++) o += "0123456789abcdef"[Math.floor(rnd() * 16)]; return o; };
  const FEATS = ["income", "loan_amount", "dti", "ltv", "property_value", "loan_term"];
  const TOL = { income: 0.15, loan_amount: 0.10, dti: 5, ltv: 5, property_value: 0.10, loan_term: 60 };
  const REL = { income: 1, loan_amount: 1, property_value: 1 };
  const LENDERS = Array.from({ length: 8 }, (_, i) => ({ lei: "5493" + hex(12).toUpperCase() + "0" + i, alias: "Lender " + "ABCDEFGH"[i] }));
  const COUNTIES = { "24003": "Anne Arundel", "24005": "Baltimore Co.", "24510": "Baltimore City", "24031": "Montgomery", "24033": "Prince George's", "24027": "Howard", "24021": "Frederick", "24017": "Charles" };
  const DENIAL = { "1": "Debt-to-income ratio", "2": "Employment history", "3": "Credit history", "4": "Collateral", "5": "Insufficient cash", "6": "Unverifiable information", "7": "Credit application incomplete", "8": "Mortgage insurance denied", "9": "Other" };

  const perturb = (app, scale) => { const t = {}; for (const f of FEATS) { const v = app[f]; if (v == null) { t[f] = null; continue; }
    const u = (rnd() * 2 - 1) * scale; t[f] = REL[f] ? +(v * (1 + u * TOL[f])).toFixed(0) : +(v + u * TOL[f]).toFixed(f === "loan_term" ? 0 : 1); } return t; };
  const dist = (a, b) => { let n = 0, sum = 0, mx = 0; for (const f of FEATS) { if (a[f] == null || b[f] == null) continue;
    const d = REL[f] ? Math.abs(a[f] - b[f]) / a[f] / TOL[f] : Math.abs(a[f] - b[f]) / TOL[f]; sum += d; mx = Math.max(mx, d); n++; } return { dist: n ? sum / n : Infinity, max_diff: mx, n }; };
  const qual = (d, mx) => d <= 0.75 && mx <= 2 ? "strong" : d <= 1.25 && mx <= 3 ? "moderate" : "weak"; // same cutoffs as src/models/financial_twins.py

  // reference case (b81daae6eb) with the values reported in the deck
  const hero = { app_id: "b81daae6eb", lei: LENDERS[2].lei, county_code: "24031", outcome: "denied", income: 141, loan_amount: 615000, dti: 46, ltv: 95, property_value: 645000, loan_term: 360, dti_is_bracket: false, completeness: 1, denial_reasons: ["4"] }; // values as in the slide deck
  const heroTwins = [
    { income: 141, loan_amount: 615000, dti: 46, ltv: 95, property_value: 645000, loan_term: 360 },
    { income: 146, loan_amount: 595000, dti: 45, ltv: 95, property_value: 625000, loan_term: 360 },
    { income: 135, loan_amount: 595000, dti: 43, ltv: 95, property_value: 635000, loan_term: 360 }];

  const apps = {}, twins = {}, queue = [];
  const add = (a, tw) => { apps[a.app_id] = a;
    for (let k = 0; k < 7; k++) tw = tw.concat([perturb(a, 1.2 + k * 0.45)]); // wider pool of approved comparators, ranked by distance
    const list = tw.map((t, i) => { const d = dist(a, t); return { twin_id: hex(10), rank: i + 1, dist: +d.dist.toFixed(3), max_diff: +d.max_diff.toFixed(2), quality: qual(d.dist, d.max_diff), ...t }; }).sort((x, y) => x.dist - y.dist);
    twins[a.app_id] = list; const best = list[0]; const n_strong = list.filter(t => t.quality === "strong").length;
    const c_match = Math.max(0, 1 - Math.min(best.dist, 1.25) / 1.25), c_count = Math.min(1, list.slice(0, 3).filter(t => t.quality === "strong").length / 3), c_lender = best.quality === "weak" ? 0 : 1, c_complete = a.completeness;
    const priority = +(100 * (0.4 * c_match + 0.2 * c_count + 0.2 * c_lender + 0.2 * c_complete)).toFixed(1);  // same weights as src/models/prioritisation.py
    a.priority_components = { c_match: +c_match.toFixed(3), c_count: +c_count.toFixed(3), c_lender: +c_lender.toFixed(3), c_complete: +c_complete.toFixed(3), priority, status: best.quality === "weak" ? "Insufficient comparable evidence" : "Queued" };
    queue.push({ app_id: a.app_id, lei: a.lei, county_code: a.county_code, n_candidates: list.length, n_strong, quality: best.quality, dist: best.dist, completeness: a.completeness, priority, eligible: best.quality !== "weak" }); };
  add(hero, heroTwins);
  for (let i = 0; i < 70; i++) {
    const inc = Math.round(45 + rnd() * 160), pv = Math.round((180 + rnd() * 520) * 1000), ltv = Math.round(60 + rnd() * 37);
    const missing = rnd() < 0.18 ? pick(["property_value", "dti", "income"]) : null;
    const a = { app_id: hex(10), lei: pick(LENDERS).lei, county_code: pick(Object.keys(COUNTIES)), outcome: "denied", income: inc, loan_amount: Math.round(pv * ltv / 100 / 1000) * 1000, dti: Math.round(25 + rnd() * 28), ltv, property_value: pv, loan_term: pick([360, 360, 360, 180, 240]), dti_is_bracket: rnd() < 0.5, denial_reasons: [pick(Object.keys(DENIAL))].concat(rnd() < 0.3 ? [pick(["3", "4", "9"])] : []) };
    if (missing) a[missing] = null; a.completeness = +(FEATS.filter(f => a[f] != null).length / 6).toFixed(2);
    const scale = pick([0.4, 0.6, 0.9, 1.3, 2.2]); add(a, [perturb(a, scale), perturb(a, scale * 1.2), perturb(a, scale * 1.6)]);
  }
  queue[0].priority = hero.priority_components.priority = 95.8; queue[0].n_candidates = 1915; // hero case leads the demo queue; candidate count as in the deck
  queue.sort((a, b) => b.priority - a.priority);
  const lenders = LENDERS.map(l => { const q = queue.filter(x => x.lei === l.lei); const n = 400 + Math.floor(rnd() * 5000); return { lei: l.lei, alias: l.alias, applications: n, denial_rate: +(0.03 + rnd() * 0.09).toFixed(4), denied: q.length, denied_with_comparator: q.filter(x => x.eligible).length }; }).sort((a, b) => b.applications - a.applications);

  const reviewers = ["reviewer-1", "reviewer-2", "reviewer-3"];
  const reviewLog = [];
  const dayAgo = h => new Date(Date.now() - h * 3600e3).toISOString();
  queue.slice(2, 26).forEach((q, i) => { if (rnd() < 0.7) reviewLog.push({ ts: dayAgo(2 + i * 3.3), app_id: q.app_id, decision: pick(["Needs additional information", "Reviewed — no conclusion", "Escalate for further review", "Reviewed — no conclusion"]), reviewer: reviewers[i % 3], comment: "", model_version: "secondlook-0.1", match_quality: q.quality, priority: q.priority, note_generator: "granite-4.0-h-350m" }); });

  const fairness = [
    { group: "Black", ref: "White", raw_rate_group: 0.131, raw_rate_ref: 0.047, raw_gap_pp: 8.4, raw_ci_lo: 7.6, raw_ci_hi: 9.2, matched_rate_group: 0.078, matched_rate_ref: 0.047, matched_gap_pp: 3.1, matched_ci_lo: 2.0, matched_ci_hi: 4.1, n_group: 6122, n_ref: 19840, n_matched: 4224, coverage: 0.69, small_sample_warning: false },
    { group: "Asian", ref: "White", raw_rate_group: 0.086, raw_rate_ref: 0.047, raw_gap_pp: 3.9, raw_ci_lo: 3.1, raw_ci_hi: 4.7, matched_rate_group: 0.058, matched_rate_ref: 0.047, matched_gap_pp: 1.1, matched_ci_lo: 0.0, matched_ci_hi: 2.2, n_group: 4292, n_ref: 19840, n_matched: 2532, coverage: 0.59, small_sample_warning: false }];
  const sensitivity = { // docs/model_evaluation.md, fairness sensitivity table
    base: { label: "same lender · strong · tol ×1", Black: [3.09, 2.1, 4.0, 0.69], Asian: [1.09, 0.0, 2.2, 0.59] },
    moderate: { label: "+ moderate matches", Black: [3.64, 2.8, 4.6, 0.85], Asian: [1.85, 0.8, 2.9, 0.79] },
    tol05: { label: "tolerances ×0.5", Black: [1.74, 0.2, 3.3, 0.30], Asian: [0.43, -1.3, 2.3, 0.24] },
    tol2: { label: "tolerances ×2", Black: [4.89, 3.9, 5.9, 0.91], Asian: [2.38, 1.4, 3.5, 0.87] },
    msa: { label: "same lender + MSA", Black: [2.89, 1.6, 4.0, 0.46], Asian: [1.05, -0.2, 2.3, 0.44] },
    market: { label: "market (MSA, cross-lender)", Black: [3.11, 2.1, 4.1, 0.93], Asian: [1.35, 0.3, 2.3, 0.93] } };
  const modelSens = { logreg: { auc_a: 0.806, auc_b: 0.816, groups: { White: [4.7, 5.5, 4.7], Black: [13.1, 11.1, 13.2], Asian: [8.6, 7.6, 8.5] } },
    xgb: { auc_a: 0.867, auc_b: 0.873, groups: { White: [4.7, 5.3, 4.7], Black: [13.1, 11.5, 13.1], Asian: [8.6, 7.7, 8.4] } } };
  const evaluation = { precision_at_200: [["Same-lender nearest (baseline A)", 0.59], ["SecondLook (constrained + priority)", 0.34], ["Random", 0.09], ["Global nearest approved (baseline B)", 0.00]],
    coverage: { strong: 1338, moderate: 388, weak: 825, none: 49 }, synthetic: "200 approved apps perturbed 1-3% and relabelled denied; mean of 5 seeds." };
  const throughput = [[1, 235, 4.0, 5.7], [2, 343, 4.9, 9.6], [4, 438, 7.9, 17.7], [8, 460, 14.0, 41.1], [16, 435, 32.3, 76.9]];
  const summary = { applications: 37491, denied: 2600, lenders: 447, denied_with_strong_comparator: 1338, review_queue_size: 1726, insufficient_evidence: 874,
    missing_share: { income: 0.021, loan_amount: 0, dti: 0.094, ltv: 0.031, property_value: 0.118, loan_term: 0.004 } };

  const QUESTIONS = { explain: "What differences could explain the denial?", strength: "How strong are the comparators?", missing: "What information is missing from this application?", reasons: "Do the stated reasons match the reported data?" };
  const rel = (a, b, f) => a == null || b == null ? null : REL[f] ? (b - a) / a / TOL[f] : (b - a) / TOL[f];
  const LBL = { income: "income", loan_amount: "loan amount", dti: "DTI", ltv: "LTV", property_value: "property value", loan_term: "loan term" };
  function reasonReview(a) { const tw = twins[a.app_id].filter(t => t.quality !== "weak"); const items = [];
    for (const c of a.denial_reasons) { const name = DENIAL[c]; let status, detail;
      if (c === "1") { const ds = tw.map(t => t.dti).filter(x => x != null); const hi = ds.filter(x => x >= a.dti).length;
        status = a.dti == null ? "Not assessable (DTI not reported)" : hi ? "Comparable approved applications had similar or higher DTI" : "Consistent with reported data";
        detail = a.dti == null ? "" : `Applicant DTI ${a.dti}%${a.dti_is_bracket ? " (bracket midpoint)" : ""}; approved twins ${ds.join("%, ")}%.`; }
      else if (c === "4") { const ls = tw.map(t => t.ltv).filter(x => x != null); status = a.ltv == null ? "Not assessable" : ls.some(x => x >= a.ltv) ? "Comparable approved applications had similar or higher LTV" : "Consistent with reported data"; detail = `Applicant LTV ${a.ltv}% vs comparators' median ${ls.sort((x, y) => x - y)[Math.floor(ls.length / 2)]}%. Appraisal details are not public.`; }
      else if (c === "5") { status = "Partly assessable"; detail = "Cash reserves are not in public HMDA; loan-to-value is comparable to approved twins."; }
      else { status = "Not assessable with public data"; detail = `${name} is not reported in HMDA; a reviewer would need the lender file.`; }
      items.push({ reason: name, status, detail }); }
    const n = items.filter(i => i.status.startsWith("Comparable")).length;
    return { summary: n ? `${n} of ${items.length} stated reason(s) are contradicted by the comparators' reported data; the rest cannot be checked with public data.` : `No stated reason is contradicted by public data; ${items.filter(i => /Not assessable/.test(i.status)).length} cannot be checked.`,
      items, evidence_to_request: ["Credit report and score used at decision time", "Automated underwriting system findings", "Verified income and asset documentation", "Appraisal / collateral review"] }; }
  function answer(qid, a) { const tw = twins[a.app_id].filter(t => t.quality !== "weak"); const best = twins[a.app_id][0];
    if (qid === "explain") { const gaps = FEATS.map(f => [f, rel(a[f], best[f], f)]).filter(x => x[1] != null).sort((x, y) => Math.abs(y[1]) - Math.abs(x[1]));
      const [f, g] = gaps[0]; return `Against the closest approved comparator the largest reported difference is ${LBL[f]} (${Math.abs(g).toFixed(2)} tolerance units, ${Math.abs(g) <= 1 ? "inside" : "outside"} tolerance). All other fields are closer. Fields not in public HMDA (credit score, assets, employment) could also explain it.`; }
    if (qid === "strength") return `${tw.length} comparators used (${tw.filter(t => t.quality === "strong").length} strong). Best distance ${best.dist} tolerance units, largest single gap ${best.max_diff}. All from the same lender.`;
    if (qid === "missing") { const m = FEATS.filter(f => a[f] == null); return m.length ? `Not reported: ${m.map(f => LBL[f]).join(", ")}. Matching used the remaining fields only, which lowers confidence.` : "All six matching fields are reported for this application. Credit history, assets and employment are never in public HMDA."; }
    return reasonReview(a).summary; }
  const notes = {}; notes[hero.app_id] = { note: "This denied application was queued because 3 approved applications from the same lender, out of 1,915 candidates, report closely similar income, loan amount, debt-to-income ratio, loan-to-value ratio, property value and loan term. The stated denial reason was collateral. Appraisal details are not in public data; a second look is recommended.", generator: "granite-4.0-h-350m", validation: "passed", granite_gen_ms: 13400, granite_tokens: 61, cached: true };
  function note(id) { if (notes[id]) return notes[id]; const q = queue.find(x => x.app_id === id); const a = apps[id]; const m = FEATS.filter(f => a[f] == null);
    return { note: `${q.n_strong || "No"} strong and ${twins[id].filter(t => t.quality === "moderate").length} moderate approved comparator(s) from the same lender were found (best distance ${q.dist}). Stated reason(s): ${a.denial_reasons.map(c => DENIAL[c]).join(", ")}.${m.length ? " Not reported: " + m.map(f => LBL[f]).join(", ") + "." : ""} Review recommended; this is not a finding about the decision.`, generator: "template-fallback", validation: "n/a", cached: false }; }
  const activity = [];
  reviewLog.slice(0, 8).forEach(e => activity.push({ ts: e.ts, kind: "decision", text: `${e.reviewer} · ${e.decision}`, app_id: e.app_id }));
  [1, 3, 5].forEach((i, k) => activity.push({ ts: dayAgo(1 + k * 1.7), kind: "note", text: "Granite note validated", app_id: queue[i].app_id }));
  [0, 4].forEach((i, k) => activity.push({ ts: dayAgo(0.5 + k), kind: "ask", text: "Question: what could explain the denial?", app_id: queue[i].app_id }));
  activity.sort((a, b) => b.ts < a.ts ? -1 : 1);

  return { FEATS, TOL, REL, DENIAL, COUNTIES, LENDERS, QUESTIONS, apps, twins, queue, lenders, reviewLog, fairness, sensitivity, modelSens, evaluation, throughput, summary, reasonReview, answer, note, activity, dist, qual, LBL,
    health: { status: "ok", arch: "s390x (replay)", python: "3.12.3", model_load_s: 0.17, version: "secondlook-0.1" }, metrics: { n_requests: 300, median_ms: 3.4, p95_ms: 4.1, max_rss_mb: 114 } };
})();
