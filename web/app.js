/* CIRO Web Dashboard – app.js
 *
 * Pipeline flow (all calls to FastAPI at BASE_URL):
 *   POST /ingest/signal   → SignalBatch
 *   POST /detect/crisis   → CrisisEvent
 *   POST /reason/analyse  → CrisisAnalysis
 *   POST /plan/actions    → ActionPlan  (accepts CrisisEvent body)
 *   POST /simulate/execute → SimulationResult
 *
 * Signal feed polls GET /mock/social every 4 s.
 */

const BASE_URL = 'http://localhost:8000';

/* ── Sample signals to inject on TRIGGER ─────────────────────────── */
const SAMPLE_SIGNALS = [
  {
    source: 'social',
    text: 'G-10 mein pani bhar gaya hai, gaariyan phans gayi hain. Shadeed baarish jari hai.',
    metadata: { geo: 'G-10' }
  },
  {
    source: 'social',
    text: 'Flash flood in George Town Karachi — roads completely submerged, people stranded on rooftops.',
    metadata: {}
  },
  {
    source: 'weather',
    text: 'Heavy rainfall warning issued for Islamabad-Rawalpindi. Flash flood risk in G-10 and I-8 sectors.',
    metadata: { geo: 'G-10' }
  },
  {
    source: 'social',
    text: 'Shahrah-e-Faisal completely jammed after truck accident near old airport. Emergency services needed.',
    metadata: {}
  },
  {
    source: 'social',
    text: 'Karachi mein shadeed garmi, 48 degrees recorded. People collapsing on the street near Saddar.',
    metadata: {}
  }
];

/* ── State ───────────────────────────────────────────────────────── */
let signalFeedInterval = null;
let pipelineRunning = false;
let leafletMap = null;
let mapLayers = [];

/* ── Boot ────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  startClock();
  startSignalFeed();
  initMap();
  document.getElementById('triggerBtn').addEventListener('click', handleTrigger);
  document.getElementById('resetBtn').addEventListener('click', handleReset);
  document.getElementById('trace-toggle').addEventListener('click', toggleTracePanel);
});

/* ── Clock ───────────────────────────────────────────────────────── */
function startClock() {
  const el = document.getElementById('timestamp');
  function tick() { el.textContent = new Date().toLocaleTimeString(); }
  tick();
  setInterval(tick, 1000);
}

/* ── Signal Feed ─────────────────────────────────────────────────── */
function startSignalFeed() {
  fetchAndShowSignal();
  signalFeedInterval = setInterval(fetchAndShowSignal, 4000);
}

async function fetchAndShowSignal() {
  try {
    const signal = await get('/mock/social');
    prependSignalCard(signal);
  } catch (_) { /* silently skip on connection failure */ }
}

function prependSignalCard(signal) {
  const feed = document.getElementById('signal-feed');

  // Remove empty-state placeholder if present
  const empty = feed.querySelector('.empty-state');
  if (empty) empty.remove();

  const card = document.createElement('div');
  card.className = 'signal-card';

  const sevClass = signal.severity_hint === 'high' ? 'sev-high'
    : signal.severity_hint === 'medium' ? 'sev-medium' : 'sev-low';

  card.innerHTML = `
    <div class="signal-card-header">
      <span class="signal-source">${esc(signal.source || '—')}</span>
      <span class="signal-location">${esc(signal.location || signal.metadata?.geo || '')}</span>
    </div>
    <div class="signal-text">${esc(signal.content || signal.text || '')}</div>
    <span class="signal-sev ${sevClass}">${esc((signal.severity_hint || 'low').toUpperCase())}</span>
  `;

  feed.insertBefore(card, feed.firstChild);

  // Keep only the last 5 cards
  const cards = feed.querySelectorAll('.signal-card');
  if (cards.length > 5) cards[cards.length - 1].remove();
}

/* ── Trigger Pipeline ────────────────────────────────────────────── */
const AGENT_KEYS = ['ingest', 'detect', 'reason', 'plan', 'simulate'];

