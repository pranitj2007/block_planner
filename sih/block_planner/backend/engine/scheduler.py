"""
scheduler.py — Greedy scheduling algorithm with conflict resolution logging.

Algorithm:
1. Score all block requests (via scoring.py).
2. For each corridor+day, compute available gaps from the timetable.
3. Sort requests by priority score, descending.
4. Greedily assign each request to the best-fit gap on its preferred day.
5. If no gap fits on the preferred day, try other days of the week.
6. Log every conflict resolution: which request won, which was bumped, why.
"""

import pandas as pd
import os
from copy import deepcopy
from .scoring import compute_scores
from .conflict import get_available_windows, DAYS_ORDER

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _try_fit(gaps, duration_hours):
    """
    Find the best-fit gap for a given duration.
    Returns (gap_index, start_time, end_time) or None.
    Best-fit = smallest gap that fits (minimize wasted time).
    """
    candidates = []
    for i, g in enumerate(gaps):
        if g['duration_hours'] >= duration_hours:
            candidates.append((i, g))

    if not candidates:
        return None

    # Best fit: smallest gap that accommodates the request
    candidates.sort(key=lambda x: x[1]['duration_hours'])
    idx, gap = candidates[0]
    start_min = gap['start_minutes']
    end_min = start_min + int(duration_hours * 60)
    return idx, gap['start'], _min_to_time(end_min)


