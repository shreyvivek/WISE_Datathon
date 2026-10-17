/* SecondLook UI — hash router + views. No build step, no CDN. */
const M = window.MOCK, A = window.API;
const $ = s => document.querySelector(s);
const view = $("#view");
const FEATS = M.FEATS, TOL = M.TOL, REL = M.REL;
const LABEL = { income: "Income", loan_amount: "Loan amount", dti: "DTI", ltv: "LTV", property_value: "Property value", loan_term: "Term" };
const COLOR = { income: "#7aa2ff", loan_amount: "#4fe0a6", dti: "#ffb547", ltv: "#b48cff", property_value: "#ff8fa3", loan_term: "#8a8984" };
// post-render motion: count numbers up, grow bars from zero
function afterRender() {
  if (new URLSearchParams(location.search).has("noanim")) return;
  view.querySelectorAll(".tile .n, .cov .pct").forEach(el => { if (el.dataset.counted) return; el.dataset.counted = 1; const m = el.textContent.match(/^([\d,]+)(.*)$/s); if (!m) return; const target = +m[1].replace(/,/g, ""), rest = el.innerHTML.slice(m[1].length); if (!isFinite(target) || target < 10) return;
    const t0 = performance.now(), dur = 900; const tick = now => { const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3); el.innerHTML = Math.round(target * e).toLocaleString() + rest; if (p < 1) requestAnimationFrame(tick); }; requestAnimationFrame(tick); });
  view.querySelectorAll(".bar i[style*='width'], .stack i[style*='width']").forEach(i => { const w = i.style.width; i.style.transition = "none"; i.style.width = "0"; requestAnimationFrame(() => requestAnimationFrame(() => { i.style.transition = ""; i.style.width = w; })); });
}
const DECISIONS = ["Needs additional information", "Reviewed — no conclusion", "Escalate for further review"];
const state = { case: localStorage.getItem("sl_case") || "b81daae6eb", twin: 0, reviewer: localStorage.getItem("sl_reviewer") || "reviewer-1" };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const fmt = (f, v) => v == null ? null : f === "income" ? `$${Math.round(v)}K` : f === "dti" || f === "ltv" ? `${(+v).toFixed(0)}%` : f === "loan_term" ? `${Math.round(v)} mo` : `$${Math.round(v).toLocaleString()}`;
const n0 = v => (+v).toLocaleString();
const lender = lei => (M.LENDERS.find(l => l.lei === lei) || {}).alias || "LEI …" + String(lei).slice(-4);
const county = c => c == null ? "" : M.COUNTIES[c] ? `${M.COUNTIES[c]} (${c})` : String(c);
const ago = ts => { const h = (Date.now() - new Date(ts)) / 36e5; return h < 1 ? `${Math.max(1, Math.round(h * 60))} min ago` : h < 24 ? `${Math.round(h)} h ago` : `${Math.round(h / 24)} d ago`; };
const av = (name, i = 0) => `<span class="av a${(i % 3) + 1}">${esc(String(name).replace(/[^a-z0-9]/gi, "").slice(-2).toUpperCase())}</span>`;
const diffTol = (a, b, f) => a == null || b == null ? null : REL[f] ? (b - a) / a / TOL[f] : (b - a) / TOL[f];
const dclass = d => d == null ? "na" : Math.abs(d) <= 0.6 ? "in" : Math.abs(d) <= 1 ? "edge" : "out";
const statusPill = s => s === "Escalate for further review" ? "violet" : s === "Needs additional information" ? "amber" : s === "Reviewed — no conclusion" ? "blue" : "mute";
const shortStatus = s => ({ "Needs additional information": "Needs info", "Reviewed — no conclusion": "No conclusion", "Escalate for further review": "Escalated" })[s] || "Pending";
function toast(t) { const e = $("#toast"); e.textContent = t; e.classList.add("show"); clearTimeout(e._t); e._t = setTimeout(() => e.classList.remove("show"), 2200); }
function setCase(id) { state.case = id; state.twin = 0; localStorage.setItem("sl_case", id); }

// ---------- charts (inline SVG) ----------
function ring(pct, color, label) { const r = 50, c = 2 * Math.PI * r, p = Math.max(0, Math.min(1, pct));
  return `<div class="ring"><svg width="120" height="120" viewBox="0 0 120 120"><circle cx="60" cy="60" r="${r}" fill="none" stroke="var(--line)" stroke-width="10"/><circle cx="60" cy="60" r="${r}" fill="none" stroke="${color}" stroke-width="10" stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - p)}" style="transition:stroke-dashoffset .8s"/></svg><div class="c">${Math.round(p * 100)}<small>${label}</small></div></div>`; }
function donut(parts, size = 150) { const tot = parts.reduce((s, p) => s + p[1], 0), r = 54, c = 2 * Math.PI * r; let off = 0;
  return `<svg width="${size}" height="${size}" viewBox="0 0 150 150">${parts.map(([l, v, col]) => { const s = `<circle cx="75" cy="75" r="${r}" fill="none" stroke="${col}" stroke-width="22" stroke-dasharray="${c * v / tot} ${c}" stroke-dashoffset="${-off}" transform="rotate(-90 75 75)"/>`; off += c * v / tot; return s; }).join("")}</svg>`; }
