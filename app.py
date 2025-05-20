import streamlit as st
import os
from openai import OpenAI
import requests
from fpdf import FPDF
import matplotlib.pyplot as plt
import tempfile

# Page setup
st.set_page_config(page_title="AquaCortex 2.0", page_icon="🌊", layout="wide")
st.title("💧 AquaCortex 2.0: Water Intelligence Platform")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Sidebar mode
mode = st.sidebar.radio("Choose Mode", ["📊 Test Data Analysis", "💬 AI Water Chat"])

# Source Info
st.markdown("### 📝 Water Source Information")
col1, col2 = st.columns(2)
with col1:
    source_name = st.text_input("🌍 Water Source Name", key="src_name")
with col2:
    location = st.text_input("📍 Location", key="src_loc")
source_type = st.selectbox("💧 Type of Source", ["River", "Canal", "Lake", "Pond", "Ground Aquifer", "Tap", "Sewage Line", "Others"])
description = st.text_area("📝 Description", height=80)

# GPS Coordinates
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

if mode == "💬 AI Water Chat":
    st.subheader("💬 Ask AquaCortex")
    question = st.text_input("Your question (only water/env/civil related)")
    if st.button("Ask"):
        if question.strip():
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a water/environment/civil engineering expert."},
                        {"role": "user", "content": question}
                    ]
                )
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"API Error: {e}")
        else:
            st.warning("❗ Please type your question.")

elif mode == "📊 Test Data Analysis":
    st.subheader("📊 Enter Test Data")
    standards = {
        "pH": (7.0, 8.5), "BOD5": (0, 3), "DO": (14.6, 5), "COD": (0, 10), "Turbidity": (0, 5),
        "TSS": (0, 25), "NH3N": (0, 0.5), "NO3": (0, 10), "Temperature": (0, 25), "Pb": (0, 0.01), "As": (0, 0.01)
    }

    input_data = {}
    for label in standards:
        st.markdown(f"**{label}**")
        col1, col2, col3 = st.columns(3)
        with col1:
            v1 = st.text_input(f"Sample 1 ({label})", key=f"{label}_1")
        with col2:
            v2 = st.text_input(f"Sample 2 ({label})", key=f"{label}_2")
        with col3:
            v3 = st.text_input(f"Sample 3 ({label})", key=f"{label}_3")
        input_data[label] = [v1, v2, v3]

    if st.button("Analyze Water Quality"):
        st.markdown("### 🌊 Water Quality Index (WQI)")
        weights = {k: 1 / standards[k][1] for k in standards}
        sum_wi_qi = 0
        sum_wi = 0

        for param, (ideal, std) in standards.items():
            values = [float(v) for v in input_data[param] if v.strip()]
            if values:
                vi = sum(values) / len(values)
                v0 = ideal
                si = std
                qi = abs((vi - v0) / (si - v0)) * 100
                wi = 1 / si
                sum_wi_qi += wi * qi
                sum_wi += wi

        if sum_wi > 0:
            wqi = sum_wi_qi / sum_wi
            st.success(f"WQI (Weighted Arithmetic): {wqi:.2f}")
            wqi_status = (
                "Excellent" if wqi <= 25 else "Good" if wqi <= 50 else
                "Poor" if wqi <= 75 else "Very Poor" if wqi <= 100 else "Unsuitable"
            )
            st.markdown(f"**Status**: {wqi_status}")
        else:
            st.warning("Not enough data for WQI.")
            wqi = None
            wqi_status = "N/A"

        # RPI
        def rpi_score(p, val):
            if p == "DO":
                return 1 if val >= 6.5 else 3 if val >= 4.6 else 6 if val >= 2.1 else 8
            if p == "BOD5":
                return 1 if val <= 3 else 3 if val <= 4.9 else 6 if val <= 9.9 else 8
            if p == "TSS":
                return 1 if val <= 20 else 3 if val <= 49.9 else 6 if val <= 99.9 else 8
            if p == "NH3N":
                return 1 if val <= 0.5 else 3 if val <= 0.99 else 6 if val <= 1.99 else 8

        rpi_vals = []
        for key in ["DO", "BOD5", "TSS", "NH3N"]:
            vals = input_data.get(key, [])
            valid = [float(v) for v in vals if v.strip()]
            if valid:
                avg = sum(valid) / len(valid)
                rpi_vals.append(rpi_score(key, avg))

        if len(rpi_vals) == 4:
            rpi = sum(rpi_vals) / 4
            st.success(f"🧪 River Pollution Index (RPI): {rpi:.2f}")
            rpi_status = (
                "Non/mildly polluted" if rpi <= 2 else "Lightly polluted" if rpi <= 3 else
                "Moderately polluted" if rpi <= 6 else "Severely polluted"
            )
            st.markdown(f"**Pollution Status**: {rpi_status}")
        else:
            rpi = None
            rpi_status = "N/A"

        # AI Report
        st.subheader("🧠 AI Summary")
        try:
            prompt = f"""You are an environmental expert. Analyze the following water test results for a {source_type} at {location}.
Suggest:
1. Suitability (drinking, irrigation, recreation, etc.)
2. Risks involved
3. Simple treatment options

Values:
{input_data}
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            ai_report = response.choices[0].message.content
            st.markdown(ai_report)
        except Exception as e:
            ai_report = "API ERROR"
            st.error(ai_report)

        # PDF Report
        st.subheader("📄 Download PDF Report")
        if st.button("📥 Generate PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "AquaCortex 2.0 - Water Report", ln=True, align="C")

            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, f"Source: {source_name}
Location: {location}
GPS: {gps_coords}
Type: {source_type}
Description: {description}")
            pdf.ln()

            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"WQI: {wqi:.2f} ({wqi_status})", ln=True)
            pdf.cell(0, 10, f"RPI: {rpi:.2f} ({rpi_status})", ln=True)
            pdf.ln()
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 10, ai_report)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                pdf.output(tmp_file.name)
                with open(tmp_file.name, "rb") as f:
                    st.download_button("📎 Download PDF", data=f, file_name="AquaCortex_Report.pdf", mime="application/pdf")
