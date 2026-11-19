import pandas as pd
import numpy as np
import json

# Load the data for the 'Annealed' sheet
file_path = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
df = pd.read_excel(file_path, sheet_name='Annealed')

# Extract relevant columns
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values
d_weight = df['Deriv. Weight (%/°C)'].values

# Find the onset temperature using extrapolation method
# 1. Identify the region of maximum weight loss rate (peak of DTG)
max_loss_idx = np.argmin(d_weight) # Most negative value corresponds to max weight loss rate
peak_temp = temp[max_loss_idx]

# 2. Determine a baseline before degradation starts (e.g., first 5% of data or stable region)
# We look for the initial flat part where weight is ~100% and d_weight is near 0
baseline_indices = np.where(temp < peak_temp * 0.5)[0]
if len(baseline_indices) > 0:
    # Use a subset of the baseline to fit a line (should be roughly horizontal)
    baseline_end = min(len(baseline_indices), int(0.1 * len(temp))) # Take up to 10% of data or until half peak temp
    if baseline_end > 5:
        b_temp = temp[:baseline_end]
        b_weight = weight[:baseline_end]
        
        # Fit linear regression to baseline
        coeffs = np.polyfit(b_temp, b_weight, 1)
        baseline_slope = coeffs[0]
        baseline_intercept = coeffs[1]
    else:
        baseline_slope = 0
        baseline_intercept = np.mean(weight[:5])
else:
    baseline_slope = 0
    baseline_intercept = np.mean(weight[:5])

# 3. Find the tangent point at the inflection point of the main degradation step
# The inflection point is often close to the peak of DTG. 
# To get a better tangent, we select points around the peak of DTG within the steep decline region.
window_size = 15
start_idx = max(0, max_loss_idx - window_size)
end_idx = min(len(temp), max_loss_idx + window_size)

tangent_temp = temp[start_idx:end_idx]
tangent_weight = weight[start_idx:end_idx]

# Fit linear regression to the steepest part to get the tangent slope
if len(tangent_temp) > 2:
    t_coeffs = np.polyfit(tangent_temp, tangent_weight, 1)
    tangent_slope = t_coeffs[0]
    tangent_intercept = t_coeffs[1]
    
    # 4. Calculate Onset Temperature
    # Intersection of baseline line and tangent line
    # y = m1*x + c1  (baseline)
    # y = m2*x + c2  (tangent)
    # x = (c2 - c1) / (m1 - m2)
    if abs(baseline_slope - tangent_slope) > 1e-9:
        onset_temp = (tangent_intercept - baseline_intercept) / (baseline_slope - tangent_slope)
    else:
        onset_temp = peak_temp
else:
    onset_temp = peak_temp

# Prepare ECharts Option
option = {
    "title": {
        "text": "TGA/DTG Analysis: Annealed Sample",
        "subtext": f"Onset Temperature: {onset_temp:.2f} °C",
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)", "Onset Point"],
        "top": "10%"
    },
    "grid": [
        {
            "id": "grid_tga",
            "left": "10%",
            "right": "10%",
            "height": "40%",
            "top": "15%"
        },
        {
            "id": "grid_dtg",
            "left": "10%",
            "right": "10%",
            "height": "25%",
            "bottom": "10%"
        }
    ],
    "xAxis": [
        {
            "id": "x_axis_tga",
            "type": "value",
            "name": "Temperature (°C)",
            "min": 30,
            "max": 900,
            "gridIndex": 0,
            "axisLabel": {"show": False},
            "splitLine": {"show": True}
        },
        {
            "id": "x_axis_dtg",
            "type": "value",
            "name": "Temperature (°C)",
            "min": 30,
            "max": 900,
            "gridIndex": 1,
            "splitLine": {"show": True}
        }
    ],
    "yAxis": [
        {
            "id": "y_axis_tga",
            "type": "value",
            "name": "Weight (%)",
            "min": 0,
            "max": 105,
            "gridIndex": 0,
            "splitLine": {"show": True}
        },
        {
            "id": "y_axis_dtg",
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "gridIndex": 1,
            "splitLine": {"show": True}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": [[float(t), float(w)] for t, w in zip(temp, weight)],
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#5470C6"},
            "markPoint": {
                "data": [
                    {
                        "coord": [onset_temp, np.interp(onset_temp, temp, weight)],
                        "name": "Onset",
                        "itemStyle": {"color": "#EE6666"},
                        "label": {
                            "formatter": f"Onset\n{onset_temp:.1f}°C",
                            "position": "top",
                            "fontSize": 12,
                            "fontWeight": "bold"
                        },
                        "symbolSize": 10
                    }
                ]
            },
            "markLine": {
                "data": [
                    {
                        "xAxis": onset_temp,
                        "label": {"formatter": "Onset Temp"},
                        "lineStyle": {"color": "#EE6666", "type": "dashed"}
                    }
                ]
            }
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "xAxisIndex": 1,
            "yAxisIndex": 1,
            "data": [[float(t), float(dw)] for t, dw in zip(temp, d_weight)],
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#91CC75"},
            "areaStyle": {"opacity": 0.1}
        }
    ]
}

result = {
    "figures": [
        {
            "name": "annealed_tga_onset",
            "option": option,
            "width": 800,
            "height": 600,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result))