// gap chart: raw (hollow) → matched (solid) per group; the matched marker is drawn at x=0 and translated so CSS can animate it
function dumbbell(rows, maxX = 10, W = 1100) {
  const L = 190, R = 60, H = 96, x = v => L + (W - L - R) * v / maxX; const h = rows.length * H + 60;
  let s = `<svg viewBox="0 0 ${W} ${h}">`;
  for (let t = 0; t <= maxX; t += 2) s += `<line x1="${x(t)}" y1="14" x2="${x(t)}" y2="${h - 44}" stroke="var(--line)" stroke-dasharray="2 6"/><text class="tick" x="${x(t)}" y="${h - 24}" text-anchor="middle">${t}${t === maxX ? " pp" : ""}</text>`;
  s += `<line x1="${x(0)}" y1="14" x2="${x(0)}" y2="${h - 44}" stroke="var(--line2)"/>`;
  rows.forEach((r, i) => { const y = 50 + i * H;
    s += `<text class="lab" x="${L - 22}" y="${y + 6}" text-anchor="end">${esc(r.label)}</text><text class="tick" x="${L - 22}" y="${y + 24}" text-anchor="end">vs ${esc(r.ref)}</text>`;
    if (r.band) s += `<rect class="band" x="${x(r.band[0])}" y="${y - 14}" width="${x(r.band[1]) - x(r.band[0])}" height="28" rx="14" fill="rgba(255,181,71,.08)"/>`;
    s += `<line class="raw" x1="${x(0)}" y1="${y}" x2="${x(r.raw)}" y2="${y}" stroke="var(--line2)" stroke-width="1.5" stroke-dasharray="4 6"/>`;
    s += `<g class="raw"><circle cx="${x(r.raw)}" cy="${y}" r="10" fill="var(--panel)" stroke="var(--ink)" stroke-width="2.5"/><text class="num" x="${x(r.raw)}" y="${y - 20}" text-anchor="middle" fill="var(--ink)">${r.raw.toFixed(1)}</text></g>`;
    s += `<g class="ci" style="transform:translateX(${x(r.lo)}px)"><line x1="0" y1="${y}" x2="${x(r.hi) - x(r.lo)}" y2="${y}" stroke="var(--acc)" stroke-width="5" stroke-linecap="round" opacity=".55"/></g>`;
    s += `<g class="mv" style="--raw:${x(r.raw)}px;transform:translateX(${x(r.m)}px)"><circle cx="0" cy="${y}" r="13" fill="var(--acc)"/><circle cx="0" cy="${y}" r="13" fill="none" stroke="var(--acc)" opacity=".35"><animate attributeName="r" from="13" to="28" dur="2.2s" repeatCount="indefinite"/><animate attributeName="opacity" from=".4" to="0" dur="2.2s" repeatCount="indefinite"/></circle><text class="num" x="0" y="${y - 22}" text-anchor="middle" fill="var(--acc)">${r.m.toFixed(1)}</text></g>`; });
  return s + `</svg>`; }
function slope(groups, W = 340, H = 210) { // actual vs predicted-without-demographics, per group
  const L = 110, R = 64, T = 32, B = 26, vals = Object.values(groups).flatMap(v => [v[0], v[1]]), max = Math.max(...vals) * 1.1, y = v => T + (H - T - B) * (1 - v / max);
  let s = `<svg class="slope" viewBox="0 0 ${W} ${H}" width="100%"><text x="${L}" y="16" text-anchor="middle" style="font:600 12px var(--body);fill:var(--mute)">Actual</text><text x="${W - R}" y="16" text-anchor="middle" style="font:600 12px var(--body);fill:var(--mute)">Predicted, no demographics</text><line x1="${L}" y1="${T}" x2="${L}" y2="${H - B}" stroke="var(--line)"/><line x1="${W - R}" y1="${T}" x2="${W - R}" y2="${H - B}" stroke="var(--line)"/>`;
  Object.entries(groups).forEach(([g, [a, b]]) => { const under = b < a - 1, c = under ? "var(--acc)" : "var(--ink2)";
    s += `<line x1="${L}" y1="${y(a)}" x2="${W - R}" y2="${y(b)}" stroke="${c}" stroke-width="${under ? 2.5 : 1.5}" ${under ? "" : 'opacity=".6"'}/><circle cx="${L}" cy="${y(a)}" r="4" fill="${c}"/><circle cx="${W - R}" cy="${y(b)}" r="4" fill="${c}"/><text x="${L - 10}" y="${y(a) + 5}" text-anchor="end" font-size="14" font-weight="600" fill="${c}">${g} ${a}%</text><text x="${W - R + 10}" y="${y(b) + 5}" font-size="14" font-weight="600" fill="${c}">${b}%</text>`; });
  return s + `</svg>`; }
function lineChart(pts, W = 520, H = 220, ymax = 500) { const L = 44, B = 30, x = i => L + i * (W - L - 20) / (pts.length - 1), y = v => 14 + (H - B - 14) * (1 - v / ymax);
  const path = pts.map((p, i) => `${i ? "L" : "M"}${x(i)} ${y(p[1])}`).join(" "); const peak = pts.reduce((m, p, i) => p[1] > pts[m][1] ? i : m, 0);
  return `<svg viewBox="0 0 ${W} ${H}" width="100%"><g stroke="var(--line)">${[0, .5, 1].map(f => `<line x1="${L}" y1="${y(f * ymax)}" x2="${W - 20}" y2="${y(f * ymax)}" stroke-dasharray="2 6"/>`).join("")}</g>
  ${[0, .5, 1].map(f => `<text x="${L - 8}" y="${y(f * ymax) + 4}" text-anchor="end" font-size="11" fill="var(--mute)">${f * ymax}</text>`).join("")}
  <path d="${path} L${x(pts.length - 1)} ${y(0)} L${x(0)} ${y(0)} Z" fill="rgba(255,181,71,.08)"/><path d="${path}" fill="none" stroke="var(--acc)" stroke-width="2.5" stroke-dasharray="1200" stroke-dashoffset="1200" style="animation:draw 1.6s var(--ease) forwards"/><style>@keyframes draw{to{stroke-dashoffset:0}}</style>
  ${pts.map((p, i) => `<circle cx="${x(i)}" cy="${y(p[1])}" r="${i === peak ? 6 : 4}" fill="var(--acc)"/><text x="${x(i)}" y="${H - 8}" text-anchor="middle" font-size="11" fill="var(--mute)">${p[0]}</text>`).join("")}
  <text x="${x(peak)}" y="${y(pts[peak][1]) - 14}" text-anchor="middle" font-size="15" font-weight="800" fill="var(--ink)">${pts[peak][1]} req/s</text></svg>`; }

