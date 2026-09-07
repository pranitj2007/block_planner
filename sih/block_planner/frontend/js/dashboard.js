/**
 * dashboard.js — Dashboard page: corridor schematic hero, KPIs, department/severity dot-meters.
 */

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

document.addEventListener('DOMContentLoaded', async () => {
  buildNav('index.html');
  await loadCorridorDropdown('corridor-select', 'C4');

  const select = document.getElementById('corridor-select');
  select.addEventListener('change', () => loadDashboard(select.value));
  loadDashboard('C4');
});

async function loadDashboard(corridor) {
  try {
    const [dashData, priorityData, conflictData, scheduleData] = await Promise.all([
      api.dashboard(),
      api.priority({ corridor: corridor || undefined }),
      api.conflicts({ corridor: corridor || undefined }),
      api.schedule({ corridor: corridor || undefined }),
    ]);

    renderSubtitle(corridor, priorityData.data);
    renderKPIs(dashData);
    renderCorridorSchematic(scheduleData, conflictData.data, corridor);
    renderDepartments(dashData, priorityData.data);
    renderSeverity(dashData, priorityData.data);
    renderConflictHotspots(conflictData.data);
  } catch (e) {
    console.error('Dashboard load error:', e);
    document.getElementById('kpi-row').innerHTML =
      '<div class="empty-state" style="color:var(--signal-red)">Failed to load dashboard data. Is the Flask server running on port 5001?</div>';
  }
}

function renderSubtitle(corridor, requests) {
  const el = document.getElementById('header-subtitle');
  if (!el) return;
  const cid = corridor || 'All';
  const name = requests.length > 0 && requests[0].corridor_name ? requests[0].corridor_name : '';
  const suffix = name ? ` \u00b7 ${name}` : '';
  el.textContent = `${cid}${suffix} \u00b7 ${requests.length} block requests`;
}

function renderKPIs(data) {
  const k = data.kpis;
  const grid = document.getElementById('kpi-row');
  const items = [
    { value: k.total_requests, label: 'Total requests', cls: '' },
    { value: k.scheduled, label: 'Scheduled', cls: 'green' },
    { value: k.conflicts_resolved, label: 'Conflicts resolved', cls: 'amber' },
    { value: k.avg_overdue_days, label: 'Avg overdue (days)', cls: '' },
    { value: k.corridors_covered, label: 'Corridors', cls: '' },
    { value: k.unscheduled, label: 'Unscheduled', cls: k.unscheduled > 0 ? 'red' : '' },
  ];

  grid.innerHTML = items.map(i => `
    <div class="kpi-stat">
      <div class="kpi-stat__value ${i.cls}">${i.value}</div>
      <div class="kpi-stat__label">${i.label}</div>
    </div>
  `).join('');
}

function renderCorridorSchematic(scheduleData, conflicts, corridorFilter) {
  const container = document.getElementById('corridor-schematic');
  if (!container) return;

  const scheduled = scheduleData.scheduled || [];
  const conflictDays = {};
  for (const c of conflicts) {
    const key = `${c.corridor_id}_${c.day}`;
    conflictDays[key] = c;
  }

  // Group scheduled items by day
  const dayMap = {};
  for (const d of DAYS) { dayMap[d] = []; }
  for (const s of scheduled) {
    if (dayMap[s.day]) dayMap[s.day].push(s);
  }

  container.innerHTML = `
    <div class="corridor-track">
      ${DAYS.map(day => {
        const items = dayMap[day];
        // Determine conflict status for this day across all corridors shown
        const conflictKeys = Object.keys(conflictDays).filter(k => k.endsWith(`_${day}`));
        const hasConflict = conflictKeys.length > 0;

        // Build nodes
        let nodesHtml = '';
        if (items.length > 0) {
          nodesHtml = items.map(s => {
            let cls = 'resolved';
            if (s.was_bumped) cls = 'pending';
            return `<div class="node ${cls}" title="${s.request_id} ${s.department} ${s.start_time}\u2013${s.end_time}"></div>`;
          }).join('');
        } else if (hasConflict) {
          nodesHtml = '<div class="node conflict"></div>';
        }

        // Flag note
        let flagHtml = '';
        if (hasConflict && items.length > 0) {
          const c = conflictDays[conflictKeys[0]];
          flagHtml = `<div class="flag-note">${c.requests.length}-way conflict resolved</div>`;
        } else if (hasConflict) {
          flagHtml = '<div class="flag-note">conflict</div>';
        } else if (items.length === 0) {
          flagHtml = '<div class="flag-note green">clear</div>';
        }

        return `
          <div class="day-segment">
            <div class="node-row">${nodesHtml}</div>
            <div class="track-line"></div>
            <div class="day-label">${day}</div>
            ${flagHtml}
          </div>
        `;
      }).join('')}
    </div>
  `;
}

