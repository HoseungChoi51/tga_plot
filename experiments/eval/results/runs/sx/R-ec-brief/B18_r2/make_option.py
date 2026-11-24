import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

def calculate_onset_temperature(temp, weight):
    """
    Calculate the onset temperature using a common TGA method:
    1. Find the point of maximum mass loss rate (DTG peak) in the main decomposition region.
    2. Draw a tangent line at that point.
    3. Extrapolate this tangent to intersect with the baseline weight (usually 100% or the initial stable weight).
    
    For simplicity and robustness in script form without complex curve fitting libraries beyond scipy/numpy:
    We will find the DTG peak first. Then we take a small window around it, fit a linear regression,
    and find where this line intersects the initial weight level (approx 100%).
    """
    # Ensure data is sorted by temperature just in case
    df = pd.DataFrame({'Temp': temp, 'Weight': weight})
    df = df.sort_values('Temp').reset_index(drop=True)
    
    # Calculate derivative dW/dT
    dt = np.gradient(df['Temp'])
    dw = np.gradient(df['Weight'])
    dtg = dw / dt
    
    # Filter out noise at very low temps (< 50 C) and high temps (> 800 C) for peak finding
    mask = (df['Temp'] > 50) & (df['Temp'] < 800)
    valid_indices = df.index[mask]
    
    if len(valid_indices) == 0:
        return None, None, None
        
    valid_dtg = dtg[valid_indices]
    valid_temp = df['Temp'][valid_indices]
    
    # Find index of minimum DTG (most negative, i.e., max mass loss rate)
    min_idx_rel = np.argmin(valid_dtg)
    min_idx_abs = valid_indices[min_idx_rel]
    
    peak_temp = float(df['Temp'].iloc[min_idx_abs])
    peak_weight = float(df['Weight'].iloc[min_idx_abs])
    
    # Define a window around the peak for linear fitting (e.g., +/- 20 degrees or +/- 10 points)
    window_size = 15
    start_idx = max(0, min_idx_abs - window_size)
    end_idx = min(len(df), min_idx_abs + window_size)
    
    # Get data for fitting
    fit_temp = df['Temp'].iloc[start_idx:end_idx].values.astype(float)
    fit_weight = df['Weight'].iloc[start_idx:end_idx].values.astype(float)
    
    # Linear regression: y = mx + c
    try:
        coeffs = np.polyfit(fit_temp, fit_weight, 1)
        m, c = coeffs
        
        # Baseline weight assumption: The weight before significant degradation starts.
        # Usually close to 100%. Let's use the average weight of the first 10% of the temperature range or simply 100.
        # A more robust way for "onset" intersection is often with the horizontal baseline at 100%.
        baseline_weight = 100.0 
        
        # Solve for x where y = baseline_weight: baseline = m*x + c => x = (baseline - c) / m
        if m != 0:
            onset_temp = float((baseline_weight - c) / m)
        else:
            onset_temp = peak_temp
            
        # Sanity check: onset should be lower than peak temp
        if onset_temp < 0 or onset_temp > peak_temp:
             onset_temp = peak_temp # Fallback
             
        return onset_temp, peak_temp, peak_weight
    except Exception:
        return None, peak_temp, peak_weight

# Read the specific sheet
sheet_name = "Annealed"
try:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
except Exception as e:
    print(json.dumps({"error": str(e)}))
    exit()

# Extract columns
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

if temp_col not in df.columns or weight_col not in df.columns:
    # Try generic indices if names don't match exactly due to encoding
    cols = df.columns
    temp_col = cols[1] # B
    weight_col = cols[2] # C
    dtg_col = cols[3] # D

temps = df[temp_col].dropna().values.astype(float)
weights = df[weight_col].dropna().values.astype(float)
dtgs = df[dtg_col].dropna().values.astype(float)

# Align lengths
min_len = min(len(temps), len(weights), len(dtgs))
temps = temps[:min_len]
weights = weights[:min_len]
dtgs = dtgs[:min_len]

