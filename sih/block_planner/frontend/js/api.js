/**
 * api.js — Shared API client and utilities for all pages.
 */

const API_BASE = (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin !== 'null' && !window.location.origin.startsWith('file://'))
  ? `${window.location.origin}/api`
  : 'http://localhost:5001/api';

const api = {
  async get(endpoint, params = {}) {
    const url = new URL(`${API_BASE}/${endpoint}`);
    for (const [k, v] of Object.entries(params)) {
      if (v !== null && v !== undefined && v !== '') {
        url.searchParams.set(k, v);
      }
    }
    const res = await fetch(url);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },

  dashboard(params)    { return this.get('dashboard', params); },
  priority(params)     { return this.get('priority', params); },
  conflicts(params)    { return this.get('conflicts', params); },
  schedule(params)     { return this.get('schedule', params); },
  impact(params)       { return this.get('impact', params); },
  corridors()          { return this.get('corridors'); },
  windows(params)      { return this.get('windows', params); },
};

/* ── Badge helpers ── */

function severityBadge(severity) {
  return `<span class="badge ${severity.toLowerCase()}">${severity.toLowerCase()}</span>`;
}

function departmentBadge(dept) {
  return `<span class="badge ${dept.toLowerCase()}">${dept}</span>`;
}

function statusBadge(status) {
  return `<span class="badge ${status.toLowerCase()}">${status.toLowerCase()}</span>`;
}

/* ── Loading state ── */

function showLoading(container) {
  container.innerHTML = `
    <div class="loading-state">
      <div class="loading-spinner"></div>
      <span>Loading data\u2026</span>
    </div>
  `;
}

/* ── Corridor dropdown ── */

async function loadCorridorDropdown(selectId, defaultValue = 'C4') {
  try {
    const data = await api.corridors();
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = '<option value="">All corridors</option>';
    for (const c of data.data) {
      const selected = c.corridor_id === defaultValue ? ' selected' : '';
      select.innerHTML += `<option value="${c.corridor_id}"${selected}>${c.corridor_id} \u2014 ${c.corridor_name}</option>`;
    }
  } catch (e) {
    console.error('Failed to load corridors:', e);
  }
}

/* ── Dot meter helper ── */

function dotMeter(filled, total, colorClass) {
  const cls = colorClass || 'filled';
  let html = '<div class="dot-meter">';
  for (let i = 0; i < total; i++) {
    html += `<div class="dot${i < filled ? ' ' + cls : ''}"></div>`;
  }
  html += '</div>';
  return html;
}

/* ── Build navigation ── */

function buildNav(activePage) {
  const pages = [
    { href: 'index.html',         label: 'Dashboard' },
    { href: 'explainability.html', label: 'Explainability' },
    { href: 'conflicts.html',     label: 'Conflicts' },
    { href: 'gantt.html',         label: 'Gantt plan' },
    { href: 'impact.html',        label: 'Impact' },
  ];

  const nav = document.querySelector('.console-nav .nav-links');
  if (!nav) return;

  nav.innerHTML = pages.map(p =>
    `<a href="${p.href}" class="${p.href === activePage ? 'active' : ''}">${p.label}</a>`
  ).join('');
}

/* ── Department colour map ── */

const DEPT_COLORS = {
  'Engineering': '#60a5fa',
  'Signal':      '#E8A33D',
  'Traction':    '#4CAF6D',
};
