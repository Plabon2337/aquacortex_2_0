import streamlit as st
import os
import requests
from openai import OpenAI

st.set_page_config(page_title="AquaCortex 2.1", page_icon="🌊", layout="wide")
st.title("AquaCortex 2.1: Water Intelligence Platform")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

mode = st.sidebar.radio("Choose Mode", ["Test Data Analysis", "AI Water Chat"])

if mode == "Test Data Analysis":
    st.markdown("### 📝 Water Source Information")
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

    st.markdown("### 🔢 Enter Sample Data (up to 3 samples per parameter)")
    parameters = {
        "pH": "-", "Temperature": "°C", "DO": "mg/L", "BOD5": "mg/L",
        "COD": "mg/L", "TSS": "mg/L", "Turbidity": "NTU", "NH3-N": "mg/L",
        "NO3-N": "mg/L", "Total Coliform": "CFU/100mL", "Fecal Coliform": "CFU/100mL",
        "Arsenic (As)": "mg/L", "Lead (Pb)": "mg/L", "Chromium (Cr)": "mg/L"
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
        st.markdown("### 🌊 Basic Water Quality Index (BWQI)")
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

        st.markdown("### 🧪 River Pollution Index (RPI)")
        def rpi_score(p, val):
            if p == "DO (mg/L)": return 1 if val >= 6.5 else 3 if val >= 4.6 else 6 if val >= 2.1 else 8
            if p == "BOD5 (mg/L)": return 1 if val <= 3 else 3 if val <= 4.9 else 6 if val <= 9.9 else 8
            if p == "TSS (mg/L)": return 1 if val <= 20 else 3 if val <= 49.9 else 6 if val <= 99.9 else 8
            if p == "NH3-N (mg/L)": return 1 if val <= 0.5 else 3 if val <= 0.99 else 6 if val <= 1.99 else 8

        rpi_vals = []
        for key in ["DO (mg/L)", "BOD5 (mg/L)", "TSS (mg/L)", "NH3-N (mg/L)"]:
            vals = input_data.get(key, [])
            valid = [float(v) for v in vals if v.strip()]
            if valid:
                avg = sum(valid) / len(valid)
                rpi_vals.append(rpi_score(key, avg))

        if len(rpi_vals) == 4:
            rpi = sum(rpi_vals) / 4
            rpi_status = "Non/mildly polluted" if rpi <= 2 else "Lightly polluted" if rpi <= 3 else "Moderately polluted" if rpi <= 6 else "Severely polluted"
            st.success(f"RPI: {rpi:.2f} — {rpi_status}")
        else:
            st.warning("Not enough data to calculate RPI.")

        st.subheader("🧠 AI-Based Water Quality Assessment")
        try:
            prompt = f"""
You are a professional water quality engineer. Based on the following sample test results for water collected from a {source_type} at {location}, write a structured technical analysis:

1. **Water Quality Analysis**:
   - Evaluate the overall condition of the water.
   - Identify suitability for **drinking**, **irrigation**, and **recreational** use.

2. **Human and Agricultural Risk**:
   - Discuss potential health risks if the water is used for drinking or recreation.
   - Highlight any concerns related to heavy metals, toxins, carcinogens, microplastics, or pathogens.
   - Predict possible crop-related issues (e.g., growth retardation, yield loss, toxicity in vegetables/fruits).

3. **Treatment Recommendations**:
   - Suggest **basic, low-cost methods** (e.g., filtration, boiling, sedimentation).
   - Recommend **advanced or chemical-based treatments** where necessary.
   - Mention any **innovative or emerging treatment options** if applicable.

Input Data:
{input_data}
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a water quality expert."}, {"role": "user", "content": prompt}]
            )
            ai_text = response.choices[0].message.content
            st.markdown(ai_text)
        except Exception as e:
            st.error(f"OpenAI API error: {e}")

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
