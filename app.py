import streamlit as st
import os
from openai import OpenAI
import requests

# Set up the page
st.set_page_config(page_title="AquaCortex 2.0", page_icon="🌊", layout="wide")
st.title("💧 AquaCortex 2.0: Water Intelligence Platform")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Sidebar mode selector
mode = st.sidebar.radio(
    "Select Mode:",
    ("💬 AI-Assisted Chat", "📊 Water Test Data Analysis")
)

# ─────────────────────────────
# Common Input Block: Water Source Info (Visible for Both Modes)
# ─────────────────────────────
st.markdown("### 📝 Water Source Information")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        source_name = st.text_input("🌍 Water Source Name (e.g., Turag River)", key="src_name")
    with col2:
        location = st.text_input("📍 Location (e.g., Mirpur Bridge)", key="src_loc")

source_type = st.selectbox("💧 Type of Water Source", [
    "River", "Canal", "Lake", "Pond", "Ground Aquifer", "Tap", "Sewage Line", "Others"
])

description = st.text_area("📝 Short Description or Site Notes", key="src_desc", height=80)

# Fetch GPS Coordinates using Google Maps Geocoding API (you must replace with your own API key)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
gps_coords = "Not Available"
if location and GOOGLE_MAPS_API_KEY:
    try:
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API_KEY}"
        )
        geo_data = response.json()
        if geo_data["status"] == "OK":
            latlng = geo_data["results"][0]["geometry"]["location"]
            gps_coords = f"{latlng['lat']}, {latlng['lng']}"
            st.success(f"📍 GPS Coordinates: {gps_coords}")
        else:
            st.warning("⚠️ Could not find GPS location. Try refining your location name.")
    except Exception as e:
        st.error("❌ Error fetching coordinates.")

# ─────────────────────────────
# Mode 1: AI-Assisted Chat
# ─────────────────────────────
if mode == "💬 AI-Assisted Chat":
    st.subheader("💬 Ask AquaCortex")
    user_input = st.text_input("Ask about water quality, pollution, treatment, or civil/environmental engineering:")

    if st.button("Ask"):
        if any(kw in user_input.lower() for kw in [
            "water", "pollution", "river", "treatment", "ecology", "climate",
            "irrigation", "quality", "groundwater", "civil", "wastewater", "hydrology", "environment"
        ]):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant who only answers questions related to water quality, environment, and civil engineering."},
                        {"role": "user", "content": user_input}
                    ]
                )
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"OpenAI API error: {e}")
        else:
            st.warning("❌ AquaCortex only responds to water, environment, or civil engineering questions.")

# ─────────────────────────────
# Mode 2: Water Test Data Analysis
# ─────────────────────────────
elif mode == "📊 Water Test Data Analysis":
    st.subheader("📊 Water Quality Index & Pollution Index Tool")

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
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            val1 = st.text_input(f"Sample 1 ({key})", key=f"{key}_1")
        with col2:
            val2 = st.text_input(f"Sample 2 ({key})", key=f"{key}_2")
        with col3:
            val3 = st.text_input(f"Sample 3 ({key})", key=f"{key}_3")
        input_data[key] = [val1, val2, val3]

    if st.button("Analyze Water Quality"):
        st.success("🧠 AI Analysis, WQI, and RPI logic goes here.")
        st.info("Due to space, this code includes input fields + GPS. Insert analysis code here.")