// ---------- views ----------
const V = {};
V.overview = async () => {
  view.innerHTML = `<div class="top"><h1>Overview</h1><span class="sub">Maryland HMDA 2025</span><span class="grow"></span><a class="btn" href="#queue">Queue</a><a class="btn primary" href="#case">Top case →</a></div><div class="grid g5 stagger" id="tiles"></div><div class="grid g21 stagger" style="margin-top:14px"><div class="card" id="qtab"></div><div class="grid" style="gap:16px"><div class="card" id="funnel"></div><div class="card" id="feed"></div></div></div>`;
  const [{ data: s }, { data: q }, { data: log }, { data: ev }] = await Promise.all([A.summary(), A.queue(10), A.reviewLog(), A.evaluation()]);
  const cov = ev.coverage || M.evaluation.coverage; const esc_ = log.filter(e => e.decision === DECISIONS[2]).length, info = log.filter(e => e.decision === DECISIONS[0]).length, noc = log.filter(e => e.decision === DECISIONS[1]).length;
  const tile = (n, l, col, rows, ico) => `<div class="card tile"><div class="n ${col}">${n}</div><div class="ico">${ico}</div><div class="l">${l}</div>${rows.map(([k, t, v]) => `<div class="row"><span class="k">${k}</span>${t}${v ? `<span class="v">${v}</span>` : ""}</div>`).join("")}</div>`;
  $("#tiles").innerHTML = tile(n0(s.applications), "Applications", "c-blue", [[n0(s.lenders), "lenders"], ["6", "financial fields"], ["0", "demographics"]], "▦")
    + tile(n0(s.denied), "Denied", "c-red", [[n0(cov.strong), "strong twin"], [n0(cov.moderate), "moderate twin"], [n0(cov.weak + cov.none), "weak / none"]], "✕")
    + tile(n0(s.review_queue_size), "Queued", "c-amber", [[n0(s.denied_with_strong_comparator), "strong"], [n0(s.review_queue_size - s.denied_with_strong_comparator), "moderate"], [n0(s.insufficient_evidence), "low evidence"]], "☰")
    + tile(n0(log.length), "Reviewed", "c-teal", [[esc_, "escalated"], [info, "need info"], [noc, "no conclusion"]], "✓")
    + tile(n0(esc_), "Flagged", "c-violet", [[new Set(log.map(e => e.reviewer)).size, "reviewers"], ["0", "loans changed"]], "▲");
  $("#qtab").innerHTML = `<h3>Top of the queue <span class="grow"></span><a href="#queue" class="c-amber">all ${n0(s.review_queue_size)} →</a></h3>` + queueTable(q);
  $("#funnel").innerHTML = `<h3>Funnel</h3><div style="display:flex;gap:18px;align-items:center">${donut([["queued", s.review_queue_size, "#ffb547"], ["insufficient", s.insufficient_evidence, "#7aa2ff"], ["approved", s.applications - s.denied, "#222228"]], 130)}<div class="kv"><b><i style="color:#222228">●</i> approved</b><span>${n0(s.applications - s.denied)}</span><b><i class="c-amber">●</i> queued</b><span>${n0(s.review_queue_size)}</span><b><i class="c-blue">●</i> not enough evidence</b><span>${n0(s.insufficient_evidence)}</span></div></div>`;
  const acts = [...log.slice(0, 6).map(e => ({ ts: e.ts, col: `var(--${statusPill(e.decision)})`, text: `${e.reviewer} · ${e.decision}`, id: e.app_id })), ...A.activity.filter(a => a.kind !== "decision").map(a => ({ ts: a.ts, col: a.kind === "note" ? "var(--blue)" : "var(--teal)", text: a.text, id: a.app_id }))].sort((a, b) => b.ts < a.ts ? -1 : 1).slice(0, 8);
  $("#feed").innerHTML = `<h3>Recent activity</h3><div class="feed">${acts.map(a => `<div class="ev"><span class="dot" style="background:${a.col}"></span><div>${esc(a.text)}<br><a href="#case" class="mono c-mute" data-case="${a.id}">${a.id}</a></div><span class="t">${ago(a.ts)}</span></div>`).join("")}</div>`;
  if (!acts.length) $("#feed").innerHTML += '<div class="empty">No activity yet.</div>';
  bindCaseLinks();
};

function queueTable(q, full = false) {
  return `<table class="qt"><thead><tr><th>Application</th><th>Lender</th>${full ? "<th>County</th>" : ""}<th>Match</th><th>Status</th></tr></thead><tbody>${q.map((r, i) => `<tr class="row ${r.app_id === state.case ? "sel" : ""}" data-case="${r.app_id}"><td><div class="appcell">${av(r.app_id, i)}<span class="mono">${r.app_id}</span><span class="dd"><button class="ddb" data-menu>▾</button><div class="menu"><a data-go="case">View in detail</a><a data-go="compare">Compare twins</a></div></span></div></td><td>${lender(r.lei)}</td>${full ? `<td>${county(r.county_code).split(" (")[0]}</td>` : ""}<td><span class="q ${r.quality}">${r.quality}</span></td><td><span class="pill ${statusPill(r.review_status)}">${shortStatus(r.review_status)}</span></td></tr>`).join("")}</tbody></table>`; }
function bindCaseLinks() {
  view.querySelectorAll("[data-case]").forEach(el => el.addEventListener("click", e => { const go = e.target.dataset.go; if (e.target.dataset.menu !== undefined) { e.stopPropagation(); const m = e.target.nextElementSibling; view.querySelectorAll(".menu.open").forEach(x => x !== m && x.classList.remove("open")); m.classList.toggle("open"); return; }
    setCase(el.dataset.case); if (go) { e.preventDefault(); location.hash = go; } else if (el.tagName === "TR") location.hash = "case"; }));
  document.addEventListener("click", () => view.querySelectorAll(".menu.open").forEach(x => x.classList.remove("open")), { once: true }); }

