# Autonomous Space Spacing & Conjunction Engine

A high-performance, physics-driven Python architecture designed to track active satellite constellations and compute real-time 3D orbital hazard zones using standard SGP4 propagation modeling and advanced AI telemetry decoding.

---

## The Vision
With thousands of active satellites in Low Earth Orbit (LEO), space congestion and orbital debris management have become critical infrastructure challenges. This project simulates an independent, automated mission control layer that:
1. Fetches live **Two-Line Element (TLE)** orbital parameters directly from NORAD/Celestrak databases.
2. Propagates exact, real-time satellite positions utilizing the **SGP4 mathematical model**.
3. Evaluates true **3D Euclidean Distance Matrices** to detect proximity threat profiles.
4. Integrates with **xAI's Grok API** to generate automated aerospace safety briefs.

---

## System Architecture & Features

### 1. High-Fidelity SGP4 Propagation Engine
Unlike basic API parsers, this system computes the exact Latitude, Longitude, and Altitude of orbital assets at any precise microsecond. It uses the industry-standard SGP4 analytical model to factor in atmospheric drag and orbital perturbations.

### 2. Multi-Node Threat Cross-Referencing
The pipeline concurrently ingests telemetry vectors for active satellite constellations (e.g., Starlink) and historical space junk clusters (e.g., Cosmos-2251 Debris). It dynamically flags close-approach alerts based on a highly accurate spatial distance matrix.

### 3. Dynamic Visual Mapping Layer
Using advanced geospatial libraries, the system auto-compiles an interactive dark-theme map dashboard (`advanced_space_density_map.html`). It plots precise satellite positions and draws automated threat vectors (dashed danger indicators) between intersecting paths.

### 4. xAI Grok Control Payload
The architecture securely formats the computed close-approach dataset and streams it into the **xAI Grok API (`grok-beta`)**. Acting as an automated Orbital Dynamics Commander, the AI analyzes the telemetry and drafts standard collision avoidance maneuver recommendations.

---

## How to Run (Bring Your Own API Key)

This infrastructure is 100% open-source, lightweight, and built entirely on a mobile development environment—proving complex aerospace data pipelines can be deployed anywhere.

### Prerequisites
Ensure you have Python installed, then set up the required mathematical and structural dependencies:
```bash
pip install requests folium numpy sgp4 openai