def _min_to_time(mins):
    h = int(mins // 60) % 24
    m = int(mins % 60)
    return f"{h:02d}:{m:02d}"


def _split_gap(gap, duration_hours):
    """
    After assigning a request to a gap, split the remaining time
    into a new (smaller) gap. Returns list of 0-2 remaining gaps.
    """
    used_minutes = int(duration_hours * 60)
    new_start = gap['start_minutes'] + used_minutes
    remaining = []
    if new_start < gap['end_minutes']:
        rem_dur = (gap['end_minutes'] - new_start) / 60
        remaining.append({
            'start': _min_to_time(new_start),
            'end': gap['end'],
            'duration_hours': round(rem_dur, 2),
            'start_minutes': new_start,
            'end_minutes': gap['end_minutes'],
        })
    return remaining


def run_scheduler(corridor_filter=None, horizon='weekly'):
    """
    Run the greedy scheduler.

    Args:
        corridor_filter: Optional corridor_id to filter (None = all)
        horizon: 'weekly' (Mon-Sun) or 'monthly' (4 weeks)

    Returns:
        {
            'scheduled': [...],     # Successfully placed blocks
            'unscheduled': [...],   # Couldn't fit anywhere
            'conflict_log': [...],  # Resolution history
        }
    """
    scored = compute_scores()
    if corridor_filter:
        scored = [s for s in scored if s['corridor_id'] == corridor_filter]

    # Build mutable gap structure: {(corridor, day): [gaps]}
    all_windows = get_available_windows(corridor_filter)
    # Deep copy so we can mutate
    avail = {}
    for key, gaps in all_windows.items():
        avail[key] = deepcopy(gaps)

    # If monthly, replicate gaps for weeks 2-4
    weeks = 1 if horizon == 'weekly' else 4
    if weeks > 1:
        base_avail = deepcopy(avail)
        for week in range(2, weeks + 1):
            for (cid, day), gaps in base_avail.items():
                avail[(cid, f"W{week}_{day}")] = deepcopy(gaps)

    scheduled = []
    unscheduled = []
    conflict_log = []

    # Track which gaps are assigned to whom (for conflict logging)
    gap_assignments = {}  # (corridor, day, gap_start) → request_id

    for req in scored:
        cid = req['corridor_id']
        dur = req['requested_duration_hours']
        pref_day = req['preferred_day']
        placed = False

        # Try preferred day first, then other days
        day_order = [pref_day] + [d for d in DAYS_ORDER if d != pref_day]
        if weeks > 1:
            extended = []
            for d in day_order:
                extended.append(d)
                for w in range(2, weeks + 1):
                    extended.append(f"W{w}_{d}")
            day_order = extended

        for day in day_order:
            key = (cid, day)
            if key not in avail:
                continue

            result = _try_fit(avail[key], dur)
            if result is None:
                continue

            gap_idx, start, end = result
            gap = avail[key][gap_idx]

            # Check if this was a contested gap
            was_bumped = day != pref_day
            bump_reason = ''
            if was_bumped:
                bump_reason = (
                    f"No gap ≥ {dur}h available on {pref_day} for {cid}. "
                    f"Higher-priority requests occupied the large windows."
                )
                conflict_log.append({
                    'type': 'bumped',
                    'request_id': req['request_id'],
                    'department': req['department'],
                    'severity': req['severity'],
                    'priority_score': req['priority_score'],
                    'original_day': pref_day,
                    'assigned_day': day.split('_', 1)[1] if (day.startswith('W') and '_' in day) else day,
                    'corridor_id': cid,
                    'reason': bump_reason,
                })

            # Assign the block
            display_day = day
            week_num = 1
            if day.startswith('W') and '_' in day:
                parts = day.split('_', 1)
                week_num = int(parts[0][1:])
                display_day = parts[1]

            entry = {
                'request_id': req['request_id'],
                'task_id': req['task_id'],
                'corridor_id': cid,
                'corridor_name': req.get('corridor_name', ''),
                'department': req['department'],
                'severity': req['severity'],
                'priority_score': req['priority_score'],
                'day': display_day,
                'week': week_num,
                'start_time': start,
                'end_time': end,
                'duration_hours': dur,
                'status': 'Scheduled',
                'was_bumped': was_bumped,
                'original_preferred_day': pref_day,
            }
            scheduled.append(entry)

            # Split the gap
            remaining = _split_gap(gap, dur)
            avail[key] = (
                avail[key][:gap_idx] + remaining + avail[key][gap_idx + 1:]
            )

            placed = True
            break

        if not placed:
            unscheduled.append({
                'request_id': req['request_id'],
                'task_id': req['task_id'],
                'corridor_id': cid,
                'department': req['department'],
                'severity': req['severity'],
                'priority_score': req['priority_score'],
                'requested_duration_hours': dur,
                'preferred_day': pref_day,
                'status': 'Unscheduled',
                'reason': f"No available gap of {dur}h found in any day for {cid}.",
            })

    # Also log "won" entries for highest-priority requests on contested days
    # Find contests: multiple requests wanted same corridor+day
    day_groups = {}
    for req in scored:
        key = (req['corridor_id'], req['preferred_day'])
        day_groups.setdefault(key, []).append(req)

    for (cid, day), reqs in day_groups.items():
        if len(reqs) < 2:
            continue
        winner = reqs[0]  # Highest score (already sorted)
        for loser in reqs[1:]:
            # Check if the loser was bumped
            bumped_entry = next(
                (s for s in scheduled
                 if s['request_id'] == loser['request_id'] and s['was_bumped']),
                None
            )
            if bumped_entry:
                conflict_log.append({
                    'type': 'won',
                    'winner_id': winner['request_id'],
                    'winner_dept': winner['department'],
                    'winner_score': winner['priority_score'],
                    'loser_id': loser['request_id'],
                    'loser_dept': loser['department'],
                    'loser_score': loser['priority_score'],
                    'corridor_id': cid,
                    'day': day,
                    'reason': (
                        f"{winner['request_id']} ({winner['department']}, "
                        f"score {winner['priority_score']}) won over "
                        f"{loser['request_id']} ({loser['department']}, "
                        f"score {loser['priority_score']}) because of higher "
                        f"priority score."
                    ),
                })

    return {
        'scheduled': scheduled,
        'unscheduled': unscheduled,
        'conflict_log': conflict_log,
        'summary': {
            'total_requests': len(scored),
            'scheduled_count': len(scheduled),
            'unscheduled_count': len(unscheduled),
            'conflicts_resolved': len([c for c in conflict_log if c['type'] == 'bumped']),
            'corridors': list(set(r['corridor_id'] for r in scored)),
        }
    }
