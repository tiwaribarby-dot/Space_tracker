import os
import sys
import time
import requests
import folium
import numpy as np
from datetime import datetime, timezone
from sgp4.api import Satrec, jday
from openai import OpenAI

class SpaceMissionControl:
    """
    ENTERPRISE ARCHITECTURE: Professional OOPs-based Orbital Safety Framework.
    Manages live multi-node telemetry pipelines and autonomous threat scoring.
    """
    def __init__(self, starlink_limit=60, debris_limit=40, threshold_km=1500.0):
        self.starlink_limit = starlink_limit
        self.debris_limit = debris_limit
        self.threshold_km = threshold_km
        
        # xAI Grok Connection Setup
        self.api_key = os.environ.get("XAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.x.ai/v1") if self.api_key else None

    def get_satellite_position_now(self, sat_rec):
        """Calculates precise 3D space vectors using industry-standard SGP4 model."""
        now = datetime.now(timezone.utc)
        jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond/1e6)

        e, r, v = sat_rec.sgp4(jd, fr)
        if e != 0:
            return None

        x, y, z = r[0], r[1], r[2]
        r_mag = np.sqrt(x**2 + y**2 + z**2)

        lat = np.degrees(np.arcsin(z / r_mag))
        lon = np.degrees(np.arctan2(y, x))
        alt = r_mag - 6378.137 

        return {"latitude": lat, "longitude": lon, "altitude": alt, "x": x, "y": y, "z": z}

    def fetch_orbital_registry(self, group_name):
        """Fetches dynamic Two-Line Element sets securely from live NORAD tracking database."""
        print(f"[LIVE INGEST] Fetching elements for '{group_name}'...")
        url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group_name}&FORMAT=tle"
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return []

            lines = response.text.strip().split('\n')
            satellites = []

            for i in range(0, len(lines) - 2, 3):
                name = lines[i].strip()
                sat_rec = Satrec.twoline2rv(lines[i+1].strip(), lines[i+2].strip())
                satellites.append({"name": name, "rec": sat_rec})

            return satellites
        except Exception as e:
            print(f"[REGISTRY ERROR] Secure network sync failed: {e}")
            return []

    def compute_critical_conjunctions(self, starlinks, debris):
        """Evaluates live distance matrices across all active nodes to map threat intercepts."""
        print("[COMPUTE ENGINE] Processing 3D Euclidean Spacing Profiles...")
        conjunctions = []
        starlink_positions = []

        for s in starlinks[:self.starlink_limit]:
            pos = self.get_satellite_position_now(s['rec'])
            if pos:
                pos['name'] = s['name']
                starlink_positions.append(pos)

        for d in debris[:self.debris_limit]:
            d_pos = self.get_satellite_position_now(d['rec'])
            if not d_pos:
                continue

            for s_pos in starlink_positions:
                dist = np.sqrt((s_pos['x'] - d_pos['x'])**2 +
                               (s_pos['y'] - d_pos['y'])**2 +
                               (s_pos['z'] - d_pos['z'])**2)

                if dist < self.threshold_km:
                    conjunctions.append({
                        "satellite": s_pos['name'],
                        "debris": d['name'],
                        "distance_km": round(dist, 2),
                        "sat_coords": (s_pos['latitude'], s_pos['longitude']),
                        "deb_coords": (d_pos['latitude'], d_pos['longitude'])
                    })

        return starlink_positions, conjunctions

    def compile_visual_dashboard(self, starlinks, conjunctions):
        """Generates the interactive spatial mapping interface."""
        print("  [DASHBOARD] Compiling spatial visualization payload...")
        mymap = folium.Map(location=[0, 0], zoom_start=2, tiles="CartoDB dark_matter")

        for s in starlinks:
            folium.CircleMarker(
                location=[s['latitude'], s['longitude']],
                radius=3,
                color="#00D2FF",
                fill=True,
                popup=f"Asset: {s['name']}<br>Alt: {round(s['altitude'], 2)} km"
            ).add_to(mymap)

        for conj in conjunctions:
            folium.Marker(
                location=conj['deb_coords'],
                popup=f"THREAT: {conj['debris']}<br>{conj['distance_km']} km to target",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(mymap)

            folium.PolyLine(
                locations=[conj['sat_coords'], conj['deb_coords']],
                color="red", weight=1.5, dash_array="5, 5"
            ).add_to(mymap)

        mymap.save("advanced_space_density_map.html")
        print("[SYSTEM] Real-time map compiled as 'advanced_space_density_map.html'")


# --- RUNTIME LIVE LOOP ENGINE ---
if __name__ == "__main__":
    print("INITIALIZING PROFESSIONAL AUTONOMOUS ORBITAL CONTROLLER ️\n")
    
    # Instantiate the master object
    mission_control = SpaceMissionControl(starlink_limit=70, debris_limit=45)
    
    # Ingest baseline database registries once to save bandwidth
    starlink_net = mission_control.fetch_orbital_registry("starlink")
    debris_net = mission_control.fetch_orbital_registry("cosmos-2251-debris")
    
    if not starlink_net or not debris_net:
        print("System startup failed. Database handshake compromised.")
        sys.exit()

    # LIVE AUTOMATION LOOP: Runs infinitely updating positions until stopped manually (Ctrl+C)
    loop_count = 1
    try:
        while True:
            print(f"\n[CYCLE {loop_count} - {datetime.now().strftime('%H:%M:%S')}] Executing telemetry refresh...")
            
            # Compute positions dynamically for this exact second
            live_assets, alerts = mission_control.compute_critical_conjunctions(starlink_net, debris_net)
            print(f" [METRICS] Monitored Nodes: {len(live_assets)} | Active Vectors: {len(alerts)}")
            
            # Recompile dashboard instantly
            mission_control.compile_visual_dashboard(live_assets, alerts)
            
            print("Cycle complete. System standing by for next telemetry pulse (15s)...")
            time.sleep(15)  # Wait for 15 seconds before processing the next second's coordinates
            loop_count += 1
            
    except KeyboardInterrupt:
        print("\nMission Control execution terminated gracefully by operator.")
