import streamlit as st
import os
from openai import OpenAI

# Set up the page
st.set_page_config(page_title="AquaCortex 2.0", layout="centered")
st.title("💧 AquaCortex 2.0: Water Intelligence Platform")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Sidebar mode selector
mode = st.sidebar.radio(
    "Select Mode:",
    ("💬 AI-Assisted Chat", "📊 Water Test Data Analysis")
)

# ─────────────────────────────
# Mode 1: AI-Assisted Chat
# ─────────────────────────────
if mode == "💬 AI-Assisted Chat":
    st.subheader("💬 AI Assistant — Water, Environment & Civil Engineering Only")
    user_input = st.text_input("Ask a question related to water, environment, or civil engineering:")

    if st.button("Ask"):
        if any(kw in user_input.lower() for kw in ["water", "pollution", "river", "treatment", "ecology", "climate", "irrigation", "quality", "groundwater", "civil", "wastewater", "hydrology", "environment"]):
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
            st.warning("❌ This assistant only responds to questions about water, environment, or civil engineering.")

# ─────────────────────────────
# Mode 2: Water Test Data Analysis
# ─────────────────────────────
elif mode == "📊 Water Test Data Analysis":
    st.subheader("📊 Water Quality Index & Pollution Index Tool")
    st.markdown("Enter your water quality test results. You may leave any field blank.")

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
        col1, col2, col3 = st.columns(3)
        with col1:
            val1 = st.text_input(f"{label} - Sample 1", key=f"{key}_1")
        with col2:
            val2 = st.text_input(f"{label} - Sample 2", key=f"{key}_2")
        with col3:
            val3 = st.text_input(f"{label} - Sample 3", key=f"{key}_3")
        input_data[key] = [val1, val2, val3]

    if st.button("Analyze Water Quality"):
        total_inputs = sum(
            1 for param in input_data.values()
            for v in param if v.strip() != ""
        )
        st.info(f"✅ You provided {total_inputs} individual test values.")
        if total_inputs < 3:
            st.warning("⚠️ Very few parameters entered. WQI and RPI may not be reliable. Consider adding more data.")

        # WQI CALCULATION
        standards = {
            "pH": 7.0,
            "BOD5": 3,
            "DO": 6,
            "COD": 10,
            "Turbidity": 5,
            "TSS": 25,
            "NH3N": 1.0,
            "NO3": 10,
            "Temperature": 25,
            "Pb": 0.01,
            "As": 0.01
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
            st.success(f"🌊 **Water Quality Index (WQI): {wqi:.2f}**")
            if wqi <= 25:
                st.markdown("✅ Status: **Excellent**")
            elif wqi <= 50:
                st.markdown("✅ Status: **Good**")
            elif wqi <= 75:
                st.markdown("⚠️ Status: **Poor**")
            elif wqi <= 100:
                st.markdown("❌ Status: **Very Poor**")
            else:
                st.markdown("🚨 Status: **Unsuitable for use**")
        else:
            st.warning("⚠️ Not enough valid data to calculate WQI. Please enter at least 3 key parameters.")

        # RPI CALCULATION
        def get_rpi_score(param, value):
            if param == "DO":
                if value >= 6.5: return 1
                elif value >= 4.6: return 3
                elif value >= 2.1: return 6
                else: return 8
            elif param == "BOD5":
                if value <= 3.0: return 1
                elif value <= 4.9: return 3
                elif value <= 9.9: return 6
                else: return 8
            elif param == "TSS":
                if value <= 20: return 1
                elif value <= 49.9: return 3
                elif value <= 99.9: return 6
                else: return 8
            elif param == "NH3N":
                if value <= 0.5: return 1
                elif value <= 0.99: return 3
                elif value <= 1.99: return 6
                else: return 8
            return None

        rpi_scores = []
        for key in ["DO", "BOD5", "TSS", "NH3N"]:
            samples = input_data.get(key, [])
            valid = [float(v) for v in samples if v.strip() != ""]
            if valid:
                avg = sum(valid) / len(valid)
                score = get_rpi_score(key, avg)
                rpi_scores.append(score)

        if len(rpi_scores) == 4:
            rpi = sum(rpi_scores) / 4
            st.success(f"🧪 **Pollution Index (RPI): {rpi:.2f}**")
            if rpi <= 2:
                st.markdown("✅ Pollution Level: **Non/mildly polluted**")
            elif rpi <= 3:
                st.markdown("⚠️ Pollution Level: **Lightly polluted**")
            elif rpi <= 6:
                st.markdown("❌ Pollution Level: **Moderately polluted**")
            else:
                st.markdown("🚨 Pollution Level: **Severely polluted**")
        else:
            st.warning("⚠️ At least DO, BOD₅, TSS, and NH₃-N values are required to calculate RPI.")

        # AI-BASED REPORT
st.markdown("---")
st.subheader("🧠 AI-Based Report: Suitability + Treatment Suggestion")

prompt = f"""
You are an expert environmental engineer. Analyze the following river water quality test results and provide a professional report that includes:
1. Suitability of the water for uses like drinking, irrigation, recreation, or industrial use.
2. Potential health or environmental risks.
3. Simple treatment methods to make this water potable or usable.

Water test data:
{input_data}

Use global standards like WHO and ECR. Be brief and professional.
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

# ─────────────────────────────
# Optional: Water Source Info + Print Summary
# ─────────────────────────────
st.markdown("---")
st.subheader("📝 Optional: Water Source Information")

source_name = st.text_input("Water Source Name (e.g., Turag River)", key="src_name")
location = st.text_input("Location (e.g., Mirpur Bridge)", key="src_loc")
description = st.text_area("Short Description", key="src_desc")

if "print_ready" not in st.session_state:
    st.session_state.print_ready = ""

# Ensure WQI, RPI, and AI output exist before allowing print
if 'wqi' in locals() and 'rpi' in locals() and ai_text:
    st.markdown("---")
    if st.button("📄 Generate Printable Summary"):
        summary = f"""
### AquaCortex 2.0 — Water Quality Report

**Water Source**: {source_name or "N/A"}  
**Location**: {location or "N/A"}  

**Short Description**:  
{description or "N/A"}  

---

**🌊 Water Quality Index (WQI)**: {wqi:.2f}  
- Classification: {"Excellent" if wqi <= 25 else "Good" if wqi <= 50 else "Poor" if wqi <= 75 else "Very Poor" if wqi <= 100 else "Unsuitable"}

**🧪 Pollution Index (RPI)**: {rpi:.2f}  
- Classification: {"Non/mildly polluted" if rpi <= 2 else "Lightly polluted" if rpi <= 3 else "Moderately polluted" if rpi <= 6 else "Severely polluted"}

---

**🧠 AI Analysis Summary & Treatment Recommendation**:  
{ai_text}
"""
        st.session_state.print_ready = summary
        st.success("✅ Printable report generated below.")

    if st.session_state.print_ready:
        st.markdown("## 🖨️ Print Preview")
        st.markdown(st.session_state.print_ready)
        st.download_button(
            label="⬇️ Download Report (.txt)",
            data=st.session_state.print_ready,
            file_name="AquaCortex_Report.txt",
            mime="text/plain"
        )
