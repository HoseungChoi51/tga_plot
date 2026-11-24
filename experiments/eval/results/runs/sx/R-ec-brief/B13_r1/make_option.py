import pandas as pd
import numpy as np
import json

def find_peaks_and_inflections(df, temp_col='Temperature (°C)', weight_col='Weight (%)', deriv_col='Deriv. Weight (%/°C)'):
    """
    Find significant DTG peaks (where mass loss rate is highest) to indicate 'sharp drops' in weight.
    We look for local minima in the derivative column (which correspond to max rates of weight loss).
    Since the prompt asks for "two places where weight bends sharply", we interpret this as the two main decomposition stages,
    identified by the most prominent DTG peaks (negative values).
    """
    temps = df[temp_col].values.astype(float)
    weights = df[weight_col].values.astype(float)
    dtg = df[deriv_col].values.astype(float)
    
    # Filter out noise at the beginning and end if necessary, but generally TGA data is clean enough.
    # Focus on the range where significant decomposition happens (usually > 100-200 C)
    mask = temps > 150 
    t_filtered = temps[mask]
    w_filtered = weights[mask]
    dtg_filtered = dtg[mask]
    
    if len(t_filtered) == 0:
        return [], []

    # Identify peaks in DTG (local minima since DTG is negative during loss)
    # A simple way: find indices where dtg[i] < dtg[i-1] and dtg[i] < dtg[i+1]
    # To avoid small fluctuations, we can smooth or just pick the top N most negative points that are separated.
    
    # Let's find all local minima
    local_min_indices = []
    for i in range(1, len(dtg_filtered)-1):
        if dtg_filtered[i] < dtg_filtered[i-1] and dtg_filtered[i] <= dtg_filtered[i+1]:
            # Check if it's a significant drop (e.g., value < -0.1 %/deg or relative to max abs)
            local_min_indices.append(i)
            
    if not local_min_indices:
        # Fallback: just take the point with the absolute minimum DTG
        min_idx = int(np.argmin(dtg_filtered))
        return [float(t_filtered[min_idx])], [float(w_filtered[min_idx])]
        
    # Sort these minima by how negative the DTG value is (strongest degradation first)
    # But we want distinct temperature regions. PVC typically has HCl elimination (~300C) and backbone breakdown (~450C).
    
    # Strategy: Group nearby minima into clusters and pick the deepest one from each cluster.
    # Simple clustering: if distance between temps > 50C, they are separate peaks.
    
    sorted_indices = sorted(local_min_indices, key=lambda x: dtg_filtered[x]) # Most negative first
    
    selected_temps = []
    selected_weights = []
    
    used_indices = set()
    
    for idx in sorted_indices:
        if idx in used_indices:
            continue
            
        current_temp = float(t_filtered[idx])
        current_dtg = float(dtg_filtered[idx])
        
        # Mark neighbors within a certain temperature window as used
        # Window size depends on heating rate, but 50C is reasonable for separating major stages
        window = 50 
        for other_idx in local_min_indices:
            if abs(float(t_filtered[other_idx]) - current_temp) < window:
                used_indices.add(other_idx)
                
        selected_temps.append(current_temp)
        selected_weights.append(float(w_filtered[idx]))
        
        if len(selected_temps) >= 2:
            break
            
    # If we found fewer than 2, try to find the next best ones from remaining unused minima or just split the curve
    if len(selected_temps) < 2:
        # Try finding another peak further away
        remaining_candidates = [i for i in local_min_indices if i not in used_indices]
        if remaining_candidates:
            # Pick the most negative among remaining
            best_rem = min(remaining_candidates, key=lambda x: dtg_filtered[x])
            selected_temps.append(float(t_filtered[best_rem]))
            selected_weights.append(float(w_filtered[best_rem]))
        else:
            # If still only 1, maybe just pick the inflection point visually? 
            # Or just report the single main peak twice? No, better to find the shoulder.
            # Let's just ensure we have 2 entries. If not, duplicate the main one or pick midpoint.
            if len(selected_temps) == 1:
                 # Heuristic: second stage often follows. Just add a placeholder or skip? 
                 # The user asked for TWO places. If data doesn't support 2 clear peaks, we might just show 1.
                 # However, PVC definitely has 2. Let's trust the clustering worked.
                 pass

    return selected_temps, selected_weights

# Load Data
file_path = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
sheet_name = "PVC"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    print(json.dumps({"error": str(e)}))
    exit()

# Column names based on preview
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

# Extract data
temps = df[temp_col].values.astype(float)
weights = df[weight_col].values.astype(float)
dtg_vals = df[dtg_col].values.astype(float)

# Prepare series data for ECharts
# Series 1: Weight (%) -> y1
series_weight_data = [[float(t), float(w)] for t, w in zip(temps, weights)]

# Series 2: DTG (-DTG) -> y2
# Multiply by -1 so peaks point up
dtg_neg = [-v for v in dtg_vals]
series_dtg_data = [[float(t), float(d)] for t, d in zip(temps, dtg_neg)]

# Find the two sharp bend temperatures
peak_temps, peak_weights = find_peaks_and_inflections(df, temp_col, weight_col, dtg_col)

# Prepare markPoints for the labels
mark_points = []
for i, (pt, pw) in enumerate(zip(peak_temps, peak_weights)):
    mark_points.append({
        "coord": [float(pt), float(pw)],
        "name": f"Stage {i+1}",
        "value": f"{round(float(pt), 1)} °C",
        "symbol": "circle",
        "symbolSize": 8,
        "itemStyle": {"color": "#d62728"},
        "label": {
            "show": True,
            "formatter": "{b}\n{c}", # Shows name and value
            "position": "top",
            "fontSize": 12,
            "color": "#d62728"
        }
    })

# Also standard residue label at 800C
residue_temp = 800.0
idx_res = int(np.argmin(np.abs(temps - residue_temp)))
res_weight = float(weights[idx_res])
res_actual_temp = float(temps[idx_res])

mark_points.append({
    "coord": [res_actual_temp, res_weight],
    "name": "Residue",
    "value": f"{round(res_weight, 1)}%",
    "symbol": "diamond",
    "symbolSize": 10,
    "itemStyle": {"color": "#1f4e9c"},
    "label": {
        "show": True,
        "formatter": "Residue\n{c}",
        "position": "bottom",
        "fontSize": 12,
        "color": "#1f4e9c"
    }
})

option = {
    "title": {
        "text": "TGA Curve: PVC",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "-DTG (%/°C)"],
        "top": "10%",
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
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 30,
        "max": 900,
        "splitLine": {
            "show": True,
            "lineStyle": {
                "type": "dashed",
                "color": "#ccc"
            }
        },
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "min": 0,
            "max": 110,
            "position": "left",
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": False
            }
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 40,
            "position": "right",
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": series_weight_data,
            "smooth": True,
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "itemStyle": {
                "color": "#1f4e9c"
            },
            "yAxisIndex": 0,
            "markPoint": {
                "data": mark_points
            }
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "data": series_dtg_data,
            "smooth": True,
            "lineStyle": {
                "color": "#c0392b",
                "width": 2
            },
            "itemStyle": {
                "color": "#c0392b"
            },
            "yAxisIndex": 1
        }
    ]
}

output = {
    "figures": [
        {
            "name": "pvc_tga",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output, ensure_ascii=False))
