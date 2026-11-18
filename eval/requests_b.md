# Set B requests (evaluation)

Made with `python eval/requests_b.py`. Data: `eval/inputs_b/` (gallery generator). Groups: in = a key exists but no example covers it, messy = unusual wording, out = no spec key exists.

## B01_bands

group: in

```text
파일: eval/inputs_b/caox.csv
질량이 줄어드는 세 구간(120~250, 430~580, 640~830 °C)을 각각 다른 색으로 연하게 칠하고, 구간 위에 H2O, CO, CO2라고 써줘
```

## B02_heat_flow_peaks

group: in

```text
파일: eval/inputs_b/caox.csv
오른쪽 축에 DTG 대신 Heat Flow를 그리고, 흡열 피크 두 개와 발열 피크 하나의 온도를 표시해줘
```

## B03_log_axes

group: in

```text
파일: eval/inputs_b/rheology.csv
주파수에 따른 G'(왼쪽 축)와 G''(오른쪽 축)를 그려줘. x축과 두 y축 모두 로그 스케일로
```

## B04_xrd_peaks

group: in

```text
파일: eval/inputs_b/xrd.csv
XRD 패턴 그려주고 강한 피크 5개의 2θ 값을 표시해줘. 오른쪽 축은 필요 없어
```

## B05_two_files

group: out

```text
파일: eval/inputs_b/cnt_lot_A.csv, eval/inputs_b/cnt_lot_B.txt
두 파일을 한 그림에 겹쳐 그리고 범례에는 Lot A, Lot B라고 써줘
```

## B06_time_axis

group: in

```text
파일: eval/inputs_b/isothermal.txt
시간(분)을 x축으로, 무게는 왼쪽 축, 온도는 오른쪽 축에 그려줘. 140분일 때 무게를 표시해줘
```

## B07_sheet_number

group: in

```text
파일: eval/inputs_b/polymers.xlsx
두 번째 시트만 그리고, 300 °C와 600 °C에서의 무게를 표시해줘
```

## B08_hline_note

group: in

```text
파일: eval/inputs_b/cnt_batches.xlsx
Raw 시트에 무게 50% 위치에 가로 보조선 넣고, 오른쪽 위에 '공기, 10 °C/min'이라고 메모해줘
```

## B09_typos

group: messy

```text
파일: eval/inputs_b/polymers.xlsx
PE시트 그래프 x축 범위 100~700 으로하고 틱간격 100, y1 선 굵게(3) 빨간색으로 해주세용
```

## B10_paper_bw

group: messy

```text
파일: eval/inputs_b/cnt_batches.xlsx
Annealed 시트 논문에 넣을 거라 흑백으로 해줘. 글자 크기 8, 그림 3.5×2.6 인치, 600 dpi
```

## B11_many_changes

group: messy

```text
파일: eval/inputs_b/polymers.xlsx
PET 시트, 제목은 'PET 열분해', 범례는 왼쪽 아래, 격자 켜고, 잔류량은 소수 둘째 자리까지
```

## B12_english

group: messy

```text
파일: eval/inputs_b/caox.csv
Please plot the weight curve only (no DTG), x range 100 to 900, and label the residue at 900 °C
```

## B13_vague_term

group: messy

```text
파일: eval/inputs_b/polymers.xlsx
PVC 시트에서 무게가 확 꺾이는 데 두 군데 온도 표시해줘
```

## B14_slide

group: messy

```text
파일: eval/inputs_b/polymers.xlsx
PVC 시트 발표 슬라이드용으로 크게. 가로 10인치, 글자 16
```

## B15_legend_outside

group: out

```text
파일: eval/inputs_b/polymers.xlsx
세 시트 겹쳐 그리고 범례는 그래프 바깥 오른쪽에 둬
```

## B16_two_panels

group: out

```text
파일: eval/inputs_b/caox.csv
무게는 위 그래프, DTG는 아래 그래프로 따로 나눠서 그려줘 (x축은 같이)
```

## B17_offset

group: out

```text
파일: eval/inputs_b/polymers.xlsx
세 시트 무게 곡선을 겹치지 않게 20%씩 위아래로 띄워서(offset) 한 그림에 그려줘
```

## B18_onset

group: out

```text
파일: eval/inputs_b/cnt_batches.xlsx
Annealed 시트에서 외삽 개시 온도(onset)를 구해서 그래프에 표시해줘
```

## B19_mass_loss

group: out

```text
파일: eval/inputs_b/polymers.xlsx
PVC 시트에서 200 °C부터 400 °C 사이 질량 감소량(%)을 계산해서 그래프에 표시해줘
```

## B20_minor_ticks

group: out

```text
파일: eval/inputs_b/cnt_batches.xlsx
Acid-washed 시트, x축에 보조 눈금(minor tick)도 넣어줘
```

## B21_reversed_x

group: out

```text
파일: eval/inputs_b/cnt_batches.xlsx
Raw 시트를 x축 방향 뒤집어서(높은 온도가 왼쪽) 그려줘
```

## B22_dry_basis

group: out

```text
파일: eval/inputs_b/cnt_batches.xlsx
Raw 시트를 150 °C 무게를 100%로 다시 계산해서(건조 기준) 그려줘
```

## B23_sample_colors

group: out

```text
파일: eval/inputs_b/cnt_batches.xlsx
세 시료 겹쳐서 그리고 Raw는 검정, Acid-washed는 파랑, Annealed는 빨강으로 해줘
```

## B24_kelvin

group: out

```text
파일: eval/inputs_b/polymers.xlsx
PE 시트를 온도 단위 켈빈(K)으로 바꿔서 그려줘
```
