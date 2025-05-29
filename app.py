import streamlit as st
import os
from openai import OpenAI
import requests

# --------------------- Page Setup ---------------------
st.set_page_config(page_title="AquaCortex 2.0", page_icon="🌊", layout="wide")
st.title("💧 AquaCortex 2.0: Water Intelligence Platform")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# --------------------- Sidebar Mode ---------------------
mode = st.sidebar.radio("Choose Mode", ["📊 Test Data Analysis", "💬 AI Water Chat"])

# --------------------- Water Source Inputs ---------------------
st.markdown("### 📝 Water Source Information")
col1, col2 = st.columns(2)
with col1:
    source_name = st.text_input("🌍 Water Source Name", key="src_name")
with col2:
    location = st.text_input("📍 Location", key="src_loc")
source_type = st.selectbox("💧 Type of Source", ["River", "Canal", "Lake", "Pond", "Ground Aquifer", "Tap", "Sewage Line", "Others"])
description = st.text_area("📝 Description", height=80)

gps_coords = "Not Available"
if location and GOOGLE_MAPS_API_KEY:
    try:
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API_KEY}"
        ).json()
        if response["status"] == "OK":
            latlng = response["results"][0]["geometry"]["location"]
            gps_coords = f"{latlng['lat']}, {latlng['lng']}"
            st.success(f"📍 GPS Coordinates: {gps_coords}")
    except:
        st.warning("❌ Unable to fetch GPS coordinates.")

# --------------------- Water Quality Standards ---------------------
standards = {
    "pH": ("-", "-"),
    "Temperature": ("-", "-"),
    "DO": (6.0, 5.0),
    "BOD5": (0.2, 3.0),
    "COD": (4.0, 10.0),
    "TSS": (0.0, 25.0),
    "Turbidity": (0.0, 5.0),
    "NH3N": (0.0, 0.5),
    "NO3": (0.0, 10.0),
    "Total Coliform": (0.0, 0.0),
    "Fecal Coliform": (0.0, 0.0),
    "As": (0.0, 0.01),
    "Pb": (0.0, 0.01),
    "Cr": (0.0, 0.05)
}

# --------------------- User Input ---------------------
if mode == "📊 Test Data Analysis":
    st.subheader("📊 Enter Test Data")
    input_data = {}

    for param, (ideal, standard) in standards.items():
        st.markdown(f"**{param} ({'mg/L' if 'Coliform' not in param else 'MPN/100mL'})**")
        values = []
        col1, col2, col3 = st.columns(3)
        values.append(col1.text_input("Sample 1", key=f"{param}_1"))
        values.append(col2.text_input("Sample 2", key=f"{param}_2"))
        values.append(col3.text_input("Sample 3", key=f"{param}_3"))

        parsed_vals = []
        for v in values:
            try:
                parsed_vals.append(float(v))
            except:
                pass
        input_data[param] = parsed_vals

    if st.button("Analyze Water Quality"):
        st.markdown("#### 💧 Basic Water Quality Index (BWQI)")

        ideal_vals = {"DO": 6.0, "BOD5": 0.2, "COD": 4.0}
        standard_vals = {"DO": 5.0, "BOD5": 3.0, "COD": 10.0}
        weights = {param: 1 / standard for param, standard in standard_vals.items()}

        bwqi = 0.0
        for param in ["DO", "BOD5", "COD"]:
            vals = input_data.get(param, [])
            if vals:
                vi = sum(vals) / len(vals)
                si = standard_vals[param]
                ii = ideal_vals[param]
                wi = weights[param]
                qi = abs((vi - si) / (si - ii)) * 100
                bwqi += qi * wi


        if bwqi <= 25:
            wqi_status = "Excellent"
        elif bwqi <= 50:
            wqi_status = "Good"
        elif bwqi <= 75:
            wqi_status = "Poor"
        elif bwqi <= 100:
            wqi_status = "Very Poor"
        else:
            wqi_status = "Unsuitable for use"

        st.success(f"BWQI Score: {bwqi:.2f} — {wqi_status}")

        st.markdown("#### 🧪 River Pollution Index (RPI)")

        def rpi_score(p, val):
            if p == "DO":
                return 1 if val >= 6.5 else 3 if val >= 4.6 else 6 if val >= 2.1 else 8
            elif p == "BOD5":
                return 1 if val <= 3 else 3 if val <= 4.9 else 6 if val <= 9.9 else 8
            elif p == "TSS":
                return 1 if val <= 20 else 3 if val <= 49.9 else 6 if val <= 99.9 else 8
            elif p == "NH3N":
                return 1 if val <= 0.5 else 3 if val <= 0.99 else 6 if val <= 1.99 else 8

        rpi_vals = []
        for param in ["DO", "BOD5", "TSS", "NH3N"]:
            vals = input_data.get(param, [])
            if vals:
                avg_val = sum(vals) / len(vals)
                rpi_vals.append(rpi_score(param, avg_val))

        if len(rpi_vals) == 4:
            rpi = sum(rpi_vals) / 4
            if rpi <= 2:
                rpi_status = "Non/mildly polluted"
            elif rpi <= 3:
                rpi_status = "Lightly polluted"
            elif rpi <= 6:
                rpi_status = "Moderately polluted"
            else:
                rpi_status = "Severely polluted"
            st.success(f"RPI Score: {rpi:.2f} — {rpi_status}")
        else:
            st.warning("❗ Not enough data to compute RPI.")

        st.subheader("🧠 AI-Based Analysis Report")
        try:
            prompt = f"""You are an expert in water quality and environmental pollution assessment. Analyze the following sample data from a {source_type} at {location}. Your analysis must include:
1. Overall water quality classification
2. Suitability for drinking, agriculture, recreation
3. Human and environmental health risks (e.g. presence of toxins, heavy metals, carcinogens, microbial threats)
4. Treatment methods to improve water quality – include both basic and advanced (chemical/technological) options

Parameters:
{input_data}
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            ai_report = response.choices[0].message.content
            st.markdown(ai_report)
        except Exception as e:
            st.error(f"AI Error: {e}")

elif mode == "💬 AI Water Chat":
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.subheader("💬 Ask AquaCortex")

    for entry in st.session_state.chat_history:
        st.markdown(f"**You:** {entry['user']}")
        st.markdown(f"**AquaCortex:** {entry['ai']}")

    user_input = st.text_input("Type your message here...")
    if st.button("Send") and user_input:
        try:
            st.session_state.chat_history.append({"user": user_input, "ai": "..."})
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a water, environmental, and civil engineering expert."}
                ] + [{"role": "user", "content": m["user"]} for m in st.session_state.chat_history]
            )
            ai_response = response.choices[0].message.content
            st.session_state.chat_history[-1]["ai"] = ai_response
            st.rerun()
        except Exception as e:
            st.error(f"AI Error: {e}")
