# AquaCortex 2.0 – Final Version with Correct WQI Calculation
# This Streamlit app uses the Weighted Arithmetic Index Method (globally accepted WQI formula)
# for river water quality analysis and provides AI-based insights.


# Corrected WQI Calculation Section:
st.markdown("### 🌊 Water Quality Index (WQI)")

        k = 1.0  # Scaling constant for weights
        total_weight = 0.0
        weighted_qi_sum = 0.0

        for param in standards:
            values = [float(v) for v in input_data[param] if v.strip()]
            if values:
                vi = sum(values) / len(values)
                si = standard_values[param]
                vi_ideal = ideal_values[param]
                wi = k / si
                try:
                    qi = ((vi - vi_ideal) / (si - vi_ideal)) * 100
                    qi = max(0, min(qi, 100))  # Limit between 0–100
                except ZeroDivisionError:
                    qi = 0
                weighted_qi_sum += qi * wi
                total_weight += wi

        if total_weight > 0:
            wqi = weighted_qi_sum / total_weight
            wqi_status = (
                "Excellent" if wqi <= 25 else
                "Good" if wqi <= 50 else
                "Poor" if wqi <= 75 else
                "Very Poor" if wqi <= 100 else
                "Unsuitable for use"
            )
        else:
            wqi = None
            wqi_status = "N/A"

# (Rest of the app follows...)
