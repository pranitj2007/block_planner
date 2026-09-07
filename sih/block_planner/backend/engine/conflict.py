"""
conflict.py — Detect scheduling conflicts between block requests.

For a given corridor+day, this module:
1. Derives available maintenance windows by finding gaps in the train timetable.
2. Identifies block requests that compete for the same limited windows.
3. Groups conflicting requests and explains the nature of each conflict.
"""

import pandas as pd
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

DAYS_ORDER = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _time_to_minutes(t_str):
    """Convert 'HH:MM' to minutes since midnight."""
    h, m = map(int, t_str.strip().split(':'))
    return h * 60 + m


def _minutes_to_time(mins):
    """Convert minutes since midnight to 'HH:MM'."""
    h = int(mins // 60) % 24
    m = int(mins % 60)
    return f"{h:02d}:{m:02d}"


def get_available_windows(corridor_id=None, day=None):
    """
    Compute available maintenance windows for each corridor+day combination.

    A window is a gap between consecutive train movements (or between
    midnight and the first train / last train and midnight).

    Returns: dict keyed by (corridor_id, day) → list of
             {'start': 'HH:MM', 'end': 'HH:MM', 'duration_hours': float}
    """
    timetable = pd.read_csv(os.path.join(DATA_DIR, 'train_timetable.csv'))

    if corridor_id:
        timetable = timetable[timetable['corridor_id'] == corridor_id]
    if day:
        timetable = timetable[timetable['day'] == day]

    windows = {}
    for (cid, d), group in timetable.groupby(['corridor_id', 'day']):
        # Collect all occupied intervals
        occupied = []
        for _, row in group.iterrows():
            dep = _time_to_minutes(row['departure_time'])
            arr = _time_to_minutes(row['arrival_time'])
            occupied.append((dep, arr))
        occupied.sort()

        # Find gaps
        gaps = []
        prev_end = 0  # midnight
        for start, end in occupied:
            if start > prev_end:
                dur = (start - prev_end) / 60
                gaps.append({
                    'start': _minutes_to_time(prev_end),
                    'end': _minutes_to_time(start),
                    'duration_hours': round(dur, 2),
                    'start_minutes': prev_end,
                    'end_minutes': start,
                })
            prev_end = max(prev_end, end)
        # Gap after last train until midnight
        if prev_end < 1440:
            dur = (1440 - prev_end) / 60
            gaps.append({
                'start': _minutes_to_time(prev_end),
                'end': '24:00',
                'duration_hours': round(dur, 2),
                'start_minutes': prev_end,
                'end_minutes': 1440,
            })

        windows[(cid, d)] = gaps

    return windows


def detect_conflicts(corridor_id=None):
    """
    Detect conflicts: groups of block requests competing for the same
    corridor+day where total requested time exceeds available window time,
    or multiple requests need a window larger than any single gap.

    Returns a list of conflict groups:
    [
      {
        'corridor_id': 'C4',
        'day': 'Mon',
        'total_requested_hours': 9.5,
        'total_available_hours': 12.5,
        'largest_gap_hours': 3.0,
        'requests': [...],
        'conflict_type': 'gap_contention' | 'capacity_overflow',
        'description': '...'
      }
    ]
    """
    requests = pd.read_csv(os.path.join(DATA_DIR, 'block_requests.csv'))
    if corridor_id:
        requests = requests[requests['corridor_id'] == corridor_id]

    windows = get_available_windows(corridor_id)
    conflicts = []

    for (cid, day), day_requests in requests.groupby(['corridor_id', 'preferred_day']):
        if len(day_requests) < 2:
            continue  # Need at least 2 requests for a conflict

        gaps = windows.get((cid, day), [])
        total_available = sum(g['duration_hours'] for g in gaps)
        largest_gap = max((g['duration_hours'] for g in gaps), default=0)
        total_requested = day_requests['requested_duration_hours'].sum()

        req_list = []
        for _, r in day_requests.iterrows():
            req_list.append({
                'request_id': r['request_id'],
                'task_id': r['task_id'],
                'department': r['department'],
                'severity': r['severity'],
                'overdue_days': int(r['overdue_days']),
                'requested_duration_hours': float(r['requested_duration_hours']),
            })

        # Determine conflict type
        oversized = [r for r in req_list
                     if r['requested_duration_hours'] > largest_gap]
        needs_large = [r for r in req_list
                       if r['requested_duration_hours'] > min(
                           (g['duration_hours'] for g in gaps if g['duration_hours'] >= 1),
                           default=0
                       )]

        # Count how many requests need a gap larger than the median gap
        large_gap_count = sum(
            1 for r in req_list
            if r['requested_duration_hours'] > 1.5
        )

        large_gaps_available = sum(
            1 for g in gaps if g['duration_hours'] >= 2
        )

        is_conflict = False
        conflict_type = ''
        description = ''

        if total_requested > total_available:
            is_conflict = True
            conflict_type = 'capacity_overflow'
            description = (
                f"Total requested time ({total_requested:.1f}h) exceeds "
                f"available window time ({total_available:.1f}h)."
            )
        elif large_gap_count > large_gaps_available:
            is_conflict = True
            conflict_type = 'gap_contention'
            description = (
                f"{large_gap_count} requests need gaps ≥ 2h, but only "
                f"{large_gaps_available} such gaps exist. Departments must "
                f"compete for limited large maintenance windows."
            )
        elif len(req_list) > len([g for g in gaps if g['duration_hours'] >= 1]):
            is_conflict = True
            conflict_type = 'slot_shortage'
            description = (
                f"{len(req_list)} requests compete for only "
                f"{len([g for g in gaps if g['duration_hours'] >= 1])} "
                f"usable gaps (≥ 1h)."
            )

        if is_conflict:
            conflicts.append({
                'corridor_id': cid,
                'day': day,
                'total_requested_hours': round(total_requested, 2),
                'total_available_hours': round(total_available, 2),
                'largest_gap_hours': round(largest_gap, 2),
                'available_gaps': gaps,
                'requests': req_list,
                'conflict_type': conflict_type,
                'description': description,
            })

    # Sort: C4 first, then by number of conflicting requests descending
    conflicts.sort(key=lambda c: (
        0 if c['corridor_id'] == 'C4' else 1,
        -len(c['requests'])
    ))
    return conflicts
