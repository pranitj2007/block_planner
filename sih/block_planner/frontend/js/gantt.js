/**
 * gantt.js — Plotly Gantt chart + corridor schematic + schedule table.
 */

let currentCorridor = 'C4';
let currentHorizon = 'weekly';
let currentDept = '';
let scheduleData = null;

const DAY_OFFSETS = {
  'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6
};

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

document.addEventListener('DOMContentLoaded', async () => {
  buildNav('gantt.html');
  await loadCorridorDropdown('corridor-select', 'C4');

  const corridorSelect = document.getElementById('corridor-select');
  if (corridorSelect) {
    corridorSelect.addEventListener('change', () => {
      currentCorridor = corridorSelect.value;
      loadSchedule();
    });
  }

  const deptFilter = document.getElementById('dept-filter');
  if (deptFilter) {
    deptFilter.addEventListener('change', () => {
      currentDept = deptFilter.value;
      renderAll();
    });
  }

  loadSchedule();
});

function setHorizon(horizon) {
  currentHorizon = horizon;
  const btnWeekly = document.getElementById('btn-weekly');
  const btnMonthly = document.getElementById('btn-monthly');

  if (horizon === 'weekly') {
    btnWeekly.classList.add('active');
    btnMonthly.classList.remove('active');
  } else {
    btnMonthly.classList.add('active');
    btnWeekly.classList.remove('active');
  }

  loadSchedule();
}

async function loadSchedule() {
  const chartContainer = document.getElementById('gantt-chart');
  showLoading(chartContainer);

  try {
    const res = await api.schedule({
      corridor: currentCorridor || undefined,
      horizon: currentHorizon,
    });

    scheduleData = res;
    renderAll();
  } catch (err) {
    console.error('Failed to load schedule:', err);
    chartContainer.innerHTML = '<div class="empty-state" style="color:var(--signal-red)">Failed to load schedule data.</div>';
  }
}

function renderAll() {
  if (!scheduleData) return;
  const filtered = filterTasks(scheduleData.scheduled || []);
  renderTrackSchematic(scheduleData.scheduled || []);
  renderGantt(filtered);
  renderTable(filtered);
  updateMeta(scheduleData);
}

function filterTasks(tasks) {
  if (!currentDept) return tasks;
  return tasks.filter(t => t.department === currentDept);
}

function updateMeta(data) {
  const el = document.getElementById('schedule-meta');
  if (el) {
    el.textContent = `${data.summary.scheduled_count} scheduled \u00b7 ${data.summary.unscheduled_count} unscheduled`;
  }
  const sub = document.getElementById('gantt-subtitle');
  if (sub) {
    sub.textContent = `${currentHorizon} view \u00b7 ${data.summary.total_requests} total requests`;
  }
}