async function handleTrigger() {
  if (pipelineRunning) return;
  pipelineRunning = true;
  const btn = document.getElementById('triggerBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Running…';

  clearSimLog();
  resetAgentCards();
  clearCrisisPanel();
  clearTracePanel();
  resetOutcomeCards();

  const sample = SAMPLE_SIGNALS[Math.floor(Math.random() * SAMPLE_SIGNALS.length)];

  // Optimistic animation: first 4 agents pulse RUNNING in parallel with the fetch.
  setAgentStatus('ingest', 'running');
  addLog('info', `Ingesting signal: "${sample.text.slice(0, 60)}…"`);

  let result;
  try {
    result = await post('/pipeline/run', sample);
  } catch (err) {
    addLog('error', `Pipeline error: ${err.message}`);
    AGENT_KEYS.forEach(k => setAgentStatus(k, 'error'));
    pipelineRunning = false;
    btn.disabled = false;
    btn.textContent = '▶ TRIGGER PIPELINE';
    return;
  }

  const { batch, event, analysis, plan, simulation, run_id } = result;

  try {
    // Drive the 5-card animation from the actual run.
    await animateAgentsFromRun(run_id, { batch, event, analysis, plan, simulation });

    renderCrisisPanel(event, analysis);
    renderSimulationResults(simulation);

    // Map + Trace + Outcome – fired in parallel.
    await Promise.all([
      renderMapForLocation(event.location),
      renderTraceFromLatest(),
      renderOutcomeSummary(),
    ]);
  } catch (err) {
    addLog('error', `Render error: ${err.message}`);
  } finally {
    pipelineRunning = false;
    btn.disabled = false;
    btn.textContent = '▶ TRIGGER PIPELINE';
  }
}

async function animateAgentsFromRun(_runId, { batch, event, analysis, plan, simulation }) {
  // Pull the trace so per-step durations match reality where possible.
  let steps = [];
  try {
    const trace = await get('/trace/latest');
    steps = trace.steps || [];
  } catch (_) { /* ignore */ }

  const stepFor = (agent) => steps.find(s => s.agent && s.agent.startsWith(agent)) || {};

  // Step 1 — already showing RUNNING
  setAgentStatus('ingest', 'complete');
  addLog('info', `Batch built — ${batch.signals?.length ?? 1} signal(s), location: ${batch.primary_location || 'unknown'}`);
  await delay(180);

  setAgentStatus('detect', 'running');
  await delay(Math.min(stepFor('event-detection').duration_ms || 250, 700));
  setAgentStatus('detect', 'complete');
  addLog('info', `Crisis detected: ${event.crisis_type.toUpperCase()} | Confidence: ${Math.round(event.confidence * 100)}% | Severity: ${event.severity.toUpperCase()}`);

  setAgentStatus('reason', 'running');
  await delay(Math.min(stepFor('reasoning').duration_ms || 250, 700));
  setAgentStatus('reason', 'complete');
  addLog('info', `Analysis — ${(analysis.affected_population || 0).toLocaleString()} affected | Urgency: ${analysis.urgency}`);

  setAgentStatus('plan', 'running');
  await delay(Math.min(stepFor('action-planning').duration_ms || 200, 600));
  setAgentStatus('plan', 'complete');
  addLog('info', `Plan ready — ${plan.actions?.length ?? 0} action(s) queued`);

  setAgentStatus('simulate', 'running');
  await delay(Math.min(stepFor('simulation').duration_ms || 200, 600));
  setAgentStatus('simulate', 'complete');
}

/* ── Reset ───────────────────────────────────────────────────────── */
async function handleReset() {
  try {
    await post('/simulate/reset', {});
  } catch (_) { /* ignore */ }
  resetAgentCards();
  clearCrisisPanel();
  clearSimLog();
  clearTracePanel();
  resetOutcomeCards();
  clearMap();
}

/* ── Agent Card Helpers ──────────────────────────────────────────── */
const AGENT_IDS = { ingest: 'agent-ingest', detect: 'agent-detect', reason: 'agent-reason', plan: 'agent-plan', simulate: 'agent-simulate' };
const BADGE_TEXT = { idle: 'IDLE', running: 'RUNNING', complete: '✓ DONE', error: '✗ ERROR' };

function setAgentStatus(key, status) {
  const card = document.getElementById(AGENT_IDS[key]);
  if (!card) return;
  card.dataset.status = status;
  const badge = card.querySelector('.agent-badge');
  if (badge) badge.textContent = BADGE_TEXT[status] || status.toUpperCase();
}

function resetAgentCards() {
  Object.keys(AGENT_IDS).forEach(k => setAgentStatus(k, 'idle'));
}

/* ── Crisis Panel ────────────────────────────────────────────────── */
function clearCrisisPanel() {
  const display = document.getElementById('crisis-display');
  display.innerHTML = `
    <div class="crisis-idle">
      <div class="crisis-idle-icon">⚠</div>
      <div class="crisis-idle-text">No active crisis detected</div>
      <div class="crisis-idle-sub">Trigger the pipeline to run detection</div>
    </div>`;
}

function renderCrisisPanel(event, analysis) {
  const display = document.getElementById('crisis-display');
  const confidence = event.confidence;
  const pct = Math.round(confidence * 100);

  /* SVG semicircle gauge
   * Arc: M 10 80 A 70 70 0 0 1 150 80
   * Arc length ≈ π * 70 ≈ 220 */
  const ARC_LEN = 220;
  const dashOffset = ARC_LEN * (1 - confidence);

  /* Gauge colour by severity */
  const gaugeColor = {
    critical: '#f85149',
    high: '#e3843a',
    medium: '#d29922',
    low: '#3fb950'
  }[event.severity?.toLowerCase()] || '#58a6ff';

  const sevClass = `sev-${(event.severity || 'LOW').toUpperCase()}`;

  const impactHTML = (analysis.impact || []).slice(0, 2)
    .map(i => `<li>${esc(i)}</li>`).join('');

  display.innerHTML = `
    <div class="crisis-active">
      <div class="crisis-type-label">${esc(event.crisis_type?.toUpperCase() || '—')}</div>

      <div class="gauge-wrap">
        <svg class="gauge-svg" viewBox="0 0 160 88">
          <path class="gauge-bg-path"
            d="M 10 80 A 70 70 0 0 1 150 80"
            stroke-dasharray="${ARC_LEN} ${ARC_LEN}"
          />
          <path class="gauge-fill-path"
            id="gauge-fill"
            d="M 10 80 A 70 70 0 0 1 150 80"
            stroke="${gaugeColor}"
            stroke-dasharray="${ARC_LEN} ${ARC_LEN}"
            stroke-dashoffset="${ARC_LEN}"
          />
        </svg>
        <div class="gauge-label" id="gauge-pct" style="color:${gaugeColor}">0%</div>
      </div>

      <div class="severity-badge ${sevClass}">${esc((event.severity || 'LOW').toUpperCase())}</div>

      <div class="crisis-location">&#128205; ${esc(event.location || 'Unknown')}</div>

      <div class="crisis-explanation">${esc(event.explanation || '')}</div>

      <div class="crisis-meta">
        <div class="crisis-meta-item">
          <div class="crisis-meta-value">${(analysis.affected_population || 0).toLocaleString()}</div>
          <div class="crisis-meta-key">Affected</div>
        </div>
        <div class="crisis-meta-item">
          <div class="crisis-meta-value">${esc(analysis.urgency || '—')}</div>
          <div class="crisis-meta-key">Urgency</div>
        </div>
      </div>

      ${impactHTML ? `<ul style="font-size:0.68rem;color:var(--text-muted);padding-left:14px;width:100%;line-height:1.5">${impactHTML}</ul>` : ''}
    </div>`;

  // Animate gauge after DOM insert
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      const fill = document.getElementById('gauge-fill');
      const label = document.getElementById('gauge-pct');
      if (fill) fill.style.strokeDashoffset = dashOffset;
      // Count-up animation for label
      let current = 0;
      const step = () => {
        current = Math.min(current + 2, pct);
        if (label) label.textContent = `${current}%`;
        if (current < pct) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
  });
}