V.queue = async () => {
  view.innerHTML = `<div class="top"><h1>Queue</h1><span class="sub">denied, with comparable approvals at the same lender</span></div><div class="card"><div class="filters"><input id="f-q" placeholder="Search id / lender"><select id="f-l"><option value="">All lenders</option></select><select id="f-m"><option value="">Any match</option><option>strong</option><option>moderate</option></select><select id="f-s"><option value="">Any status</option><option>Pending review</option>${DECISIONS.map(d => `<option>${d}</option>`).join("")}</select><span class="grow"></span><span class="pill" id="f-n"></span></div><div id="tbl"></div></div>`;
  const { data: q } = await A.queue(200); const lenders = [...new Set(q.map(r => r.lei))];
  $("#f-l").innerHTML += lenders.map(l => `<option value="${l}">${lender(l)}</option>`).join("");
  let sort = ["priority", -1];
  const draw = () => { const t = $("#f-q").value.toLowerCase(), l = $("#f-l").value, m = $("#f-m").value, s = $("#f-s").value;
    const rows = q.filter(r => (!t || r.app_id.includes(t) || lender(r.lei).toLowerCase().includes(t)) && (!l || r.lei === l) && (!m || r.quality === m) && (!s || r.review_status === s)).sort((a, b) => (a[sort[0]] > b[sort[0]] ? 1 : -1) * sort[1]);
    $("#f-n").textContent = `${rows.length} cases`; $("#tbl").innerHTML = queueTable(rows, true); bindCaseLinks();
    view.querySelectorAll("th").forEach((th, i) => th.onclick = () => { const k = ["app_id", "lei", "county_code", "quality", "review_status"][i]; if (!k) return; sort = sort[0] === k ? [k, -sort[1]] : [k, -1]; draw(); }); };
  ["f-q", "f-l", "f-m", "f-s"].forEach(id => $("#" + id).oninput = draw); draw();
};

V.compare = async () => {
  view.innerHTML = `<div class="top"><h1>Compare</h1><span class="grow"></span><div class="combo" id="combo"><button class="combo-b" id="combo-b"><span class="micro">Denied</span><b class="mono" id="combo-v"></b><i>▾</i></button><div class="combo-p" id="combo-p"><input class="txt" id="pk-q" placeholder="Search id, lender, county"><div class="list" id="pk-list"></div></div></div></div>
  <div class="stagger"><div class="cands" id="cands"></div><div id="cmp" style="margin-top:14px"></div></div>`;
  const { data: q } = await A.queue(200);
  if (!q.find(r => r.app_id === state.case)) setCase(q[0].app_id);
  const combo = $("#combo"), pop = $("#combo-p");
  $("#combo-b").onclick = e => { e.stopPropagation(); pop.classList.toggle("open"); if (pop.classList.contains("open")) $("#pk-q").focus(); };
  document.addEventListener("click", e => { if (!combo.contains(e.target)) pop.classList.remove("open"); });
  const drawPick = () => { const s = $("#pk-q").value.toLowerCase(); $("#combo-v").textContent = state.case;
    const rows = q.filter(r => !s || r.app_id.includes(s) || lender(r.lei).toLowerCase().includes(s) || county(r.county_code).toLowerCase().includes(s)).slice(0, 60);
    $("#pk-list").innerHTML = rows.map((r, i) => `<div class="li ${r.app_id === state.case ? "on" : ""}" data-id="${r.app_id}">${av(r.app_id, i)}<div><b class="mono">${r.app_id}</b><small>${lender(r.lei)} · ${county(r.county_code).split(" (")[0]}</small></div><span class="grow"></span><span class="q ${r.quality}">${r.quality}</span></div>`).join("") || `<div class="empty">No match</div>`;
    view.querySelectorAll("#pk-list .li").forEach(el => el.onclick = () => { setCase(el.dataset.id); state.twin = 0; pop.classList.remove("open"); drawPick(); drawCase(); }); };
  $("#pk-q").oninput = drawPick; drawPick();
  const drawCase = async () => { $("#cmp").innerHTML = ""; $("#cands").innerHTML = "";
    const [{ data: a }, { data: tw }, { data: log }] = await Promise.all([A.application(state.case), A.twins(state.case), A.reviewLog(state.case)]);
    if (a.county_code == null) a.county_code = (q.find(r => r.app_id === state.case) || {}).county_code;
    const twins = [...tw].sort((x, y) => x.dist - y.dist); if (state.twin >= twins.length) state.twin = 0; const t = twins[state.twin];
    $("#cands").innerHTML = `<div class="cands-h"><span>Approved comparators</span><span class="c-mute">${twins.length} · same lender · ranked by distance</span></div><div class="cands-r">${twins.map((x, i) => `<button class="cand ${i === state.twin ? "on" : ""}" data-i="${i}"><span class="rk">#${i + 1}</span><b class="mono">${x.twin_id}</b><span class="q ${x.quality}">${(+x.dist).toFixed(2)}</span></button>`).join("")}</div>`;
    view.querySelectorAll(".cand").forEach(el => el.onclick = () => { state.twin = +el.dataset.i; drawCase(); });
    drawPair(a, twins, t, log); };
  const drawPair = (a, twins, t, log) => {
    const ti = twins.indexOf(t), reasons = (a.denial_reasons || []).map(c => M.DENIAL[c] || c), miss = FEATS.filter(f => a[f] == null);
    const rows = FEATS.map(f => { const d = diffTol(a[f], t[f], f), c = dclass(d), w = d == null ? 0 : Math.min(50, Math.abs(d) * 33);
      const lbl = d == null ? "—" : (Math.abs(d) < 1e-9 ? "" : d > 0 ? "+" : "−") + (REL[f] ? (100 * Math.abs(d) * TOL[f]).toFixed(1) + "%" : (Math.abs(d) * TOL[f]).toFixed(f === "loan_term" ? 0 : 1) + (f === "loan_term" ? " mo" : " pts"));
      return `<div class="cr"><span class="cf">${LABEL[f]}</span><span class="cv ${a[f] == null ? "na" : ""}">${a[f] == null ? "not reported" : fmt(f, a[f])}</span>
        <div class="cg"><i class="band"></i><i class="zero"></i><i class="gb ${c}" style="${d > 0 ? "left:50%" : "right:50%"};width:${w}%"></i><span class="gl ${c}">${lbl}<small>${d == null ? "" : " · " + Math.abs(d).toFixed(2) + "×"}</small></span></div>
        <span class="cv r ${t[f] == null ? "na" : ""}">${t[f] == null ? "not reported" : fmt(f, t[f])}</span></div>`; }).join("");
    $("#cmp").innerHTML = `<div class="card ctab">
      <div class="ch"><div><div class="co c-red">Denied</div><b class="mono">${a.app_id}</b><small>${lender(a.lei)} · ${county(a.county_code).split(" (")[0]}</small></div>
        <div class="cmid"><button class="tab" id="prev" ${ti === 0 ? "disabled" : ""}>‹</button><span><b>#${ti + 1}</b><small class="c-mute"> of ${twins.length}</small></span><button class="tab" id="next" ${ti === twins.length - 1 ? "disabled" : ""}>›</button><div class="c-mute" style="font-size:13px;margin-top:4px">gap · <span class="q ${t.quality}">${t.quality}</span> · distance ${(+t.dist).toFixed(2)}</div></div>
        <div style="text-align:right"><div class="co c-green">Approved</div><b class="mono">${t.twin_id}</b><small>${lender(a.lei)} · same lender</small></div></div>
      <div class="cbody">${rows}</div>
      <div class="cfoot"><div class="chips">${reasons.map(r => `<span class="pill red">${esc(r)}</span>`).join("")}${miss.length ? `<span class="pill amber">missing: ${miss.map(f => LABEL[f]).join(", ")}</span>` : ""}</div><span class="grow"></span><span class="pill ${statusPill(log[0] && log[0].decision)}">${esc(log[0] ? log[0].decision : "Pending review")}</span><a class="btn primary" href="#case">View in detail →</a></div></div>
      <div class="help" style="margin-top:8px">Bar = difference in units of the field's tolerance; shaded band = within tolerance.</div>`;
    $("#prev").onclick = () => { state.twin = ti - 1; drawCase(); }; $("#next").onclick = () => { state.twin = ti + 1; drawCase(); };
    requestAnimationFrame(() => requestAnimationFrame(() => $("#cmp").classList.add("go")));
  };
  drawCase();
};

