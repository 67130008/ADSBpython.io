import pandas as pd
import math
import itertools
from tqdm import tqdm

def haversine(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance in nautical miles."""
    R = 3443.8
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# --- Read CSV ---
data = pd.read_csv('day1.csv')
data = data[['time', 'callsign', 'lat', 'lon', 'baroaltitude']]
data = data.sort_values('time')

# --- Initialize lists and dictionaries ---
horizontal_conflicts = []
vertical_conflicts = []
combined_conflicts = []

ongoing_horizontal = {}
ongoing_vertical = {}
ongoing_combined = {}

# --- Loop through each timestamp ---
for time, group in tqdm(data.groupby('time'), desc="Checking conflicts"):
    aircraft_list = group.to_dict('records')

    for a1, a2 in itertools.combinations(aircraft_list, 2):
        pair = tuple(sorted([str(a1['callsign']), str(a2['callsign'])]))

        dist_nm = haversine(a1['lat'], a1['lon'], a2['lat'], a2['lon'])
        alt_diff = abs(a1['baroaltitude'] - a2['baroaltitude'])

        hor = dist_nm < 3       # Horizontal conflict
        ver = alt_diff < 1000   # Vertical conflict

        # --- Horizontal-only conflict ---
        if hor and not ver:
            if pair not in ongoing_horizontal:
                ongoing_horizontal[pair] = time
        else:
            if pair in ongoing_horizontal:
                horizontal_conflicts.append({
                    'type': 'Horizontal',
                    'callsign1': pair[0],
                    'callsign2': pair[1],
                    'start_time': ongoing_horizontal[pair],
                    'end_time': time
                })
                del ongoing_horizontal[pair]

        # --- Vertical-only conflict ---
        if ver and not hor:
            if pair not in ongoing_vertical:
                ongoing_vertical[pair] = time
        else:
            if pair in ongoing_vertical:
                vertical_conflicts.append({
                    'type': 'Vertical',
                    'callsign1': pair[0],
                    'callsign2': pair[1],
                    'start_time': ongoing_vertical[pair],
                    'end_time': time
                })
                del ongoing_vertical[pair]

        # --- Combined conflict ---
        if hor and ver:
            if pair not in ongoing_combined:
                ongoing_combined[pair] = time
        else:
            if pair in ongoing_combined:
                combined_conflicts.append({
                    'type': 'Combined',
                    'callsign1': pair[0],
                    'callsign2': pair[1],
                    'start_time': ongoing_combined[pair],
                    'end_time': time
                })
                del ongoing_combined[pair]

# --- Close remaining ongoing conflicts ---
last_time = data['time'].max()

for ongoing, conflict_list, conflict_type in [
    (ongoing_horizontal, horizontal_conflicts, 'Horizontal'),
    (ongoing_vertical, vertical_conflicts, 'Vertical'),
    (ongoing_combined, combined_conflicts, 'Combined')
]:
    for pair, start in ongoing.items():
        conflict_list.append({
            'type': conflict_type,
            'callsign1': pair[0],
            'callsign2': pair[1],
            'start_time': start,
            'end_time': last_time
        })

# --- Combine all conflicts into a single DataFrame and sort by start_time ---
all_conflicts = pd.DataFrame(horizontal_conflicts + vertical_conflicts + combined_conflicts)
all_conflicts = all_conflicts.sort_values('start_time').reset_index(drop=True)
all_conflicts.to_csv('conflicts_inorder.csv', index=False)

# --- Count conflicts per aircraft ---
all_callsigns = data['callsign'].unique()
count_data = []

for cs in all_callsigns:
    h_count = len(all_conflicts[((all_conflicts['callsign1'] == cs) | (all_conflicts['callsign2'] == cs)) & (
                all_conflicts['type'] == 'Horizontal')])
    v_count = len(all_conflicts[((all_conflicts['callsign1'] == cs) | (all_conflicts['callsign2'] == cs)) & (
                all_conflicts['type'] == 'Vertical')])
    c_count = len(all_conflicts[((all_conflicts['callsign1'] == cs) | (all_conflicts['callsign2'] == cs)) & (
                all_conflicts['type'] == 'Combined')])
    count_data.append({'callsign': cs, 'Horizontal': h_count, 'Vertical': v_count, 'Combined': c_count})

count_df = pd.DataFrame(count_data)
count_df.to_csv('count_per_plane.csv', index=False)

# --- Display total counts ---
print(f"Total Horizontal Conflicts: {len(horizontal_conflicts)}")
print(f"Total Vertical Conflicts: {len(vertical_conflicts)}")
print(f"Total Combined Conflicts: {len(combined_conflicts)}")
