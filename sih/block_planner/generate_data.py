"""
Generate all 6 CSV data files for the Glass-Box Block Scheduler demo.
Ensures C4 (Howrah-Delhi Corridor) has the highest conflict density,
with a 3-way department collision on Monday.
"""
import csv
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), 'backend', 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def write_csv(filename, headers, rows):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"  ✓ {filename} ({len(rows)} rows)")


def generate_asset_master():
    headers = ['asset_id', 'corridor_id', 'corridor_name', 'department',
               'asset_type', 'install_year', 'criticality_level']
    rows = [
        # C1 — Delhi-Agra Corridor
        ['A001', 'C1', 'Delhi-Agra Corridor', 'Engineering', 'Track Section', 2015, 'High'],
        ['A002', 'C1', 'Delhi-Agra Corridor', 'Signal', 'Signal Box', 2018, 'Medium'],
        ['A013', 'C1', 'Delhi-Agra Corridor', 'Traction', 'OHE Section', 2013, 'High'],
        ['A019', 'C1', 'Delhi-Agra Corridor', 'Engineering', 'Level Crossing', 2014, 'Medium'],
        # C2 — Mumbai-Pune Corridor
        ['A003', 'C2', 'Mumbai-Pune Corridor', 'Engineering', 'Bridge', 2010, 'High'],
        ['A004', 'C2', 'Mumbai-Pune Corridor', 'Traction', 'OHE Section', 2016, 'Medium'],
        ['A015', 'C2', 'Mumbai-Pune Corridor', 'Signal', 'Signal Box', 2017, 'Low'],
        ['A018', 'C2', 'Mumbai-Pune Corridor', 'Engineering', 'Tunnel', 2005, 'High'],
        # C3 — Chennai-Bangalore Corridor
        ['A005', 'C3', 'Chennai-Bangalore Corridor', 'Signal', 'Relay Room', 2019, 'Low'],
        ['A006', 'C3', 'Chennai-Bangalore Corridor', 'Engineering', 'Track Section', 2012, 'High'],
        ['A014', 'C3', 'Chennai-Bangalore Corridor', 'Traction', 'Transformer', 2015, 'Medium'],
        ['A020', 'C3', 'Chennai-Bangalore Corridor', 'Engineering', 'Culvert', 2011, 'Low'],
        # C4 — Howrah-Delhi Corridor (demo corridor — high density)
        ['A007', 'C4', 'Howrah-Delhi Corridor', 'Engineering', 'Track Section', 2008, 'High'],
        ['A008', 'C4', 'Howrah-Delhi Corridor', 'Signal', 'Interlocking System', 2014, 'High'],
        ['A009', 'C4', 'Howrah-Delhi Corridor', 'Traction', 'OHE Section', 2011, 'High'],
        ['A010', 'C4', 'Howrah-Delhi Corridor', 'Engineering', 'Bridge', 2006, 'Medium'],
        ['A016', 'C4', 'Howrah-Delhi Corridor', 'Traction', 'Transformer', 2009, 'Medium'],
        # C5 — Secunderabad-Kazipet Corridor
        ['A011', 'C5', 'Secunderabad-Kazipet Corridor', 'Signal', 'Interlocking System', 2017, 'Medium'],
        ['A012', 'C5', 'Secunderabad-Kazipet Corridor', 'Traction', 'PSI Equipment', 2020, 'Low'],
        ['A017', 'C5', 'Secunderabad-Kazipet Corridor', 'Engineering', 'Track Section', 2016, 'High'],
    ]
    write_csv('asset_master.csv', headers, rows)