V.case = async () => {
  view.innerHTML = `<div class="top"><a class="btn ghost sm" href="#queue">← Queue</a><h1 class="mono" id="ttl">${esc(state.case)}</h1><span class="grow"></span><a class="btn" href="#compare">Compare twins ⇄</a></div><div id="ex" class="empty">Loading…</div>`;
  const [{ data: a }, { data: tw }, { data: rr }, { data: qs }, { data: log }, { data: q }] = await Promise.all([A.application(state.case), A.twins(state.case), A.reasonReview(state.case), A.questions(), A.reviewLog(state.case), A.queue(200)]);
  const twins = [...tw].sort((x, y) => x.dist - y.dist), t = twins[0], pc = a.priority_components || {}, qr = q.find(r => r.app_id === state.case) || {};
  if (a.county_code == null) a.county_code = qr.county_code;
  const W = { c_match: [.45, "Closeness", "#ffb547"], c_count: [.25, "Strong twins", "#4fe0a6"], c_lender: [.15, "Lender", "#b48cff"], c_complete: [.15, "Completeness", "#7aa2ff"] };
  const contrib = FEATS.map(f => [f, Math.abs(diffTol(a[f], t[f], f) ?? 0)]); const tot = contrib.reduce((s, c) => s + c[1], 0) || 1;
  const stIcon = s => /^Comparable|Not distinguished/i.test(s) ? ["≈", "c-amber", "Not distinguished by reported data"] : /Not assessable/i.test(s) ? ["?", "c-amber", "Not assessable with public data"] : /Partly/i.test(s) ? ["½", "c-amber", "Partly assessable"] : ["✓", "c-green", "Consistent with reported data"];
  const cap = x => x ? x[0].toUpperCase() + x.slice(1) : x;
  const maxv = Object.fromEntries(FEATS.map(f => [f, Math.max(a[f] || 0, ...twins.slice(0, 3).map(x => x[f] || 0)) || 1]));
  $("#ex").className = ""; $("#ex").innerHTML = `<div class="stagger">
  <div class="card hero"><div class="hero-l"><span class="stamp c-red" style="margin:0 0 8px">DENIED</span><div class="c-mute">${lender(a.lei)}${a.county_code ? " · " + county(a.county_code) : ""}</div><div class="chips" style="margin-top:12px"><span class="pill ${statusPill(qr.review_status)}">${esc(qr.review_status || "Pending review")}</span><span class="pill ${t.quality === "strong" ? "green" : "amber"}">${t.quality} match</span>${(a.denial_reasons || []).map(c => `<span class="pill red">${esc(M.DENIAL[c] || c)}</span>`).join("")}</div></div>
    <div class="hero-stats"><div><div class="n display c-amber">${(+pc.priority || 0).toFixed(0)}</div><div class="micro">priority</div></div><div><div class="n display">${(+t.dist).toFixed(2)}</div><div class="micro">distance</div></div><div><div class="n display">${twins.filter(x => x.quality === "strong").length}<span class="c-mute">/${twins.length}</span></div><div class="micro">strong twins</div></div><div><div class="n display">${Math.round(100 * (a.completeness ?? 1))}<span class="c-mute">%</span></div><div class="micro">fields reported</div></div></div></div>
  <div class="grid g3" style="margin-top:14px">
  <div class="grid" style="gap:14px;align-content:start">
    <div class="card"><h3>Application</h3><div class="vals">${FEATS.map(f => `<div class="v"><span class="num ${a[f] == null ? "na" : ""}" style="min-width:110px">${a[f] == null ? "not reported" : fmt(f, a[f])}</span><div class="bar"><i style="width:${a[f] == null ? 0 : 100 * a[f] / maxv[f]}%;background:${COLOR[f]}"></i></div><span class="micro" style="width:90px;text-align:right">${LABEL[f]}</span></div>`).join("")}</div></div>
    <div class="card"><h3>Closest approved twins</h3>${twins.slice(0, 3).map((x, i) => `<div class="li sim" data-i="${i}" style="padding:8px 4px"><b class="rk">${i + 1}</b><div><b class="mono">${x.twin_id}</b><small><span class="q ${x.quality}" style="font-size:11px">${x.quality}</span> · d=${(+x.dist).toFixed(2)}</small></div><span class="grow"></span><div class="gaps">${FEATS.map(f => `<i class="${dclass(diffTol(a[f], x[f], f))}"></i>`).join("")}</div></div>`).join("")}<a class="btn sm" href="#compare" style="margin-top:10px">All ${twins.length} →</a></div>
    <div class="card"><h3>Why queued <span class="grow"></span><b class="c-amber">${(+pc.priority || 0).toFixed(0)}</b></h3><div class="stack">${Object.entries(W).map(([k, [w, l, c]]) => `<i style="width:${100 * w * (pc[k] || 0)}%;background:${c}" title="${l}"></i>`).join("")}</div><div class="legend">${Object.entries(W).map(([k, [w, l, c]]) => `<span><i style="background:${c}"></i>${l} ${Math.round(100 * (pc[k] || 0))}%</span>`).join("")}</div></div>
    <div class="card"><h3>Gap by field <span class="grow"></span><span style="text-transform:none;letter-spacing:0">vs twin 1</span></h3>${contrib.sort((x, y) => y[1] - x[1]).map(([f, v]) => `<div class="hbar"><span class="lab">${LABEL[f]}</span><div class="bar"><i style="width:${100 * v / tot}%;background:${COLOR[f]}"></i></div><span class="n">${Math.round(100 * v / tot)}%</span></div>`).join("")}</div>
  </div>
  <div class="grid" style="gap:14px;align-content:start">
    <div class="card"><h3>Stated reasons vs data</h3>${rr.items.map(i => { const [ic, col, st] = stIcon(i.status); return `<div class="reason"><div class="ic ${col}">${ic}</div><div><b>${esc(cap(i.reason))}</b><div class="st ${col}">${st}</div><p>${esc(i.detail)}</p></div></div>`; }).join("") || "<div class='c-mute'>No stated reasons.</div>"}</div>
    <div class="card"><h3>Reviewer note <span class="grow"></span><button class="btn sm" id="gen">Generate</button></h3><div class="note" id="note"><span class="gtag">GRANITE 4.0</span> <small>facts only · no $ · no demographics</small><p class="c-mute">Cached notes are instant; a fresh one takes 15–45 s on LinuxONE.</p></div></div>
    <div class="card"><h3>Evidence to request</h3><div class="chips">${rr.evidence_to_request.map(e => `<span class="pill">${esc(e)}</span>`).join("")}</div></div>
  </div>
  <div class="grid" style="gap:14px;align-content:start">
    <div class="card"><h3>Ask</h3><div class="qchips">${Object.entries(qs).map(([k, v]) => `<button data-q="${k}">${esc(v)}</button>`).join("")}</div><div id="ans"></div></div>
    <div class="card"><h3>Decision <span class="grow"></span><span class="pill mute">advisory</span></h3><div class="decide">${DECISIONS.map((d, i) => `<button data-d="${i}">${["ⓘ", "○", "▲"][i]}&nbsp; ${d}</button>`).join("")}</div><div style="display:flex;gap:8px;margin-top:10px"><input class="txt" id="rev" value="${esc(state.reviewer)}" style="max-width:130px"><input class="txt" id="cmt" placeholder="Comment" maxlength="300"></div><button class="btn primary" id="save" style="margin-top:10px;width:100%;justify-content:center" disabled>Save</button>
    <div class="trail" id="trail">${log.map(e => `<div class="e" style="--c:var(--${statusPill(e.decision)})">${esc(e.decision)}<small>${esc(e.reviewer)} · ${ago(e.ts)} · ${esc(e.match_quality)}</small></div>`).join("")}<div class="e" style="--c:var(--blue)">Queued<small>priority ${(+pc.priority || 0).toFixed(0)} · ${t.quality} twin</small></div></div></div>
  </div></div></div>`;
  view.querySelectorAll(".li.sim").forEach(el => el.onclick = () => { state.twin = +el.dataset.i; location.hash = "compare"; });
  let decision = null;
  view.querySelectorAll(".decide button").forEach(b => b.onclick = () => { view.querySelectorAll(".decide button").forEach(x => x.classList.remove("on")); b.classList.add("on"); decision = DECISIONS[+b.dataset.d]; $("#save").disabled = false; });
  $("#save").onclick = async () => { state.reviewer = $("#rev").value || "reviewer"; localStorage.setItem("sl_reviewer", state.reviewer); $("#save").disabled = true;
    try { const { data } = await A.decide(state.case, decision, state.reviewer, $("#cmt").value); const e = data.entry; $("#trail").insertAdjacentHTML("afterbegin", `<div class="e fade" style="--c:var(--${statusPill(e.decision)})">${esc(e.decision)}<small>${esc(e.reviewer)} · just now · ${esc(e.model_version)} · ${esc(e.match_quality)}</small></div>`); toast("Recorded. " + data.note); } catch (err) { toast("Not recorded: " + err.message); $("#save").disabled = false; } };
  view.querySelectorAll(".qchips button").forEach(b => b.onclick = async () => { view.querySelectorAll(".qchips button").forEach(x => x.classList.remove("on")); b.classList.add("on"); $("#ans").innerHTML = `<div class="answer c-mute">…</div>`; const { data } = await A.ask(state.case, b.dataset.q); $("#ans").innerHTML = `<div class="answer fade">${esc(data.answer)}</div>`; });
  $("#gen").onclick = async () => { const p = $("#note p"); p.className = "typing"; p.textContent = ""; $("#gen").disabled = true;
    const { data } = await A.note(state.case); const txt = data.note; let i = 0; const tick = () => { p.textContent = txt.slice(0, i += 3); if (i < txt.length) setTimeout(tick, 12); else { p.className = ""; $("#note").insertAdjacentHTML("beforeend", `<small>${data.generator} · validation ${data.validation} · ${data.cached ? "cached" : "fresh"}${data.granite_gen_ms ? ` · ${(data.granite_gen_ms / 1000).toFixed(1)} s, ${data.granite_tokens} tokens` : ""}</small>`); } }; tick(); };
};
V.explain = V.case;

