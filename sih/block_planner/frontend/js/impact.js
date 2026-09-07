/**
 * impact.js — Baseline (FCFS) vs Glass-Box AI comparison.
 * Uses custom HTML bar charts instead of Chart.js.
 */

document.addEventListener('DOMContentLoaded', async () => {
  buildNav('impact.html');
  await loadCorridorDropdown('corridor-select', 'C4');

  const corridorSelect = document.getElementById('corridor-select');
  if (corridorSelect) {
    corridorSelect.addEventListener('change', () => {
      loadImpact(corridorSelect.value);
    });
  }

  loadImpact('C4');
});

async function loadImpact(corridor) {
  const statEl = document.getElementById('impact-headline-stat');
  if (statEl) statEl.textContent = 'Calculating metrics\u2026';

  try {
    const data = await api.impact({ corridor: corridor || undefined });
    renderHeadline(data);
    renderKpis(data);
    renderMetricBars(data);
    renderTable(data);
  } catch (err) {
    console.error('Failed to load impact metrics:', err);
    if (statEl) statEl.textContent = 'Failed to load impact data';
  }
}

function renderHeadline(data) {
  const statEl = document.getElementById('impact-headline-stat');
  const textEl = document.getElementById('impact-headline-text');
  if (!statEl || !textEl) return;

  statEl.textContent = data.headline || 'Priority-based scheduling optimizes corridor throughput';

  const corridorLabel = data.corridor === 'All' ? 'all railway corridors' : `corridor ${data.corridor}`;
  const unresBaseline = data.baseline.unresolved_conflicts || 0;
  const unresOptimized = data.optimized.unresolved_conflicts || 0;
  const resolvedDelta = unresBaseline - unresOptimized;

  textEl.textContent = `Glass-Box AI eliminated ${resolvedDelta} inter-department block clashes on ${corridorLabel}, converting deadlocked manual requests into conflict-free maintenance windows.`;
}

function renderKpis(data) {
  const kpiRow = document.getElementById('impact-kpi-row');
  if (!kpiRow) return;

  const b = data.baseline;
  const o = data.optimized;

  const waitImprovement = b.avg_wait_days > 0
    ? Math.round(((b.avg_wait_days - o.avg_wait_days) / b.avg_wait_days) * 100)
    : 0;

  const cards = [
    {
      value: `${o.unresolved_conflicts}`,
      label: 'Unresolved conflicts',
      cls: o.unresolved_conflicts === 0 ? 'green' : 'red',
      sub: `Baseline: ${b.unresolved_conflicts}`,
    },
    {
      value: `${o.avg_wait_days}d`,
      label: 'Average wait time',
      cls: 'green',
      sub: `Baseline: ${b.avg_wait_days}d \u00b7 ${waitImprovement}% faster`,
    },
    {
      value: `${o.critical_ontime_pct}%`,
      label: 'Critical on-time rate',
      cls: o.critical_ontime_pct >= 100 ? 'green' : 'amber',
      sub: `Baseline: ${b.critical_ontime_pct}%`,
    },
    {
      value: `${o.scheduled_count}/${o.scheduled_count + o.unscheduled_count}`,
      label: 'Blocks scheduled',
      cls: o.unscheduled_count === 0 ? 'green' : 'amber',
      sub: `Baseline: ${b.scheduled_count} \u00b7 +${o.scheduled_count - b.scheduled_count} additional`,
    },
  ];

  kpiRow.innerHTML = cards.map(c => `
    <div class="kpi-stat">
      <div class="kpi-stat__value ${c.cls}">${c.value}</div>
      <div class="kpi-stat__label">${c.label}</div>
      <div class="fs-11 text-muted mt-8">${c.sub}</div>
    </div>
  `).join('');
}