/* ── Simulation Log ─────────────────────────────────────────────── */
function clearSimLog() {
  const log = document.getElementById('sim-log');
  log.innerHTML = '<div class="empty-state">No simulation results yet</div>';
}

function renderSimulationResults(result) {
  const log = document.getElementById('sim-log');
  const empty = log.querySelector('.empty-state');
  if (empty) empty.remove();

  // Route updates
  (result.routes_updated || []).forEach(r => {
    addLogEntry('reroute', `Traffic rerouted on <strong>${esc(r.route)}</strong>: ${r.before}% → ${r.after}% congestion`);
  });

  // Tickets
  (result.tickets_created || []).forEach(t => {
    addLogEntry('ticket', `<strong>${esc(t.unit_dispatched)}</strong> dispatched to ${esc(t.location)} — ETA: ${t.eta_minutes} min`);
  });

  // Alerts
  (result.alerts_sent || []).forEach(a => {
    addLogEntry('alert', `Alert sent to <strong>${esc(a.target_area)}</strong> — ${a.recipients_count?.toLocaleString() ?? '?'} recipients via ${esc(a.channel)}`);
  });

  // Summary
  if (result.estimated_congestion_reduction > 0 || result.actions_executed?.length) {
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'log-summary';
    summaryDiv.innerHTML = `
      <div><strong>${result.estimated_congestion_reduction?.toFixed(1) ?? 0}%</strong><br><small>Congestion reduced</small></div>
      <div><strong>${result.estimated_response_time_minutes ?? 0} min</strong><br><small>Min response ETA</small></div>
      <div><strong>${(result.tickets_created || []).length}</strong><br><small>Tickets created</small></div>
      <div><strong>${(result.alerts_sent || []).length}</strong><br><small>Alerts sent</small></div>
    `;
    log.appendChild(summaryDiv);
  }
}

