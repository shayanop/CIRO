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

/* ── Boot ────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  startClock();
  startSignalFeed();
  document.getElementById('triggerBtn').addEventListener('click', handleTrigger);
  document.getElementById('resetBtn').addEventListener('click', handleReset);
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
async function handleTrigger() {
  if (pipelineRunning) return;
  pipelineRunning = true;
  const btn = document.getElementById('triggerBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Running…';

  clearSimLog();
  resetAgentCards();
  clearCrisisPanel();

  const sample = SAMPLE_SIGNALS[Math.floor(Math.random() * SAMPLE_SIGNALS.length)];

  try {
    /* ── Step 1: Ingest ────── */
    setAgentStatus('ingest', 'running');
    addLog('info', `Ingesting signal: "${sample.text.slice(0, 60)}…"`);
    const batch = await post('/ingest/signal', sample);
    setAgentStatus('ingest', 'complete');
    addLog('info', `Signal batch built — ${batch.signals?.length ?? 1} signal(s), location: ${batch.primary_location || 'unknown'}`);

    await delay(300);

    /* ── Step 2: Detect ────── */
    setAgentStatus('detect', 'running');
    addLog('info', 'Running event detection…');
    const event = await post('/detect/crisis', batch);
    setAgentStatus('detect', 'complete');
    addLog('info', `Crisis detected: ${event.crisis_type.toUpperCase()} | Confidence: ${Math.round(event.confidence * 100)}% | Severity: ${event.severity.toUpperCase()}`);

    await delay(300);

    /* ── Step 3: Reason ────── */
    setAgentStatus('reason', 'running');
    addLog('info', 'Analysing impact and affected population…');
    const analysis = await post('/reason/analyse', event);
    setAgentStatus('reason', 'complete');
    addLog('info', `Analysis complete — ${analysis.affected_population.toLocaleString()} people affected | Urgency: ${analysis.urgency}`);

    // Render crisis panel now (we have both event and analysis)
    renderCrisisPanel(event, analysis);

    await delay(300);

    /* ── Step 4: Plan ────── */
    setAgentStatus('plan', 'running');
    addLog('info', 'Generating action plan…');
    const plan = await post('/plan/actions', event);
    setAgentStatus('plan', 'complete');
    addLog('info', `Action plan ready — ${plan.actions?.length ?? 0} action(s) queued`);

    await delay(300);

    /* ── Step 5: Simulate ────── */
    setAgentStatus('simulate', 'running');
    addLog('info', 'Executing actions against world state…');
    const result = await post('/simulate/execute', plan);
    setAgentStatus('simulate', 'complete');

    renderSimulationResults(result);

  } catch (err) {
    addLog('error', `Pipeline error: ${err.message}`);
  } finally {
    pipelineRunning = false;
    btn.disabled = false;
    btn.textContent = '▶ TRIGGER PIPELINE';
  }
}

/* ── Reset ───────────────────────────────────────────────────────── */
async function handleReset() {
  try {
    await post('/simulate/reset', {});
  } catch (_) { /* ignore */ }
  resetAgentCards();
  clearCrisisPanel();
  clearSimLog();
}

/* ── Agent Card Helpers ──────────────────────────────────────────── */
const AGENT_IDS = { ingest: 'agent-ingest', detect: 'agent-detect', reason: 'agent-reason', plan: 'agent-plan', simulate: 'agent-simulate' };
const BADGE_TEXT = { idle: 'IDLE', running: 'RUNNING', complete: '✓ DONE' };

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
    high:     '#e3843a',
    medium:   '#d29922',
    low:      '#3fb950'
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
