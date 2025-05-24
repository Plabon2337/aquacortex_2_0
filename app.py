import streamlit as st
import os
import requests
from openai import OpenAI

# Page configuration
st.set_page_config(page_title="AquaCortex 2.1", page_icon="💧", layout="wide")
st.title("💧 AquaCortex 2.1: Water Intelligence Platform")

# Load API keys
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Mode selection
mode = st.sidebar.radio("Choose Mode", ["📊 Test Data Analysis", "💬 AI Water Chat"])

# --- Water Source Input Section ---
st.markdown("### 📝 Water Source Information")
col1, col2 = st.columns(2)
with col1:
    source_name = st.text_input("🌍 Water Source Name")
with col2:
    location = st.text_input("📍 Location")
source_type = st.selectbox("💧 Type of Source", ["River", "Canal", "Lake", "Pond", "Ground Aquifer", "Tap", "Sewage Line", "Others"])
description = st.text_area("📝 Description (optional)", height=80)

# GPS lookup
gps_coords = "Not Available"
if location and GOOGLE_MAPS_API_KEY:
    try:
        response = requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API_KEY}").json()
        if response["status"] == "OK":
            coords = response["results"][0]["geometry"]["location"]
            gps_coords = f"{coords['lat']}, {coords['lng']}"
            st.success(f"📍 GPS Coordinates: {gps_coords}")
    except:
        st.warning("❌ Failed to fetch GPS coordinates.")

# --- Test Data Analysis Mode ---
if mode == "📊 Test Data Analysis":
    st.subheader("📊 Enter Test Parameters (up to 3 samples each)")

    # Parameter definitions with units
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
        values = []
        for i, col in enumerate([c1, c2, c3]):
            with col:
                val = st.text_input(f"Sample {i+1}", key=f"{param}_{i}")
                values.append(val)
        input_data[param] = values

    if st.button("Analyze Water Quality"):
        st.subheader("🔍 Results")

        # --- BWQI Calculation ---
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
                vals = input_data.get(param, [])
                clean_vals = [float(v) for v in vals if v.strip()]
                if clean_vals:
                    avg = sum(clean_vals) / len(clean_vals)
                    q_i = abs((avg - limits["ideal"]) / (limits["standard"] - limits["ideal"])) * 100
                    q_i = min(max(q_i, 0), 100)
                    w_i = 1 / limits["standard"]
                    sum_wi_qi += w_i * q_i
                    sum_wi += w_i
            bwqi = round(sum_wi_qi / sum_wi, 2) if sum_wi else None
            bwqi_status = (
                "Excellent" if bwqi <= 25 else
                "Good" if bwqi <= 50 else
                "Poor" if bwqi <= 75 else
                "Very Poor" if bwqi <= 100 else
                "Unsuitable"
            )
            st.success(f"BWQI Score: {bwqi} — {bwqi_status}" if bwqi is not None else "BWQI could not be calculated.")
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
            rpi_total = 0
            rpi_count = 0
            for key in ["DO", "BOD₅", "TSS", "NH₃–N"]:
                samples = [float(v) for v in input_data.get(key, []) if v.strip()]
                if samples:
                    avg = sum(samples) / len(samples)
                    rpi_total += rpi_score(key, avg)
                    rpi_count += 1
            rpi = round(rpi_total / rpi_count, 2) if rpi_count == 4 else None
            rpi_status = (
                "Non/mildly polluted" if rpi <= 2 else
                "Lightly polluted" if rpi <= 3 else
                "Moderately polluted" if rpi <= 6 else
                "Severely polluted"
            )
            st.success(f"RPI Score: {rpi} — {rpi_status}" if rpi is not None else "RPI could not be calculated.")
        except Exception as e:
            st.error(f"RPI Error: {e}")

        # --- AI Assessment ---
        st.markdown("#### 🧠 AI-Based Suitability Analysis & Treatment Recommendation")
        try:
            prompt = f"""
You are an expert water and environmental engineer. Analyze the following test data from a {source_type} at {location}.

Parameters:
{input_data}

Respond with:
1. Suitability for drinking, recreation, irrigation, aquatic use
2. Harmful risks to health (e.g., heavy metals, microplastics, pathogens)
3. Potential agricultural effects
4. Suggested treatment options (basic + advanced)

Source name: {source_name or "N/A"}
Location: {location or "N/A"}
GPS Coordinates: {gps_coords}
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            ai_output = response.choices[0].message.content
            st.markdown(ai_output)
        except Exception as e:
            st.error(f"AI Analysis Error: {e}")

# --- AI Water Chat Mode ---
elif mode == "💬 AI Water Chat":
    st.subheader("💬 Chat with AquaCortex")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Ask a question (water/environment/civil related only):")
    if st.button("Send") and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in water quality and environmental engineering."}
                ] + st.session_state.chat_history
            )
            reply = response.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"Chat Error: {e}")

    for chat in st.session_state.chat_history:
        icon = "👤" if chat["role"] == "user" else "🤖"
        st.markdown(f"**{icon}**: {chat['content']}")
