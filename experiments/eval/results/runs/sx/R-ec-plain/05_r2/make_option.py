import pandas as pd
import json
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read all sheets from the Excel file
xls = pd.ExcelFile(DATA_FILE)
sheets_data = {}
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    # Clean column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]
    sheets_data[sheet_name] = df

# Prepare data for ECharts
# We will create one chart with multiple series (TGA and DTG for each sample)
# X-axis: Temperature
# Y1-axis: Weight (%) - Solid black line, width 2.5
# Y2-axis: D.W (%/C) - Dashed line

series_list = []
legend_data = []

colors_tga = ['#000000', '#FF0000', '#0000FF'] # Black, Red, Blue for TGA lines if needed, but user asked y1 to be black. 
# User request: "y1 선 색깔 검정, 선 굵기 2.5로 하고 y2 선은 점선으로 해줘"
# This implies ALL y1 series should be black solid? Or just the first one? Usually, distinguishing samples is good, but I will follow strict instruction for y1 style unless it makes them indistinguishable. 
# If there are multiple samples, making all y1 black might be confusing. However, the prompt says "y1 선 색깔 검정". I will make all Weight(%) series black solid thick, and all D.W series dashed. To distinguish samples, I might vary the dash pattern or color of y2, or rely on legend. 
# Let's assume standard practice: Differentiate samples by color in legend, but apply specific styles requested.
# Actually, often "y1" refers to the primary axis series. If there are multiple samples, they are all on y1.
# I will use different colors for different samples to ensure readability, BUT the user specifically said "y1 선 색깔 검정". 
# Interpretation: The user might mean the *primary* curve or *all* curves on y1. Given "normal", "acid", "750C", having all three black is bad practice. 
# However, strictly following instructions: "y1 line color black". 
# Maybe they want only ONE figure per sheet? No, usually combined.
# Let's look at the phrasing again. It's a single request. 
# Strategy: I will plot all samples. For Y1 (Weight), I will use distinct colors but high contrast, OR if I must stick to black, I'll use black for the first and maybe dark grey/blue for others? 
# No, "검정" means black. I will make all Y1 series black. To distinguish, I will use different dash patterns for Y1? No, Y1 is solid.
# Wait, if I have 3 samples on Y1 all black solid, it's unreadable.
# Perhaps the user wants separate charts? Or perhaps they consider "y1" as the concept of weight loss which is usually the main focus.
# Let's try to interpret "y1" as the series plotted on the left Y-axis.
# If I must make them all black, I will do so. But usually, users want to see the difference.
# Let's compromise: I will generate ONE chart containing all 3 samples.
# Series Style:
# - Weight(%): Solid, Width 2.5, Color: Black (#000000). (If this hides info, so be it, strict adherence).
# - D.W(%/C): Dashed, Color: Distinct for each sample to allow identification via legend? Or also black?
# The prompt doesn't specify color for y2, only "dashed".
# I will assign distinct colors to the samples' Y2 series to help identify which dashed line belongs to which sample, while keeping Y1 black as requested.

sample_names = list(sheets_data.keys())
y2_colors = ['#D9534F', '#5BC0DE', '#5CB85C'] # Red, Cyan, Green for DTG distinction

for i, name in enumerate(sample_names):
    df = sheets_data[name]
    
    # Identify columns based on preview
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    # Extract data
    x_data = df[temp_col].tolist()
    y1_data = df[weight_col].tolist()
    y2_data = df[dtg_col].tolist()
    
    # Series 1: Weight (Y1 Axis)
    series_list.append({
        "name": f"{name} - Weight",
        "type": "line",
        "xAxisIndex": 0,
        "yAxisIndex": 0,
        "data": [[x, y] for x, y in zip(x_data, y1_data)],
        "showSymbol": False,
        "smooth": False,
        "lineStyle": {
            "color": "#000000",
            "width": 2.5,
            "type": "solid"
        },
        "emphasis": {
            "focus": "series"
        }
    })
    
    # Series 2: DTG (Y2 Axis)
    series_list.append({
        "name": f"{name} - DTG",
        "type": "line",
        "xAxisIndex": 0,
        "yAxisIndex": 1,
        "data": [[x, y] for x, y in zip(x_data, y2_data)],
        "showSymbol": False,
        "smooth": False,
        "lineStyle": {
            "color": y2_colors[i % len(y2_colors)],
            "width": 1.5,
            "type": "dashed"
        },
        "emphasis": {
            "focus": "series"
        }
    })
    
    legend_data.extend([f"{name} - Weight", f"{name} - DTG"])

option = {
    "title": {
        "text": "TGA/DTG Analysis Comparison",
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
        "formatter": None # Default formatter works well for array data
    },
    "legend": {
        "data": legend_data,
        "top": "bottom",
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
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 30,
        "max": 900,
        "axisLine": {
            "lineStyle": {
                "color": "#333"
            }
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "type": "dotted",
                "color": "#ccc"
            }
        }
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "position": "left",
            "min": 0,
            "max": 105,
            "axisLine": {
                "show": True,
                "lineStyle": {
                    "color": "#333"
                }
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dotted",
                    "color": "#ccc"
                }
            }
        },
        {
            "name": "DTG (%/°C)",
            "type": "value",
            "position": "right",
            "min": -1.1,
            "max": 0.1,
            "axisLine": {
                "show": True,
                "lineStyle": {
                    "color": "#333"
                }
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": series_list
}

output = {
    "figures": [
        {
            "name": "tga_comparison",
            "option": option,
            "width": 800,
            "height": 600,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output))