function addLogEntry(type, html) {
  const log = document.getElementById('sim-log');
  const entry = document.createElement('div');
  entry.className = `log-entry log-${type}`;
  const now = new Date().toLocaleTimeString();
  entry.innerHTML = `
    <div class="log-entry-time">${now}</div>
    <div class="log-entry-text">${html}</div>
  `;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}

function addLog(type, text) {
  addLogEntry(type, esc(text));
}

/* ── HTTP helpers ────────────────────────────────────────────────── */
async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function post(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`POST ${path} → ${res.status}: ${text}`);
  }
  return res.json();
}

/* ── Utilities ───────────────────────────────────────────────────── */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── Leaflet Map (3.5) ───────────────────────────────────────────── */
function initMap() {
  if (typeof L === 'undefined') return;
  leafletMap = L.map('leaflet-map', {
    zoomControl: true,
    attributionControl: false,
  }).setView([30.3753, 69.3451], 5); // Pakistan centroid

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap',
  }).addTo(leafletMap);

  L.control.attribution({ prefix: false }).addAttribution('&copy; OpenStreetMap').addTo(leafletMap);
}

function clearMap() {
  if (!leafletMap) return;
  mapLayers.forEach(l => leafletMap.removeLayer(l));
  mapLayers = [];
  leafletMap.setView([30.3753, 69.3451], 5);
  const metaEl = document.getElementById('map-location');
  if (metaEl) metaEl.textContent = 'No active crisis';
}

