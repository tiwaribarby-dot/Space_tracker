# Autonomous Space Debris Tracker & Safety Analyst

A high-performance Python-based space monitoring architecture designed to track active satellites and analyze real-time orbital hazard zones using international telemetry data and advanced AI analysis.

---

##  The Vision
Space congestion is one of the biggest challenges for future interplanetary travel and satellite constellations like Starlink. This project was built to simulate an automated, independent defense and observation layer that:
1. Fetches live satellite telemetry.
2. Cross-references live positions with international Space Debris databases.
3. Automatically maps potential hazard sectors.
4. Leverages **xAI's Grok API** to generate instantaneous safety assessment reports.

---

##  System Architecture & Features

### 1. Live Telemetry Pipeline
The backend establishes an active connection with space tracking endpoints to pull exact coordinates, altitude, and current velocity of orbital assets.

### 2. CelesTrak Database Integration (Space Debris Engine)
The system queries live datasets from CelesTrak to fetch the positions of historical orbital debris (e.g., fragments from historical space collisions). It automatically calculates a **300KM Proximity Hazard Zone** around each debris element.

### 3. Dynamic Visual Mapping Layer
Using geographical mapping libraries, the system generates an interactive, high-fidelity visual dashboard (`satellite_track.html`) plotting both the asset and nearby danger vectors locally without any external overhead.

### 4. Automated AI Safety Reports (Powered by xAI Grok)
The architecture is designed to pack the raw coordinate data, proximity telemetry, and hazard density, and pass it to **xAI's Grok API (`grok-4.3`)**. Grok acts as the automated space scientist, evaluating whether the orbital path requires a collision avoidance maneuver.

---

## How to Run (Bring Your Own API Key)

This project is built using an open-source architecture with a zero-budget development model. It does not hardcode any sensitive credentials. Users can bring their own computing environment and xAI infrastructure to run the full pipeline.

### Prerequisites
Ensure you have Python installed, then set up the required dependencies:
```bash
pip install requests folium openai

Configuration
​Set your official xAI API Key in your environment variables:
	
	export XAI_API_KEY="your_grok_api_key_here"

Execution
​Run the core pipeline processor:
	python space_tracker.py
	
Note: If no XAI_API_KEY is provided, the system will gracefully degrade to Local Map Mode, successfully plotting the satellite_track.html mapping dashboard while skipping the AI text analysis.

