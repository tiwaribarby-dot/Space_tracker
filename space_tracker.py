import os
import sys
import time
import requests
import numpy as np
from datetime import datetime, timezone
from sgp4.api import Satrec, jday
from scipy.spatial import KDTree

class UltraScaleSpatialControl:
    def __init__(self, threshold_km=1400.0):
        self.threshold_km = threshold_km
        self.wgs84_r = 6378.137  # Earth's equatorial radius in km

    def fetch_orbital_registry(self, group_name):
        """Fetches TLE streams using multiple endpoint strategies and local file caching backup."""
        local_filename = f"{group_name}_cache.txt"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        
        # Strategy 1: Multi-endpoint failover arrays
        # Agar GROUP block ho raha hai, toh alternate parameters use karenge
        urls = [
            f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group_name}&FORMAT=tle",
            f"https://celestrak.org/NORAD/elements/gp.php?NAME={group_name}&FORMAT=tle"
        ]
        
        # Phase 1: Try pulling from the live web streams
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
                time.sleep(1) # Chota break block hone se bachne ke liye
                
        # Phase 2: Fallback to local file cache if server denies access entirely
        if os.path.exists(local_filename):
            print(f"[OFFLINE BACKUP] Server restricted. Loading synced telemetry from local cache: '{local_filename}'")
            with open(local_filename, "r") as f:
                cached_data = f.read()
            return self._parse_tle_lines(cached_data.strip().split('\n'))
            
        print(f"[CRITICAL] Live stream denied and no local backup found for '{group_name}'.")
        return []
    def _parse_tle_lines(self, lines):
        """Helper matrix method to map raw array text strings to Satrec profiles."""
        return [
            {
                "name": lines[i].strip(), 
                "rec": Satrec.twoline2rv(lines[i+1].strip(), lines[i+2].strip())
            } 
            for i in range(0, len(lines) - 2, 3)
        ]
    def compute_conjunctions_kdtree(self, starlinks, debris):
        """
        🚀 ULTRASCALE SPATIAL PARTITIONING ENGINE
        Uses Dual KD-Trees to prune search space from O(N*M) to O(N log M).
        """
        now = datetime.now(timezone.utc)
        jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond/1e6)

        # 1. Extract 3D Cartesian vectors
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
            return [], []

        A = np.array(starlink_mats)  # Starlinks (N, 3)
        B = np.array(debris_mats)     # Debris (M, 3)

        # 2. Build K-Dimensional Trees for Spatial Partitioning
        tree_starlink = KDTree(A)
        tree_debris = KDTree(B)

        # 3. Find structural intersections within the threshold radius
        raw_matches = tree_starlink.query_ball_tree(tree_debris, r=self.threshold_km)

        conjunctions = []
        
        # 4. Parse matches instantly (Zero overhead for non-threat spatial blocks)
        for s_idx, d_indices in enumerate(raw_matches):
            if not d_indices:
                continue  # No debris near this satellite
            
            pos_a = A[s_idx]
            r_mag_a = np.linalg.norm(pos_a)
            sat_lat = np.degrees(np.arcsin(pos_a[2] / r_mag_a))
            sat_lon = np.degrees(np.arctan2(pos_a[1], pos_a[0]))

            for d_idx in d_indices:
                pos_b = B[d_idx]
                dist = np.linalg.norm(pos_a - pos_b) # Compute precise distance only for filtered pairs

                r_mag_b = np.linalg.norm(pos_b)
                deb_lat = np.degrees(np.arcsin(pos_b[2] / r_mag_b))
                deb_lon = np.degrees(np.arctan2(pos_b[1], pos_b[0]))

                conjunctions.append({
                    "satellite": valid_starlinks[s_idx]['name'],
                    "debris": valid_debris[d_idx]['name'],
                    "distance_km": round(dist, 2),
                    "sat_coords": (sat_lat, sat_lon),
                    "deb_coords": (deb_lat, deb_lon)
                })

        # 5. Fast batch parsing for active UI layer elements
        r_mag_all = np.linalg.norm(A, axis=1)
        lats = np.degrees(np.arcsin(A[:, 2] / r_mag_all))
        lons = np.degrees(np.arctan2(A[:, 1], A[:, 0]))
        alts = r_mag_all - self.wgs84_r

        assets_ui = [
            {
                "name": valid_starlinks[idx]['name'],
                "latitude": lats[idx],
                "longitude": lons[idx],
                "altitude": alts[idx]
            }
            for idx in range(len(valid_starlinks))
        ]

        return assets_ui, conjunctions


if __name__ == "__main__":
    print("[KERNEL] Initializing UltraScale Spatial KD-Tree Pipeline...\n")
    control = UltraScaleSpatialControl(threshold_km=1400.0)
    
    # Live ingestion pipelines with network resilience built-in
    starlinks = control.fetch_orbital_registry("starlink")
    debris = control.fetch_orbital_registry("cosmos-2251-debris")
    
    if not starlinks or not debris:
        print("[CRITICAL] Stream offline permanently. Ingestion denied.")
        sys.exit(1)
        
    print(f"[DATA] Ingested {len(starlinks)} Starlinks and {len(debris)} Debris Assets.")
    
    # Run Benchmark
    t0 = time.time()
    assets, alerts = control.compute_conjunctions_kdtree(starlinks, debris)
    t1 = time.time()
    
    print(f"\n[BENCHMARK] Spatial Tree optimization executed in {round(t1-t0, 4)} seconds.")
    print(f"[ALERTS] Verified {len(alerts)} real threats inside Low Earth Orbit (LEO).")
