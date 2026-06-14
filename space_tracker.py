import os
import requests
import folium
from openai import OpenAI

# 1. xAI Client Initialize
XAI_API_KEY = os.environ.get("XAI_API_KEY")

client = None
if XAI_API_KEY:
    client = OpenAI(
        api_key=XAI_API_KEY,
        base_url="https://api.x.ai/v1",
    )

def fetch_live_satellite_data():
    """Live Satellite data fetch function (Free Public API)"""
    print("Fetching live space data from API...")
    try:
        url = "https://api.wheretheiss.at/v1/satellites/25544"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        print("Failed to fetch data from Space API.")
        return None
    except Exception as e:
        print(f"Error fetching space data: {e}")
        return None

def fetch_space_debris_data():
    print("Fetching nearby Space Debris data...")
    try:
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=json"
        response = requests.get(url)
        
        if response.status_code == 200:
            raw_debris = response.json()[:3]
            return raw_debris
        return []
    except Exception as e:
        print(f"Warning: Could not fetch debris data, skipping. ({e})")
        return []

def create_interactive_map(sat_data, debris_list):
    
    if not sat_data:
        return
    
    sat_lat = sat_data['latitude']
    sat_lon = sat_data['longitude']
    
    print(f"Satellite Coordinates: Lat {sat_lat}, Lon {sat_lon}")
    print(" Generating Interactive World Map with Debris Zones...")
    
    tile_style = "OpenStreetMap"
    mymap = folium.Map(location=[sat_lat, sat_lon], zoom_start=3, tiles=tile_style)

    # 1. LIVE SATELLITE MARKER (Red Color)
    sat_info = f"Satellite Live<br>Speed: {round(sat_data['velocity'],2)} km/h"
    folium.Marker(
        location=[sat_lat, sat_lon],
        popup=sat_info,
        icon=folium.Icon(color="red", icon="fullscreen", prefix="fa")
    ).add_to(mymap)

    # 2. SPACE DEBRIS MARKERS (Orange/Black Color
    offset = 5.0
    for i, debris in enumerate(debris_list):
        debris_lat = sat_lat + (offset * (i + 1)) if sat_lat + (offset * (i + 1)) < 90 else sat_lat
        debris_lon = sat_lon - (offset * (i + 1)) if sat_lon - (offset * (i + 1)) > -180 else sat_lon
        
        debris_name = debris.get('OBJECT_NAME', f'Unknown Debris #{i+1}')
        debris_id = debris.get('OBJECT_ID', 'N/A')
        
        folium.Marker(
            location=[debris_lat, debris_lon],
            popup=f"DEBRIS: {debris_name}<br>ID: {debris_id}",
            icon=folium.Icon(color="orange", icon="trash", prefix="fa")
        ).add_to(mymap)
        
        folium.Circle(
            location=[debris_lat, debris_lon],
            radius=300000, # 300 KM danger radius
            color="yellow",
            fill=True,
            fill_opacity=0.2
        ).add_to(mymap)

    mymap.save("satellite_track.html")
    print("Success! Map with Debris integrated saved as satellite_track.html")

def analyze_with_grok(satellite_data, debris_list):
    """Grok API Analysis with Debris Safety Check"""
    if not client:
        return "[LOCAL MODE]: Grok analysis skipped. Add your XAI_API_KEY to secrets to enable."

    print("Sending Telemetry + Debris data to xAI Grok for safety analysis...")
    
    full_space_report = {
        "active_satellite": satellite_data,
        "detected_debris_count": len(debris_list),
        "debris_samples": [d.get('OBJECT_NAME', 'Unknown') for d in debris_list]
    }

    prompt = f"""
    You are Grok, an expert aerospace AI developed by xAI. 
    Analyze this combined real-time data of an active satellite and nearby space debris objects.
    Provide a professional but easy-to-read safety assessment report for a 19-year-old developer.
    Mention if there is any collision risk in the current sector based on the coordinates.
    
    Data: {str(full_space_report)}
    """

    try:
        response = client.chat.completions.create(
            model="grok-4.3",
            messages=[
                {"role": "system", "content": "You are Grok, a master space debris tracker and collision avoidance AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Grok API Error: {e}"

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print(" Starting Starlink/ISS Tracker & Space Debris Analyzer...")
    print("-" * 50)

    # 1. Fetch data from both pipelines
    space_data = fetch_live_satellite_data()
    debris_data = fetch_space_debris_data()

    if space_data:
        print(f"\nTelemetry Secured. Found {len(debris_data)} trackable debris elements in DB.")
        
        # 2. Generate Advanced Map
        create_interactive_map(space_data, debris_data)
        print("-" * 50)

        # 3. Grok AI Safety Analysis
        analysis_report = analyze_with_grok(space_data, debris_data)
        print("\n[GROK SPACE SAFETY REPORT]:")
        print(analysis_report)
    else:
        print("Could not process further without telemetry data.")
