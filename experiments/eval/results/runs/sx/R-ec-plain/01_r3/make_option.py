import pandas as pd
import json
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def main():
    # Read all sheets from the Excel file
    xl_file = pd.ExcelFile(DATA_FILE)
    
    figures = []
    
    for sheet_name in xl_file.sheet_names:
        df = pd.read_excel(xl_file, sheet_name=sheet_name, header=0)
        
        # Identify columns based on standard TGA naming conventions from preview
        # Assuming column names are consistent or we can map by position if needed.
        # From preview: A=Time, B=Temperature, C=Weight(%), D=D.W(%/C)
        
        # Find temperature column (x-axis)
        temp_col = None
        weight_col = None
        dtg_col = None
        
        cols = df.columns.tolist()
        
        # Heuristic to find columns
        for c in cols:
            c_lower = str(c).lower()
            if 'temp' in c_lower:
                temp_col = c
            elif 'weight' in c_lower and '%' in c_lower:
                weight_col = c
            elif 'd.w' in c_lower or 'dtg' in c_lower or 'dw' in c_lower:
                dtg_col = c
                
        # Fallback if exact match fails, assume order based on preview description
        if temp_col is None and len(cols) >= 2:
            temp_col = cols[1] # Usually second column is Temperature
        if weight_col is None and len(cols) >= 3:
            weight_col = cols[2] # Third is Weight
        if dtg_col is None and len(cols) >= 4:
            dtg_col = cols[3] # Fourth is DTG
            
        if temp_col is None or weight_col is None:
            continue
            
        # Extract data
        temps = df[temp_col].values
        weights = df[weight_col].values
        
        dtgs = []
        if dtg_col is not None:
            dtgs = df[dtg_col].values
        
        # Clean data: remove NaNs
        mask = ~np.isnan(temps) & ~np.isnan(weights)
        temps_clean = temps[mask]
        weights_clean = weights[mask]
        
        if dtg_col is not None:
            dtgs_clean = dtgs[mask]
        else:
            dtgs_clean = None

        # Prepare series data for ECharts
        # Series 1: Weight (%) - Left Y Axis
        series_weight_data = [[float(t), float(w)] for t, w in zip(temps_clean, weights_clean)]
        
        # Series 2: DTG (%/C) - Right Y Axis (if available)
        series_dtg_data = []
        if dtgs_clean is not None:
            # Filter out NaNs in DTG specifically if they exist independently, though usually aligned
            valid_dtg_mask = ~np.isnan(dtgs_clean)
            # Re-align with temps just in case, but assuming same length after previous filter
            # Actually, let's create pairs for DTG using the same filtered temps
            dtg_pairs = [[float(t), float(d)] for t, d in zip(temps_clean, dtgs_clean) if not np.isnan(d)]
            series_dtg_data = dtg_pairs

        # Determine colors for different samples
        # Normal: Blue, Acid: Red, 750C: Green (example mapping)
        color_map = {
            "normal": "#5470c6",
            "acid": "#ee6666",
            "750c": "#91cc75"
        }
        
        # Try to identify sample type from sheet name
        sheet_lower = sheet_name.lower()
        line_color = "#5470c6" # default blue
        if "normal" in sheet_lower:
            line_color = "#5470c6"
        elif "acid" in sheet_lower:
            line_color = "#ee6666"
        elif "750" in sheet_lower:
            line_color = "#91cc75"
            
        # Create Option
        option = {
            "backgroundColor": "#ffffff",
            "title": {
                "text": f"TGA Analysis: {sheet_name}",
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
                },
                "formatter": "{a} <br/> Temp: {b} °C <br/> Value: {c}"
            },
            "legend": {
                "data": ["Weight (%)", "DTG (%/°C)"],
                "top": "10%",
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
                "type": "value",
                "min": 0,
                "max": 900,
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR"
                },
                "axisLabel": {
                    "formatter": "{value}"
                }
            },
            "yAxis": [
                {
                    "name": "Weight (%)",
                    "type": "value",
                    "min": 0,
                    "max": 105,
                    "position": "left",
                    "nameTextStyle": {
                        "fontFamily": "Noto Sans CJK KR"
                    },
                    "splitLine": {
                        "lineStyle": {
                            "color": "#eee"
                        }
                    }
                },
                {
                    "name": "DTG (%/°C)",
                    "type": "value",
                    "position": "right",
                    "nameTextStyle": {
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
                    "symbol": "none",
                    "lineStyle": {
                        "width": 2,
                        "color": line_color
                    },
                    "itemStyle": {
                        "color": line_color
                    },
                    "yAxisIndex": 0
                }
            ]
        }
        
        # Add DTG series if data exists
        if series_dtg_data:
            option["series"].append({
                "name": "DTG (%/°C)",
                "type": "line",
                "data": series_dtg_data,
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "width": 2,
                    "type": "dashed",
                    "color": "#fac858" # Orange/Yellow for DTG typically
                },
                "itemStyle": {
                    "color": "#fac858"
                },
                "yAxisIndex": 1
            })
            
        fig_entry = {
            "name": f"tga_{sheet_name.replace(' ', '_').replace('-', '_')}",
            "option": option,
            "width": 800,
            "height": 500,
            "dpi": 300,
            "formats": ["png"]
        }
        
        figures.append(fig_entry)

    output = {"figures": figures}
    print(json.dumps(output))

if __name__ == "__main__":
    main()