function renderDepartments(dashData, requests) {
  const container = document.getElementById('dept-rows');
  const meta = document.getElementById('dept-meta');
  if (!container) return;

  const depts = dashData.department_breakdown;
  const total = Object.values(depts).reduce((a, b) => a + b, 0);
  if (meta) meta.textContent = `${total} requests total`;

  // Compute avg score per dept
  const deptScores = {};
  const deptCounts = {};
  for (const r of requests) {
    deptScores[r.department] = (deptScores[r.department] || 0) + r.priority_score;
    deptCounts[r.department] = (deptCounts[r.department] || 0) + 1;
  }

  const maxDots = 5;
  container.innerHTML = Object.entries(depts).map(([dept, count]) => {
    const avg = deptCounts[dept] ? (deptScores[dept] / deptCounts[dept]).toFixed(1) : '0';
    const filled = Math.round((count / total) * maxDots);
    return `
      <div class="dept-row">
        <div class="dept-name">${dept}</div>
        <div class="dept-count">${count} requests</div>
        ${dotMeter(filled, maxDots, 'filled')}
        <div class="dept-score">avg ${avg}</div>
      </div>
    `;
  }).join('');
}

function renderSeverity(dashData, requests) {
  const container = document.getElementById('severity-rows');
  const meta = document.getElementById('severity-meta');
  if (!container) return;

  const sevs = dashData.severity_breakdown;
  const total = Object.values(sevs).reduce((a, b) => a + b, 0);
  if (meta) meta.textContent = `${total} requests`;

  const colorMap = { 'Critical': 'filled-red', 'Major': 'filled', 'Minor': 'filled' };
  const maxDots = 5;

  container.innerHTML = Object.entries(sevs).map(([sev, count]) => {
    const filled = Math.round((count / total) * maxDots);
    const cls = colorMap[sev] || 'filled';
    return `
      <div class="severity-row">
        <div class="dept-name">${severityBadge(sev)}</div>
        <div class="dept-count">${count} requests</div>
        ${dotMeter(filled, maxDots, cls)}
        <div class="dept-score">${Math.round((count / total) * 100)}%</div>
      </div>
    `;
  }).join('');
}

function renderConflictHotspots(conflicts) {
  const container = document.getElementById('conflict-rows');
  const meta = document.getElementById('conflict-meta');
  if (!container) return;

  if (meta) meta.textContent = `${conflicts.length} conflict groups`;

  if (conflicts.length === 0) {
    container.innerHTML = '<div class="empty-state">No conflicts detected</div>';
    return;
  }

  container.innerHTML = conflicts.map(c => {
    const typeLabel = c.conflict_type.replace(/_/g, ' ');
    return `
      <div class="dept-row" style="grid-template-columns: 80px 60px 1fr auto;">
        <div class="dept-name mono fs-12">${c.corridor_id}</div>
        <div class="dept-count">${c.day}</div>
        <div class="fs-12 text-muted">${c.requests.length} requests competing \u00b7 ${c.total_available_hours}h available \u00b7 ${c.total_requested_hours}h requested</div>
        <div><span class="badge ${typeLabel.includes('overflow') ? 'critical' : 'major'}">${typeLabel}</span></div>
      </div>
    `;
  }).join('');
}
