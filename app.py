import streamlit as st
import os
import requests
from openai import OpenAI

# --- Page Setup ---
st.set_page_config(page_title="AquaCortex 2.1", page_icon="💧", layout="wide")
st.title("💧 AquaCortex 2.1: Water Intelligence Platform")

# --- API Setup ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# --- Mode Selection ---
mode = st.sidebar.radio("Choose Mode", ["📊 Test Data Analysis", "💬 AI Water Chat"])

# --- Water Source Information ---
st.markdown("### 📝 Water Source Information")
col1, col2 = st.columns(2)
with col1:
    source_name = st.text_input("🌍 Water Source Name")
with col2:
    location = st.text_input("📍 Location")
source_type = st.selectbox("💧 Type of Source", ["River", "Canal", "Lake", "Pond", "Ground Aquifer", "Tap", "Sewage Line", "Others"])
description = st.text_area("📝 Description (optional)", height=80)

# --- GPS Coordinates ---
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

# --- Test Data Analysis Mode ---
if mode == "📊 Test Data Analysis":
    st.subheader("📊 Enter Test Parameters (max 3 samples each)")

    parameters = {
        "pH": "–", "Temperature": "°C", "DO": "mg/L", "BOD₅": "mg/L", "COD": "mg/L",
        "TSS": "mg/L", "Turbidity": "NTU", "NH₃–N": "mg/L", "NO₃⁻": "mg/L",
        "Total Coliform": "CFU/100mL", "Fecal Coliform": "CFU/100mL", "Arsenic (As)": "mg/L",
        "Lead (Pb)": "mg/L", "Chromium (Cr)": "mg/L"
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
        st.subheader("🔍 Results")

        # --- BWQI Calculation ---
        st.markdown("#### 💧 Basic Water Quality Index (BWQI)")
        try:
            bwqi_params = {
                "DO": {"ideal": 0.0, "standard": 5.0, "type": "positive"},
                "BOD₅": {"ideal": 0.0, "standard": 3.0, "type": "negative"},
                "COD": {"ideal": 0.0, "standard": 10.0, "type": "negative"}
            }

            sum_wi_qi = 0
            sum_wi = 0

            for param, limits in bwqi_params.items():
                samples = [float(v) for v in input_data.get(param, []) if v.strip()]
                if samples:
                    avg = sum(samples) / len(samples)
                    S = limits["standard"]
                    I = limits["ideal"]
                    if S == I:
                        continue  # avoid division by zero
                    wi = 1 / S
                    if limits["type"] == "positive":
                        qi = ((S - avg) / (S - I)) * 100
                    else:
                        qi = ((avg - I) / (S - I)) * 100
                    qi = max(0, min(qi, 100))
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
                st.warning("Insufficient data for BWQI.")
        except Exception as e:
            st.error(f"BWQI Error: {e}")

        # --- RPI Calculation ---
        st.markdown("#### 🧪 River Pollution Index (RPI)")
        def rpi_score(p, v):
            if p == "DO":
                return 1 if v >= 6.5 else 3 if v >= 4.6 else 6 if v >= 2.1 else 8
            if p == "BOD₅":
                return 1 if v <= 3 else 3 if v <= 4.9 else 6 if v <= 9.9 else 8
            if p == "TSS":
                return 1 if v <= 20 else 3 if v <= 49.9 else 6 if v <= 99.9 else 8
            if p == "NH₃–N":
                return 1 if v <= 0.5 else 3 if v <= 0.99 else 6 if v <= 1.99 else 8

        try:
            rpi_vals = []
            for key in ["DO", "BOD₅", "TSS", "NH₃–N"]:
                samples = [float(v) for v in input_data.get(key, []) if v.strip()]
                if samples:
                    avg = sum(samples) / len(samples)
                    rpi_vals.append(rpi_score(key, avg))

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
                st.warning("RPI could not be calculated. All 4 parameters required.")
        except Exception as e:
            st.error(f"RPI Error: {e}")

        # --- AI Analysis ---
        st.markdown("#### 🧠 AI Analysis & Treatment Suggestions")
        try:
            prompt = f"""
You are a water/environmental engineer. Analyze the water test results below.

Source Type: {source_type}
Location: {location}
GPS: {gps_coords}
Parameters: {input_data}

Provide:
1. Suitability for drinking, irrigation, recreation, aquatic life
2. Health/environmental risks
3. Suggested treatments (basic + advanced)
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            st.markdown(response.choices[0].message.content)
        except Exception as e:
            st.error(f"AI Error: {e}")

# --- Chat Mode ---
elif mode == "💬 AI Water Chat":
    st.subheader("💬 Ask AquaCortex")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_q = st.text_input("Ask your question:")
    if st.button("Send") and user_q.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a civil/environmental/water expert."}] +
                         st.session_state.chat_history
            )
            reply = response.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"Chat Error: {e}")

    for msg in st.session_state.chat_history:
        icon = "👤" if msg["role"] == "user" else "🤖"
        st.markdown(f"**{icon}**: {msg['content']}")
