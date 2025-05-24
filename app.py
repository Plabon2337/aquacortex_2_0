import streamlit as st
import os
import requests
from openai import OpenAI

st.set_page_config(page_title="AquaCortex 2.1", page_icon="🌊", layout="wide")
st.title("AquaCortex 2.1: Water Intelligence Platform")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Sidebar Mode Selection
mode = st.sidebar.radio("Choose Mode", ["Test Data Analysis", "AI Water Chat"])

# ------------------------- INPUT SECTION -----------------------------
if mode == "Test Data Analysis":
    st.markdown("### 📅 Water Source Information")
    col1, col2 = st.columns(2)
    with col1:
        source_name = st.text_input("Water Source Name")
    with col2:
        location = st.text_input("Location")

    source_type = st.selectbox("Type of Water Source", [
        "River", "Canal", "Lake", "Pond", "Ground Aquifer", "Tap", "Sewage Line", "Others"])
    description = st.text_area("Description (Optional)", height=80)

    gps_coords = "Not Available"
    if location and GOOGLE_MAPS_API_KEY:
        try:
            response = requests.get(
                f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API_KEY}"
            ).json()
            if response["status"] == "OK":
                latlng = response["results"][0]["geometry"]["location"]
                gps_coords = f"{latlng['lat']}, {latlng['lng']}"
                st.success(f"GPS Coordinates: {gps_coords}")
        except:
            st.warning("Unable to fetch GPS coordinates.")

    # --------------------- PARAMETER INPUT ---------------------------
    st.markdown("### 🔢 Enter Sample Data (up to 3 samples per parameter)")

    parameters = {
        "pH": "-", "Temperature (°C)": "°C", "DO (mg/L)": "mg/L", "BOD5 (mg/L)": "mg/L",
        "COD (mg/L)": "mg/L", "TSS (mg/L)": "mg/L", "Turbidity (NTU)": "NTU", "NH3-N (mg/L)": "mg/L",
        "NO3-N (mg/L)": "mg/L", "Total Coliform (CFU/100mL)": "CFU/100mL", "Fecal Coliform (CFU/100mL)": "CFU/100mL",
        "Arsenic (As, mg/L)": "mg/L", "Lead (Pb, mg/L)": "mg/L", "Chromium (Cr, mg/L)": "mg/L"
    }

    input_data = {}
    for param, unit in parameters.items():
        st.markdown(f"**{param} ({unit})**")
        col1, col2, col3 = st.columns(3)
        v1 = col1.text_input(f"Sample 1", key=f"{param}_1")
        v2 = col2.text_input(f"Sample 2", key=f"{param}_2")
        v3 = col3.text_input(f"Sample 3", key=f"{param}_3")
        input_data[param] = [v1, v2, v3]

    if st.button("Analyze Water Quality"):
        st.markdown("### 💧 Basic Water Quality Index (BWQI)")
        ideal_values = {"DO (mg/L)": 5.0, "BOD5 (mg/L)": 0.0, "COD (mg/L)": 0.0}
        std_values = {"DO (mg/L)": 5.0, "BOD5 (mg/L)": 3.0, "COD (mg/L)": 10.0}

        total_weighted_qi = 0
        total_weights = 0

        for param in ["DO (mg/L)", "BOD5 (mg/L)", "COD (mg/L)"]:
            values = [float(v) for v in input_data[param] if v.strip()]
            if values:
                avg = sum(values) / len(values)
                ideal = ideal_values[param]
                std = std_values[param]
                wi = 1 / std
                qi = abs((avg - ideal) / (std - ideal)) * 100 if std != ideal else 0
                qi = max(0, min(qi, 100))
                total_weighted_qi += wi * qi
                total_weights += wi

        if total_weights > 0:
            bwqi = total_weighted_qi / total_weights
            status = "Excellent" if bwqi <= 25 else "Good" if bwqi <= 50 else "Poor" if bwqi <= 75 else "Very Poor" if bwqi <= 100 else "Unsuitable"
            st.success(f"BWQI: {bwqi:.2f} — {status}")
        else:
            st.warning("Not enough data to calculate BWQI")

        # (RPI & AI report already included in prior section)

elif mode == "AI Water Chat":
    st.subheader("💬 AquaCortex Live Chat")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "system", "content": "You are a water/environment/civil engineering expert. Reply only on those topics."}
        ]

    for msg in st.session_state.chat_history[1:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask your question here...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.chat_history
            )
            reply = response.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
        except Exception as e:
            st.error(f"OpenAI API Error: {e}")
