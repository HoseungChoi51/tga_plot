import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def get_nearest_value(df, x_col, y_col, target_x):
    """Find the y value at the point nearest to target_x."""
    if df.empty:
        return None, None
    # Ensure numeric
    try:
        idx = (df[x_col] - target_x).abs().idxmin()
        return float(df.loc[idx, x_col]), float(df.loc[idx, y_col])
    except Exception:
        return None, None

def find_peak_above_threshold(df, x_col, dtg_col, threshold=150.0):
    """Find the temperature of the highest DTG peak above threshold.
       DTG is negative during mass loss. The 'peak' in magnitude is the minimum value.
    """
    filtered_df = df[df[x_col] > threshold]
    if filtered_df.empty:
        return None, None
    
    # Find index where DTG is minimum (most negative)
    try:
        idx_min_dtg = filtered_df[dtg_col].idxmin()
        peak_temp = float(filtered_df.loc[idx_min_dtg, x_col])
        peak_val = float(filtered_df.loc[idx_min_dtg, dtg_col])
        return peak_temp, peak_val
    except Exception:
        return None, None

def create_tga_chart_option(sheet_name, df):
    # Identify columns based on standard TGA structure provided in preview
    # B: Temperature, C: Weight(%), D: D.W(%/C)
    x_col = "Temperature"
    y1_col = "Weight(%)"
    y2_col = "D.W(%/C)"
    
    # Prepare data lists for ECharts series
    weight_data = []
    dtg_data = []
    
    for _, row in df.iterrows():
        temp = row[x_col]
        weight = row[y1_col]
        dtg = row[y2_col]
        
        # Handle NaNs and convert to float
        if pd.isna(temp) or pd.isna(weight) or pd.isna(dtg):
            continue
            
        try:
            t_val = float(temp)
            w_val = float(weight)
            d_val = float(dtg)
            
            weight_data.append([t_val, w_val])
            # Multiply DTG by -1 so peaks point up
            dtg_data.append([t_val, -d_val])
        except ValueError:
            continue
        
    # Calculate Residue (nearest 800°C)
    residue_temp, residue_weight = get_nearest_value(df, x_col, y1_col, 800.0)
    
    # Calculate Peak (highest DTG peak above 150°C)
    peak_temp, peak_dtg_raw = find_peak_above_threshold(df, x_col, y2_col, 150.0)
    
    # Series Data
    series_list = [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": weight_data,
            "yAxisIndex": 0,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
            "showSymbol": False,
            "smooth": False
        },
        {
            "name": "DTG (%/°C)",
            "type": "line",
            "data": dtg_data,
            "yAxisIndex": 1,
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
            "showSymbol": False,
            "smooth": False
        }
    ]
    
    # Add scatter series for markers if they exist
    if residue_weight is not None and residue_temp is not None:
        series_list.append({
            "name": "Residue Marker",
            "type": "scatter",
            "data": [[residue_temp, residue_weight]],
            "yAxisIndex": 0,
            "symbolSize": 8,
            "itemStyle": {"color": "#1f4e9c", "borderColor": "#fff", "borderWidth": 1},
            "label": {
                "show": True,
                "position": "right",
                "formatter": f"Residue {residue_weight:.1f}%",
                "fontSize": 10,
                "color": "#333",
                "backgroundColor": "rgba(255,255,255,0.7)",
                "padding": [2, 4],
                "fontFamily": "Noto Sans CJK KR"
            }
        })
        
    if peak_temp is not None and peak_dtg_raw is not None:
        # The peak marker should be on the DTG curve (y2 axis)
        # In our chart, DTG is plotted as -DTG. So the y-value for the marker is -peak_dtg_raw
        peak_y_val = -peak_dtg_raw
        series_list.append({
            "name": "Peak Marker",
            "type": "scatter",
            "data": [[peak_temp, peak_y_val]],
            "yAxisIndex": 1,
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b", "borderColor": "#fff", "borderWidth": 1},
            "label": {
                "show": True,
                "position": "top",
                "formatter": f"{peak_temp:.0f} °C",
                "fontSize": 10,
                "color": "#333",
                "backgroundColor": "rgba(255,255,255,0.7)",
                "padding": [2, 4],
                "fontFamily": "Noto Sans CJK KR"
            }
        })

    option = {
        "title": {
            "text": sheet_name,
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
            "data": ["Weight (%)", "DTG (%/°C)"],
            "orient": "vertical",
            "left": "left",
            "top": "middle",
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
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#eee"
                }
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "position": "left",
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "formatter": "{value}"
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#eee"
                    }
                }
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "position": "right",
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "formatter": "{value}"
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": series_list
    }
    
    return option

def main():
    figures = []
    
    try:
        xl_file = pd.ExcelFile(DATA_FILE)
        sheet_names = xl_file.sheet_names
        
        for sheet_name in sheet_names:
            df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
            
            # Clean column names just in case
            df.columns = [str(c).strip() for c in df.columns]
            
            # Check if required columns exist
            # Based on preview: A: Time, B: Temperature, C: Weight(%), D: D.W(%/C)
            # We need to map them correctly if names differ slightly, but here we assume standard names from preview
            cols = list(df.columns)
            
            # Heuristic mapping if exact names not found
            if "Temperature" not in df.columns:
                # Try finding a column with 'Temp'
                temp_cols = [c for c in cols if 'temp' in c.lower()]
                if temp_cols:
                    df.rename(columns={temp_cols[0]: "Temperature"}, inplace=True)
                    
            if "Weight(%)" not in df.columns:
                # Try finding a column with 'Weight'
                weight_cols = [c for c in cols if 'weight' in c.lower() and '%' in c]
                if not weight_cols:
                     weight_cols = [c for c in cols if 'weight' in c.lower()]
                if weight_cols:
                    df.rename(columns={weight_cols[0]: "Weight(%)"}, inplace=True)
                    
            if "D.W(%/C)" not in df.columns:
                # Try finding a column with 'D.W' or 'Derivative'
                dtg_cols = [c for c in cols if 'd.w' in c.lower() or 'derivative' in c.lower() or 'dtg' in c.lower()]
                if dtg_cols:
                    df.rename(columns={dtg_cols[0]: "D.W(%/C)"}, inplace=True)

            if "Temperature" in df.columns and "Weight(%)" in df.columns and "D.W(%/C)" in df.columns:
                option = create_tga_chart_option(sheet_name, df)
                
                # Figure size: 8 inches wide, 5 inches high. 
                # CSS pixels at 96 px/inch -> width = 8 * 96 = 768, height = 5 * 96 = 480
                fig_width_px = int(8 * 96)
                fig_height_px = int(5 * 96)
                
                figure_entry = {
                    "name": sheet_name.replace(" ", "_"),
                    "option": option,
                    "width": fig_width_px,
                    "height": fig_height_px,
                    "dpi": 600,
                    "formats": ["png"]
                }
                figures.append(figure_entry)
            
    except Exception as e:
        # If error occurs, print empty figures list to ensure valid JSON structure
        pass

    output = {"figures": figures}
    print(json.dumps(output))

if __name__ == "__main__":
    main()