V.fairness = async () => {
  const SPECS = Object.entries(A.sensitivity);
  view.innerHTML = `<div class="top"><h1>Fairness</h1><span class="sub">matched on finances first, then grouped</span><span class="grow"></span><label class="selwrap"><span>Matching</span><select id="spec">${SPECS.map(([k, v]) => `<option value="${k}">${v.label}</option>`).join("")}</select></label></div>
  <div class="stagger"><div class="card"><div class="fchart" id="chart"></div>
  <div class="fnote"><span class="caveat">Observed disparity, not proof of discrimination</span><span class="legend" style="margin:0"><span><i style="background:var(--panel);border:2px solid var(--ink);border-radius:50%"></i>raw gap</span><span><i style="background:var(--acc);border-radius:50%"></i>matched gap · 95% CI</span><span><i style="background:rgba(255,181,71,.25)"></i>range across settings</span></span></div></div>
  <div class="grid g3" style="margin-top:14px"><div class="card cov" id="groups"></div><div class="card" id="reviewers"></div><div class="card" id="ms"></div></div></div>`;
  let fair = null, spec = "base";
  const gkey = g => /black/i.test(g) ? "Black" : /asian/i.test(g) ? "Asian" : g;
  const rowsFor = () => { const sp = A.sensitivity[spec];
    return fair.results.map(r => { const g = gkey(r.group), ref = gkey(r.ref), t = sp[g];
      const s = spec === "base" || !t ? [r.matched_gap_pp, r.matched_ci_lo, r.matched_ci_hi, r.coverage] : t;
      const all = Object.values(A.sensitivity).map(x => x[g] && x[g][0]).filter(x => x != null);
      return { label: g, ref, raw: r.raw_gap_pp, m: s[0], lo: s[1], hi: s[2], band: all.length ? [Math.min(...all), Math.max(...all)] : null, cov: s[3], n: r.n_group, nm: Math.round(r.n_group * s[3]) }; }); };
  const drawChart = () => { const rows = rowsFor(); const ch = $("#chart");
    ch.innerHTML = dumbbell(rows, 10); ch.classList.add("blind"); requestAnimationFrame(() => requestAnimationFrame(() => ch.classList.remove("blind")));
    $("#groups").innerHTML = `<h3>Coverage</h3>${rows.map(r => `<div style="margin-bottom:16px"><div style="display:flex;align-items:baseline;gap:10px"><span class="pct">${Math.round(100 * r.cov)}<small style="font-size:20px;color:var(--mute)">%</small></span><span class="c-mute">${r.label}</span></div><div class="bar"><i style="width:${100 * r.cov}%"></i></div><div class="c-mute" style="font-size:14px">${n0(r.nm)} of ${n0(r.n)} had a comparable twin</div></div>`).join("")}<div class="help">Stricter matching covers fewer applicants.</div>`; afterRender(); };
  const [{ data: f }, { data: lg }, msr] = await Promise.all([A.fairness().catch(() => ({ data: null })), A.reviewLog(), A.modelSensitivity().catch(() => ({ data: null }))]);
  fair = f;
  if (!fair) $("#chart").innerHTML = `<div class="empty">Demographic audit is token-gated. Add <span class="mono">?token=…</span> to the URL.</div>`; else drawChart();
  $("#spec").onchange = e => { spec = e.target.value; if (fair) drawChart(); };
  // reviewer consistency: one square per review, coloured by decision
  const byR = {}; lg.forEach(e => (byR[e.reviewer] = byR[e.reviewer] || []).push(e.decision));
  $("#reviewers").innerHTML = `<h3>Reviewer consistency</h3>${Object.entries(byR).map(([r, ds], i) => { const n = ds.length, cnt = DECISIONS.map(d => ds.filter(x => x === d).length), e = cnt[2]; return `<div class="rv"><div class="who" style="display:flex;align-items:center">${av(r, i)}<div><b>${esc(r)}</b><small>${n} reviews</small></div></div><div class="sb">${DECISIONS.map((d, k) => cnt[k] ? `<i style="width:${100 * cnt[k] / n}%;background:var(--${statusPill(d)})" title="${d}">${Math.round(100 * cnt[k] / n)}%</i>` : "").join("")}</div><div class="esc c-violet">${Math.round(100 * e / n)}%<small>escalated</small></div></div>`; }).join("") || "<div class='c-mute'>No reviews yet.</div>"}<div class="legend">${DECISIONS.map(d => `<span><i style="background:var(--${statusPill(d)})"></i>${d.split(" ")[0] === "Reviewed" ? "No conclusion" : d.split(" ")[0] === "Needs" ? "Needs info" : "Escalate"}</span>`).join("")}</div>`;
  if (!Object.keys(byR).length) $("#reviewers").innerHTML += '<div class="empty">No reviews recorded yet.</div>';
  // model sensitivity as a slope chart
  const ms = msr.data && (msr.data.models || msr.data); const key = ms && (ms.xgb ? "xgb" : "logreg"); const mm = ms && ms[key];
  const grp = mm && (mm.groups || (mm.by_group && Object.fromEntries(Object.entries(mm.by_group).map(([g, v]) => [gkey(g), [+(100 * v.actual_denial_rate).toFixed(1), +(100 * v.mean_pred_A).toFixed(1), +(100 * v.mean_pred_B).toFixed(1)]]))));
  $("#ms").innerHTML = `<h3>Model sensitivity <span class="grow"></span><span style="text-transform:none;letter-spacing:0">${key === "xgb" ? "XGBoost" : "logistic"} · exploratory</span></h3>` + (grp ? slope(grp) + `<div class="help">Without demographics the model under-predicts denials for the amber group. Not evidence a lender used race.</div>` : `<div class="c-mute">Not available from this backend.</div>`);
};

