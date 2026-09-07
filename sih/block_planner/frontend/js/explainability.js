/**
 * explainability.js — Priority breakdown table with expandable score detail.
 */
document.addEventListener('DOMContentLoaded', async () => {
  buildNav('explainability.html');
  await loadCorridorDropdown('corridor-select', 'C4');

  const select = document.getElementById('corridor-select');
  select.addEventListener('change', () => loadTable(select.value));
  loadTable('C4');
});

async function loadTable(corridor) {
  const tbody = document.getElementById('priority-tbody');
  showLoading(tbody.parentElement.parentElement);

  try {
    const data = await api.priority({ corridor: corridor || undefined });
    renderTable(data.data);
  } catch (e) {
    console.error(e);
    tbody.innerHTML = '<tr><td colspan="9" style="color:var(--signal-red)">Failed to load data</td></tr>';
  }
}

function renderTable(requests) {
  const tbody = document.getElementById('priority-tbody');
  tbody.innerHTML = '';

  requests.forEach((r, i) => {
    // Main row
    const tr = document.createElement('tr');
    tr.className = 'expand-row';
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td><strong class="mono fs-12">${r.request_id}</strong></td>
      <td class="mono fs-11 text-muted">${r.task_id}</td>
      <td class="mono fs-12">${r.corridor_id}</td>
      <td>${departmentBadge(r.department)}</td>
      <td>${severityBadge(r.severity)}</td>
      <td class="mono">${r.overdue_days}d</td>
      <td>${r.criticality_level}</td>
      <td><span class="score-display">${r.priority_score}</span></td>
    `;

    // Detail row
    const detailTr = document.createElement('tr');
    detailTr.className = 'detail-row';
    const detailTd = document.createElement('td');
    detailTd.colSpan = 9;

    // Score breakdown bar
    const maxScore = 30;
    const sevPct = (r.severity_score / maxScore) * 100;
    const ovdPct = (r.overdue_score / maxScore) * 100;
    const critPct = (r.criticality_score / maxScore) * 100;

    detailTd.innerHTML = `
      <div class="breakdown-detail">
        <div class="breakdown-detail__item">
          <span class="breakdown-detail__label">Severity (${r.severity} \u2192 weight ${r.severity_weight})</span>
          <span class="breakdown-detail__value">${r.severity_weight} \u00d7 3 = ${r.severity_score}</span>
        </div>
        <div class="breakdown-detail__item">
          <span class="breakdown-detail__label">Overdue days</span>
          <span class="breakdown-detail__value">${r.overdue_days} \u00d7 0.5 = ${r.overdue_score}</span>
        </div>
        <div class="breakdown-detail__item">
          <span class="breakdown-detail__label">Asset criticality (${r.criticality_level} \u2192 weight ${r.criticality_weight})</span>
          <span class="breakdown-detail__value">${r.criticality_weight} \u00d7 2 = ${r.criticality_score}</span>
        </div>
        <div class="score-breakdown-bar" style="max-width:300px" title="severity | overdue | criticality">
          <div class="seg-severity" style="width:${sevPct}%"></div>
          <div class="seg-overdue" style="width:${ovdPct}%"></div>
          <div class="seg-crit" style="width:${critPct}%"></div>
        </div>
        <div class="formula-display">${r.formula}</div>
        <div class="mt-8 fs-11 text-muted">
          Asset: ${r.asset_type} (${r.asset_id}) \u00b7 Duration: ${r.requested_duration_hours}h \u00b7 Preferred day: ${r.preferred_day}
        </div>
      </div>
    `;

    detailTr.appendChild(detailTd);

    // Click to expand
    tr.addEventListener('click', () => {
      const isOpen = detailTr.classList.contains('open');
      // Close all
      document.querySelectorAll('.detail-row.open').forEach(el => el.classList.remove('open'));
      document.querySelectorAll('.expand-row.expanded').forEach(el => el.classList.remove('expanded'));

      if (!isOpen) {
        detailTr.classList.add('open');
        tr.classList.add('expanded');
      }
    });

    tbody.appendChild(tr);
    tbody.appendChild(detailTr);
  });
}