function renderTrackSchematic(allScheduled) {
  const container = document.getElementById('gantt-track-schematic');
  if (!container) return;

  const dayMap = {};
  for (const d of DAYS) { dayMap[d] = []; }
  for (const s of allScheduled) {
    if (dayMap[s.day]) dayMap[s.day].push(s);
  }

  container.innerHTML = `
    <div class="corridor-track">
      ${DAYS.map(day => {
        const items = dayMap[day];
        let nodesHtml = '';
        if (items.length > 0) {
          nodesHtml = items.slice(0, 6).map(s => {
            const cls = s.was_bumped ? 'pending' : 'resolved';
            return `<div class="node ${cls}" title="${s.request_id} ${s.department}"></div>`;
          }).join('');
        }

        return `
          <div class="day-segment">
            <div class="node-row">${nodesHtml}</div>
            <div class="track-line"></div>
            <div class="day-label">${day}</div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

/* Convert Day + Week + HH:MM to datetime string for Plotly */
function toDateTime(dayStr, weekNum, timeStr) {
  const offset = DAY_OFFSETS[dayStr] !== undefined ? DAY_OFFSETS[dayStr] : 0;
  const weekOffset = ((weekNum || 1) - 1) * 7;
  const totalDays = offset + weekOffset;

  const base = new Date('2026-09-07T00:00:00Z');
  base.setUTCDate(base.getUTCDate() + totalDays);

  const [hh, mm] = (timeStr || '00:00').split(':').map(Number);
  base.setUTCHours(hh || 0, mm || 0, 0, 0);

  return base.toISOString().replace('.000Z', '').replace('T', ' ');
}

function _minToTime(mins) {
  const h = Math.floor(mins / 60) % 24;
  const m = mins % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function renderGantt(tasks) {
  const chartContainer = document.getElementById('gantt-chart');
  if (!chartContainer) return;

  if (tasks.length === 0) {
    chartContainer.innerHTML = '<div class="empty-state">No scheduled blocks match the current filter criteria.</div>';
    return;
  }

  const sorted = [...tasks].sort((a, b) => {
    const dtA = toDateTime(a.day, a.week, a.start_time);
    const dtB = toDateTime(b.day, b.week, b.start_time);
    return dtA.localeCompare(dtB);
  });

  const colorMap = {
    'Engineering': '#60a5fa',
    'Signal':      '#E8A33D',
    'Traction':    '#4CAF6D',
  };

  const depts = ['Engineering', 'Signal', 'Traction'];
  const traces = [];

  depts.forEach(dept => {
    const deptTasks = sorted.filter(t => t.department === dept);
    if (deptTasks.length === 0) return;

    const y = [];
    const base = [];
    const x = [];
    const hoverText = [];
    const markerColors = [];

    deptTasks.forEach(task => {
      const yLabel = `${task.corridor_id} \u00b7 ${task.request_id}`;
      const startDt = toDateTime(task.day, task.week, task.start_time);

      let endDt = toDateTime(task.day, task.week, task.end_time);
      if (task.end_time <= task.start_time) {
        const nextDayOffset = (DAY_OFFSETS[task.day] + 1) % 7;
        const nextDay = DAYS[nextDayOffset];
        endDt = toDateTime(nextDay, task.week, task.end_time);
      }

      const startMs = new Date(startDt).getTime();
      const endMs = new Date(endDt).getTime();
      const durationMs = Math.max(endMs - startMs, (task.duration_hours || 1) * 3600 * 1000);

      y.push(yLabel);
      base.push(startDt);
      x.push(durationMs);

      const bumpNote = task.was_bumped ? `<br><b style="color:${colorMap['Signal']}">Bumped from ${task.original_preferred_day || 'original day'}</b>` : '';

      hoverText.push(
        `<b>${task.request_id}</b> (${task.department})<br>` +
        `Corridor: <b>${task.corridor_id}</b> \u2014 ${task.corridor_name || ''}<br>` +
        `Task: ${task.task_id || '\u2014'}<br>` +
        `Severity: <b>${task.severity}</b><br>` +
        `Scheduled: <b>${task.day} ${task.start_time} \u2013 ${task.end_time}</b> (${task.duration_hours}h)<br>` +
        `Priority score: <b>${task.priority_score}</b>` +
        bumpNote
      );

      markerColors.push(colorMap[dept] || '#8B98A9');
    });

    traces.push({
      type: 'bar',
      name: dept,
      orientation: 'h',
      y: y,
      x: x,
      base: base,
      hoverinfo: 'text',
      text: hoverText,
      marker: {
        color: markerColors,
        opacity: 0.85,
        line: { color: colorMap[dept] || '#8B98A9', width: 1 },
      },
    });
  });

  const minDt = '2026-09-07 00:00:00';
  const maxDt = currentHorizon === 'weekly' ? '2026-09-14 00:00:00' : '2026-10-05 00:00:00';

  const layout = {
    barmode: 'stack',
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'rgba(26, 34, 48, 0.5)',
    font: {
      family: 'IBM Plex Sans, sans-serif',
      color: '#8B98A9',
      size: 12,
    },
    margin: { l: 150, r: 20, t: 20, b: 50 },
    height: Math.max(350, sorted.length * 30 + 80),
    xaxis: {
      type: 'date',
      range: [minDt, maxDt],
      gridcolor: 'rgba(62, 92, 118, 0.3)',
      tickcolor: 'rgba(62, 92, 118, 0.5)',
      tickformat: currentHorizon === 'weekly' ? '%a %H:%M' : '%b %d',
      title: {
        text: currentHorizon === 'weekly' ? 'Timeline (day and hours)' : 'Timeline (monthly view)',
        font: { size: 11, color: '#8B98A9' },
      },
    },
    yaxis: {
      autorange: 'reversed',
      gridcolor: 'rgba(62, 92, 118, 0.15)',
      tickfont: { color: '#E8ECF1', size: 11, family: 'IBM Plex Mono, monospace' },
    },
    legend: {
      orientation: 'h',
      y: 1.1,
      x: 0,
      font: { color: '#E8ECF1', size: 12 },
    },
    hoverlabel: {
      bgcolor: '#1A2230',
      bordercolor: '#3E5C76',
      font: { family: 'IBM Plex Sans, sans-serif', color: '#E8ECF1', size: 12 },
    },
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
  };

  Plotly.newPlot('gantt-chart', traces, layout, config);
}

function renderTable(tasks) {
  const tbody = document.getElementById('schedule-tbody');
  if (!tbody) return;

  if (tasks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="text-muted" style="padding:16px">No blocks scheduled.</td></tr>';
    return;
  }

  tbody.innerHTML = tasks.map(t => {
    const bumpBadge = t.was_bumped
      ? `<span class="badge moved" title="Bumped from ${t.original_preferred_day}" style="margin-left:4px">moved</span>`
      : '';

    return `
      <tr>
        <td><strong class="mono fs-12">${t.request_id}</strong><div class="fs-11 text-muted">${t.task_id || ''}</div></td>
        <td class="mono fs-12">${t.corridor_id}</td>
        <td>${departmentBadge(t.department)}</td>
        <td>${severityBadge(t.severity)}</td>
        <td><strong>${t.day}</strong>${bumpBadge}</td>
        <td class="mono fs-12">${t.start_time} \u2013 ${t.end_time}</td>
        <td class="mono">${t.duration_hours}h</td>
        <td class="mono fw-600">${t.priority_score}</td>
        <td>${statusBadge(t.status || 'Scheduled')}</td>
      </tr>
    `;
  }).join('');
}