V.simulate = async () => {
  const { data: q } = await A.queue(50); const lenders = [...new Set(q.map(r => r.lei))];
  const F = [["income", "Income ($K)", 90], ["loan_amount", "Loan amount ($)", 280000], ["dti", "DTI (%)", 35], ["ltv", "LTV (%)", 79], ["property_value", "Property value ($)", 355000], ["loan_term", "Term (months)", 360]];
  view.innerHTML = `<div class="top"><h1>Simulate</h1><span class="sub">score a new application against the lender's approved history · SIMULATION</span></div><div class="grid g12"><div class="card"><h3>Incoming application</h3><div class="num-in"><span>Lender</span><select id="s-lei" class="txt" style="background:var(--panel2);border:1px solid var(--line2);border-radius:10px;padding:8px 12px">${lenders.map(l => `<option value="${l}">${lender(l)}</option>`).join("")}</select></div>${F.map(([k, l, v]) => `<div class="num-in"><span>${l}</span><input type="number" id="s-${k}" value="${v}"></div>`).join("")}<button class="btn primary" id="run" style="width:100%;justify-content:center;margin-top:8px">Find twins ▶</button><div class="help">Matching only. Similarity is not an approval probability.</div></div><div class="card" id="out"><div class="empty">Run a simulation to see the three closest approved applications and the server compute time.</div></div></div>`;
  $("#run").onclick = async () => { const body = { lei: $("#s-lei").value }; F.forEach(([k]) => body[k] = +$("#s-" + k).value); $("#out").innerHTML = `<div class="empty">…</div>`; const t0 = performance.now();
    try { const { data, ms } = await A.analyse(body); const rt = performance.now() - t0;
      $("#out").innerHTML = `<h3>Closest approved applications <span class="grow"></span><span class="pill green">server ${data.compute_ms} ms</span><span class="pill">round-trip ${rt.toFixed(0)} ms</span><span class="pill mute">${n0(data.n_candidates)} candidates</span></h3><div class="grid g3 fade">${data.twins.map((t, i) => `<div class="side-card ok" style="--c:var(--green)"><div class="head"><div class="big c-green">T${i + 1}</div><div><div class="id mono">${t.twin_id}</div><div class="meta"><span class="q ${t.quality}">${t.quality}</span> · d=${(+t.dist).toFixed(2)}</div></div></div><div class="vals">${FEATS.map(f => { const d = diffTol(body[f], t[f], f); return `<div class="v"><span class="num ${t[f] == null ? "na" : ""}" style="min-width:80px">${t[f] == null ? "n/r" : fmt(f, t[f])}</span><span class="d ${dclass(d)}" style="font-size:11px">${d == null ? "n/a" : Math.abs(d).toFixed(2) + "×"}</span></div>`; }).join("")}</div></div>`).join("") || "<div class='empty'>No comparable approved applications.</div>"}</div><div class="help">${esc(data.disclaimer)}</div>`; }
    catch (e) { $("#out").innerHTML = `<div class="empty c-red">${esc(e.message)}</div>`; } };
};

