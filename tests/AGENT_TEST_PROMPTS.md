# Test requests for an agent that runs commands itself (e.g. pi)

Start the agent in this folder with AGENT.md as its instructions. Paste one request at a time,
time it, and compare the plot with "Should get". The plots go to `tests/inputs/<file>_plots/`.
Delete that folder between runs if you want to see only the new plot.

## 01_minimal

```text
파일: tests/inputs/TGA.xlsx
TGA.xlsx 그래프 그려줘
```

Should get: sheets_resolved = ["1006R1-V normal", "1006R1-V acid", "1006R1-V 750C"]; annot[value_at_x].x = 800; annot[peak].count = 1

## 02_full_form

```text
파일: tests/inputs/TGA.xlsx
원하는 작업: 1006R1-V normal sheet에 있는 실험일별 인장강도를 정리해 그래프로 그려서 png로 저장해줘. B행에 있는 것들을 X축, C행에 있는 것들을 Y1축, D행에 있는 것들을 Y2 축으로 해서 그래프를 그리면 돼. weight는 20단위로 해주고, Temperature은 200단위로 표시해주고, Deriv.Weight는 0.2단위로 표시해줘. 그리고 Deriv.Weight 의 max값을 표시해주고, temperatur 800 근처일때의 Y값을 Residue {}% 으로 표시해줘.
추가·수정 요청: temperature은 0에서부터 200씩 늘어나야해. 그리고 800과 가장가까운 값을 찾아서 그때의 weight값을 residue 몇 %인지 표시하라고.
결과 형식: png
```

Should get: sheets_resolved = ["1006R1-V normal"]; col[x] = "B"; col[y1] = "C"; col[y2] = "D"; x.min = 0; x.step = 200; y1.step = 20; y2.step = 0.2; annot[value_at_x].x = 800; annot[value_at_x].method = "nearest"; annot[value_at_x].rendered = "Residue 8.0%"; annot[peak].count = 1; output.format = ["png"]

## 03_sheet_range_peaks

```text
파일: tests/inputs/TGA.xlsx
1006R1-V acid 시트만 그려줘. x축 범위 100~800, 피크 표시 2개
```

Should get: sheets_resolved = ["1006R1-V acid"]; x.min = 100; x.max = 800; annot[peak].count = 2

## 04_title

```text
파일: tests/inputs/TGA.xlsx
1006R1-V normal 시트, 그림 제목을 'CNT 산화 거동'으로 바꾸고 그림 제목 글자 크기 18, 그림 제목 글자 색깔 남색
```

Should get: title.text = "CNT 산화 거동"; title.size = 18; title.color = "navy"

## 05_lines

```text
파일: tests/inputs/TGA.xlsx
y1 선 색깔 검정, 선 굵기 2.5로 하고 y2 선은 점선으로 해줘
```

Should get: y1.color = "black"; y1.width = 2.5; y2.linestyle = "dotted"

## 06_legend_off_grid

```text
파일: tests/inputs/TGA.xlsx
범례 없애고 격자 켜줘
```

Should get: legend.show = false; grid = true

## 07_legend_place

```text
파일: tests/inputs/TGA.xlsx
범례 오른쪽 위로 옮기고 범례 글자 크기 9
```

Should get: legend.where = "upper right"; legend.size = 9

## 08_axis_labels

```text
파일: tests/inputs/TGA.xlsx
x축 라벨을 '온도 (°C)', y1축 라벨을 '무게 (%)', y2축 라벨을 '미분 무게 (%/°C)'로 바꿔줘
```

Should get: x.label = "온도 (°C)"; y1.label = "무게 (%)"; y2.label = "미분 무게 (%/°C)"

## 09_ticks

```text
파일: tests/inputs/TGA.xlsx
틱 방향 바깥쪽으로, 틱 라벨 크기 9
```

Should get: tick_direction = "out"; x.tick_size = 9; y1.tick_size = 9; y2.tick_size = 9

## 10_residue_temp_decimals

```text
파일: tests/inputs/TGA.xlsx
잔류량 표시를 700 °C로 바꾸고 소수점 둘째 자리까지 보여줘
```

Should get: annot[value_at_x].x = 700; annot[value_at_x].rendered_contains = "8.01"; annot[value_at_x].rendered_not_contains = "8.012"

## 11_remove_peak

```text
파일: tests/inputs/TGA.xlsx
피크 표시 지워줘
```

Should get: absent = "annot[peak]"; annot[value_at_x].x = 800

## 12_vline

```text
파일: tests/inputs/TGA.xlsx
450 °C에 세로 보조선 넣고 '산화 시작'이라고 써줘
```

Should get: annot[vline].x = 450; annot[vline].rendered_contains = "산화 시작"; annot[peak].count = 1

## 13_column_by_name

```text
파일: tests/inputs/extra_columns.xlsx
y1축은 Weight (mg) 열로 그려줘. y1축 라벨은 'Weight (mg)'
```

Should get: col[y1] = "D"; col[x] = "B"; col[y2] = "G"; y1.label = "Weight (mg)"

## 14_formats

```text
파일: tests/inputs/korean_excel.csv
korean_excel.csv 그래프 그리고 pdf랑 png 둘 다로 저장해줘
```

Should get: output.format = ["pdf", "png"]

## 15_combine

```text
파일: tests/inputs/TGA.xlsx
TGA.xlsx 시트 전부 한 그림에 겹쳐 그려줘
```

Should get: combine = true; sheets_resolved = ["1006R1-V normal", "1006R1-V acid", "1006R1-V 750C"]

## 16_no_y2

```text
파일: tests/inputs/TGA.xlsx
1006R1-V normal 시트, y2축 없이 무게만 그려줘
```

Should get: y2.show = false; sheets_resolved = ["1006R1-V normal"]

## 17_size_dpi

```text
파일: tests/inputs/TGA.xlsx
그림 크기 가로 8 세로 5, 해상도 600으로
```

Should get: size = [8, 5]; dpi = 600

## 18_step_range

```text
파일: tests/inputs/TGA.xlsx
x축 틱 간격 100, y2축 범위 -0.05~1.2
```

Should get: x.step = 100; y2.min = -0.05; y2.max = 1.2

## 19_global_text

```text
파일: tests/inputs/TGA.xlsx
전체 글자 색깔 회색, 글자 크기 13
```

Should get: text_color = "gray"; font_size = 13

## 20_extra_code

```text
파일: tests/inputs/TGA.xlsx
300~450 °C 구간을 연한 회색으로 칠해줘
```

Should get: code_contains = "axvspan"

## 21_letters_haeng

```text
파일: tests/inputs/blank_rows_on_top.xlsx
C행을 X축, D행을 Y1축, E행을 Y2축으로 그래프 그려줘
```

Should get: col[x] = "C"; col[y1] = "D"; col[y2] = "E"

## 22_y2_colors

```text
파일: tests/inputs/TGA.xlsx
y2 선 색깔 초록으로, y2축 라벨 글자 색깔도 초록
```

Should get: y2.color = "green"; y2.label_color = "green"

## 23_text_file_template

```text
파일: tests/inputs/instrument_export.txt
잔류량 글자를 'Residue: {}%'로 바꿔줘
```

Should get: annot[value_at_x].rendered = "Residue: 8.0%"

## 24_heat_flow_y2

```text
파일: tests/inputs/extra_columns.xlsx
Heat Flow를 y2축으로 그려주고 y2축 라벨은 'Heat flow (W/g)', 피크 표시는 빼줘
```

Should get: col[y2] = "F"; y2.label = "Heat flow (W/g)"; absent = "annot[peak]"
