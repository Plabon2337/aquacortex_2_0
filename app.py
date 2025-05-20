import streamlit as st
import os
from openai import OpenAI
import requests

st.set_page_config(page_title="AquaCortex 2.0", page_icon="🌊", layout="wide")
st.title("💧 AquaCortex 2.0: Water Intelligence Platform")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

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

if mode == "📊 Test Data Analysis":
    st.subheader("📊 Enter Test Data")
    standards = {
        "pH": (7.0, 8.5), "BOD5": (0, 3), "DO": (14.6, 5), "COD": (0, 10), "Turbidity": (0, 5),
        "TSS": (0, 25), "NH3N": (0, 0.5), "NO3": (0, 10), "Temperature": (0, 25),
        "Pb": (0, 0.01), "As": (0, 0.01)
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
            wqi_status = (
                "Excellent" if wqi <= 25 else
                "Good" if wqi <= 50 else
                "Poor" if wqi <= 75 else
                "Very Poor" if wqi <= 100 else
                "Unsuitable"
            )
        else:
            wqi, wqi_status = None, "N/A"

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
            rpi_status = (
                "Non/mildly polluted" if rpi <= 2 else
                "Lightly polluted" if rpi <= 3 else
                "Moderately polluted" if rpi <= 6 else
                "Severely polluted"
            )
        else:
            rpi, rpi_status = None, "N/A"

        # AI Summary
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
            ai_report = response.choices[0].message.content.replace("\n", "<br>")
        except Exception as e:
            ai_report = f"AI Error: {e}"

        # Show results before printable block
        if wqi is not None:
            st.success(f"💧 Water Quality Index (WQI): {wqi:.2f} — {wqi_status}")
        else:
            st.warning("WQI could not be calculated.")

        if rpi is not None:
            st.success(f"🧪 River Pollution Index (RPI): {rpi:.2f} — {rpi_status}")
        else:
            st.warning("RPI could not be calculated.")

        st.subheader("🧠 AI-Based Analysis Report")
        st.markdown(ai_report, unsafe_allow_html=True)

        st.markdown("""
> 💡 **To save the below report as PDF:** Press **Ctrl + P** (or **Cmd + P** on Mac) → Choose **Save as PDF** → Click **Print**.
""")

        # Printable Report
        st.markdown(f"""
<div style='padding:15px; border:2px solid #ccc; border-radius:10px; background:#f9f9f9; font-family:Arial'>
<h2>AquaCortex 2.0 – Water Quality Report</h2>
<b>Water Source:</b> {source_name}<br>
<b>Location:</b> {location}<br>
<b>GPS:</b> {gps_coords}<br>
<b>Source Type:</b> {source_type}<br>
<b>Description:</b> {description}<br><hr>
<b>WQI:</b> {f"{wqi:.2f}" if wqi is not None else "N/A"} — <i>{wqi_status}</i><br>
<b>RPI:</b> {f"{rpi:.2f}" if rpi is not None else "N/A"} — <i>{rpi_status}</i><hr>
<h4>AI-Based Summary & Recommendation:</h4>
<div>{ai_report}</div>
</div>
""", unsafe_allow_html=True)

# AI Chat Mode
elif mode == "💬 AI Water Chat":
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
