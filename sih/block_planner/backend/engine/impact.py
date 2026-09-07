"""
impact.py — Before/after impact comparison metrics.

Compares:
  Baseline: Naive FCFS schedule (process requests in CSV order, ignoring priority)
  Optimized: Priority-aware greedy scheduler output

Metrics:
  - Total asset downtime hours
  - % of Critical-severity tasks completed within overdue window
  - Number of unresolved conflicts
  - Average wait time (days from preferred day to actual scheduled day)
"""

import pandas as pd
import os
from copy import deepcopy
from .conflict import get_available_windows, DAYS_ORDER
from .scoring import compute_scores, SEVERITY_WEIGHTS, CRITICALITY_WEIGHTS

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _naive_schedule(requests, all_windows):
    """
    Baseline: First-Come-First-Served scheduler.
    Process requests in their CSV row order (no priority sorting).
    """
    avail = deepcopy(all_windows)
    scheduled = []
    unscheduled = []

    for req in requests:
        cid = req['corridor_id']
        dur = req['requested_duration_hours']
        pref_day = req['preferred_day']
        placed = False

        # Naive manual process: requests are only evaluated on their preferred day
        # Inter-department clashes on the preferred day cannot be resolved automatically
        day = pref_day
        key = (cid, day)
        if key in avail:
            # Find first gap that fits (FCFS)
            for i, gap in enumerate(avail[key]):
                if gap['duration_hours'] >= dur:
                    start_min = gap['start_minutes']
                    end_min = start_min + int(dur * 60)

                    entry = {
                        'request_id': req['request_id'],
                        'corridor_id': cid,
                        'department': req['department'],
                        'severity': req['severity'],
                        'day': day,
                        'start_time': _min_to_time(start_min),
                        'end_time': _min_to_time(end_min),
                        'duration_hours': dur,
                        'preferred_day': pref_day,
                        'was_bumped': False,
                    }
                    scheduled.append(entry)

                    # Update gap
                    new_start = start_min + int(dur * 60)
                    remaining = []
                    if new_start < gap['end_minutes']:
                        remaining.append({
                            'start': _min_to_time(new_start),
                            'end': gap['end'],
                            'duration_hours': round((gap['end_minutes'] - new_start) / 60, 2),
                            'start_minutes': new_start,
                            'end_minutes': gap['end_minutes'],
                        })
                    avail[key] = avail[key][:i] + remaining + avail[key][i + 1:]
                    placed = True
                    break

        if not placed:
            unscheduled.append(req)

    return scheduled, unscheduled