def generate_tms_maintenance():
    """Engineering department maintenance tasks."""
    headers = ['task_id', 'asset_id', 'corridor_id', 'department',
               'defect_description', 'severity', 'reported_date_offset_days',
               'overdue_days', 'estimated_repair_hours', 'min_block_duration_hours']
    rows = [
        ['TMS001', 'A007', 'C4', 'Engineering', 'Rail fracture detected at km 342', 'Critical', 5, 15, 2.5, 3.0],
        ['TMS002', 'A010', 'C4', 'Engineering', 'Bridge pier erosion — monsoon damage', 'Minor', 20, 3, 1.5, 1.5],
        ['TMS003', 'A001', 'C1', 'Engineering', 'Track geometry deterioration', 'Major', 12, 5, 2.0, 2.0],
        ['TMS004', 'A003', 'C2', 'Engineering', 'Bridge deck corrosion', 'Critical', 3, 20, 3.0, 3.0],
        ['TMS005', 'A006', 'C3', 'Engineering', 'Track buckling risk — summer heat', 'Major', 8, 10, 2.5, 2.5],
        ['TMS006', 'A018', 'C2', 'Engineering', 'Tunnel seepage and lining cracks', 'Major', 15, 7, 2.0, 2.0],
        ['TMS007', 'A017', 'C5', 'Engineering', 'Rail wear exceeding limits', 'Major', 10, 6, 1.5, 2.0],
        ['TMS008', 'A007', 'C4', 'Engineering', 'Weld joint inspection overdue', 'Major', 25, 11, 2.0, 2.0],
    ]
    write_csv('tms_maintenance.csv', headers, rows)


def generate_smms_maintenance():
    """Signal department maintenance tasks."""
    headers = ['task_id', 'asset_id', 'corridor_id', 'department',
               'defect_description', 'severity', 'reported_date_offset_days',
               'overdue_days', 'estimated_repair_hours', 'min_block_duration_hours']
    rows = [
        ['SMMS001', 'A008', 'C4', 'Signal', 'Interlocking relay failure', 'Major', 7, 8, 1.5, 2.5],
        ['SMMS002', 'A002', 'C1', 'Signal', 'Signal lamp degradation', 'Minor', 30, 2, 1.0, 1.5],
        ['SMMS003', 'A005', 'C3', 'Signal', 'Relay contact resistance high', 'Minor', 14, 1, 1.0, 1.5],
        ['SMMS004', 'A015', 'C2', 'Signal', 'Signal cable insulation breakdown', 'Critical', 2, 14, 2.0, 2.5],
        ['SMMS005', 'A011', 'C5', 'Signal', 'Point machine sluggish operation', 'Major', 9, 6, 1.5, 2.0],
        ['SMMS006', 'A008', 'C4', 'Signal', 'Track circuit intermittent failure', 'Critical', 4, 18, 2.0, 2.0],
    ]
    write_csv('smms_maintenance.csv', headers, rows)


def generate_tdms_maintenance():
    """Traction Distribution department maintenance tasks."""
    headers = ['task_id', 'asset_id', 'corridor_id', 'department',
               'defect_description', 'severity', 'reported_date_offset_days',
               'overdue_days', 'estimated_repair_hours', 'min_block_duration_hours']
    rows = [
        ['TDMS001', 'A009', 'C4', 'Traction', 'OHE wire sag exceeding limits', 'Critical', 6, 12, 2.0, 2.5],
        ['TDMS002', 'A004', 'C2', 'Traction', 'OHE mast foundation cracking', 'Major', 18, 7, 2.0, 2.0],
        ['TDMS003', 'A014', 'C3', 'Traction', 'Transformer oil level low', 'Major', 11, 9, 1.5, 2.0],
        ['TDMS004', 'A012', 'C5', 'Traction', 'PSI calibration drift', 'Minor', 22, 4, 1.0, 1.5],
        ['TDMS005', 'A013', 'C1', 'Traction', 'OHE insulator flashover marks', 'Critical', 3, 18, 2.0, 2.0],
        ['TDMS006', 'A016', 'C4', 'Traction', 'Transformer bushing degradation', 'Minor', 28, 5, 1.5, 1.5],
    ]
    write_csv('tdms_maintenance.csv', headers, rows)