V.system = async () => {
  view.innerHTML = `<div class="top"><h1>System</h1><span class="sub">where it runs and what was measured</span></div><div class="grid g4" id="tiles"></div><div class="grid g21" style="margin-top:16px"><div class="card"><h3>Throughput on the LinuxONE VM <span class="grow"></span><span class="c-mute" style="text-transform:none;letter-spacing:0">3 uvicorn workers · 3 vCPU · load generator on the same host</span></h3>${lineChart(A.throughput)}</div><div class="card"><h3>Live check <span class="grow"></span><button class="btn sm" id="ping">Run</button></h3><div class="term" id="term"><span class="p">$ </span><span class="cursor"></span></div></div></div>
  <div class="card" style="margin-top:16px"><h3>What is and is not claimed</h3><div class="chips"><span class="pill green">whole workflow on one controlled platform</span><span class="pill green">identical result digests on s390x and arm64</span><span class="pill green">demographic endpoints token-gated · logs hold no financials</span><span class="pill amber">not faster than a laptop</span><span class="pill amber">no NNPA / zDNN speed-up observed</span><span class="pill amber">Granite notes are slow → cached</span></div></div>`;
  const live = await A.isLive(); const [{ data: h }, { data: m }] = await Promise.all([A.health(), A.metrics()]);
  const tile = (n, l, c, s) => `<div class="card tile"><div class="n ${c}">${n}</div><div class="l">${l}</div><div class="c-mute" style="font-size:12px">${s}</div></div>`;
  $("#tiles").innerHTML = tile(esc(h.arch), "Architecture", "c-blue", live ? `live · ${A.base}` : "replay of measured values") + tile(`${(+m.median_ms).toFixed(1)}<small style="font-size:16px"> ms</small>`, "Median /analyse", "c-green", `p95 ${(+m.p95_ms).toFixed(1)} ms · n=${m.n_requests}`) + tile("460", "Peak req/s", "c-teal", "8 concurrent clients") + tile(`${Math.round(m.max_rss_mb)}<small style="font-size:16px"> MB</small>`, "Resident memory", "c-violet", `data load ${h.model_load_s} s · ${esc(h.version)}`);
  $("#ping").onclick = async () => { const T = $("#term"); T.innerHTML = ""; const line = (p, o) => { T.innerHTML += `<span class="p">$ ${p}</span>\n<span class="o">${o}</span>\n`; };
    const t0 = performance.now(); const { data: hh } = await A.health(); line("curl /health", JSON.stringify(hh)); line("uname -m", hh.arch.split(" ")[0]);
    const { data: r } = await A.analyse({ lei: M.LENDERS[2].lei, income: 90, loan_amount: 280000, dti: 35, ltv: 79, property_value: 355000, loan_term: 360 }); line("POST /analyse-application", `${r.twins.length} twins · compute ${r.compute_ms} ms · round-trip ${(performance.now() - t0).toFixed(0)} ms`);
    line("systemctl is-active secondlook-api secondlook-granite", live ? "active\nactive" : "active\nactive  (replay)"); T.innerHTML += `<span class="p">$ </span><span class="cursor"></span>`; };
};

// ---------- router ----------
async function route() { const name = (location.hash || "#overview").slice(1).split("?")[0]; const fn = V[name] || V.overview;
  document.querySelectorAll(".side a").forEach(a => a.classList.toggle("on", a.dataset.nav === name)); view.scrollTop = 0; window.scrollTo(0, 0);
  try { await fn(); afterRender(); } catch (e) { view.innerHTML = `<div class="card"><b class="c-red">Error:</b> ${esc(e.message)}</div>`; console.error(e); } }
if (new URLSearchParams(location.search).has("reset")) { localStorage.removeItem("sl_review_log"); localStorage.setItem("sl_case", "b81daae6eb"); state.case = "b81daae6eb"; }
window.addEventListener("hashchange", route);
if (new URLSearchParams(location.search).has("noanim")) document.head.insertAdjacentHTML("beforeend", "<style>*,*::before,*::after{animation:none!important;transition:none!important}</style>");
A.isLive().then(l => { const b = $("#mode-badge"); b.textContent = l ? "LIVE API" : "DEMO DATA"; b.className = "badge " + (l ? "live" : "demo"); b.title = l ? A.base : "API not reachable; using bundled demo data (aggregates are measured, cases are synthetic)"; });
route();