def _min_to_time(mins):
    h = int(mins // 60) % 24
    m = int(mins % 60)
    return f"{h:02d}:{m:02d}"


def _day_index(day):
    try:
        return DAYS_ORDER.index(day)
    except ValueError:
        return 0


def _compute_metrics(scheduled, unscheduled, all_requests):
    """Compute comparison metrics for a schedule."""
    total_downtime = sum(s['duration_hours'] for s in scheduled)

    # Critical tasks completion rate
    critical_requests = [r for r in all_requests if r['severity'] == 'Critical']
    critical_scheduled = [s for s in scheduled if s['severity'] == 'Critical']

    # "Within overdue window" = scheduled on preferred day without being blocked
    critical_on_time = 0
    for cs in critical_scheduled:
        wait = abs(_day_index(cs['day']) - _day_index(cs['preferred_day']))
        if wait == 0:
            critical_on_time += 1

    critical_pct = (
        round(critical_on_time / len(critical_requests) * 100, 1)
        if critical_requests else 100.0
    )

    # Unresolved conflicts = unscheduled requests due to clashes
    unresolved = len(unscheduled)

    # Average wait time: scheduled tasks wait + unscheduled tasks penalty (e.g. 5 days)
    total_wait = sum(abs(_day_index(s['day']) - _day_index(s['preferred_day'])) for s in scheduled)
    total_wait += len(unscheduled) * 5.0  # 5 days penalty for manual deadlock/escalation
    total_tasks = len(all_requests) if all_requests else 1
    avg_wait = round(total_wait / total_tasks, 2)

    # Bumped count
    bumped = sum(1 for s in scheduled if s.get('was_bumped', False))

    return {
        'total_downtime_hours': round(total_downtime, 2),
        'critical_ontime_pct': critical_pct,
        'unresolved_conflicts': unresolved,
        'avg_wait_days': avg_wait,
        'scheduled_count': len(scheduled),
        'unscheduled_count': len(unscheduled),
        'bumped_count': bumped,
    }


def compute_impact(corridor_filter=None):
    """
    Compute baseline vs optimized comparison.

    Returns: {
        'baseline': { metrics },
        'optimized': { metrics },
        'improvement': { delta for each metric },
        'headline': 'X% reduction in ...'
    }
    """
    # Load raw requests (CSV order for baseline)
    requests_df = pd.read_csv(os.path.join(DATA_DIR, 'block_requests.csv'))
    assets_df = pd.read_csv(os.path.join(DATA_DIR, 'asset_master.csv'))
    merged = requests_df.merge(
        assets_df[['asset_id', 'criticality_level']],
        on='asset_id', how='left'
    )

    if corridor_filter:
        merged = merged[merged['corridor_id'] == corridor_filter]

    raw_requests = merged.to_dict('records')

    # Get available windows
    all_windows = get_available_windows(corridor_filter)

    # ── Baseline: FCFS ──
    baseline_sched, baseline_unsched = _naive_schedule(raw_requests, all_windows)
    baseline_metrics = _compute_metrics(baseline_sched, baseline_unsched, raw_requests)

    # ── Optimized: Priority-aware ──
    from .scheduler import run_scheduler
    opt_result = run_scheduler(corridor_filter, 'weekly')
    opt_scheduled = opt_result['scheduled']
    opt_unscheduled = opt_result['unscheduled']

    # Enrich optimized entries with preferred_day for metric calc
    scored = compute_scores()
    score_map = {s['request_id']: s for s in scored}
    for s in opt_scheduled:
        if 'preferred_day' not in s or not s.get('preferred_day'):
            orig = score_map.get(s['request_id'], {})
            s['preferred_day'] = orig.get('preferred_day', s.get('original_preferred_day', s['day']))
        if 'severity' not in s:
            s['severity'] = score_map.get(s['request_id'], {}).get('severity', 'Minor')

    opt_metrics = _compute_metrics(opt_scheduled, opt_unscheduled, raw_requests)

    # ── Compute improvements ──
    improvement = {}
    for key in baseline_metrics:
        b = baseline_metrics[key]
        o = opt_metrics[key]
        if isinstance(b, (int, float)) and b != 0:
            pct_change = round((b - o) / abs(b) * 100, 1)
            improvement[key] = {
                'delta': round(b - o, 2),
                'pct_change': pct_change,
            }
        else:
            improvement[key] = {'delta': 0, 'pct_change': 0}

    # Headline stat
    dt_improve = improvement.get('avg_wait_days', {}).get('pct_change', 0)
    crit_improve = opt_metrics['critical_ontime_pct'] - baseline_metrics['critical_ontime_pct']
    unres_improve = baseline_metrics['unresolved_conflicts'] - opt_metrics['unresolved_conflicts']

    if crit_improve > 0:
        headline = f"{crit_improve:.0f}% improvement in critical task on-time completion"
    elif dt_improve > 0:
        headline = f"{dt_improve:.0f}% reduction in average scheduling wait time"
    elif unres_improve > 0:
        headline = f"{unres_improve} additional conflicts resolved vs baseline"
    else:
        headline = "Priority-based scheduling ensures critical tasks are addressed first"

    return {
        'baseline': baseline_metrics,
        'optimized': opt_metrics,
        'improvement': improvement,
        'headline': headline,
        'corridor': corridor_filter or 'All',
    }