def generate_train_timetable():
    """
    Train timetable for all corridors across the week.
    C4 Monday is intentionally busy to create a tight scheduling window.
    """
    headers = ['train_id', 'corridor_id', 'day', 'departure_time', 'arrival_time', 'train_type']
    rows = []
    tid = 1

    def add(cid, day, dep, arr, ttype):
        nonlocal tid
        rows.append([f'T{tid:03d}', cid, day, dep, arr, ttype])
        tid += 1

    # ── C4 Monday — busiest schedule (creates narrow maintenance windows) ──
    add('C4', 'Mon', '00:30', '01:30', 'Goods')
    add('C4', 'Mon', '04:30', '05:30', 'Goods')
    add('C4', 'Mon', '06:00', '07:00', 'Express')
    add('C4', 'Mon', '08:00', '09:00', 'Express')
    add('C4', 'Mon', '10:00', '11:00', 'Passenger')
    add('C4', 'Mon', '11:30', '12:30', 'Express')
    add('C4', 'Mon', '13:30', '14:30', 'Express')
    add('C4', 'Mon', '15:30', '16:30', 'Passenger')
    add('C4', 'Mon', '17:30', '18:30', 'Express')
    add('C4', 'Mon', '19:30', '20:30', 'Express')
    add('C4', 'Mon', '21:30', '22:30', 'Goods')
    # Gaps on Mon: 01:30-04:30(3h), 05:30-06:00(0.5h), 07:00-08:00(1h),
    #   09:00-10:00(1h), 11:00-11:30(0.5h), 12:30-13:30(1h), 14:30-15:30(1h),
    #   16:30-17:30(1h), 18:30-19:30(1h), 20:30-21:30(1h), 22:30-24:00(1.5h)
    # Biggest gap: 3h night window. Most gaps are 1h.
    # A 3h request ONLY fits in the night window. A 2.5h request ONLY fits there too.

    # ── C4 other days — lighter schedule ──
    for day in ['Tue', 'Wed', 'Thu', 'Fri']:
        add('C4', day, '06:00', '07:00', 'Express')
        add('C4', day, '09:30', '10:30', 'Passenger')
        add('C4', day, '13:00', '14:00', 'Express')
        add('C4', day, '17:00', '18:00', 'Express')
        add('C4', day, '21:00', '22:00', 'Goods')
    for day in ['Sat', 'Sun']:
        add('C4', day, '07:00', '08:00', 'Passenger')
        add('C4', day, '12:00', '13:00', 'Express')
        add('C4', day, '18:00', '19:00', 'Passenger')

    # ── C1 — moderate traffic ──
    for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
        add('C1', day, '05:30', '06:30', 'Passenger')
        add('C1', day, '08:00', '09:00', 'Express')
        add('C1', day, '11:00', '12:00', 'Express')
        add('C1', day, '14:30', '15:30', 'Passenger')
        add('C1', day, '18:00', '19:00', 'Express')
        add('C1', day, '22:00', '23:00', 'Goods')
    for day in ['Sat', 'Sun']:
        add('C1', day, '07:00', '08:00', 'Passenger')
        add('C1', day, '13:00', '14:00', 'Express')
        add('C1', day, '19:00', '20:00', 'Passenger')

    # ── C2 — moderate traffic ──
    for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
        add('C2', day, '06:00', '07:00', 'Express')
        add('C2', day, '09:00', '10:00', 'Passenger')
        add('C2', day, '12:00', '13:00', 'Express')
        add('C2', day, '15:00', '16:00', 'Express')
        add('C2', day, '18:30', '19:30', 'Passenger')
        add('C2', day, '21:30', '22:30', 'Goods')
    for day in ['Sat', 'Sun']:
        add('C2', day, '08:00', '09:00', 'Passenger')
        add('C2', day, '14:00', '15:00', 'Express')
        add('C2', day, '20:00', '21:00', 'Goods')

    # ── C3 — lighter traffic ──
    for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
        add('C3', day, '06:30', '07:30', 'Express')
        add('C3', day, '10:00', '11:00', 'Passenger')
        add('C3', day, '14:00', '15:00', 'Express')
        add('C3', day, '19:00', '20:00', 'Passenger')
    for day in ['Sat', 'Sun']:
        add('C3', day, '08:00', '09:00', 'Passenger')
        add('C3', day, '15:00', '16:00', 'Express')

    # ── C5 — lightest traffic ──
    for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
        add('C5', day, '07:00', '08:00', 'Passenger')
        add('C5', day, '12:00', '13:00', 'Express')
        add('C5', day, '17:00', '18:00', 'Passenger')
    for day in ['Sat', 'Sun']:
        add('C5', day, '09:00', '10:00', 'Passenger')
        add('C5', day, '16:00', '17:00', 'Express')

    write_csv('train_timetable.csv', headers, rows)