# Calculate Onset
onset_temp, peak_temp, peak_weight = calculate_onset_temperature(temps, weights)

# Prepare Data for ECharts
# TGA Plot: x=Temp, y1=Weight, y2=-DTG

data_weight = [[float(t), float(w)] for t, w in zip(temps, weights)]
data_dtg = [[float(t), float(-d)] for t, d in zip(temps, dtgs)] # Multiply DTG by -1 so peaks point up

# Find Residue at 800C
idx_800 = int(np.argmin(np.abs(temps - 800)))
residue_val = float(weights[idx_800])
residue_temp = float(temps[idx_800])

# Find Peak Info for Label (Highest DTG peak > 150C)
mask_peak = (temps > 150)
if np.any(mask_peak):
    idx_max_dtg = int(np.argmax(-dtgs[mask_peak])) # Max of -DTG corresponds to min of DTG
    actual_idx = int(np.where(mask_peak)[0][idx_max_dtg])
    label_peak_temp = float(temps[actual_idx])
else:
    label_peak_temp = float(peak_temp)

# Build Option
option = {
    "title": {
        "text": f"{sheet_name} TGA",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    },
    "legend": {
        "data": ["Weight (%)", "-DTG (%/°C)", "Onset Tangent"],
        "top": 30,
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "type": "value",
        "scale": True,
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "type": "value",
            "position": "left",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        {
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 40,
            "type": "value",
            "position": "right",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": data_weight,
            "showSymbol": False,
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "markPoint": {
                "data": [
                    {
                        "coord": [residue_temp, residue_val],
                        "symbolSize": 10,
                        "itemStyle": {"color": "#1f4e9c"},
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue_val:.1f}%",
                            "position": "bottom",
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 10
                        }
                    }
                ]
            }
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": data_dtg,
            "showSymbol": False,
            "lineStyle": {
                "color": "#c0392b",
                "width": 2
            },
            "markPoint": {
                "data": [
                    {
                        "coord": [label_peak_temp, float(-dtgs[int(np.argmin(np.abs(temps - label_peak_temp)))])),
                        "symbolSize": 10,
                        "itemStyle": {"color": "#c0392b"},
                        "label": {
                            "show": True,
                            "formatter": f"{label_peak_temp:.0f} °C",
                            "position": "top",
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 10
                        }
                    }
                ]
            }
        }
    ]
}

# Add Onset Marker and Line if calculated
if onset_temp is not None:
    # To draw the tangent line visually, we need two points.
    # Point 1: Intersection with baseline (100%) -> (onset_temp, 100)
    # Point 2: Some point further down the tangent. 
    # We approximated the tangent slope earlier. Let's recalculate slope roughly for drawing or just draw a vertical marker?
    # The user asked to "display" the onset. A vertical dashed line at the onset temp is clear.
    # Or better, mark the point on the weight curve corresponding to the onset temp.
    
    # Interpolate weight at onset_temp
    if onset_temp >= temps.min() and onset_temp <= temps.max():
        w_at_onset = float(np.interp(onset_temp, temps, weights))
        
        # Add a series for the marker/annotation
        option["series"].append({
            "name": "Onset Tangent",
            "type": "scatter",
            "data": [[float(onset_temp), w_at_onset]],
            "symbolSize": 15,
            "itemStyle": {
                "color": "#27ae60",
                "borderColor": "#000",
                "borderWidth": 1
            },
            "label": {
                "show": True,
                "formatter": f"Onset\n{onset_temp:.1f} °C",
                "position": "right",
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 11,
                "color": "#27ae60",
                "fontWeight": "bold"
            }
        })
        
        # Optional: Draw a vertical dashed line from bottom to the point
        option["series"].append({
            "name": "Onset Line",
            "type": "line",
            "data": [[float(onset_temp), 0.0], [float(onset_temp), w_at_onset]],
            "showSymbol": False,
            "lineStyle": {
                "color": "#27ae60",
                "type": "dashed",
                "width": 1.5
            },
            "z": 1 # Behind other lines
        })

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
