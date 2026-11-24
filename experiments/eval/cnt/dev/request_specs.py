# DEV split request specs (personas: 공정 엔지니어, 라인 작업자).
# Consumed by ../make_expectations.py (exec'd; H = helper class there).
# Each turn: text, kind, data (source/sheet/x/y/by/filter/agg/...), asks, alts, needs.
# Expression strings (derive / _prep / asks.expr) are evaluated against the written data files.

PERSONAS = {
    "공정 엔지니어": "precise; process jargon (PV/SP, sccm, binning, overlay); terse imperative 반말; gives exact columns",
    "라인 작업자": "short, casual; typos and abbreviations (ㄱㄱ, r2, dtg); rarely names exact columns or units",
}

RL = {"source": "data/run_log.xlsx", "sheet": "런로그"}
WS = {"source": "data/run_log.xlsx", "sheet": "주간요약"}
DT = {"source": "data/downtime.xlsx", "sheet": "정지이력"}
TGA = "data/tga_batches.xlsx"
ZONE = {"source": "data/r2_zone_temps.csv"}
DOE = {"source": "data/doe_temp_h2.csv"}
DIA = {"source": "data/diameters.csv"}
L3 = {"source": "data/L3_MES_export_202607.csv"}
RAMAN = {"source": "data/raman/*.csv"}
MONTH = {"월": "df['일자'].dt.month"}
TAU_EDGES = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]


def D(base, **kw):
    d = dict(base)
    if "derive" in kw and "derive" in d:
        kw["derive"] = {**d["derive"], **kw["derive"]}
    d.update(kw)
    return d


def T(text, kind, data, asks=(), alts=(), needs=(), **kw):
    return dict(text=text, kind=kind, data=data, asks=list(asks), alts=list(alts), needs=list(needs), **kw)


def single(id, persona, *a, **kw):
    return dict(id=id, persona=persona, turns=[T(*a, **kw)])


def session(id, persona, turns):
    return dict(id=id, persona=persona, turns=turns)


ENG, OPR = "공정 엔지니어", "라인 작업자"

