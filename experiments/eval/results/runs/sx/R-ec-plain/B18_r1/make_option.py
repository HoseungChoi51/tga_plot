import pandas as pd
import numpy as np
import json

# Load the 'Annealed' sheet from the Excel file
file_path = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
df = pd.read_excel(file_path, sheet_name='Annealed')

# Extract relevant columns
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values
d_weight = df['Deriv. Weight (%/°C)'].values

# Filter out initial stable region and final stable region to focus on decomposition
# We look for the first significant drop in weight or peak in derivative weight
# For TGA onset, we typically look at the temperature where mass loss begins significantly.
# A common method is to find the inflection point of the TG curve, which corresponds to the minimum of the DTG curve.
# However, "onset" often refers to extrapolated onset, found by drawing a tangent at the steepest slope and intersecting with the baseline.

# Let's find the index of the minimum value in d_weight (steepest mass loss rate)
min_idx = np.argmin(d_weight)
peak_temp = temp[min_idx]

# To estimate the extrapolated onset:
# 1. Identify the baseline before decomposition (e.g., first 50 points or until temp < 100 if no early loss)
#    Looking at data, weight starts at 100 and stays relatively flat initially.
#    Let's take points where temp < 100 as baseline reference if they are stable.
#    If not, just use the first few points.
baseline_mask = temp < 100
if len(baseline_mask[baseline_mask]) > 5:
    # Use linear regression on the baseline part to get the baseline trend (usually horizontal)
    x_base = temp[baseline_mask]
    y_base = weight[baseline_mask]
    coeffs = np.polyfit(x_base, y_base, 1)
    baseline_slope = coeffs[0]
    baseline_intercept = coeffs[1]
else:
    baseline_slope = 0
    baseline_intercept = weight[0]

# 2. Find the tangent at the steepest point (min_idx)
#    The slope of the tangent is approximately the derivative value at that point? 
#    No, the derivative column IS the slope. So the slope of the TG curve at min_idx is d_weight[min_idx].
#    Wait, d_weight is %/deg C. So yes, it is the slope of Weight vs Temp.
tangent_slope = d_weight[min_idx]
tangent_point_x = temp[min_idx]
tangent_point_y = weight[min_idx]

# Equation of tangent line: y - y0 = m(x - x0) => y = m*x + (y0 - m*x0)
tangent_intercept = tangent_point_y - tangent_slope * tangent_point_x

# 3. Intersection of tangent line and baseline line
#    Baseline: y = baseline_slope * x + baseline_intercept
#    Tangent: y = tangent_slope * x + tangent_intercept
#    Set equal: baseline_slope * x + baseline_intercept = tangent_slope * x + tangent_intercept
#    x * (baseline_slope - tangent_slope) = tangent_intercept - baseline_intercept
#    x = (tangent_intercept - baseline_intercept) / (baseline_slope - tangent_slope)

denominator = baseline_slope - tangent_slope
if abs(denominator) > 1e-6:
    onset_temp = (tangent_intercept - baseline_intercept) / denominator
else:
    onset_temp = tangent_point_x # Fallback

# Sanity check: onset should be less than peak temp
if onset_temp > tangent_point_x or onset_temp < 0:
    # Simple fallback: onset is roughly where weight drops by 5% from initial
    initial_weight = weight[0]
    threshold = initial_weight * 0.95
    onset_indices = np.where(weight <= threshold)[0]
    if len(onset_indices) > 0:
        onset_temp = temp[onset_indices[0]]
    else:
        onset_temp = tangent_point_x

# Prepare data for ECharts
# Downsample if necessary, but 871 points is fine for SVG/PNG
x_data = temp.tolist()
y_tg = weight.tolist()
y_dtg = d_weight.tolist()

# Markers for onset and peak
mark_points = [
    {
        "coord": [float(onset_temp), float(np.interp(onset_temp, temp, weight))],
        "name": f"Onset: {onset_temp:.1f} °C",
        "symbolSize": 10,
        "itemStyle": {"color": "#ff4d4f"}
    },
    {
        "coord": [float(peak_temp), float(weight[min_idx])],
        "name": f"Peak: {peak_temp:.1f} °C",
        "symbolSize": 10,
        "itemStyle": {"color": "#1890ff"}
    }
]

option = {
    "title": {
        "text": "TGA/DTG Analysis (Annealed)",
        "subtext": f"Extrapolated Onset Temperature: {onset_temp:.2f} °C",
        "left": "center",
        "top": "2%",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        "subtextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "formatter": None # Default formatter works well enough
    },
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
        "top": "10%"
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "scale": True
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "scale": True
        },
        {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "position": "right",
            "scale": True,
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "data": list(zip(x_data, y_tg)),
            "yAxisIndex": 0,
            "markPoint": {
                "data": mark_points
            },
            "lineStyle": {"width": 2}
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "data": list(zip(x_data, y_dtg)),
            "yAxisIndex": 1,
            "lineStyle": {"width": 2, "type": "dashed"}
        }
    ]
}

output = {
    "figures": [
        {
            "name": "plot1",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output))