def generate_block_requests():
    """
    Block requests. C4 Monday has a 3-way department collision:
      BR001 (Engineering, Critical, 3h)
      BR002 (Signal, Major, 2.5h)
      BR003 (Traction, Critical, 2.5h)
    All three need the only large gap (01:30-04:30, 3h) — only one fits.
    """
    headers = ['request_id', 'task_id', 'asset_id', 'corridor_id', 'department',
               'requested_duration_hours', 'severity', 'overdue_days',
               'preferred_day', 'status']
    rows = [
        # ── C4 Monday — the 3-way collision ──
        ['BR001', 'TMS001', 'A007', 'C4', 'Engineering', 3.0, 'Critical', 15, 'Mon', 'Pending'],
        ['BR002', 'SMMS001', 'A008', 'C4', 'Signal', 2.5, 'Major', 8, 'Mon', 'Pending'],
        ['BR003', 'TDMS001', 'A009', 'C4', 'Traction', 2.5, 'Critical', 12, 'Mon', 'Pending'],
        ['BR004', 'TMS002', 'A010', 'C4', 'Engineering', 1.5, 'Minor', 3, 'Mon', 'Pending'],
        # ── C4 other days ──
        ['BR014', 'SMMS006', 'A008', 'C4', 'Signal', 2.0, 'Critical', 18, 'Tue', 'Pending'],
        ['BR017', 'TMS008', 'A007', 'C4', 'Engineering', 2.0, 'Major', 11, 'Wed', 'Pending'],
        ['BR018', 'TDMS006', 'A016', 'C4', 'Traction', 1.5, 'Minor', 5, 'Thu', 'Pending'],
        # ── C1 ──
        ['BR005', 'TMS003', 'A001', 'C1', 'Engineering', 2.0, 'Major', 5, 'Tue', 'Pending'],
        ['BR006', 'SMMS002', 'A002', 'C1', 'Signal', 1.5, 'Minor', 2, 'Tue', 'Pending'],
        ['BR013', 'TDMS005', 'A013', 'C1', 'Traction', 2.0, 'Critical', 18, 'Mon', 'Pending'],
        # ── C2 ──
        ['BR007', 'TMS004', 'A003', 'C2', 'Engineering', 3.0, 'Critical', 20, 'Wed', 'Pending'],
        ['BR008', 'TDMS002', 'A004', 'C2', 'Traction', 2.0, 'Major', 7, 'Wed', 'Pending'],
        ['BR016', 'SMMS004', 'A015', 'C2', 'Signal', 2.5, 'Critical', 14, 'Mon', 'Pending'],
        # ── C3 ──
        ['BR009', 'SMMS003', 'A005', 'C3', 'Signal', 1.5, 'Minor', 1, 'Thu', 'Pending'],
        ['BR010', 'TMS005', 'A006', 'C3', 'Engineering', 2.5, 'Major', 10, 'Thu', 'Pending'],
        ['BR015', 'TDMS003', 'A014', 'C3', 'Traction', 2.0, 'Major', 9, 'Mon', 'Pending'],
        # ── C5 ──
        ['BR011', 'SMMS005', 'A011', 'C5', 'Signal', 2.0, 'Major', 6, 'Fri', 'Pending'],
        ['BR012', 'TDMS004', 'A012', 'C5', 'Traction', 1.5, 'Minor', 4, 'Fri', 'Pending'],
        ['BR019', 'TMS007', 'A017', 'C5', 'Engineering', 2.0, 'Major', 6, 'Tue', 'Pending'],
        # Extra C4 Monday request to intensify conflict
        ['BR020', 'TMS008', 'A007', 'C4', 'Engineering', 2.0, 'Major', 11, 'Mon', 'Pending'],
    ]
    write_csv('block_requests.csv', headers, rows)


if __name__ == '__main__':
    print("Generating CSV data files...")
    generate_asset_master()
    generate_tms_maintenance()
    generate_smms_maintenance()
    generate_tdms_maintenance()
    generate_train_timetable()
    generate_block_requests()
    print(f"\nAll files generated in {DATA_DIR}")
