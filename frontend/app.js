'use strict';

// When served from FastAPI (port 8000) use relative URLs.
// When served from a static server (any other port) point directly to FastAPI.
const BASE = window.location.port === '8000'
  ? ''
  : `${window.location.protocol}//${window.location.hostname}:8000`;

const state = {
  clients: [],
  activeClientId: null,
  activeClient: null,
  activeTab: 'profile',
  activeMealPlan: null,
  activeWorkoutPlan: null,
  logs: [],
  report: null,
};

// ── API ───────────────────────────────────────────────────────────────────────

const api = {
  async _fetch(url, opts = {}) {
    const r = await fetch(BASE + url, {
      headers: { 'Content-Type': 'application/json' },
      ...opts,
    });
    if (r.status === 204) return null;
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
    return data;
  },
  getClients:          ()         => api._fetch('/api/clients/'),
  getClient:           (id)       => api._fetch(`/api/clients/${id}`),
  createClient:        (d)        => api._fetch('/api/clients/', { method: 'POST', body: JSON.stringify(d) }),
  updateClient:        (id, d)    => api._fetch(`/api/clients/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
  deleteClient:        (id)       => api._fetch(`/api/clients/${id}`, { method: 'DELETE' }),
  generateMealPlan:    (id)       => api._fetch(`/api/clients/${id}/meal-plans/generate`, { method: 'POST' }),
  getActiveMealPlan:   (id)       => api._fetch(`/api/clients/${id}/meal-plans/active`),
  generateWorkoutPlan: (id)       => api._fetch(`/api/clients/${id}/workout-plans/generate`, { method: 'POST' }),
  getActiveWorkoutPlan:(id)       => api._fetch(`/api/clients/${id}/workout-plans/active`),
  createLog:           (id, d)    => api._fetch(`/api/clients/${id}/logs/`, { method: 'POST', body: JSON.stringify(d) }),
  getLogs:             (id)       => api._fetch(`/api/clients/${id}/logs/`),
  deleteLog:           (id, dt)   => api._fetch(`/api/clients/${id}/logs/${dt}`, { method: 'DELETE' }),
  generateReport:      (id, days) => api._fetch(`/api/clients/${id}/reports/generate`, {
    method: 'POST', body: JSON.stringify({ period_days: days }),
  }),
};

// ── Toast ─────────────────────────────────────────────────────────────────────

function toast(msg, type = 'success') {
  const el = document.createElement('div');
  el.className = `toast ${type === 'error' ? 'error' : type === 'warning' ? 'warning' : ''}`;
  el.textContent = msg;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Loading state ─────────────────────────────────────────────────────────────

function setLoading(btn, loading, originalText) {
  if (loading) {
    btn._orig = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Loading…';
    btn.disabled = true;
  } else {
    btn.innerHTML = btn._orig || originalText || btn.innerHTML;
    btn.disabled = false;
  }
}

// ── Navigate ──────────────────────────────────────────────────────────────────

async function navigate(view, clientId = null) {
  document.getElementById('client-list-view').style.display = view === 'list' ? '' : 'none';
  document.getElementById('client-detail-view').style.display = view === 'detail' ? '' : 'none';

  if (view === 'list') {
    await loadClientList();
  } else if (view === 'detail' && clientId) {
    state.activeClientId = clientId;
    state.activeMealPlan = null;
    state.activeWorkoutPlan = null;
    state.logs = [];
    state.report = null;
    await loadClientDetail(clientId);
  }
}

// ── Client List ───────────────────────────────────────────────────────────────

async function loadClientList() {
  try {
    state.clients = await api.getClients();
    renderClientList(state.clients);
  } catch (e) {
    toast('Failed to load clients: ' + e.message, 'error');
  }
}

function renderClientList(clients) {
  const grid = document.getElementById('client-cards');
  grid.innerHTML = '';

  clients.forEach(c => {
    const card = document.createElement('div');
    card.className = 'client-card';
    card.innerHTML = `
      <div class="badge badge-${c.goal || 'maintain'}">${(c.goal || 'no goal').replace('_', ' ')}</div>
      <div class="card-name">${c.name}</div>
      <div class="card-stats">
        ${c.weight_kg ? c.weight_kg + ' kg' : ''}<br>
        ${c.target_kcal ? c.target_kcal.toFixed(0) + ' kcal target' : ''}
      </div>
    `;
    card.onclick = () => navigate('detail', c.id);
    grid.appendChild(card);
  });

  const add = document.createElement('div');
  add.className = 'client-card add-card';
  add.innerHTML = '<span style="font-size:1.8rem">+</span><span>Add Client</span>';
  add.onclick = () => showCreateModal();
  grid.appendChild(add);
}

// ── Client Detail ─────────────────────────────────────────────────────────────

async function loadClientDetail(clientId) {
  try {
    state.activeClient = await api.getClient(clientId);
    document.getElementById('client-name-heading').textContent = state.activeClient.name;
    activateTab('profile');
  } catch (e) {
    toast('Failed to load client: ' + e.message, 'error');
  }
}

// ── Tabs ──────────────────────────────────────────────────────────────────────

function activateTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === `tab-${tab}`));

  if (tab === 'profile')   renderProfile(state.activeClient);
  if (tab === 'meal-plan') loadAndRenderMealPlan();
  if (tab === 'workout')   loadAndRenderWorkoutPlan();
  if (tab === 'log')       loadAndRenderLogs();
  if (tab === 'report')    renderReportEmpty();
}

// ── Profile ───────────────────────────────────────────────────────────────────

function renderProfile(c) {
  if (!c) return;
  const f = document.getElementById('profile-form');
  f.querySelector('[name=name]').value = c.name || '';
  f.querySelector('[name=age]').value = c.age || '';
  f.querySelector('[name=sex]').value = c.sex || '';
  f.querySelector('[name=height_cm]').value = c.height_cm || '';
  f.querySelector('[name=weight_kg]').value = c.weight_kg || '';
  f.querySelector('[name=goal]').value = c.goal || '';
  f.querySelector('[name=activity_level]').value = c.activity_level || '';
  f.querySelector('[name=dietary_restrictions]').value = (c.dietary_restrictions || []).join(', ');
  f.querySelector('[name=injuries]').value = (c.injuries || []).join(', ');

  document.getElementById('stat-bmr').textContent = c.bmr ? c.bmr.toFixed(0) : '—';
  document.getElementById('stat-tdee').textContent = c.tdee ? c.tdee.toFixed(0) : '—';
  document.getElementById('stat-target').textContent = c.target_kcal ? c.target_kcal.toFixed(0) : '—';
}

async function handleSaveProfile(e) {
  e.preventDefault();
  const btn = e.target.querySelector('[type=submit]');
  setLoading(btn, true);
  const f = document.getElementById('profile-form');
  const raw = dr => dr.split(',').map(s => s.trim()).filter(Boolean);
  const data = {
    name:                  f.querySelector('[name=name]').value,
    age:                   parseInt(f.querySelector('[name=age]').value) || null,
    sex:                   f.querySelector('[name=sex]').value || null,
    height_cm:             parseFloat(f.querySelector('[name=height_cm]').value) || null,
    weight_kg:             parseFloat(f.querySelector('[name=weight_kg]').value) || null,
    goal:                  f.querySelector('[name=goal]').value || null,
    activity_level:        f.querySelector('[name=activity_level]').value || null,
    dietary_restrictions:  raw(f.querySelector('[name=dietary_restrictions]').value),
    injuries:              raw(f.querySelector('[name=injuries]').value),
  };
  try {
    state.activeClient = await api.updateClient(state.activeClientId, data);
    renderProfile(state.activeClient);
    toast('Profile saved');
  } catch (err) {
    toast('Save failed: ' + err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

async function handleDeleteClient() {
  if (!confirm(`Delete ${state.activeClient.name}? This cannot be undone.`)) return;
  try {
    await api.deleteClient(state.activeClientId);
    toast('Client deleted');
    navigate('list');
  } catch (e) {
    toast('Delete failed: ' + e.message, 'error');
  }
}

// ── Meal Plan ─────────────────────────────────────────────────────────────────

async function loadAndRenderMealPlan() {
  if (state.activeMealPlan) { renderMealPlan(state.activeMealPlan); return; }
  try {
    state.activeMealPlan = await api.getActiveMealPlan(state.activeClientId);
    renderMealPlan(state.activeMealPlan);
  } catch {
    renderMealPlan(null);
  }
}

function renderMealPlan(plan) {
  const el = document.getElementById('meal-plan-content');
  if (!plan) {
    el.innerHTML = `
      <div class="empty-state">
        <p>No meal plan yet.</p>
        <button class="btn" onclick="generateMealPlan(this)">Generate Meal Plan</button>
      </div>`;
    return;
  }
  const days = plan.plan_data?.days || [];
  el.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <span style="color:var(--text-muted);font-size:0.82rem">Avg: ${plan.plan_data?.weekly_avg_kcal || '—'} kcal/day</span>
      <button class="btn btn-sm btn-secondary" onclick="generateMealPlan(this)">Regenerate</button>
    </div>
    <div class="day-cards">
      ${days.map(d => `
        <div class="day-card">
          <div class="day-card-header" onclick="toggleDay(this)">
            <span class="day-name">${d.day}</span>
            <span class="day-kcal">${d.day_total_kcal} kcal</span>
          </div>
          <div class="day-card-body">
            ${(d.meals || []).map(m => `
              <div class="meal-item">
                <div class="meal-name">${m.name}</div>
                <div class="meal-foods">${(m.foods || []).join(', ')}</div>
                <div class="macro-chips">
                  <span class="chip">${m.kcal} kcal</span>
                  <span class="chip chip-p">P ${m.protein_g}g</span>
                  <span class="chip chip-c">C ${m.carbs_g}g</span>
                  <span class="chip chip-f">F ${m.fat_g}g</span>
                </div>
              </div>`).join('')}
          </div>
        </div>`).join('')}
    </div>
    ${plan.plan_data?.notes ? `<p style="margin-top:1rem;color:var(--text-muted);font-size:0.82rem">${plan.plan_data.notes}</p>` : ''}
  `;
}

function toggleDay(header) {
  const body = header.nextElementSibling;
  body.classList.toggle('open');
}

async function generateMealPlan(btn) {
  setLoading(btn, true);
  try {
    state.activeMealPlan = await api.generateMealPlan(state.activeClientId);
    renderMealPlan(state.activeMealPlan);
    toast('Meal plan generated');
  } catch (e) {
    toast('Generation failed: ' + e.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

// ── Workout Plan ──────────────────────────────────────────────────────────────

async function loadAndRenderWorkoutPlan() {
  if (state.activeWorkoutPlan) { renderWorkoutPlan(state.activeWorkoutPlan); return; }
  try {
    state.activeWorkoutPlan = await api.getActiveWorkoutPlan(state.activeClientId);
    renderWorkoutPlan(state.activeWorkoutPlan);
  } catch {
    renderWorkoutPlan(null);
  }
}

function renderWorkoutPlan(plan) {
  const el = document.getElementById('workout-content');
  if (!plan) {
    el.innerHTML = `
      <div class="empty-state">
        <p>No workout plan yet.</p>
        <button class="btn" onclick="generateWorkoutPlan(this)">Generate Workout Plan</button>
      </div>`;
    return;
  }
  const days = plan.plan_data?.days || [];
  el.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <span style="color:var(--text-muted);font-size:0.82rem">
        Rest days: ${(plan.plan_data?.rest_days || []).join(', ') || '—'}
      </span>
      <button class="btn btn-sm btn-secondary" onclick="generateWorkoutPlan(this)">Regenerate</button>
    </div>
    <div class="day-cards">
      ${days.map(d => `
        <div class="day-card">
          <div class="day-card-header" onclick="toggleDay(this)">
            <span class="day-name">${d.day}</span>
            <span class="day-kcal" style="color:${d.focus==='rest'?'var(--text-muted)':'var(--success)'}">
              ${d.focus === 'rest' ? 'Rest' : (d.duration_min ? d.duration_min + ' min' : d.focus)}
            </span>
          </div>
          <div class="day-card-body">
            ${d.focus === 'rest' ? '<p style="color:var(--text-muted);font-size:0.85rem;padding-top:0.5rem">Rest & recovery day</p>' :
              `<p style="color:var(--text-muted);font-size:0.82rem;margin-bottom:0.5rem">${d.focus}</p>
              ${(d.exercises || []).map(ex => `
                <div class="exercise-item">
                  <span class="exercise-name">${ex.name}</span>
                  <span class="sets-badge">${ex.sets}×${ex.reps}</span>
                  <span class="rest-badge">${ex.rest_seconds}s rest</span>
                </div>`).join('')}`
            }
          </div>
        </div>`).join('')}
    </div>
    ${plan.plan_data?.notes ? `<p style="margin-top:1rem;color:var(--text-muted);font-size:0.82rem">${plan.plan_data.notes}</p>` : ''}
  `;
}

async function generateWorkoutPlan(btn) {
  setLoading(btn, true);
  try {
    state.activeWorkoutPlan = await api.generateWorkoutPlan(state.activeClientId);
    renderWorkoutPlan(state.activeWorkoutPlan);
    toast('Workout plan generated');
  } catch (e) {
    toast('Generation failed: ' + e.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

// ── Daily Log ─────────────────────────────────────────────────────────────────

async function loadAndRenderLogs() {
  try {
    state.logs = await api.getLogs(state.activeClientId);
  } catch { state.logs = []; }
  renderLogTab();
}

function renderLogTab() {
  const today = new Date().toISOString().split('T')[0];
  const todayLog = state.logs.find(l => l.log_date === today);
  const pane = document.getElementById('tab-log');

  pane.innerHTML = `
    <div class="card">
      <div class="card-title">Log Today — ${today}</div>
      <form id="log-form">
        <div class="form-grid">
          <div class="form-group">
            <label>Date</label>
            <input type="date" name="log_date" value="${today}">
          </div>
          <div class="form-group">
            <label>Body Weight (kg)</label>
            <input type="number" name="body_weight_kg" step="0.1" placeholder="e.g. 80.5"
              value="${todayLog?.body_weight_kg || ''}">
          </div>
        </div>

        <div style="margin-top:1rem">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
            <label>Food Items</label>
            <button type="button" class="btn btn-sm btn-secondary" onclick="addFoodRow()">+ Add Food</button>
          </div>
          <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr auto;gap:0.4rem;margin-bottom:0.3rem">
            <span style="font-size:0.72rem;color:var(--text-muted)">Name</span>
            <span style="font-size:0.72rem;color:var(--text-muted)">kcal</span>
            <span style="font-size:0.72rem;color:var(--text-muted)">Protein</span>
            <span style="font-size:0.72rem;color:var(--text-muted)">Carbs</span>
            <span style="font-size:0.72rem;color:var(--text-muted)">Fat</span>
            <span></span>
          </div>
          <div id="food-rows"></div>
        </div>

        <div class="form-grid" style="margin-top:1rem">
          <div class="form-group">
            <label>
              <input type="checkbox" name="workout_done" style="width:auto;margin-right:0.4rem"
                ${todayLog?.workout_done ? 'checked' : ''}>
              Workout done today
            </label>
          </div>
          <div class="form-group">
            <label>Workout Notes</label>
            <input type="text" name="workout_notes" placeholder="e.g. Chest day, 5×5 bench"
              value="${todayLog?.workout_notes || ''}">
          </div>
          <div class="form-group full">
            <label>General Notes</label>
            <textarea name="general_notes" placeholder="Energy, sleep, mood…">${todayLog?.general_notes || ''}</textarea>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn">Save Log</button>
        </div>
      </form>
    </div>

    <div class="card" style="margin-top:1rem">
      <div class="card-title">History (last 30 days)</div>
      ${renderLogHistory(state.logs)}
    </div>
  `;

  document.getElementById('log-form').addEventListener('submit', handleAddLog);

  if (todayLog?.food_items?.length) {
    todayLog.food_items.forEach(f => addFoodRow(f));
  } else {
    addFoodRow();
  }
}

function addFoodRow(item = {}) {
  const row = document.createElement('div');
  row.className = 'food-row';
  row.innerHTML = `
    <input type="text"   placeholder="Chicken breast 150g" value="${item.name || ''}">
    <input type="number" placeholder="248"  step="1"   value="${item.kcal || ''}">
    <input type="number" placeholder="46g"  step="0.1" value="${item.protein_g || ''}">
    <input type="number" placeholder="0g"   step="0.1" value="${item.carbs_g || ''}">
    <input type="number" placeholder="5g"   step="0.1" value="${item.fat_g || ''}">
    <button type="button" class="btn btn-sm btn-danger" onclick="this.closest('.food-row').remove()">✕</button>
  `;
  document.getElementById('food-rows').appendChild(row);
}

function renderLogHistory(logs) {
  if (!logs.length) return '<p style="color:var(--text-muted);font-size:0.85rem">No entries yet.</p>';
  return `
    <table class="log-table">
      <thead><tr>
        <th>Date</th><th>kcal</th><th>Balance</th><th>P/C/F</th><th>Workout</th><th></th>
      </tr></thead>
      <tbody>
        ${logs.map(l => {
          const bal = l.kcal_balance;
          const cls = bal > 150 ? 'balance-pos' : bal < -150 ? 'balance-neg' : 'balance-ok';
          const sign = bal > 0 ? '+' : '';
          return `<tr>
            <td>${l.log_date}</td>
            <td>${l.total_kcal_consumed.toFixed(0)}</td>
            <td class="${cls}">${sign}${bal.toFixed(0)}</td>
            <td style="font-size:0.78rem;color:var(--text-muted)">
              ${l.total_protein_g.toFixed(0)}/${l.total_carbs_g.toFixed(0)}/${l.total_fat_g.toFixed(0)}g
            </td>
            <td>${l.workout_done ? '✓' : '—'}</td>
            <td><button class="btn btn-sm btn-danger" onclick="deleteLog('${l.log_date}',this)">✕</button></td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>
  `;
}

async function handleAddLog(e) {
  e.preventDefault();
  const btn = e.target.querySelector('[type=submit]');
  setLoading(btn, true);

  const f = e.target;
  const rows = document.querySelectorAll('#food-rows .food-row');
  const food_items = [];
  rows.forEach(r => {
    const inputs = r.querySelectorAll('input');
    const name = inputs[0].value.trim();
    if (!name) return;
    food_items.push({
      name,
      kcal:      parseFloat(inputs[1].value) || 0,
      protein_g: parseFloat(inputs[2].value) || 0,
      carbs_g:   parseFloat(inputs[3].value) || 0,
      fat_g:     parseFloat(inputs[4].value) || 0,
    });
  });

  const data = {
    log_date:       f.querySelector('[name=log_date]').value,
    body_weight_kg: parseFloat(f.querySelector('[name=body_weight_kg]').value) || null,
    food_items,
    workout_done:   f.querySelector('[name=workout_done]').checked,
    workout_notes:  f.querySelector('[name=workout_notes]').value,
    general_notes:  f.querySelector('[name=general_notes]').value,
  };

  try {
    await api.createLog(state.activeClientId, data);
    state.logs = await api.getLogs(state.activeClientId);
    renderLogTab();
    toast('Log saved');
  } catch (err) {
    toast('Save failed: ' + err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

async function deleteLog(logDate, btn) {
  if (!confirm(`Delete log for ${logDate}?`)) return;
  setLoading(btn, true);
  try {
    await api.deleteLog(state.activeClientId, logDate);
    state.logs = await api.getLogs(state.activeClientId);
    renderLogTab();
    toast('Log deleted');
  } catch (e) {
    toast('Delete failed: ' + e.message, 'error');
    setLoading(btn, false);
  }
}

// ── Report ────────────────────────────────────────────────────────────────────

function renderReportEmpty() {
  if (state.report) { renderReport(state.report); return; }
  document.getElementById('report-content').innerHTML = `
    <div class="empty-state">
      <p>Generate a progress report for the last 30 days.</p>
      <button class="btn" onclick="generateReport(this, 30)">Generate Report</button>
    </div>
  `;
}

async function generateReport(btn, days) {
  setLoading(btn, true);
  try {
    state.report = await api.generateReport(state.activeClientId, days);
    renderReport(state.report);
    toast('Report ready');
  } catch (e) {
    toast('Report failed: ' + e.message, 'error');
    setLoading(btn, false);
  }
}

function renderReport(r) {
  const el = document.getElementById('report-content');

  const sparkline = buildSparkline(r.weight_trend);

  el.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <span style="color:var(--text-muted);font-size:0.82rem">Last ${r.period_days} days · ${r.total_days_logged} logs</span>
      <button class="btn btn-sm btn-secondary" onclick="generateReport(this, ${r.period_days})">Refresh</button>
    </div>

    <div class="stat-grid">
      <div class="report-stat">
        <div class="big-num">${r.avg_kcal_consumed.toFixed(0)}</div>
        <div class="big-lbl">Avg kcal / day</div>
      </div>
      <div class="report-stat">
        <div class="big-num">${r.kcal_adherence_pct}%</div>
        <div class="big-lbl">Kcal adherence</div>
      </div>
      <div class="report-stat">
        <div class="big-num">${r.workout_days}</div>
        <div class="big-lbl">Workouts logged</div>
      </div>
      <div class="report-stat">
        <div class="big-num">${r.workout_consistency_pct}%</div>
        <div class="big-lbl">Workout consistency</div>
      </div>
    </div>

    ${sparkline ? `<div class="weight-chart-wrap">${sparkline}</div>` : ''}

    <div class="card-title" style="margin-bottom:0.5rem">Coaching Recommendations</div>
    <div class="recommendations">${r.recommendations}</div>
  `;
}

function buildSparkline(trend) {
  if (!trend || trend.length < 2) return '';
  const weights = trend.map(t => t.weight_kg);
  const min = Math.min(...weights);
  const max = Math.max(...weights);
  const range = max - min || 1;
  const W = 600, H = 70, PAD = 8;
  const pts = trend.map((t, i) => {
    const x = PAD + (i / (trend.length - 1)) * (W - PAD * 2);
    const y = PAD + ((max - t.weight_kg) / range) * (H - PAD * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const first = trend[0], last = trend[trend.length - 1];
  const delta = (last.weight_kg - first.weight_kg).toFixed(1);
  const color = delta < 0 ? 'var(--success)' : 'var(--accent2)';
  return `
    <div style="display:flex;justify-content:space-between;margin-bottom:0.4rem;font-size:0.78rem;color:var(--text-muted)">
      <span>Weight trend</span>
      <span style="color:${color}">${delta > 0 ? '+' : ''}${delta} kg (${first.date} → ${last.date})</span>
    </div>
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
      <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round"/>
    </svg>`;
}

// ── Create Client Modal ───────────────────────────────────────────────────────

function showCreateModal() {
  document.getElementById('create-modal').style.display = '';
}

function hideCreateModal() {
  document.getElementById('create-modal').style.display = 'none';
  document.getElementById('create-form').reset();
}

async function handleCreateClient(e) {
  e.preventDefault();
  const btn = e.target.querySelector('[type=submit]');
  setLoading(btn, true);
  const f = e.target;
  const raw = dr => dr.split(',').map(s => s.trim()).filter(Boolean);
  const data = {
    name:                 f.querySelector('[name=name]').value,
    age:                  parseInt(f.querySelector('[name=age]').value) || null,
    sex:                  f.querySelector('[name=sex]').value || null,
    height_cm:            parseFloat(f.querySelector('[name=height_cm]').value) || null,
    weight_kg:            parseFloat(f.querySelector('[name=weight_kg]').value) || null,
    goal:                 f.querySelector('[name=goal]').value || null,
    activity_level:       f.querySelector('[name=activity_level]').value || null,
    dietary_restrictions: raw(f.querySelector('[name=dietary_restrictions]').value),
    injuries:             raw(f.querySelector('[name=injuries]').value),
  };
  try {
    const client = await api.createClient(data);
    hideCreateModal();
    toast(`${client.name} added`);
    navigate('detail', client.id);
  } catch (err) {
    toast('Create failed: ' + err.message, 'error');
    setLoading(btn, false);
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('back-btn').onclick = () => navigate('list');

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.onclick = () => activateTab(btn.dataset.tab);
  });

  document.getElementById('profile-form').addEventListener('submit', handleSaveProfile);
  document.getElementById('delete-client-btn').onclick = handleDeleteClient;

  document.getElementById('create-form').addEventListener('submit', handleCreateClient);
  document.getElementById('cancel-create').onclick = hideCreateModal;
  document.querySelector('.modal-backdrop').onclick = hideCreateModal;

  navigate('list');
});
