import streamlit as st
import os
import requests
from openai import OpenAI

# App setup
st.set_page_config(page_title="AquaCortex 2.1", page_icon="💧", layout="wide")
st.title("💧 AquaCortex 2.1: Water Intelligence Platform")

# OpenAI and Maps setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Sidebar mode selection
mode = st.sidebar.radio("Choose Mode", ["📊 Test Data Analysis", "💬 AI Water Chat"])

# Water source information
st.markdown("### 📝 Water Source Information")
col1, col2 = st.columns(2)
with col1:
    source_name = st.text_input("🌍 Water Source Name")
with col2:
    location = st.text_input("📍 Location")
source_type = st.selectbox("💧 Type of Source", ["River", "Canal", "Lake", "Pond", "Ground Aquifer", "Tap", "Sewage Line", "Others"])
description = st.text_area("📝 Description (optional)", height=80)

gps_coords = "Not Available"
if location and GOOGLE_MAPS_API_KEY:
    try:
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API_KEY}"
        ).json()
        if response["status"] == "OK":
            loc = response["results"][0]["geometry"]["location"]
            gps_coords = f"{loc['lat']}, {loc['lng']}"
            st.success(f"📍 GPS Coordinates: {gps_coords}")
    except:
        st.warning("❌ Could not fetch GPS coordinates.")

# ========== TEST DATA ANALYSIS ==========
if mode == "📊 Test Data Analysis":
    st.subheader("📊 Input Test Data (Up to 3 samples per parameter)")

    # Parameters
    parameters = {
        "pH": "–",
        "Temperature": "°C",
        "DO": "mg/L",
        "BOD₅": "mg/L",
        "COD": "mg/L",
        "TSS": "mg/L",
        "Turbidity": "NTU",
        "NH₃–N": "mg/L",
        "NO₃⁻": "mg/L",
        "Total Coliform": "CFU/100mL",
        "Fecal Coliform": "CFU/100mL",
        "Arsenic (As)": "mg/L",
        "Lead (Pb)": "mg/L",
        "Chromium (Cr)": "mg/L"
    }

    input_data = {}
    for param, unit in parameters.items():
        st.markdown(f"**{param} [{unit}]**")
        c1, c2, c3 = st.columns(3)
        inputs = []
        for i, c in enumerate([c1, c2, c3]):
            with c:
                val = st.text_input(f"Sample {i+1}", key=f"{param}_{i}")
                inputs.append(val)
        input_data[param] = inputs

    if st.button("Analyze Water Quality"):
        st.subheader("🧪 Analysis Results")

        # ---------- BWQI ----------
        st.markdown("#### 💧 Basic Water Quality Index (BWQI)")
        try:
            bwqi_params = {
                "DO": {"ideal": 5.0, "standard": 5.0},
                "BOD₅": {"ideal": 0.0, "standard": 3.0},
                "COD": {"ideal": 0.0, "standard": 10.0}
            }

            sum_wi_qi = 0
            sum_wi = 0

            for param, limits in bwqi_params.items():
                values = input_data.get(param, [])
                samples = [float(v) for v in values if v.strip()]
                if samples:
                    avg = sum(samples) / len(samples)
                    ideal = limits["ideal"]
                    std = limits["standard"]

                    if std == ideal:
                        continue  # Skip this parameter to avoid division by zero

                    qi = abs((avg - ideal) / (std - ideal)) * 100
                    qi = min(max(qi, 0), 100)  # Bound qi between 0–100
                    wi = 1 / std
                    sum_wi_qi += wi * qi
                    sum_wi += wi

            if sum_wi > 0:
                bwqi = round(sum_wi_qi / sum_wi, 2)
                bwqi_status = (
                    "Excellent" if bwqi <= 25 else
                    "Good" if bwqi <= 50 else
                    "Poor" if bwqi <= 75 else
                    "Very Poor" if bwqi <= 100 else
                    "Unsuitable"
                )
                st.success(f"BWQI Score: {bwqi} — {bwqi_status}")
            else:
                bwqi = None
                st.warning("BWQI could not be calculated due to missing or invalid values.")
        except Exception as e:
            st.error(f"BWQI Error: {e}")

        # ---------- RPI ----------
        st.markdown("#### 🧪 River Pollution Index (RPI)")
        def rpi_score(p, val):
            if p == "DO":
                return 1 if val >= 6.5 else 3 if val >= 4.6 else 6 if val >= 2.1 else 8
            if p == "BOD₅":
                return 1 if val <= 3 else 3 if val <= 4.9 else 6 if val <= 9.9 else 8
            if p == "TSS":
                return 1 if val <= 20 else 3 if val <= 49.9 else 6 if val <= 99.9 else 8
            if p == "NH₃–N":
                return 1 if val <= 0.5 else 3 if val <= 0.99 else 6 if val <= 1.99 else 8

        try:
            rpi_vals = []
            for key in ["DO", "BOD₅", "TSS", "NH₃–N"]:
                samples = [float(v) for v in input_data.get(key, []) if v.strip()]
                if samples:
                    avg = sum(samples) / len(samples)
                    score = rpi_score(key, avg)
                    rpi_vals.append(score)

            if len(rpi_vals) == 4:
                rpi = round(sum(rpi_vals) / 4, 2)
                rpi_status = (
                    "Non/mildly polluted" if rpi <= 2 else
                    "Lightly polluted" if rpi <= 3 else
                    "Moderately polluted" if rpi <= 6 else
                    "Severely polluted"
                )
                st.success(f"RPI Score: {rpi} — {rpi_status}")
            else:
                rpi = None
                st.warning("RPI could not be calculated (need all 4 parameters).")
        except Exception as e:
            st.error(f"RPI Error: {e}")

        # ---------- AI REPORT ----------
        st.markdown("#### 🧠 AI-Based Analysis & Treatment Suggestions")
        try:
            prompt = f"""
You are an environmental water quality expert. Given the test results for the following parameters:

{input_data}

Water Source: {source_name or "N/A"}
Location: {location or "N/A"} (GPS: {gps_coords})
Type: {source_type}

Provide:
1. Suitability for drinking, irrigation, recreation, and aquatic life
2. Any health or agricultural risks
3. Advanced and basic treatment recommendations
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            st.markdown(response.choices[0].message.content)
        except Exception as e:
            st.error(f"AI Error: {e}")

# ========== CHATBOT MODE ==========
elif mode == "💬 AI Water Chat":
    st.subheader("💬 Ask AquaCortex Anything (Water/Env/Civil Only)")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_msg = st.text_input("Ask your question:")
    if st.button("Send") and user_msg.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a water and environmental engineering expert."}]
                + st.session_state.chat_history
            )
            reply = response.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"Chat Error: {e}")

    for chat in st.session_state.chat_history:
        icon = "👤" if chat["role"] == "user" else "🤖"
        st.markdown(f"**{icon}**: {chat['content']}")