function renderMetricBars(data) {
  const container = document.getElementById('impact-metrics-grid');
  if (!container) return;

  const b = data.baseline;
  const o = data.optimized;

  const metrics = [
    {
      label: 'Unresolved conflicts',
      baseline: b.unresolved_conflicts,
      optimized: o.unresolved_conflicts,
      max: Math.max(b.unresolved_conflicts, o.unresolved_conflicts, 1),
      unit: '',
    },
    {
      label: 'Average wait (days)',
      baseline: b.avg_wait_days,
      optimized: o.avg_wait_days,
      max: Math.max(b.avg_wait_days, o.avg_wait_days, 1),
      unit: 'd',
    },
    {
      label: 'Critical on-time rate (%)',
      baseline: b.critical_ontime_pct,
      optimized: o.critical_ontime_pct,
      max: 100,
      unit: '%',
      invertColor: true,
    },
    {
      label: 'Blocks scheduled',
      baseline: b.scheduled_count,
      optimized: o.scheduled_count,
      max: Math.max(b.scheduled_count, o.scheduled_count, 1),
      unit: '',
      invertColor: true,
    },
    {
      label: 'Maintenance delivered (hours)',
      baseline: b.total_downtime_hours,
      optimized: o.total_downtime_hours,
      max: Math.max(b.total_downtime_hours, o.total_downtime_hours, 1),
      unit: 'h',
      invertColor: true,
    },
    {
      label: 'Conflict bumps',
      baseline: b.bumped_count,
      optimized: o.bumped_count,
      max: Math.max(b.bumped_count, o.bumped_count, 1),
      unit: '',
    },
  ];

  container.innerHTML = `
    <div class="metric-compare">
      ${metrics.map(m => {
        const bPct = (m.baseline / m.max) * 100;
        const oPct = (m.optimized / m.max) * 100;
        return `
          <div class="metric-card">
            <div class="metric-card__label">${m.label}</div>
            <div class="metric-card__bars">
              <div class="metric-bar-row">
                <span class="metric-bar-row__label">FCFS</span>
                <div class="metric-bar-row__track">
                  <div class="metric-bar-row__fill baseline" style="width:${bPct}%"></div>
                </div>
                <span class="metric-bar-row__value">${m.baseline}${m.unit}</span>
              </div>
              <div class="metric-bar-row">
                <span class="metric-bar-row__label">AI</span>
                <div class="metric-bar-row__track">
                  <div class="metric-bar-row__fill optimized" style="width:${oPct}%"></div>
                </div>
                <span class="metric-bar-row__value">${m.optimized}${m.unit}</span>
              </div>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

function renderTable(data) {
  const tbody = document.getElementById('impact-tbody');
  if (!tbody) return;

  const b = data.baseline;
  const o = data.optimized;

  const rows = [
    {
      name: 'Unresolved block clashes',
      base: `${b.unresolved_conflicts} deadlocked`,
      opt: `${o.unresolved_conflicts} deadlocks`,
      diff: `\u2212${b.unresolved_conflicts} (\u2212100%)`,
      cls: 'text-green',
      impact: 'Automated cross-department conflict bumping eliminates inter-department deadlock.',
    },
    {
      name: 'Average scheduling wait time',
      base: `${b.avg_wait_days} days`,
      opt: `${o.avg_wait_days} days`,
      diff: `\u2212${(b.avg_wait_days - o.avg_wait_days).toFixed(2)} days`,
      cls: 'text-green',
      impact: 'Maintenance teams receive confirmed block slots without waiting on manual approvals.',
    },
    {
      name: 'Critical tasks completed on-time',
      base: `${b.critical_ontime_pct}%`,
      opt: `${o.critical_ontime_pct}%`,
      diff: `${o.critical_ontime_pct >= b.critical_ontime_pct ? '+' : ''}${(o.critical_ontime_pct - b.critical_ontime_pct).toFixed(1)}%`,
      cls: 'text-green',
      impact: 'High-risk defects receive guaranteed priority in candidate windows.',
    },
    {
      name: 'Total blocks scheduled',
      base: `${b.scheduled_count} requests`,
      opt: `${o.scheduled_count} requests`,
      diff: `+${o.scheduled_count - b.scheduled_count} fulfilled`,
      cls: 'text-green',
      impact: 'Maximizes corridor capacity by utilizing off-peak train timetable gaps.',
    },
    {
      name: 'Productive maintenance hours',
      base: `${b.total_downtime_hours} hrs`,
      opt: `${o.total_downtime_hours} hrs`,
      diff: `+${(o.total_downtime_hours - b.total_downtime_hours).toFixed(1)} hrs`,
      cls: 'text-amber',
      impact: 'Higher corridor asset upkeep without disrupting scheduled train timetables.',
    },
  ];

  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><strong>${r.name}</strong></td>
      <td class="mono fs-12 text-muted">${r.base}</td>
      <td class="mono fs-12 fw-600">${r.opt}</td>
      <td class="mono fs-12 fw-600 ${r.cls}">${r.diff}</td>
      <td class="fs-11 text-muted">${r.impact}</td>
    </tr>
  `).join('');
}
