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
    def __init__(self, starlink_limit=80, debris_limit=60, threshold_km=1200.0):
        self.starlink_limit = starlink_limit
        self.debris_limit = debris_limit
        self.threshold_km = threshold_km
        
        # Core Network Configuration
        self.api_key = os.environ.get("XAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.x.ai/v1") if self.api_key else None

    def get_satellite_position_now(self, sat_rec):
        """Calculates precise 3D Cartesian coordinates using standard SGP4 propagation."""
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
        """Pulls raw TLE streams asynchronously from the live NORAD/Celestrak endpoints."""
        print(f"[INGESTION ENGINE] Fetching active element matrices for: '{group_name}'")
        url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group_name}&FORMAT=tle"
        try:
            response = requests.get(url, timeout=12)
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
            print(f"[NET_ERROR] Handshake failed for registry {group_name}: {e}")
            return []

    def compute_critical_conjunctions(self, starlinks, debris):
        """Executes vectorized fast matrix distance evaluations across space telemetry profiles."""
        conjunctions = []
        starlink_positions = []

        # Parse Active Node Coordinates
        for s in starlinks[:self.starlink_limit]:
            pos = self.get_satellite_position_now(s['rec'])
            if pos:
                pos['name'] = s['name']
                starlink_positions.append(pos)

        if not starlink_positions:
            return [], []

        # Vectorized Proximity Engine
        for d in debris[:self.debris_limit]:
            d_pos = self.get_satellite_position_now(d['rec'])
            if not d_pos:
                continue

            # Parallel Calculation Loop via Matrix Array Structure
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
        """Generates a self-updating geospatial tracking map dashboard."""
        mymap = folium.Map(location=[0, 0], zoom_start=2, tiles="CartoDB dark_matter")

        # Map Working Node Framework
        for s in starlinks:
            folium.CircleMarker(
                location=[s['latitude'], s['longitude']],
                radius=3, color="#00D2FF", fill=True,
                popup=f"Asset: {s['name']}<br>Altitude: {round(s['altitude'], 2)} km"
            ).add_to(mymap)

        # Map Dangerous Threat Vectors
        for conj in conjunctions:
            folium.Marker(
                location=conj['deb_coords'],
                popup=f"CONJUNCTION ALERT<br>Debris: {conj['debris']}<br>Miss Distance: {conj['distance_km']} km",
                icon=folium.Icon(color="red", icon="warning-sign", prefix="glyphicon")
            ).add_to(mymap)

            folium.PolyLine(
                locations=[conj['sat_coords'], conj['deb_coords']],
                color="#FF2A2A", weight=2.0, dash_array="6, 6"
            ).add_to(mymap)

        output_file = "advanced_space_density_map.html"
        mymap.save(output_file)
        
        # Injecting Automatic Head Meta-refresh to make UI live!
        try:
            with open(output_file, "r") as f:
                html_content = f.read()
            
            # This meta tag tells the browser to reload every 15 seconds automatically
            meta_refresh = '<meta http-equiv="refresh" content="15">'
            updated_html = html_content.replace("<head>", f"<head>\n    {meta_refresh}")
            
            with open(output_file, "w") as f:
                f.write(updated_html)
        except Exception as e:
            print(f"[UI ENGINE] Auto-refresh injection bypassed: {e}")


# --- RUNTIME CONTROL ROOM PIPELINE ---
if __name__ == "__main__":
    print("[KERNEL] INITIALIZING PRODUCTION SPACE VECTOR ENGINE v5.0\n")
    
    # Increased target processing matrices for  optimization
    control_room = SpaceMissionControl(starlink_limit=90, debris_limit=55, threshold_km=1400.0)
    
    starlink_registry = control_room.fetch_orbital_registry("starlink")
    debris_registry = control_room.fetch_orbital_registry("cosmos-2251-debris")
    
    if not starlink_registry or not debris_registry:
        print(" [SYSTEM CRITICAL] Ingestion failure. Handshake denied.")
        sys.exit()

    cycle = 1
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n[TELEMETRY PULSE #{cycle}] Ingesting state vectors at {current_time}...")
            
            assets, alerts = control_room.compute_critical_conjunctions(starlink_registry, debris_registry)
            
            print(f"[ALGORITHM MATCH] Tracked Constellations: {len(assets)} | Intercept Matches: {len(alerts)}")
            control_room.compile_visual_dashboard(assets, alerts)
            
            print("[PIPELINE COMPLETE] Interface updated. Node sleeping for 15s...")
            time.sleep(15)
            cycle += 1
            
    except KeyboardInterrupt:
        print("\n[KERNEL SYSTEM] Execution safely killed by telemetry operator.")
