import os
import requests
import folium
import numpy as np
from datetime import datetime, timezone
from sgp4.api import Satrec, WGS84, jday
from openai import OpenAI

# 1. xAI Client Initialization
XAI_API_KEY = os.environ.get("XAI_API_KEY")
client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1") if XAI_API_KEY else None

def get_satellite_position_now(sat_rec):
    """
    Calculate real-time satellite Lat, Lon and Alt using SGP4 model for current second.
    """
    now = datetime.now(timezone.utc)
    # Compute real-time current Julian Date
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond/1e6)

    # SGP4 engine standard propagation (Position in km, Velocity)
    e, r, v = sat_rec.sgp4(jd, fr)
    if e!= 0:
        return None

    x, y, z = r[0], r[1], r[2]
    r_mag = np.sqrt(x**2 + y**2 + z**2)

    lat = np.degrees(np.arcsin(z / r_mag))
    lon = np.degrees(np.arctan2(y, x))
    alt = r_mag - 6378.137 # Subtract Earth radius

    return {"latitude": lat, "longitude": lon, "altitude": alt, "x": x, "y": y, "z": z}

def fetch_and_parse_celestrak_group(group_name):
    print(f"Fetching Live Orbital Elements for '{group_name}' from Celestrak...")
    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group_name}&FORMAT=tle"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code!= 200:
            return []

        lines = response.text.strip().split('\n')
        satellites = []

        for i in range(0, len(lines) - 2, 3):
            name = lines[i].strip()
            line1 = lines[i+1].strip()
            line2 = lines[i+2].strip()

            sat_rec = Satrec.twoline2rv(line1, line2)
            satellites.append({"name": name, "rec": sat_rec})

        return satellites
    except Exception as e:
        print(f"Error fetching group {group_name}: {e}")
        return []

def calculate_dynamic_density_and_conjunctions(starlink_list, debris_list, threshold_km=1500.0):
    print("Calculating Real-time Dynamic 3D Spacing Matrix...")
    dangerous_conjunctions = []
    active_starlinks_pos = []

    for s in starlink_list[:60]: # Processing subset for speed optimization
        pos = get_satellite_position_now(s['rec'])
        if pos:
            pos['name'] = s['name']
            active_starlinks_pos.append(pos)

    for d in debris_list[:40]:
        d_pos = get_satellite_position_now(d['rec'])
        if not d_pos:
            continue

        for s_pos in active_starlinks_pos:
            # Mathematical 3D Vector Distance
            dist = np.sqrt((s_pos['x'] - d_pos['x'])**2 +
                           (s_pos['y'] - d_pos['y'])**2 +
                           (s_pos['z'] - d_pos['z'])**2)

            if dist < threshold_km:
                dangerous_conjunctions.append({
                    "satellite": s_pos['name'],
                    "debris": d['name'],
                    "distance_km": round(dist, 2),
                    "sat_coords": (s_pos['latitude'], s_pos['longitude']),
                    "deb_coords": (d_pos['latitude'], d_pos['longitude'])
                })

    return active_starlinks_pos, dangerous_conjunctions

def generate_next_level_map(starlinks, conjunctions):
    if not starlinks:
        print("No live coordinates available to map.")
        return

    print("Compiling Interactive Autonomous Space Density Map...")
    mymap = folium.Map(location=[0, 0], zoom_start=2, tiles="CartoDB dark_matter")

    # Live Starlink Positioning
    for s in starlinks:
        folium.CircleMarker(
            location=[s['latitude'], s['longitude']],
            radius=3,
            color="#00D2FF",
            fill=True,
            popup=f"Starlink: {s['name']}<br>Alt: {round(s['altitude'], 2)} km"
        ).add_to(mymap)

    # Threat Vector Mapping
    for conj in conjunctions:
        folium.Marker(
            location=conj['deb_coords'],
            popup=f"DEBRIS TRACE: {conj['debris']}<br>Distance: {conj['distance_km']} km to {conj['satellite']}",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(mymap)

        folium.PolyLine(
            locations=[conj['sat_coords'], conj['deb_coords']],
            color="red",
            weight=1.5,
            dash_array="5, 5"
        ).add_to(mymap)

    mymap.save("advanced_space_density_map.html")
    print("Success! Advanced Map saved as 'advanced_space_density_map.html'")

def grok_orbital_mechanics_analysis(conjunctions):
    if not client:
        return "[LOCAL MODE]: XAI_API_KEY not found. Telemetry logging complete."

    print("Transmitting Spatial Coordinates to xAI Grok Control Engine...")

    prompt = f"""
    You are Grok, an elite Aerospace Engineer at xAI Mission Control.
    Review this real-time SGP4 analytical data representing satellite space tracking vectors.
    Identify potential spatial optimizations or close-approach anomalies.

    Dataset:
    {str(conjunctions[:3])}

    Provide an engineering summary detailing current vector safety indices and telemetry health.
    """

    try:
        response = client.chat.completions.create(
            # Using current active API model
            model="grok-beta",
            messages=[
                {"role": "system", "content": "You are Grok, an elite Aerospace Engineer and Orbital Dynamics Commander."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Grok API Telemetry Error: {e}"

if __name__ == "__main__":
    print("INITIALIZING GENUINE ORBITAL MECHANICS ENGINE\n")
    starlink_network = fetch_and_parse_celestrak_group("starlink")
    cosmos_debris = fetch_and_parse_celestrak_group("cosmos-2251-debris")

    if starlink_network and cosmos_debris:
        live_starlinks, close_calls = calculate_dynamic_density_and_conjunctions(starlink_network, cosmos_debris)
        print(f"\nProcessing Complete. Active Starlinks Mapped: {len(live_starlinks)}. Dynamic Threat Vectors: {len(close_calls)}.")
        generate_next_level_map(live_starlinks, close_calls)

        grok_report = grok_orbital_mechanics_analysis(close_calls)
        print("\n[GROK MISSION CONTROL TELEMETRY BRIEF]:")
        print(grok_report)
    else:
        print("Failed to sync with NORAD/Celestrak database.")       
