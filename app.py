import streamlit as st
import os
from openai import OpenAI

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
        total_inputs = sum(1 for param in input_data.values() for v in param if v.strip() != "")
        st.info(f"✅ You provided {total_inputs} test values.")
        if total_inputs < 3:
            st.warning("⚠️ Please enter at least 3 valid values for WQI calculation.")

        standards = {
            "pH": 7.0, "BOD5": 3, "DO": 6, "COD": 10, "Turbidity": 5,
            "TSS": 25, "NH3N": 1.0, "NO3": 10, "Temperature": 25,
            "Pb": 0.01, "As": 0.01
        }

        weights = {k: 1/v for k, v in standards.items()}
        q_values = []
        w_values = []

        for param, samples in input_data.items():
            valid = [float(v) for v in samples if v.strip() != ""]
            if valid and param in standards:
                avg = sum(valid) / len(valid)
                q = (avg / standards[param]) * 100
                q_values.append(q * weights[param])
                w_values.append(weights[param])

        if len(q_values) >= 3:
            wqi = sum(q_values) / sum(w_values)
            st.success(f"🌊 Water Quality Index (WQI): {wqi:.2f}")
            wqi_status = ("Excellent" if wqi <= 25 else "Good" if wqi <= 50 else
                          "Poor" if wqi <= 75 else "Very Poor" if wqi <= 100 else "Unsuitable")
            st.markdown(f"Status: {wqi_status}")
        else:
            st.warning("⚠️ Not enough valid parameters to calculate WQI.")
            wqi = None
            wqi_status = "N/A"

        def get_rpi_score(param, value):
            if param == "DO":
                return 1 if value >= 6.5 else 3 if value >= 4.6 else 6 if value >= 2.1 else 8
            elif param == "BOD5":
                return 1 if value <= 3.0 else 3 if value <= 4.9 else 6 if value <= 9.9 else 8
            elif param == "TSS":
                return 1 if value <= 20 else 3 if value <= 49.9 else 6 if value <= 99.9 else 8
            elif param == "NH3N":
                return 1 if value <= 0.5 else 3 if value <= 0.99 else 6 if value <= 1.99 else 8

        rpi_scores = []
        for key in ["DO", "BOD5", "TSS", "NH3N"]:
            values = input_data.get(key, [])
            valid = [float(v) for v in values if v.strip() != ""]
            if valid:
                avg = sum(valid) / len(valid)
                rpi_scores.append(get_rpi_score(key, avg))

        if len(rpi_scores) == 4:
            rpi = sum(rpi_scores) / 4
            st.success(f"🧪 Pollution Index (RPI): {rpi:.2f}")
            rpi_status = ("Non/mildly polluted" if rpi <= 2 else "Lightly polluted" if rpi <= 3
                          else "Moderately polluted" if rpi <= 6 else "Severely polluted")
            st.markdown(f"Pollution Level: {rpi_status}")
        else:
            st.warning("⚠️ Need DO, BOD₅, TSS, and NH₃-N for RPI.")
            rpi = None
            rpi_status = "N/A"

        st.markdown("---")
        st.subheader("🧠 AI-Based Report")

        prompt = f"""
You are an expert environmental engineer. Analyze the following river water quality test results and provide:
1. Suitability for use (drinking, irrigation, recreation, etc.)
2. Health/environmental risks
3. Simple treatment methods.

Test data:
{input_data}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that only answers water, environmental, and civil engineering-related questions."},
                    {"role": "user", "content": prompt}
                ]
            )
            ai_text = response.choices[0].message.content
            st.markdown(ai_text)
        except Exception as e:
            ai_text = None
            st.error(f"OpenAI API error: {e}")

        st.markdown("---")
        st.subheader("📝 Source Info + Printable Summary")

        source_name = st.text_input("Water Source Name", key="src_name")
        location = st.text_input("Location", key="src_loc")
        description = st.text_area("Short Description", key="src_desc")

        if wqi and rpi and ai_text:
            if st.button("📄 Generate Printable Summary"):
                summary = f"""
### AquaCortex 2.0 — Water Quality Report

**Water Source**: {source_name or 'N/A'}
**Location**: {location or 'N/A'}

**Short Description**:
{description or 'N/A'}

---

**🌊 WQI**: {wqi:.2f}  |  Status: {wqi_status}
**🧪 RPI**: {rpi:.2f}  |  Status: {rpi_status}

---

**🧠 AI Summary & Treatment Suggestion**:
{ai_text}
"""
                st.download_button(
                    label="⬇️ Download Report (.txt)",
                    data=summary,
                    file_name="AquaCortex_Report.txt",
                    mime="text/plain"
                )
                st.markdown("✅ Report generated successfully.")
