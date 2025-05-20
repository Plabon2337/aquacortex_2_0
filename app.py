import streamlit as st
import os
from openai import OpenAI
import requests

# Set page
st.set_page_config(page_title="AquaCortex 2.0", page_icon="🌊", layout="wide")
st.title("💧 AquaCortex 2.0: Water Intelligence Platform")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────── WATER SOURCE INFO ───────────
st.markdown("### 📝 Water Source Information")
col1, col2 = st.columns(2)
with col1:
    source_name = st.text_input("🌍 Water Source Name", key="src_name")
with col2:
    location = st.text_input("📍 Location", key="src_loc")

source_type = st.selectbox("💧 Type of Source", [
    "River", "Canal", "Lake", "Pond", "Ground Aquifer", "Tap", "Sewage Line", "Others"
])
description = st.text_area("📝 Description (Optional)", key="src_desc", height=80)

# ─────────── GPS Coordinates from Google Maps ───────────
gps_coords = "Not Available"
api_key = os.getenv("GOOGLE_MAPS_API_KEY")
if location and api_key:
    try:
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}"
        )
        geo_data = response.json()
        if geo_data["status"] == "OK":
            latlng = geo_data["results"][0]["geometry"]["location"]
            gps_coords = f"{latlng['lat']}, {latlng['lng']}"
            st.success(f"📍 GPS Coordinates: {gps_coords}")
        else:
            st.warning("⚠️ Location not found.")
    except Exception as e:
        st.error("❌ Error fetching GPS coordinates.")

# ─────────── TEST DATA INPUT ───────────
st.markdown("### 📊 Enter Water Quality Test Data")
test_parameters = {
    "Dissolved Oxygen (DO) [mg/L]": "DO",
    "Biochemical Oxygen Demand (BOD₅) [mg/L]": "BOD5",
    "Chemical Oxygen Demand (COD) [mg/L]": "COD",
    "pH [-]": "pH",
    "Temperature [°C]": "Temperature",
    "Turbidity [NTU]": "Turbidity",
    "Total Suspended Solids (TSS) [mg/L]": "TSS",
    "Ammonia Nitrogen (NH₃-N) [mg/L]": "NH3N",
    "Nitrate (NO₃⁻) [mg/L]": "NO3",
    "Lead (Pb) [mg/L]": "Pb",
    "Arsenic (As) [mg/L]": "As"
}

input_data = {}
for label, key in test_parameters.items():
    st.markdown(f"**{label}**")
    col1, col2, col3 = st.columns(3)
    with col1:
        val1 = st.text_input(f"Sample 1 ({key})", key=f"{key}_1")
    with col2:
        val2 = st.text_input(f"Sample 2 ({key})", key=f"{key}_2")
    with col3:
        val3 = st.text_input(f"Sample 3 ({key})", key=f"{key}_3")
    input_data[key] = [val1, val2, val3]

# ─────────── ANALYSIS ───────────
if st.button("Analyze Water Quality"):
    standards = {
        "pH": 7.0, "BOD5": 3, "DO": 6, "COD": 10, "Turbidity": 5,
        "TSS": 25, "NH3N": 1.0, "NO3": 10, "Temperature": 25,
        "Pb": 0.01, "As": 0.01
    }
    weights = {k: 1/v for k, v in standards.items()}
    q_values, w_values = [], []

    for param, samples in input_data.items():
        valid = [float(v) for v in samples if v.strip() != ""]
        if valid and param in standards:
            avg = sum(valid) / len(valid)
            q = (avg / standards[param]) * 100
            q_values.append(q * weights[param])
            w_values.append(weights[param])

    # Water Quality Index
    if len(q_values) >= 3:
        wqi = sum(q_values) / sum(w_values)
        st.success(f"🌊 Water Quality Index (WQI): {wqi:.2f}")
        wqi_status = ("Excellent" if wqi <= 25 else "Good" if wqi <= 50 else
                      "Poor" if wqi <= 75 else "Very Poor" if wqi <= 100 else "Unsuitable")
        st.markdown(f"Status: {wqi_status}")
    else:
        st.warning("⚠️ Not enough valid data for WQI.")
        wqi = None
        wqi_status = "N/A"

    # Pollution Index
    def rpi_score(param, val):
        if param == "DO":
            return 1 if val >= 6.5 else 3 if val >= 4.6 else 6 if val >= 2.1 else 8
        if param == "BOD5":
            return 1 if val <= 3 else 3 if val <= 4.9 else 6 if val <= 9.9 else 8
        if param == "TSS":
            return 1 if val <= 20 else 3 if val <= 49.9 else 6 if val <= 99.9 else 8
        if param == "NH3N":
            return 1 if val <= 0.5 else 3 if val <= 0.99 else 6 if val <= 1.99 else 8

    rpi_vals = []
    for key in ["DO", "BOD5", "TSS", "NH3N"]:
        values = input_data.get(key, [])
        valid = [float(v) for v in values if v.strip() != ""]
        if valid:
            avg = sum(valid) / len(valid)
            rpi_vals.append(rpi_score(key, avg))

    if len(rpi_vals) == 4:
        rpi = sum(rpi_vals) / 4
        st.success(f"🧪 Pollution Index (RPI): {rpi:.2f}")
        rpi_status = ("Non/mildly polluted" if rpi <= 2 else "Lightly polluted" if rpi <= 3
                      else "Moderately polluted" if rpi <= 6 else "Severely polluted")
        st.markdown(f"Pollution Level: {rpi_status}")
    else:
        rpi = None
        rpi_status = "N/A"
        st.warning("⚠️ Need DO, BOD5, TSS, and NH3N for RPI.")

    # ─────────── AI Analysis ───────────
    st.markdown("---")
    st.subheader("🧠 AI-Based Analysis & Treatment Suggestion")

    prompt = f"""
You are an expert environmental engineer. Analyze the following river water test results and provide:
1. Suitability for use (e.g., drinking, irrigation, recreation)
2. Health/environmental risks
3. A simple water treatment method

Water test data:
{input_data}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only answers questions about water quality, environment, and civil engineering."},
                {"role": "user", "content": prompt}
            ]
        )
        ai_text = response.choices[0].message.content
        st.markdown(ai_text)
    except Exception as e:
        ai_text = "Error getting AI response"
        st.error(ai_text)

    # ─────────── REPORT OUTPUT ───────────
    st.markdown("---")
    st.subheader("📄 Download Summary Report")

    if wqi and rpi and ai_text:
        if st.button("📄 Generate Report"):
            report = f"""
### AquaCortex 2.0 — Water Quality Report

**Water Source**: {source_name}
**Location**: {location}
**Type**: {source_type}
**GPS Coordinates**: {gps_coords}

**Description**:
{description}

---

**🌊 Water Quality Index (WQI)**: {wqi:.2f} → {wqi_status}
**🧪 Pollution Index (RPI)**: {rpi:.2f} → {rpi_status}

---

**🧠 AI Assessment and Recommendation**:
{ai_text}
"""
            st.download_button("⬇️ Download Report (.txt)", data=report, file_name="AquaCortex_Report.txt", mime="text/plain")