ITEMS = [
    # ------------------------------------------------------------------ line
    single("D001", ENG,
           "run_log.xlsx 런로그 시트로 주차별 평균 CNT수율 추이 그려줘. 반응기(R1~R4)별 line 4개, x축 주차 1~26.",
           "line", D(RL, x="주차", y="CNT수율", by="반응기", agg="mean"),
           needs=["groupby"]),
    single("D002", ENG,
           "r2_zone_temps.csv 2존 PV 하루치 트렌드에 2존 SP 겹치고, 2존 PV 10분 이동평균(10 s 샘플이니까 60포인트) 라인도 추가.",
           "line", D(ZONE, x="시각", y=["2존(°C)", "2존 SP(°C)", "2존 10분 이동평균"],
                     derive={"2존 10분 이동평균": "df['2존(°C)'].rolling(60).mean()"}),
           asks=[{"what": "computed", "name": "max of 10-min moving average (°C)",
                  "expr": "df['2존 10분 이동평균'].max()", "tol": 0.5,
                  "note": "trailing 60-sample window; a centred window gives the same max shifted in time"}],
           needs=["rolling", "computed"]),
    single("D004", ENG,
           "tga_batches.xlsx에서 R1-260326-1, R1-260716-1 두 시트 TG 곡선(중량 % vs 온도 °C) overlay.",
           "line", D({"source": TGA}, sheet=["R1-260326-1", "R1-260716-1"], x="온도 (°C)", y="중량 (%)", by="_series"),
           needs=["filter"]),
    single("D005", OPR,
           "tga r4 두개 dtg 비교 그래프 ㄱㄱ",
           "line", D({"source": TGA}, sheet=["R4-260407-1", "R4-260721-1"], x="온도 (°C)", y="미분중량 (%/°C)", by="_series"),
           alts=["TG(중량 %) 곡선을 함께 그려도 됨 (DTG 두 개가 반드시 포함)",
                 "시트 선택: 이름이 R4로 시작하는 시트 = R4-260407-1, R4-260721-1"],
           needs=["filter"]),
    single("D006", ENG,
           "raman 폴더 스펙트럼 8개를 각각 G band(1550–1620 cm-1) 최대 intensity로 나눠서 정규화하고 한 그래프에 overlay. 범례는 plot 바깥 오른쪽.",
           "line", D(RAMAN, x="Raman Shift (cm-1)", y="정규화 강도", by="_series", _prep="H.raman_norm(df)"),
           asks=[{"what": "legend_loc", "value": "outside right"},
                 {"what": "computed", "name": "normalised G-band max per spectrum", "value": 1.0, "tol": 0.001}],
           needs=["normalize", "computed", "style"]),
    single("D007", ENG,
           "주간요약 시트 합격률(%) 주차별 꺾은선.",
           "line", D(WS, x="주차", y="합격률(%)"),
           needs=[]),
    single("D008", OPR,
           "수율 추이 좀 보여줘",
           "line", D(RL, x="주차", y="CNT수율", agg="mean"),
           alts=["주간요약 시트의 평균수율(g/g-cat) vs 주차 (동일한 값)",
                 "반응기별 주차 평균 4개 라인",
                 "일자별 평균 또는 런별 점/선 (x=일자)"],
           alt_values={"by_reactor": {"data": {"by": "반응기"}}},
           needs=["groupby", "underspecified"]),
    # ------------------------------------------------------------------ scatter
    single("D003", OPR,
           "r2 존온도 파일에서 1존이랑 2존 온도 상관있나 점으로 찍어봐",
           "scatter", D(ZONE, x="1존(°C)", y="2존(°C)"),
           alts=["x/y 축이 바뀐 경우도 허용"],
           needs=[]),
    single("D009", ENG,
           "체류시간(s) vs CNT수율 scatter, 반응기별 색 구분, 26주 전체 런.",
           "scatter", D(RL, x="체류시간", y="CNT수율", by="반응기"),
           needs=[]),
    single("D010", ENG,
           "잔류금속(wt%) x, IG/ID y 산점도. 등급 C 런만 빨간색, 나머지는 회색.",
           "scatter", D(RL, x="잔류금속", y="IG/ID", by="C여부",
                        derive={"C여부": "np.where(df['등급'] == 'C', 'C', 'A/B')"}),
           asks=[{"what": "colors", "value": {"C": "red", "A/B": "gray"}}],
           needs=["derive", "style"]),
    single("D011", OPR,
           "습도랑 잔류금속 같이 찍어봐 점으로",
           "scatter", D(RL, x="외기습도", y="잔류금속"),
           alts=["x/y 축이 바뀐 경우도 허용"],
           needs=[]),
    single("D012", ENG,
           "R3 런만 필터해서 H2/C2H4비 vs CNT수율 scatter.",
           "scatter", D(RL, x="H2/C2H4비", y="CNT수율", filter="`반응기` == 'R3'"),
           needs=["filter"]),
    single("D013", OPR,
           "3라인 파일 L3_MES_export_202607.csv 에서 x 금속 y 수율 산점도 P1 P2 색 다르게",
           "scatter", D(L3, x="잔류금속(wt%)", y="CNT수율(g/g-cat)", by="반응기"),
           needs=["parse"]),
    single("D014", ENG,
           "doe_temp_h2.csv: x=H2/C2H4비, y=수율(g/g-cat), 2존온도 수준(1100~1200 °C, 5수준)별 색 구분, 반복 3개 다 점으로.",
           "scatter", D(DOE, x="H2/C2H4비", y="수율(g/g-cat)", by="2존온도(°C)"),
           needs=[]),
    # ------------------------------------------------------------------ bar family
    single("D015", ENG,
           "촉매로트별 평균 CNT수율 bar. 로트 순서(FC-2602→FC-2608) 그대로, 막대 위에 값 라벨 소수 1자리.",
           "bar", D(RL, x="촉매로트", y="CNT수율", agg="mean"),
           asks=[{"what": "value_labels", "value": True, "note": "1 decimal"}],
           needs=["groupby", "style"]),
    single("D016", OPR,
           "정지원인별 총 정지시간 가로막대 큰거부터",
           "hbar", D(DT, x="원인", y="정지시간(분)", agg="sum", sort="desc"),
           alts=["정지시간을 시간(h)으로 환산해도 됨 (값 ÷ 60)"],
           needs=["groupby", "sort"]),
    single("D017", ENG,
           "반응기별 주간/야간 평균 IG/ID grouped bar.",
           "grouped_bar", D(RL, x="반응기", by="근무조", y="IG/ID", agg="mean"),
           needs=["groupby", "pivot"]),
    single("D018", OPR,
           "월별로 노즐막힘 몇번낫는지 반응기별로 묶어서 막대로 해줘요",
           "grouped_bar", D(DT, x="월", by="반응기", agg="count", filter="`원인` == '노즐 막힘'", fill=0,
                            derive=MONTH),
           alts=["x=반응기, 묶음=월 (축 바꿈)도 허용"],
           needs=["filter", "derive", "groupby", "pivot"]),
    single("D019", ENG,
           "downtime.xlsx 월별 정지시간 합계를 원인별 stacked bar로. 단위는 분 말고 시간(h)으로 환산.",
           "stacked_bar", D(DT, x="월", by="원인", y="정지시간(h)", agg="sum", fill=0,
                            derive={**MONTH, "정지시간(h)": "df['정지시간(분)'] / 60"}, _totals=True),
           asks=[{"what": "unit", "value": "h", "note": "minutes / 60"}],
           needs=["derive", "groupby", "pivot", "computed"]),
    single("D020", OPR,
           "반응기마다 등급 A B C 몇개씩인지 쌓아서 보여줘",
           "stacked_bar", D(RL, x="반응기", by="등급", agg="count", fill=0, _totals=True),
           needs=["groupby", "pivot"]),
    single("D021", ENG,
           "작업자별 평균 CNT수율 bar, 높은 순 정렬.",
           "bar", D(RL, x="작업자", y="CNT수율", agg="mean", sort="desc"),
           needs=["groupby", "sort"]),
    # ------------------------------------------------------------------ histogram
    single("D022", ENG,
           "diameters.csv에서 TEM-01, TEM-02만 직경(nm) histogram overlay, bin 1 nm 간격 3~28 nm.",
           "histogram", D(DIA, x="직경(nm)", by="시료", filter="`시료` in ['TEM-01', 'TEM-02']",
                          bins=list(range(3, 29))),
           needs=["filter", "binning"]),
    single("D023", OPR,
           "전체 런 수율 히스토그렘 그려줘",
           "histogram", D(RL, x="CNT수율"),
           alts=["bin 개수는 자유 (n과 범위만 확인)"],
           needs=[]),
    # ------------------------------------------------------------------ heatmap
    single("D024", ENG,
           "DOE heatmap: 행 2존온도, 열 H2/C2H4비, 값은 수율 3반복 평균.",
           "heatmap", D(DOE, y="2존온도(°C)", x="H2/C2H4비", value="수율(g/g-cat)", agg="mean"),
           needs=["groupby", "pivot"]),
    single("D025", ENG,
           "반응기 × 주차 평균 잔류금속(wt%) heatmap. 행 R1~R4, 열 1~26주.",
           "heatmap", D(RL, y="반응기", x="주차", value="잔류금속", agg="mean"),
           needs=["pivot"]),
    single("D026", OPR,
           "설비 정지 언제 많이나는지 요일이랑 시간대로 히트맵 해줘",
           "heatmap", D(DT, y="요일", x="시", agg="count", fill=0,
                        derive={"요일": "df['일자'].dt.dayofweek.map(dict(enumerate('월화수목금토일')))",
                                "시": "df['시작시각'].str[:2].astype(int)"},
                        row_order=list("월화수목금토일"), col_order=list(range(24))),
           alts=["시간대를 2~3시간 단위나 주간(08–20)/야간으로 묶은 것도 허용 (같은 원자료의 건수 합)",
                 "값이 정지시간 합계(분)인 경우는 차선"],
           needs=["derive", "pivot", "underspecified"]),
    single("D027", ENG,
           "런로그 수치 컬럼 상관계수 heatmap: 1존/2존/3존온도, C2H4유량, H2유량, H2/C2H4비, 체류시간, 외기습도, CNT수율, 잔류금속, 산화개시온도, IG/ID. diverging cmap, -1~1 고정.",
           "heatmap", D(RL, corr=["1존온도", "2존온도", "3존온도", "C2H4유량", "H2유량", "H2/C2H4비", "체류시간",
                                  "외기습도", "CNT수율", "잔류금속", "산화개시온도", "IG/ID"]),
           asks=[{"what": "colormap", "value": "diverging"}, {"what": "clim", "value": [-1, 1]}],
           needs=["corr", "style"]),
    # ------------------------------------------------------------------ pie
    single("D028", OPR,
           "정지원인 비율 파이로",
           "pie", D(DT, x="원인", agg="count"),
           alts=["정지시간(분) 합계 기준 비율"],
           alt_values={"by_minutes": {"data": {"y": "정지시간(분)", "agg": "sum"}}},
           needs=["groupby", "underspecified"]),
    single("D029", ENG,
           "26주 전체 등급(A/B/C) 비율 pie. 색은 A 초록, B 주황, C 빨강, % 라벨 소수 1자리.",
           "pie", D(RL, x="등급", agg="count"),
           asks=[{"what": "colors", "value": {"A": "green", "B": "orange", "C": "red"}},
                 {"what": "pct_labels", "value": True, "note": "1 decimal"}],
           needs=["groupby", "style"]),
    single("D030", ENG,
           "downtime 8월분(2026-08-01~08-30)만 원인별 정지시간(분) 비중 pie.",
           "pie", D(DT, x="원인", y="정지시간(분)", agg="sum",
                    filter="`일자` >= '2026-08-01' and `일자` <= '2026-08-30'"),
           needs=["daterange", "groupby"]),
    # ------------------------------------------------------------------ sessions
    session("DS01", ENG, [
        T("런로그 전체 런 체류시간(s) vs CNT수율 scatter.",
          "scatter", D(RL, x="체류시간", y="CNT수율")),
        T("체류시간 0.5 s 구간(2.5~7.0 s, 왼쪽 닫힘)으로 binning해서 구간별 평균 수율 bar로 바꿔.",
          "bar", D(RL, x="체류시간구간", y="CNT수율", agg="mean",
                   derive={"체류시간구간": f"H.cut(df['체류시간'], {TAU_EDGES})"}),
          needs=["binning", "groupby"]),
        T("막대 위에 구간별 런 수(n) 표시.",
          "bar", D(RL, x="체류시간구간", y="CNT수율", agg="mean",
                   derive={"체류시간구간": f"H.cut(df['체류시간'], {TAU_EDGES})"}),
          asks=[{"what": "bar_annotations", "name": "n per bin",
                 "expr": "df.groupby('체류시간구간', observed=True).size()"}],
          needs=["binning", "groupby", "style"]),
        T("이걸 반응기별로 쪼개서 heatmap으로: 행 반응기, 열 체류시간 구간, 값 평균 수율.",
          "heatmap", D(RL, y="반응기", x="체류시간구간", value="CNT수율", agg="mean",
                       derive={"체류시간구간": f"H.cut(df['체류시간'], {TAU_EDGES})"}),
          alts=["행/열 바뀐 배치도 허용"],
          needs=["binning", "pivot"]),
    ]),
    session("DS02", ENG, [
        T("tga_batches.xlsx 10개 시트 전부 TG 곡선(중량 % vs 온도) 한 그래프에 overlay.",
          "line", D({"source": TGA}, sheet="*", x="온도 (°C)", y="중량 (%)", by="_series")),
        T("R4 시트 두 개랑 R1-260326-1만 남겨.",
          "line", D({"source": TGA}, sheet=["R1-260326-1", "R4-260407-1", "R4-260721-1"], x="온도 (°C)",
                    y="중량 (%)", by="_series"),
          needs=["filter"]),
        T("y축 0~105 고정, x축 눈금 100 °C 간격, 제목 'TGA (Air, 10 °C/min)'.",
          "line", D({"source": TGA}, sheet=["R1-260326-1", "R4-260407-1", "R4-260721-1"], x="온도 (°C)",
                    y="중량 (%)", by="_series"),
          asks=[{"what": "ylim", "value": [0, 105]}, {"what": "xtick_step", "value": 100},
                {"what": "title", "value": "TGA (Air, 10 °C/min)"}],
          needs=["filter", "style"]),
    ]),
    session("DS03", OPR, [
        T("정지이력 반응기별로 몇번 섰는지 막대",
          "bar", D(DT, x="반응기", agg="count"),
          needs=["groupby"]),
        T("원인별로 쌓아줘",
          "stacked_bar", D(DT, x="반응기", by="원인", agg="count", fill=0, _totals=True),
          needs=["groupby", "pivot"]),
        T("그냥 원인별 비율 파이 하나로",
          "pie", D(DT, x="원인", agg="count"),
          alts=["정지시간 합계 기준 비율은 차선"],
          needs=["groupby"]),
        T("노즐막힘만 월별로 선그래프",
          "line", D(DT, x="월", agg="count", filter="`원인` == '노즐 막힘'", derive=MONTH, name="노즐 막힘 건수"),
          alts=["반응기별 4개 라인도 허용 (합이 같아야 함)"],
          needs=["filter", "derive", "groupby"]),
    ]),
    session("DS04", OPR, [
        T("r2 존온도 2존만 그려줘",
          "line", D(ZONE, x="시각", y="2존(°C)"),
          alts=["2존 SP를 같이 그린 것도 허용"]),
        T("저녁 8시부터 10시까지만 확대",
          "line", D(ZONE, x="시각", y="2존(°C)",
                    filter="`시각` >= '2026-06-17 20:00:00' and `시각` <= '2026-06-17 22:00:00'"),
          asks=[{"what": "xlim", "value": ["2026-06-17 20:00:00", "2026-06-17 22:00:00"],
                 "note": "x-axis zoom alone (without dropping data) is also acceptable"}],
          tolerance={"n": "±1 point (inclusive/exclusive end)"},
          needs=["daterange"]),
        T("이 구간 2존이랑 SP 차이 히스토그램으로 2도 간격",
          "histogram", D(ZONE, x="편차(°C)", derive={"편차(°C)": "df['2존(°C)'] - df['2존 SP(°C)']"},
                         filter="`시각` >= '2026-06-17 20:00:00' and `시각` <= '2026-06-17 22:00:00'",
                         bins=list(range(-4, 38, 2))),
          tolerance={"bins": "edges aligned to even °C shown; other 2 °C alignments acceptable - then check n/range only",
                     "n": "±1 point"},
          needs=["daterange", "derive", "binning", "computed"]),
    ]),
]
