import os
import sys
import time
import requests
import folium
import numpy as np
from datetime import datetime, timezone
from sgp4.api import Satrec, jday

class HyperScaleMissionControl:
    def __init__(self, threshold_km=1400.0):
        self.threshold_km = threshold_km
        self.wgs84_r = 6378.137  # Earth's equatorial radius in km

    def fetch_orbital_registry(self, group_name):
        """Fetches TLE streams from CelesTrak and parses them into Satrec objects."""
        url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group_name}&FORMAT=tle"
        try:
            response = requests.get(url, timeout=12)
            if response.status_code != 200: 
                return []
            
            lines = response.text.strip().split('\n')
            return [
                {
                    "name": lines[i].strip(), 
                    "rec": Satrec.twoline2rv(lines[i+1].strip(), lines[i+2].strip())
                } 
                for i in range(0, len(lines) - 2, 3)
            ]
        except Exception as e:
            print(f"[ERROR] Registry fetch failed for {group_name}: {e}")
            return []

    def compute_conjunctions_vectorized(self, starlinks, debris):
        """
        Calculates all combinations of distances instantly using Numpy Matrix Broadcasting.
        O(N * M) operations executed entirely at C-speed.
        """
        now = datetime.now(timezone.utc)
        jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond/1e6)

        # 1. Gather 3D Cartesian coordinates (TEME Frame)
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

        # Convert to high-performance NumPy arrays
        A = np.array(starlink_mats)  # Shape: (N, 3)
        B = np.array(debris_mats)     # Shape: (M, 3)

        # 2. Broadcasting Magic: Matrix Distance Evaluation
        # Shape of diff becomes (N, M, 3) -> Delta X, Delta Y, Delta Z
        diff = A[:, np.newaxis, :] - B[np.newaxis, :, :]
        dist_matrix = np.linalg.norm(diff, axis=2)  # Shape: (N, M)

        # 3. Quick boolean indexing to pull threat matches
        sat_indices, debris_indices = np.where(dist_matrix < self.threshold_km)

        conjunctions = []
        for s_idx, d_idx in zip(sat_indices, debris_indices):
            dist = dist_matrix[s_idx, d_idx]
            
            # Extract real position vectors for specific collision nodes
            pos_a = A[s_idx]
            pos_b = B[d_idx]
            
            r_mag_a = np.linalg.norm(pos_a)
            r_mag_b = np.linalg.norm(pos_b)

            # Accurate coordinate parsing for UI mapping
            sat_lat = np.degrees(np.arcsin(pos_a[2] / r_mag_a))
            sat_lon = np.degrees(np.arctan2(pos_a[1], pos_a[0]))
            
            deb_lat = np.degrees(np.arcsin(pos_b[2] / r_mag_b))
            deb_lon = np.degrees(np.arctan2(pos_b[1], pos_b[0]))

            conjunctions.append({
                "satellite": valid_starlinks[s_idx]['name'],
                "debris": valid_debris[d_idx]['name'],
                "distance_km": round(dist, 2),
                "sat_coords": (sat_lat, sat_lon),
                "deb_coords": (deb_lat, deb_lon)
            })

        # 4. Format asset coordinates for UI rendering
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


# --- REAL WORLD BENCHMARKING ---
if __name__ == "__main__":
    print("[SYSTEM] Starting Vectorized Aerospace Compute Pipeline...\n")
    control = HyperScaleMissionControl(threshold_km=1400.0)
    
    starlinks = control.fetch_orbital_registry("starlink")
    debris = control.fetch_orbital_registry("cosmos-2251-debris")
    
    if not starlinks or not debris:
        print("[CRITICAL] Data streams offline. Exiting.")
        sys.exit(1)
        
    print(f"[DATA] Ingested {len(starlinks)} Starlinks and {len(debris)} Debris Assets.")
    
    # Execution Check
    t0 = time.time()
    assets, alerts = control.compute_conjunctions_vectorized(starlinks, debris)
    t1 = time.time()
    
    total_checks = len(starlinks) * len(debris)
    print(f"\n[BENCHMARK] Evaluated {total_checks:,} combinations in {round(t1-t0, 4)} seconds.")
    print(f"[ALERTS] Found {len(alerts)} critical conjunction threats within {control.threshold_km} km.")
