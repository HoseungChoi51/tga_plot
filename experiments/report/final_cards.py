"""The evidence cards of the consolidated report: which runs each card shows, side by side.

Each card: id, section, title, the request (taken from the first panel), optional "what the prompt told the model"
snippets, and panels. A panel names its source (tga / cnt / pi / img) and what to highlight in the reply.
The narrative ("what happened") is written after looking at the plots (python experiments/report/build_final.py --preview).
"""

# what the system prompts say, quoted (file, text)
PROMPT = {
    "agent_linestyle": ("AGENT.md, part names table, row 9",
                        '| 9 | y1 선 | `y1.color`, `y1.width`, `y1.linestyle`, `y1.style` | "y1 선 초록, 굵기 2, 점선" → '
                        '`"y1": {"color": "green", "width": 2, "linestyle": "dotted"}` |'),
    "brief_parts": ("Raw-code brief (eval/arms.py BRIEF)",
                    "y1 선 / y2 선 = the left / right curve; 범례 = legend; … (no line-style words)"),
    "agent_inspect": ("AGENT.md, How to work, step 1",
                      'Look at the data: `python plotkit.py inspect "<file>"`. It lists sheet names, columns … and '
                      '`tga_guess`. (plotkit\'s reader then reads the file: UTF-16, cp949, metadata rows, decimal commas.)'),
    "raw_read": ("Raw-code prompt (eval/arms.py RAW_MPL)",
                 "The script must read the data file(s) given as DATA_FILE … (Excel, CSV or text files)."),
    "agent_legend": ("AGENT.md / plotkit schema, legend",
                     'legend position "center left" (default), "best", "upper right", "lower left", …, "none" '
                     "(every place is inside the axes)"),
    "agent_code": ("AGENT.md, Extra code",
                   '`"code"`: Python lines run after drawing and before saving. Names you can use: `fig`, `ax1`, `ax2`, '
                   "`x`, `y1`, `y2` (numpy arrays of the plotted data), `sheet`, `plt`, `np`."),
    "agent_answer": ("AGENT.md, How to work, step 5",
                     "Answer in Korean: the saved file path(s), the residue and peak values …, any `warnings`, and "
                     "anything you could not do."),
    "echarts_patch": ("AGENT_ECHARTS.md, Extra ECharts settings",
                      '`"echarts"` is a partial ECharts option (JSON only, no functions) … In a series you may set '
                      "`lineStyle`, `itemStyle`, `areaStyle`, … `markArea` / `markLine` / `markPoint`. "
                      "Never put the plotted data in `\"echarts\"`."),
}

