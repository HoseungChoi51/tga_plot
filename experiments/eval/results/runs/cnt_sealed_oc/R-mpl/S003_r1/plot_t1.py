import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name='정지이력')

# 날짜 컬럼을 datetime으로 변환 (이미 문자열일 수 있으므로 pd.to_datetime 사용)
# 요청 기간: 6월 1일부터 8월 30일까지
start_date = "2026-06-01"
end_date = "2026-08-30"

df['일자'] = pd.to_datetime(df['일자'])

# 필터링
mask = (df['일자'] >= start_date) & (df['일자'] <= end_date)
filtered_df = df[mask]

# 원인별 건수 계산
counts = filtered_df['원인'].value_counts()

# 데이터가 없는 경우 처리
if counts.empty:
    print("해당 기간에 정지 이력이 없습니다.")
else:
    # 파이차트 그리기 준비
    labels = counts.index.tolist()
    sizes = counts.values.tolist()
    
    # 흑백/회색조 및 해칭 패턴 정의
    # 해칭 패턴: '', '//', '\\\\', '||', '--', 'xx' 등 활용
    hatch_patterns = ['//', '\\\\', '||', '--', 'xx', '..', '++', 'oO']
    # 회색조 색상 (밝은 회색부터 어두운 회색까지 균등 분배)
    n = len(labels)
    if n > 0:
        grays = [str(i/(n+1)) for i in range(1, n+1)]
    else:
        grays = []

    fig, ax = plt.subplots(figsize=(8, 8))
    
    # 파이차트 생성
    # autopct로 퍼센트 표시
    # colors는 흰색 배경 위에 회색조 채우기를 위해 edgecolor 검정으로 구분감 확보 가능하지만
    # 지시사항대로 색 대신 회색 톤이나 해칭으로 구분되게 하므로 facecolor를 회색조로 하고 hatch를 적용
    
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%', 
        startangle=90,
        pctdistance=0.75,
        wedgeprops={'edgecolor': 'black', 'linewidth': 1}
    )
    
    # 각 조각에 회색조 색상과 해칭 적용
    for i, wedge in enumerate(wedges):
        if i < len(grays):
            wedge.set_facecolor(grays[i])
        else:
            wedge.set_facecolor('lightgray')
        
        if i < len(hatch_patterns):
            wedge.set_hatch(hatch_patterns[i % len(hatch_patterns)])
            
    # 텍스트 스타일 조정 (가독성 위해)
    for text in texts + autotexts:
        text.set_fontsize(10)
        text.set_color('black')
        
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    plt.title(f"설비 정지 원인별 비율 ({start_date[:7]} ~ {end_date[:7]})")
    
    save_path = os.path.join(OUT_DIR, "downtime_pie_chart_bw.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"차트가 저장되었습니다: {save_path}")
