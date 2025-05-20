import streamlit as st
import os
from openai import OpenAI
import requests

# Page setup
st.set_page_config(page_title="AquaCortex 2.0", page_icon="🌊", layout="wide")
st.title("💧 AquaCortex 2.0: Water Intelligence Platform")

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Sidebar Mode Selector
mode = st.sidebar.radio("Choose Mode", ["📊 Test Data Analysis", "💬 AI Water Chat"])

# Source Info
st.markdown("### 📝 Water Source Information")
col1, col2 = st.columns(2)
with col1:
    source_name = st.text_input("🌍 Water Source Name", key="src_name")
with col2:
    location = st.text_input("📍 Location", key="src_loc")

source_type = st.selectbox("💧 Type of Source", ["River", "Canal", "Lake", "Pond", "Ground Aquifer", "Tap", "Sewage Line", "Others"])
description = st.text_area("📝 Description (Optional)", key="src_desc", height=80)

# GPS Coordinates
gps_coords = "Not Available"
if location and GOOGLE_MAPS_API_KEY:
    try:
        geo = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API_KEY}"
        ).json()
        if geo["status"] == "OK":
            latlng = geo["results"][0]["geometry"]["location"]
            gps_coords = f"{latlng['lat']}, {latlng['lng']}"
            st.success(f"📍 GPS Coordinates: {gps_coords}")
    except:
        st.warning("❌ Unable to fetch GPS coordinates.")

if mode == "💬 AI Water Chat":
    st.subheader("💬 Ask AquaCortex")
    user_input = st.text_input("Ask any question related to water, pollution, civil or environmental engineering:")

    if st.button("Ask"):
        if user_input.strip():
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a water/environmental/civil engineering expert."},
                        {"role": "user", "content": user_input}
                    ]
                )
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"OpenAI API Error: {e}")
        else:
            st.warning("❗ Please type your question.")

elif mode == "📊 Test Data Analysis":
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
            v1 = st.text_input(f"Sample 1 ({key})", key=f"{key}_1")
        with col2:
            v2 = st.text_input(f"Sample 2 ({key})", key=f"{key}_2")
        with col3:
            v3 = st.text_input(f"Sample 3 ({key})", key=f"{key}_3")
        input_data[key] = [v1, v2, v3]

    if st.button("Analyze Water Quality"):
        standards = {
            "pH": 7.0, "BOD5": 3, "DO": 6, "COD": 10, "Turbidity": 5,
            "TSS": 25, "NH3N": 1.0, "NO3": 10, "Temperature": 25,
            "Pb": 0.01, "As": 0.01
        }

        # WQI calculation using weighted average method
        weights = {k: 1 / v for k, v in standards.items()}
        q_sum, w_sum = 0, 0
        for param, samples in input_data.items():
            valid = [float(x) for x in samples if x.strip() != ""]
            if valid and param in standards:
                avg = sum(valid) / len(valid)
                qi = (avg / standards[param]) * 100
                q_sum += qi * weights[param]
                w_sum += weights[param]

        if w_sum > 0:
            wqi = q_sum / w_sum
            st.success(f"🌊 Water Quality Index (WQI): {wqi:.2f}")
            wqi_status = (
                "Excellent" if wqi <= 25 else
                "Good" if wqi <= 50 else
                "Poor" if wqi <= 75 else
                "Very Poor" if wqi <= 100 else "Unsuitable"
            )
            st.markdown(f"**Status**: {wqi_status}")
        else:
            st.warning("⚠️ Not enough valid data for WQI.")
            wqi, wqi_status = None, "N/A"

        # RPI
        def rpi_score(param, val):
            if param == "DO":
                return 1 if val >= 6.5 else 3 if val >= 4.6 else 6 if val >= 2.1 else 8
            if param == "BOD5":
                return 1 if val <= 3 else 3 if val <= 4.9 else 6 if val <= 9.9 else 8
            if param == "TSS":
                return 1 if val <= 20 else 3 if val <= 49.9 else 6 if val <= 99.9 else 8
            if param == "NH3N":
                return 1 if val <= 0.5 else 3 if val <= 0.99 else 6 if val <= 1.99 else 8

        rpi_scores = []
        for key in ["DO", "BOD5", "TSS", "NH3N"]:
            vals = input_data.get(key, [])
            valid = [float(v) for v in vals if v.strip() != ""]
            if valid:
                avg = sum(valid) / len(valid)
                rpi_scores.append(rpi_score(key, avg))
        if len(rpi_scores) == 4:
            rpi = sum(rpi_scores) / 4
            st.success(f"🧪 Pollution Index (RPI): {rpi:.2f}")
            rpi_status = (
                "Non/mildly polluted" if rpi <= 2 else
                "Lightly polluted" if rpi <= 3 else
                "Moderately polluted" if rpi <= 6 else
                "Severely polluted"
            )
            st.markdown(f"**Pollution Level**: {rpi_status}")
        else:
            rpi = None
            rpi_status = "N/A"
            st.warning("⚠️ Incomplete data for RPI.")

        # AI Report
        st.markdown("---")
        st.subheader("🧠 AI-Based Assessment & Suggestions")
        try:
            prompt = f"""
You are an environmental scientist. Given these test results from a {source_type.lower()} at {location}:

Test values:
{input_data}

1. Assess water suitability (drinking, irrigation, recreation).
2. Identify potential risks.
3. Recommend simple treatment methods to make the water potable or suitable for safe use.
Use WHO and ECR 2023 as reference standards.
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a water quality and environmental engineering expert."},
                    {"role": "user", "content": prompt}
                ]
            )
            ai_text = response.choices[0].message.content
            st.markdown(ai_text)
        except Exception as e:
            ai_text = f"AI Error: {e}"
            st.error(ai_text)

        # Downloadable Report
        st.markdown("---")
        st.subheader("📄 Download Report")
        if wqi and rpi and ai_text:
            summary = f"""
### AquaCortex 2.0 — Water Quality Report

**Water Source**: {source_name}
**Location**: {location}
**Type**: {source_type}
**GPS**: {gps_coords}

**Description**:
{description}

---

🌊 **WQI**: {wqi:.2f} → {wqi_status}  
🧪 **RPI**: {rpi:.2f} → {rpi_status}  

---

**🧠 AI Recommendations**:
{ai_text}
"""
            st.download_button(
                label="⬇️ Download Report (.txt)",
                data=summary,
                file_name="AquaCortex_Report.txt",
                mime="text/plain"
            )