async function renderMapForLocation(location) {
  if (!leafletMap || !location) return;
  let overlay;
  try {
    overlay = await get(`/maps/crisis-overlay?location=${encodeURIComponent(location)}`);
  } catch (err) {
    addLog('error', `Map overlay fetch failed: ${err.message}`);
    return;
  }

  // Clear previous layers
  mapLayers.forEach(l => leafletMap.removeLayer(l));
  mapLayers = [];

  const bounds = [];

  // Crisis pin
  if (overlay.crisis_pin && overlay.crisis_pin.lat && overlay.crisis_pin.lng) {
    const pin = L.circleMarker([overlay.crisis_pin.lat, overlay.crisis_pin.lng], {
      radius: 9,
      color: '#fff',
      weight: 2,
      fillColor: '#f85149',
      fillOpacity: 0.95,
    }).bindPopup(`<strong>${esc(overlay.location || location)}</strong>`);
    pin.addTo(leafletMap);
    mapLayers.push(pin);
    bounds.push([overlay.crisis_pin.lat, overlay.crisis_pin.lng]);
  }

  // Affected polygon
  const poly = (overlay.affected_polygon || []).map(p => [p.lat, p.lng]);
  if (poly.length >= 3) {
    const polygon = L.polygon(poly, {
      color: '#f85149',
      weight: 1.5,
      fillColor: '#f85149',
      fillOpacity: 0.18,
    }).addTo(leafletMap);
    mapLayers.push(polygon);
    poly.forEach(pt => bounds.push(pt));
  }

  // Primary (blocked) route
  const primary = (overlay.primary_route?.polyline || []).map(p => [p.lat, p.lng]);
  if (primary.length >= 2) {
    const primaryLine = L.polyline(primary, {
      color: overlay.primary_route?.color || '#f85149',
      weight: 5,
      opacity: 0.85,
    }).bindTooltip(`${esc(overlay.primary_route?.name || 'Primary')} — ${esc(overlay.primary_route?.status || '')}`);
    primaryLine.addTo(leafletMap);
    mapLayers.push(primaryLine);
    primary.forEach(pt => bounds.push(pt));
  }

  // Alternate route
  const alt = (overlay.alternate_route?.polyline || []).map(p => [p.lat, p.lng]);
  if (alt.length >= 2) {
    const altLine = L.polyline(alt, {
      color: overlay.alternate_route?.color || '#3fb950',
      weight: 4,
      opacity: 0.9,
      dashArray: '8 6',
    }).bindTooltip(`${esc(overlay.alternate_route?.name || 'Alternate')} — ${esc(overlay.alternate_route?.status || '')}`);
    altLine.addTo(leafletMap);
    mapLayers.push(altLine);
    alt.forEach(pt => bounds.push(pt));
  }

  if (bounds.length) {
    leafletMap.fitBounds(bounds, { padding: [30, 30], maxZoom: 14 });
  }
  const metaEl = document.getElementById('map-location');
  if (metaEl) metaEl.textContent = overlay.location || location;
}

/* ── Trace Stepper (3.6) ─────────────────────────────────────────── */
function clearTracePanel() {
  const stepper = document.getElementById('trace-stepper');
  stepper.innerHTML = '<div class="empty-state">Trigger the pipeline to view the trace</div>';
  const meta = document.getElementById('trace-meta');
  if (meta) meta.textContent = '—';
}

function toggleTracePanel() {
  const panel = document.getElementById('panel-trace');
  panel.classList.toggle('panel-trace--collapsed');
}

const AGENT_KEY_MAP = [
  { match: 'signal-ingestion', key: 'ingest', label: 'Signal Ingestion Agent' },
  { match: 'event-detection', key: 'detect', label: 'Event Detection Agent' },
  { match: 'reasoning', key: 'reason', label: 'Reasoning & Analysis Agent' },
  { match: 'action-planning', key: 'plan', label: 'Action Planning Agent' },
  { match: 'simulation', key: 'simulate', label: 'Simulation Engine' },
];

