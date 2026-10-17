/* Data layer. Tries the SecondLook FastAPI (same origin, or ?api=http://host:port); falls back to MOCK. */
window.API = (() => {
  const M = window.MOCK;
  const qs = new URLSearchParams(location.search);
  const BASE = qs.get("api") || (location.protocol.startsWith("http") ? location.origin : "");
  const TOKEN = qs.get("token") || localStorage.getItem("sl_token") || "";
  let live = null; // null = unknown, true/false
  const LS = k => { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch { return null; } };
  const localLog = () => LS("sl_review_log") || [];

  async function http(method, path, body) {
    const r = await fetch(BASE + path, { method, headers: { "content-type": "application/json", ...(TOKEN ? { "x-audit-token": TOKEN } : {}) }, body: body ? JSON.stringify(body) : undefined });
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
    return { data: await r.json(), ms: parseFloat(r.headers.get("x-process-ms") || "NaN") };
  }
  async function probe() {
    if (live !== null) return live;
    if (!BASE) { live = false; return live; }
    try { const c = new AbortController(); setTimeout(() => c.abort(), 1500); const r = await fetch(BASE + "/health", { signal: c.signal }); live = r.ok && (await r.json()).status === "ok"; }
    catch { live = false; }
    return live;
  }
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // each call: live → API; else mock (with a tiny delay so loading states show)
  async function call(path, mockFn, method = "GET", body) {
    if (await probe()) { try { return await http(method, path, body); } catch (e) { console.warn("API failed, using demo data:", e.message); } }
    await sleep(60); return { data: mockFn(), ms: 3.2 + Math.random() };
  }
  const statusMap = () => { const st = {}; for (const e of [...M.reviewLog, ...localLog()]) st[e.app_id] = e.decision; return st; };

  return {
    isLive: probe, base: BASE,
    summary: () => call("/summary", () => M.summary),
    queue: (limit = 200) => call(`/review-queue?limit=${limit}`, () => { const st = statusMap(); return M.queue.filter(q => q.eligible).slice(0, limit).map(q => ({ ...q, review_status: st[q.app_id] || "Pending review" })); }),
    lenders: () => call("/lenders", () => M.lenders),
    application: id => call(`/application/${id}`, () => ({ ...M.apps[id] })),
    twins: id => call(`/application/${id}/twins`, () => M.twins[id]),
    reasonReview: id => call(`/application/${id}/reason-review`, () => ({ app_id: id, ...M.reasonReview(M.apps[id]) })),
    questions: () => call("/questions", () => M.QUESTIONS),
    ask: (app_id, question_id) => call("/ask", () => ({ app_id, question: M.QUESTIONS[question_id], answer: M.answer(question_id, M.apps[app_id]) }), "POST", { app_id, question_id }),
    note: (app_id, use_granite = true) => call("/generate-review-note", () => ({ app_id, ...M.note(app_id) }), "POST", { app_id, use_granite }),
    decide: (app_id, decision, reviewer, comment) => call("/review-decision", () => {
      const q = M.queue.find(x => x.app_id === app_id);
      const e = { ts: new Date().toISOString(), app_id, decision, reviewer, comment, model_version: "secondlook-0.1", match_quality: q.quality, priority: q.priority, note_generator: "demo" };
      localStorage.setItem("sl_review_log", JSON.stringify([...localLog(), e])); return { recorded: true, entry: e, note: "Advisory workflow only: no loan decision is changed." }; }, "POST", { app_id, decision, reviewer, comment }),
    reviewLog: app_id => call(`/review-log${app_id ? "?app_id=" + app_id : ""}`, () => [...M.reviewLog, ...localLog()].filter(e => !app_id || e.app_id === app_id).sort((a, b) => b.ts < a.ts ? -1 : 1)),
    fairness: () => call("/fairness-report", () => ({ method: "blind within-lender financial matching, then reveal", caveat: "Public HMDA lacks credit scores; a matched gap is not proof of discrimination.", results: M.fairness })),
    modelSensitivity: () => call("/model-sensitivity", () => M.modelSens),
    evaluation: () => call("/evaluation", () => M.evaluation),
    health: () => call("/health", () => M.health),
    metrics: () => call("/metrics", () => M.metrics),
    analyse: body => call("/analyse-application", () => { const cand = Object.values(M.twins).flat().slice(0, 400).map(t => ({ ...t, app_id: t.twin_id }));
      const scored = cand.map(c => { const d = M.dist(body, c); return { ...c, dist: +d.dist.toFixed(3), quality: M.qual(d.dist, d.max_diff) }; }).filter(c => isFinite(c.dist)).sort((a, b) => a.dist - b.dist).slice(0, 3);
      return { SIMULATION: true, compute_ms: +(2.5 + Math.random() * 2).toFixed(2), n_candidates: cand.length, twins: scored, disclaimer: "Simulated input; similarity is not an approval probability." }; }, "POST", body),
    // static reference numbers (also used in live mode for sensitivity/throughput, which have no endpoint)
    sensitivity: M.sensitivity, throughput: M.throughput, activity: M.activity,
  };
})();
