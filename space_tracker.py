import os
import sys
import time
import requests
import numpy as np
from datetime import datetime, timezone, timedelta
from sgp4.api import Satrec, jday
from scipy.spatial import cKDTree as KDTree  

class UltraScaleSpatialControl:
    def __init__(self, threshold_km=1400.0):
        self.threshold_km = threshold_km
        self.wgs84_r = 6378.137  # Earth's equatorial radius in km

    def fetch_orbital_registry(self, group_name):
        """Fetches TLE streams using multiple endpoint strategies and local file caching backup."""
        local_filename = f"{group_name}_cache.txt"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
        }
        
        urls = [
            f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group_name}&FORMAT=tle",
            f"https://celestrak.org/NORAD/elements/gp.php?NAME={group_name}&FORMAT=tle"
        ]
        
        for url in urls:
            for attempt in range(2):
                try:
                    response = requests.get(url, headers=headers, timeout=12)
                    if response.status_code == 200 and ("1 " in response.text or "STARLINK" in response.text.upper()):
                        with open(local_filename, "w") as f:
                            f.write(response.text)
                        print(f"[LIVE INGESTION] Successfully pulled and cached {group_name} data.")
                        return self._parse_tle_lines(response.text.strip().split('\n'))
                except Exception:
                    pass
                time.sleep(1)
                
        if os.path.exists(local_filename):
            print(f"[OFFLINE BACKUP] Server restricted. Loading synced telemetry from local cache: '{local_filename}'")
            with open(local_filename, "r") as f:
                cached_data = f.read()
            return self._parse_tle_lines(cached_data.strip().split('\n'))
            
        print(f"[CRITICAL] Live stream denied and no local backup found for '{group_name}'.")
        return []

    def _parse_tle_lines(self, lines):
        """Optimized generator-based mapping for raw array text strings to Satrec profiles."""
        tle_list = []
        for i in range(0, len(lines) - 2, 3):
            try:
                name = lines[i].strip()
                l1 = lines[i+1].strip()
                l2 = lines[i+2].strip()
                if l1.startswith("1 ") and l2.startswith("2 "):
                    tle_list.append({
                        "name": name, 
                        "rec": Satrec.twoline2rv(l1, l2)
                    })
            except Exception:
                continue
        return tle_list

    def compute_conjunctions_over_time(self, starlinks, debris, window_hours=2, step_minutes=10):
        """
        🚀 DAY 1 UPGRADE: Time-Window Propagation Loop
        Checks for threats across a future timeline, not just a single instant.
        """
        start_time = datetime.now(timezone.utc)
        all_conjunctions = []
        
        # Calculate how many steps we need to run
        total_steps = int((window_hours * 60) / step_minutes)
        print(f"[ENGINE] Starting Look-Ahead Propagation for the next {window_hours} hours ({total_steps} steps)...")

        for step in range(total_steps):
            check_time = start_time + timedelta(minutes=step * step_minutes)
            jd, fr = jday(check_time.year, check_time.month, check_time.day, check_time.hour, check_time.minute, check_time.second)

            # Extract positions for this specific timestamp
            starlink_mats, valid_starlinks = [], []
            for s in starlinks:
                e, r, v = s['rec'].sgp4(jd, fr)
                if e == 0:
                    starlink_mats.append(r)
                    valid_starlinks.append(s)

            debris_mats, valid_debris = [], []
            for d in debris:
                e, r, v = d['rec'].sgp4(jd, fr)
                if e == 0:
                    debris_mats.append(r)
                    valid_debris.append(d)

            if not starlink_mats or not debris_mats:
                continue

            A = np.array(starlink_mats)
            B = np.array(debris_mats)

            # Spatial Tree Query
            tree_starlink = KDTree(A)
            tree_debris = KDTree(B)
            raw_matches = tree_starlink.query_ball_tree(tree_debris, r=self.threshold_km)
            # Pre-compute coordinates for indexing
            r_mag_A = np.linalg.norm(A, axis=1)
            lats_A = np.degrees(np.arcsin(A[:, 2] / r_mag_A))
            lons_A = np.degrees(np.arctan2(A[:, 1], A[:, 0]))

            r_mag_B = np.linalg.norm(B, axis=1)
            lats_B = np.degrees(np.arcsin(B[:, 2] / r_mag_B))
            lons_B = np.degrees(np.arctan2(B[:, 1], B[:, 0]))

            # Parse matches for this specific time step
            for s_idx, d_indices in enumerate(raw_matches):
                if not d_indices:
                    continue 
                
                pos_a = A[s_idx]
                for d_idx in d_indices:
                    pos_b = B[d_idx]
                    dist = np.linalg.norm(pos_a - pos_b) 

                    all_conjunctions.append({
                        "time": check_time.strftime("%H:%M:%S UTC"),
                        "satellite": valid_starlinks[s_idx]['name'],
                        "debris": valid_debris[d_idx]['name'],
                        "distance_km": round(dist, 2),
                        "sat_coords": (round(lats_A[s_idx], 2), round(lons_A[s_idx], 2)),
                        "deb_coords": (round(lats_B[d_idx], 2), round(lons_B[d_idx], 2))
                    })

        return all_conjunctions

if __name__ == "__main__":
    print("[KERNEL] Initializing: Time-Window Spatial KD-Tree Pipeline...\n")
    control = UltraScaleSpatialControl(threshold_km=800.0) # threshold chota kiya real threats ke liye
    
    starlinks = control.fetch_orbital_registry("starlink")
    debris = control.fetch_orbital_registry("cosmos-2251-debris")
    
    if not starlinks or not debris:
        print("[CRITICAL] Stream offline permanently.")
        sys.exit(1)
        
    print(f"[DATA] Ingested {len(starlinks)} Starlinks and {len(debris)} Debris Assets.")
    
    t0 = time.time()
    # 2 ghante ka look-ahead, har 10 minute par check
    alerts = control.compute_conjunctions_over_time(starlinks, debris, window_hours=2, step_minutes=10)
    t1 = time.time()
    
    print(f"\n[BENCHMARK] Time-Window Spatial Propagation executed in {round(t1-t0, 4)} seconds.")
    print(f"[ALERTS] Found {len(alerts)} potential close-approaches in the next 2 hours.")
    
    # Print top 5 alerts as proof
    if alerts:
        print("\n[TOP ALERTS DISCOVERED]:")
        for alert in alerts[:5]:
            print(f" -> Time: {alert['time']} | {alert['satellite']} vs {alert['debris']} | Distance: {alert['distance_km']} km")