async function renderTraceFromLatest() {
  let trace;
  try {
    trace = await get('/trace/latest');
  } catch (err) {
    addLog('error', `Trace fetch failed: ${err.message}`);
    return;
  }
  const stepper = document.getElementById('trace-stepper');
  stepper.innerHTML = '';

  const steps = trace.steps || [];
  const meta = document.getElementById('trace-meta');
  if (meta) {
    meta.textContent = `${trace.run_id || ''} · ${steps.length} steps · ${trace.total_duration_ms || 0} ms total`;
  }

  steps.forEach((step, idx) => {
    const mapping = AGENT_KEY_MAP.find(m => (step.agent || '').includes(m.match));
    const key = mapping?.key || 'ingest';
    const label = mapping?.label || step.agent;

    const card = document.createElement('div');
    card.className = `trace-step trace-step--${key}`;
    card.innerHTML = `
      <div class="trace-head">
        <div class="trace-step-num">${idx + 1}</div>
        <div>
          <div class="trace-step-agent">${esc(label)}</div>
          <div class="trace-step-step">${esc(step.step || '')}</div>
        </div>
        <div class="trace-step-duration">${step.duration_ms ?? 0} ms</div>
        <span class="trace-step-caret">▸</span>
      </div>
      <div class="trace-body">
        <div class="trace-body-label">Input</div>
        <pre>${highlightJson(step.input)}</pre>
        <div class="trace-body-label">Output</div>
        <pre>${highlightJson(step.output)}</pre>
      </div>
    `;
    card.querySelector('.trace-head').addEventListener('click', () => {
      card.classList.toggle('trace-step--open');
    });
    stepper.appendChild(card);
  });

  if (!steps.length) {
    stepper.innerHTML = '<div class="empty-state">Trace is empty for this run</div>';
  }
}

function highlightJson(obj) {
  let json;
  try { json = JSON.stringify(obj, null, 2); } catch (_) { json = String(obj); }
  if (json === undefined) json = 'null';
  return esc(json)
    .replace(/&quot;([^&]+?)&quot;(\s*:)/g, '<span class="json-key">&quot;$1&quot;</span>$2')
    .replace(/: (&quot;[^<]*?&quot;)/g, ': <span class="json-str">$1</span>')
    .replace(/: (-?\d+\.?\d*)/g, ': <span class="json-num">$1</span>')
    .replace(/: (true|false)/g, ': <span class="json-bool">$1</span>')
    .replace(/: (null)/g, ': <span class="json-null">$1</span>');
}

/* ── Outcome Visualisation (3.7) ─────────────────────────────────── */
const OUTCOME_FIELDS = [
  { id: 'outcome-congestion', key: 'congestion_reduction_pct', suffix: '%', decimals: 1 },
  { id: 'outcome-vehicles', key: 'vehicles_rerouted', suffix: '' },
  { id: 'outcome-eta', key: 'min_eta_minutes', suffix: ' min' },
  { id: 'outcome-alerts', key: 'alerts_dispatched', suffix: '' },
  { id: 'outcome-tickets', key: 'tickets_created', suffix: '' },
];

function resetOutcomeCards() {
  OUTCOME_FIELDS.forEach(({ id, suffix }) => {
    const el = document.getElementById(id);
    if (el) el.textContent = suffix ? `0${suffix}` : '0';
    const card = el?.closest('.outcome-card');
    if (card) card.classList.remove('bumped');
  });
}

async function renderOutcomeSummary() {
  let summary;
  try {
    summary = await get('/outcome/summary');
  } catch (err) {
    addLog('error', `Outcome fetch failed: ${err.message}`);
    return;
  }
  OUTCOME_FIELDS.forEach(({ id, key, suffix, decimals }) => {
    const target = Number(summary[key] || 0);
    animateCounter(id, target, suffix, decimals);
    const card = document.getElementById(id)?.closest('.outcome-card');
    if (card && target > 0) {
      card.classList.add('bumped');
    }
  });
}

function animateCounter(id, target, suffix = '', decimals = 0) {
  const el = document.getElementById(id);
  if (!el) return;
  const duration = 700;
  const start = performance.now();
  function frame(now) {
    const t = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - t, 3);
    const value = target * eased;
    const display = decimals ? value.toFixed(decimals) : Math.round(value).toLocaleString();
    el.textContent = `${display}${suffix}`;
    if (t < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
