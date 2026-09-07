"""
scoring.py — Explainable priority scoring for block requests.

Score formula:
  score = (severity_weight × 3) + (overdue_days × 0.5) + (criticality_weight × 2)

Returns both the final score AND the individual component values so the
frontend can render a breakdown of WHY each request scored the way it did.
"""

import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

SEVERITY_WEIGHTS = {'Critical': 3, 'Major': 2, 'Minor': 1}
CRITICALITY_WEIGHTS = {'High': 3, 'Medium': 2, 'Low': 1}

# Multipliers for each component in the formula
SEVERITY_MULTIPLIER = 3
OVERDUE_MULTIPLIER = 0.5
CRITICALITY_MULTIPLIER = 2


def load_data():
    """Load block requests and asset master, merge on asset_id."""
    requests = pd.read_csv(os.path.join(DATA_DIR, 'block_requests.csv'))
    assets = pd.read_csv(os.path.join(DATA_DIR, 'asset_master.csv'))
    merged = requests.merge(
        assets[['asset_id', 'criticality_level', 'asset_type', 'corridor_name']],
        on='asset_id',
        how='left'
    )
    return merged


def compute_scores(df=None):
    """
    Compute explainable priority scores for all block requests.

    Returns a list of dicts, each containing:
      - All original request fields
      - severity_weight, overdue_component, criticality_weight
      - severity_score, overdue_score, criticality_score (the weighted components)
      - priority_score (the final sum)
    """
    if df is None:
        df = load_data()

    results = []
    for _, row in df.iterrows():
        sev_w = SEVERITY_WEIGHTS.get(row['severity'], 1)
        crit_w = CRITICALITY_WEIGHTS.get(row.get('criticality_level', 'Low'), 1)
        overdue = float(row.get('overdue_days', 0))

        severity_score = sev_w * SEVERITY_MULTIPLIER
        overdue_score = overdue * OVERDUE_MULTIPLIER
        criticality_score = crit_w * CRITICALITY_MULTIPLIER
        total = severity_score + overdue_score + criticality_score

        results.append({
            'request_id': row['request_id'],
            'task_id': row['task_id'],
            'asset_id': row['asset_id'],
            'corridor_id': row['corridor_id'],
            'corridor_name': row.get('corridor_name', ''),
            'department': row['department'],
            'severity': row['severity'],
            'overdue_days': int(overdue),
            'requested_duration_hours': float(row['requested_duration_hours']),
            'preferred_day': row['preferred_day'],
            'asset_type': row.get('asset_type', ''),
            'criticality_level': row.get('criticality_level', 'Low'),
            'status': row.get('status', 'Pending'),
            # ── Explainability breakdown ──
            'severity_weight': sev_w,
            'criticality_weight': crit_w,
            'severity_score': severity_score,
            'overdue_score': overdue_score,
            'criticality_score': criticality_score,
            'priority_score': round(total, 2),
            # ── Formula description (for tooltip / detail panel) ──
            'formula': (
                f"({sev_w}×{SEVERITY_MULTIPLIER}) + "
                f"({overdue}×{OVERDUE_MULTIPLIER}) + "
                f"({crit_w}×{CRITICALITY_MULTIPLIER}) = {round(total, 2)}"
            ),
        })

    results.sort(key=lambda r: r['priority_score'], reverse=True)
    return results