CARDS = [
    # ------------------------------------------------------------------ 1 reliability
    {"id": "K1", "section": "reliability", "title": "The glossary decides what “점선” means",
     "prompts": ["agent_linestyle", "brief_parts"],
     "panels": [
         {"src": "tga", "args": ("sx", "P-mpl", "05", 1), "label": "Qwen · protocol", "hl": [r"linestyle"]},
         {"src": "tga", "args": ("sx", "R-mpl-brief", "05", 1), "label": "Qwen · raw code + brief", "hl": [r"linestyle|dashed line"]},
         {"src": "tga", "args": ("luna", "R-mpl-brief", "05", 1), "label": "Luna · raw code + brief", "hl": [r"linestyle"]}]},
    {"id": "K2", "section": "reliability", "title": "The reader carries an awkward file",
     "prompts": ["agent_inspect", "raw_read"],
     "panels": [
         {"src": "tga", "args": ("sx", "P-mpl", "23", 1), "label": "Qwen · protocol", "hl": [r"residue"]},
         {"src": "tga", "args": ("sx", "R-mpl-brief", "23", 1), "label": "Qwen · raw code + brief", "hl": [r"read_csv|sep=|encoding|skiprows"]},
         {"src": "tga", "args": ("sx", "R-ec-brief", "23", 1), "label": "Qwen · raw ECharts + brief", "hl": [r"read_csv|sep=|encoding|skiprows"]}]},
    {"id": "K3", "section": "reliability", "title": "Raw code passes the checker but the reviewers see clutter",
     "prompts": [],
     "panels": [
         {"src": "tga", "args": ("sx", "P-ec", "08", 1), "label": "Qwen · protocol · ECharts · 08", "hl": [r"label"]},
         {"src": "tga", "args": ("sx", "R-ec-brief", "08", 1), "label": "Qwen · raw ECharts + brief · 08", "hl": [r"markPoint|graphic|Residue"]},
         {"src": "tga", "args": ("luna", "P-ec", "19", 1), "label": "Luna · protocol · ECharts · 19", "hl": [r"text_color|font_size"]},
         {"src": "tga", "args": ("luna", "R-ec-brief", "19", 1), "label": "Luna · raw ECharts + brief · 19", "hl": [r"legend|color"]}]},
    {"id": "K4", "section": "reliability", "title": "CNT: the layer's data grammar against hand-written pandas",
     "prompts": [],
     "panels": [
         {"src": "cnt", "args": ("sealed_oc", "P-mpl", "S045", 1, 1), "label": "protocol · matplotlib", "hl": [r"chart|agg|by"]},
         {"src": "cnt", "args": ("sealed_oc", "R-mpl", "S045", 1, 1), "label": "raw code", "hl": [r"value_counts|groupby|pie|fillna|'-'"]}]},
    {"id": "K5", "section": "reliability", "title": "CNT: where raw code wins, the layer had no word for the ask",
     "prompts": [],
     "panels": [
         {"src": "cnt", "args": ("sealed_oc", "P-mpl", "S055", 1, 1), "label": "protocol · matplotlib", "hl": [r"stack|agg|by|normalize|percent"]},
         {"src": "cnt", "args": ("sealed_oc", "R-mpl", "S055", 1, 1), "label": "raw code", "hl": [r"div|sum|percent|100|stack"]}]},
    # ------------------------------------------------------------------ 2 silent drop
    {"id": "K6", "section": "silent", "title": "No key for “legend outside”: nearest key, no error",
     "prompts": ["agent_legend"],
     "panels": [
         {"src": "tga", "args": ("sx", "P-mpl", "B15", 1), "label": "Qwen · protocol", "hl": [r"legend"]},
         {"src": "tga", "args": ("luna", "P-ec", "B15", 1), "label": "Luna · protocol · ECharts", "hl": [r"legend"]},
         {"src": "tga", "args": ("sx", "R-mpl-brief", "B15", 1), "label": "Qwen · raw code + brief", "hl": [r"bbox_to_anchor|legend\("]}]},
    {"id": "K7", "section": "silent", "title": "“흑백” is a colour ask the glossary doesn't name",
     "prompts": [],
     "panels": [
         {"src": "tga", "args": ("luna", "P-ec", "B10", 1), "label": "Luna · protocol · ECharts", "hl": [r"color|font|size|dpi"]},
         {"src": "tga", "args": ("luna", "R-ec-brief", "B10", 1), "label": "Luna · raw ECharts + brief", "hl": [r"#000|black|gray|grey|color"]}]},
    # ------------------------------------------------------------------ 3 hatch
    {"id": "K8", "section": "hatch", "title": "The code hatch: changing x or y1 after drawing changes nothing",
     "prompts": ["agent_code"],
     "panels": [
         {"src": "tga", "args": ("sx", "P-mpl", "B24", 1), "label": "Qwen · protocol · code (Kelvin)", "hl": [r"273"]},
         {"src": "tga", "args": ("luna", "P-mpl", "B22", 1), "label": "Luna · protocol · code (dry basis)", "hl": [r"y1 ="]},
         {"src": "tga", "args": ("sx", "P-mpl", "B22", 1), "label": "Qwen · protocol · code (dry basis)", "hl": [r"clear|plot|y1 ="]},
         {"src": "tga", "args": ("sx", "R-mpl-brief", "B24", 1), "label": "Qwen · raw code (Kelvin)", "hl": [r"273"]}]},
    {"id": "K9", "section": "hatch", "title": "Offset curves: possible in matplotlib code, out of reach of the ECharts patch",
     "prompts": ["echarts_patch"],
     "panels": [
         {"src": "tga", "args": ("sx", "P-mpl", "B17", 1), "label": "Qwen · protocol · code", "hl": [r"set_ydata|offset|\+"]},
         {"src": "tga", "args": ("luna", "P-ec", "B17", 1), "label": "Luna · protocol · ECharts patch", "hl": [r"offset|echarts"]},
         {"src": "tga", "args": ("sx", "R-mpl-brief", "B17", 1), "label": "Qwen · raw code + brief", "hl": [r"offset"]}]},
    # ------------------------------------------------------------------ 4 computed asks
    {"id": "K10", "section": "computed", "title": "Onset temperature: a number the spec can't compute",
     "prompts": ["agent_code"],
     "panels": [
         {"src": "tga", "args": ("sx", "P-ec", "B18", 1), "label": "Qwen · protocol · ECharts (batch)", "hl": [r"onset"]},
         {"src": "tga", "args": ("sx", "P-mpl", "B18", 1), "label": "Qwen · protocol · code (batch)", "hl": [r"onset|gradient|argmax"]},
         {"src": "pi", "args": ("P-mpl", "B18", True), "label": "Luna · protocol · Pi agent", "hl": [r"onset|gradient|tangent"]}]},
    # ------------------------------------------------------------------ 5 reasoning
    {"id": "K11", "section": "reasoning", "title": "Thinking on: raw code reasons past its budget and draws nothing",
     "prompts": [],
     "panels": [
         {"src": "tga", "args": ("t06", "R-ec-plain", "01", 1), "label": "Odin · raw ECharts, thinking on", "hl": [], "reasoning": True},
         {"src": "tga", "args": ("sx_think", "R-mpl-brief", "09", 1), "label": "Qwen · raw code, thinking on", "hl": [], "reasoning": True},
         {"src": "tga", "args": ("sx_think", "P-mpl", "09", 1), "label": "Qwen · protocol, thinking on", "hl": [r"tick"]}]},
    {"id": "K12", "section": "reasoning", "title": "With reasoning, the ECharts patch can loop on a no-key ask",
     "prompts": ["echarts_patch"],
     "panels": [
         {"src": "tga", "args": ("sx_reason", "P-ec", "B17", 1), "label": "Qwen · protocol · ECharts, reasoning", "hl": [r"echarts|offset"], "reasoning": True},
         {"src": "tga", "args": ("sx_reason", "P-mpl", "B17", 1), "label": "Qwen · protocol · matplotlib, reasoning", "hl": [r"set_ydata|offset"]}]},
    # ------------------------------------------------------------------ 6 agents
    {"id": "K13", "section": "agents", "title": "What the agent tells the user after a silent drop",
     "prompts": ["agent_answer"],
     "panels": [
         {"src": "pi", "args": ("P-mpl", "B15", False), "label": "Qwen · Pi agent · protocol", "hl": [r"legend"], "answer": True},
         {"src": "pi", "args": ("P-mpl", "B15", True), "label": "Luna · Pi agent · protocol", "hl": [r"범례|legend"], "answer": True},
         {"src": "pi", "args": ("R-mpl-brief", "B15", False), "label": "Qwen · Pi agent · raw code", "hl": [r"bbox|legend"], "answer": True}]},
    {"id": "K14", "section": "agents", "title": "An agent applies a fix twice and reports success",
     "prompts": [],
     "panels": [
         {"src": "pi", "args": ("P-mpl", "B21", False), "label": "Qwen · Pi agent · protocol", "hl": [r"invert|flip|inverse"], "answer": True},
         {"src": "pi", "args": ("P-mpl", "B21", True), "label": "Luna · Pi agent · protocol", "hl": [r"invert|flip|inverse"], "answer": True}]},
    # ------------------------------------------------------------------ 7 CNT engines
    {"id": "K15", "section": "cnt", "title": "CNT: one spec, two engines; a follow-up turn fails only on ECharts",
     "prompts": [],
     "panels": [
         {"src": "cnt", "args": ("sealed", "P-mpl", "SS01", 1, 2), "label": "Strix · protocol · matplotlib, turn 2", "hl": [r"color|week|주차|14"]},
         {"src": "cnt", "args": ("sealed", "P-ec", "SS01", 1, 2), "label": "Strix · protocol · ECharts, turn 2", "hl": [r"color|week|주차|14|echarts"]}]},
    {"id": "K16", "section": "cnt", "title": "CNT: the reader opens a messy export that hand-written pandas can't",
     "prompts": ["raw_read"],
     "panels": [
         {"src": "cnt", "args": ("sealed_oc", "P-mpl", "S037", 1, 1), "label": "protocol · matplotlib", "hl": [r"file|x|y"]},
         {"src": "cnt", "args": ("sealed_oc", "R-mpl", "S037", 1, 1), "label": "raw code", "hl": [r"read_csv|skiprows|sep|encoding|header"]}]},
    # ------------------------------------------------------------------ 9 constrained decoding
    {"id": "K17", "section": "cd", "title": "Constrained decoding on OpenCode Go drops keys silently",
     "prompts": [],
     "panels": [
         {"src": "cnt", "args": ("cd_go", "P-mpl", "D001", 1, 1), "label": "free", "hl": [r'"by"|"chart"|"agg"']},
         {"src": "cnt", "args": ("cd_go", "P-mpl+cd", "D001", 1, 1), "label": "full schema", "hl": [r'"y1"|"y2"']},
         {"src": "cnt", "args": ("cd_go", "P-mpl+cdabc", "D001", 1, 1), "label": "full schema + A–Z note", "hl": [r'"z"']},
         {"src": "cnt", "args": ("cd_go", "P-mpl+cdflat", "D001", 1, 1), "label": "flat schema", "hl": [r'"by\.col"|y\.agg']}]},
    {"id": "K18", "section": "cd", "title": "On Strix Halo the enum helps once and costs once",
     "prompts": [],
     "panels": [
         {"src": "cnt", "args": ("cd_sx", "P-mpl", "D005", 1, 1), "label": "free · D005", "hl": [r'col']},
         {"src": "cnt", "args": ("cd_sx", "P-mpl+cdflat", "D005", 1, 1), "label": "flat schema · D005", "hl": [r'column']},
         {"src": "cnt", "args": ("cd_sx", "P-mpl", "D008", 1, 1), "label": "free · D008", "hl": [r'period']},
         {"src": "cnt", "args": ("cd_sx", "P-mpl+cdflat", "D008", 1, 1), "label": "flat schema · D008", "hl": [r'"key"']}]},
]

# image-only comparisons (no model reply involved)
IMAGES = {
    "parity_linestyle": [("matplotlib", "eval/results/parity/matplotlib/probe_linestyle_dash_alias"),
                         ("ECharts", "eval/results/parity/echarts/probe_linestyle_dash_alias")],
    "parity_residue": [("matplotlib", "eval/results/parity/matplotlib/probe_residue_beyond_xmax"),
                       ("ECharts", "eval/results/parity/echarts/probe_residue_beyond_xmax")],
}
