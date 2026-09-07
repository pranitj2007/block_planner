"""
Glass-Box Block Scheduler — Flask API server.

Serves the scheduling engine via REST endpoints and
also serves the static frontend files.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

# ── Engine imports ──
from engine.scoring import compute_scores
from engine.conflict import detect_conflicts, get_available_windows
from engine.scheduler import run_scheduler
from engine.impact import compute_impact

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# ─────────────────────────── API ROUTES ────────────────────────────


@app.route('/api/priority')
def api_priority():
    """Return all block requests with priority scores and component breakdowns."""
    corridor = request.args.get('corridor')
    scores = compute_scores()
    if corridor:
        scores = [s for s in scores if s['corridor_id'] == corridor]
    return jsonify({
        'status': 'ok',
        'count': len(scores),
        'data': scores,
    })


@app.route('/api/conflicts')
def api_conflicts():
    """Return conflict groups for a corridor (or all corridors)."""
    corridor = request.args.get('corridor')
    conflicts = detect_conflicts(corridor)
    return jsonify({
        'status': 'ok',
        'count': len(conflicts),
        'data': conflicts,
    })


@app.route('/api/schedule')
def api_schedule():
    """Return the resolved schedule for Gantt rendering."""
    corridor = request.args.get('corridor')
    horizon = request.args.get('horizon', 'weekly')
    result = run_scheduler(corridor, horizon)
    return jsonify({
        'status': 'ok',
        **result,
    })


@app.route('/api/impact')
def api_impact():
    """Return baseline vs optimized comparison metrics."""
    corridor = request.args.get('corridor')
    impact = compute_impact(corridor)
    return jsonify({
        'status': 'ok',
        **impact,
    })


@app.route('/api/windows')
def api_windows():
    """Return available maintenance windows for a corridor+day."""
    corridor = request.args.get('corridor')
    day = request.args.get('day')
    windows = get_available_windows(corridor, day)
    # Convert tuple keys to strings for JSON
    result = {}
    for (cid, d), gaps in windows.items():
        key = f"{cid}_{d}"
        result[key] = gaps
    return jsonify({
        'status': 'ok',
        'data': result,
    })


@app.route('/api/corridors')
def api_corridors():
    """Return list of all corridors for dropdown menus."""
    import pandas as pd
    assets = pd.read_csv(os.path.join(os.path.dirname(__file__), 'data', 'asset_master.csv'))
    corridors = assets[['corridor_id', 'corridor_name']].drop_duplicates().sort_values('corridor_id')
    return jsonify({
        'status': 'ok',
        'data': corridors.to_dict('records'),
    })


@app.route('/api/dashboard')
def api_dashboard():
    """Return KPI summary data for the dashboard."""
    scores = compute_scores()
    schedule = run_scheduler()
    conflicts = detect_conflicts()

    total_requests = len(scores)
    conflicts_resolved = schedule['summary']['conflicts_resolved']
    avg_overdue = round(
        sum(s['overdue_days'] for s in scores) / len(scores), 1
    ) if scores else 0
    corridors_covered = len(set(s['corridor_id'] for s in scores))
    departments = list(set(s['department'] for s in scores))

    # Department breakdown
    dept_counts = {}
    for s in scores:
        dept_counts[s['department']] = dept_counts.get(s['department'], 0) + 1

    severity_counts = {}
    for s in scores:
        severity_counts[s['severity']] = severity_counts.get(s['severity'], 0) + 1

    return jsonify({
        'status': 'ok',
        'kpis': {
            'total_requests': total_requests,
            'conflicts_resolved': conflicts_resolved,
            'avg_overdue_days': avg_overdue,
            'corridors_covered': corridors_covered,
            'scheduled': schedule['summary']['scheduled_count'],
            'unscheduled': schedule['summary']['unscheduled_count'],
        },
        'department_breakdown': dept_counts,
        'severity_breakdown': severity_counts,
        'conflict_summary': {
            'total_conflict_groups': len(conflicts),
            'corridors_with_conflicts': list(set(c['corridor_id'] for c in conflicts)),
        },
    })


# ─────────────── STATIC FILE SERVING (Frontend) ───────────────


@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# ─────────────────────────── MAIN ──────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"\n  Glass-Box Block Scheduler")
    print(f"  -------------------------")
    print(f"  API:       http://localhost:{port}/api/")
    print(f"  Frontend:  http://localhost:{port}/")
    print(f"  Demo:      http://localhost:{port}/index.html\n")
    app.run(debug=True, host='127.0.0.1', port=port)
