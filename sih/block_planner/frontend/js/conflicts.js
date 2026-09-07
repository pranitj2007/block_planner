/**
 * conflicts.js — Before/after conflict resolution with request chips.
 * The single deliberate animation moment: chips slide into resolved positions.
 */
document.addEventListener('DOMContentLoaded', async () => {
  buildNav('conflicts.html');
  await loadCorridorDropdown('corridor-select', 'C4');

  const select = document.getElementById('corridor-select');
  select.addEventListener('change', () => loadConflicts(select.value));
  loadConflicts('C4');
});

async function loadConflicts(corridor) {
  const container = document.getElementById('conflicts-container');
  showLoading(container);

  try {
    const [conflictData, scheduleData, priorityData] = await Promise.all([
      api.conflicts({ corridor: corridor || undefined }),
      api.schedule({ corridor: corridor || undefined }),
      api.priority({ corridor: corridor || undefined }),
    ]);

    renderConflicts(container, conflictData.data, scheduleData, priorityData.data);
  } catch (e) {
    console.error(e);
    container.innerHTML = '<div class="empty-state" style="color:var(--signal-red)">Failed to load conflict data.</div>';
  }
}

function renderConflicts(container, conflicts, schedule, priorities) {
  if (conflicts.length === 0) {
    container.innerHTML = `
      <div class="panel">
        <div class="empty-state">No conflicts detected for this corridor. All block requests can be scheduled without contention.</div>
      </div>
    `;
    return;
  }

  const scoreMap = {};
  for (const p of priorities) { scoreMap[p.request_id] = p; }
  const schedMap = {};
  for (const s of schedule.scheduled) { schedMap[s.request_id] = s; }

  container.innerHTML = conflicts.map((conflict, idx) => {
    // Build before chips
    const beforeChips = conflict.requests.map(r => {
      const scored = scoreMap[r.request_id] || {};
      return `
        <div class="request-chip">
          <span class="chip-label">${r.department} \u00b7 ${scored.asset_type || r.task_id}</span>
          <span class="request-id">${r.request_id}</span>
          ${severityBadge(r.severity)}
        </div>
      `;
    }).join('');

    // Build after chips
    const afterChips = conflict.requests.map(r => {
      const sched = schedMap[r.request_id];
      const isWinner = sched && !sched.was_bumped && sched.day === conflict.day;
      const wasBumped = sched && sched.was_bumped;
      const chipClass = isWinner ? 'winner' : (wasBumped ? 'bumped' : '');
      const timeLabel = sched
        ? `${sched.start_time}\u2013${sched.end_time} \u00b7 ${isWinner ? 'kept slot' : 'bumped to ' + sched.day}`
        : 'unscheduled';
      const scored = scoreMap[r.request_id] || {};

      return `
        <div class="request-chip ${chipClass}">
          <span class="chip-label">${r.department} \u00b7 ${scored.asset_type || r.task_id}</span>
          <span class="request-id">${timeLabel}</span>
        </div>
      `;
    }).join('');

    // Available windows
    const windowsHtml = (conflict.available_gaps || [])
      .filter(g => g.duration_hours >= 0.5)
      .map(g => `<span class="window-tag">${g.start}\u2013${g.end} (${g.duration_hours}h)</span>`)
      .join('');

    // Resolution log
    const resolutions = (schedule.conflict_log || []).filter(
      cl => cl.corridor_id === conflict.corridor_id &&
            (cl.day === conflict.day || cl.original_day === conflict.day)
    );

    const resolutionHtml = resolutions.length > 0 ? `
      <div class="resolution-log">
        <h3>Resolution log</h3>
        ${resolutions.map(r => `
          <div class="resolution-entry">
            <div class="resolution-entry__icon">${r.type === 'won' ? '\u25b6' : '\u2192'}</div>
            <div>${r.reason}</div>
          </div>
        `).join('')}
      </div>
    ` : '';

    const typeLabel = conflict.conflict_type.replace(/_/g, ' ');

    return `
      <div class="panel conflict-group">
        <div class="conflict-group__header">
          <div class="conflict-group__title">${conflict.corridor_id} \u2014 ${conflict.day}</div>
          <span class="badge ${typeLabel.includes('overflow') ? 'critical' : 'major'}">${typeLabel}</span>
          <span class="conflict-group__meta">${conflict.requests.length} requests \u00b7 ${conflict.total_available_hours}h available \u00b7 ${conflict.total_requested_hours}h requested</span>
        </div>

        <div class="conflict-group__desc">${conflict.description}</div>

        ${windowsHtml ? `
          <div style="margin-bottom:14px">
            <div class="fs-11 fw-600 text-muted mb-16" style="margin-bottom:6px">Available maintenance windows</div>
            <div class="windows-row">${windowsHtml}</div>
          </div>
        ` : ''}

        <div class="conflict-compare conflict-resolved" id="conflict-${idx}">
          <div class="compare-col">
            <h3>Before \u2014 ${conflict.requests.length} requests, same window</h3>
            ${beforeChips}
          </div>
          <div class="compare-col">
            <h3>After \u2014 auto-resolved</h3>
            ${afterChips}
          </div>
        </div>

        <div style="margin-top:12px">
          <button class="btn" onclick="animateResolve('conflict-${idx}')">Resolve conflict</button>
        </div>

        ${resolutionHtml}
      </div>
    `;
  }).join('');

  // Auto-animate first conflict after a short delay
  setTimeout(() => {
    const first = document.getElementById('conflict-0');
    if (first) first.classList.add('animate');
  }, 300);
}

function animateResolve(id) {
  const el = document.getElementById(id);
  if (!el) return;
  // Reset then re-trigger
  el.classList.remove('animate');
  // Force reflow
  void el.offsetWidth;
  el.classList.add('animate');
}
