import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# 컬럼명 확인 및 매핑
grade_col = [c for c in df.columns if '등급' in str(c)][0]
reactor_col = '반응기'
date_col = '일자'

# 날짜 처리: 미리보기에 따르면 컬럼 헤더 이름이 "일자 (yyyy-mm-dd)"일 수 있음.
# 실제 값은 문자열 또는 datetime일 수 있으므로, 안전한 방식으로 파싱 시도
# 만약 컬럼명이 정확히 '일자'가 아니라면 찾아서 할당
if date_col not in df.columns:
    date_cols = [c for c in df.columns if '일자' in str(c)]
    if date_cols:
        date_col = date_cols[0]

# pd.to_datetime으로 변환 시 errors='coerce'를 사용하여 해석 불가능한 값은 NaT로 만들고, 
# 전체가 실패하는 경우를 방지하기 위해 포맷을 명시하거나 유연하게 처리
try:
    df['날짜_변환'] = pd.to_datetime(df[date_col], format='%Y-%m-%d', errors='coerce')
except ValueError:
    # 형식이 다른 경우 자동 추론 시도
    df['날짜_변환'] = pd.to_datetime(df[date_col], errors='coerce')

# 변환된 날짜에서 월 추출
df['월'] = df['날짜_변환'].dt.month
df['월라벨'] = df['월'].apply(lambda x: f"{x}월" if pd.notna(x) else "")

# 합격 여부 계산 (A 또는 B 등급)
df['is_pass'] = df[grade_col].isin(['A', 'B']).astype(int)

# 반응기별, 월별 평균 합격률 계산
# 유효한 날짜(월)가 있는 행만 사용
valid_df = df.dropna(subset=['월'])
grouped = valid_df.groupby(['월', reactor_col])['is_pass'].mean().reset_index(name='합격률(%)')
grouped['합격률(%)'] *= 100

# 피벗 테이블 형태로 변환하여 막대 그래프 그리기 쉽게 만듦
pivot_df = grouped.pivot(index='월', columns=reactor_col, values='합격률(%)')

# 월 순서 정렬
pivot_df = pivot_df.sort_index()

# 반응기 목록 (정렬된 순서 유지: R1, R2, R3, R4)
reactors = sorted(pivot_df.columns.tolist())
months = pivot_df.index.tolist()
month_labels = [f"{int(m)}월" for m in months]

# 플롯 생성
fig, ax = plt.subplots(figsize=(12, 7))

# 막대 그룹 간 간격을 위한 설정
n_reactors = len(reactors)
bar_width = 0.8 / n_reactors
index = np.arange(len(months))

colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'] # 기본 색상 팔레트 확장 가능

for i, reactor in enumerate(reactors):
    bars = ax.bar(index + i * bar_width, pivot_df[reactor], bar_width, label=reactor, color=colors[i % len(colors)])
    
    # 각 막대에 값 표시
    for bar in bars:
        height = bar.get_height()
        if not np.isnan(height):
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{height:.0f}',
                    ha='center', va='bottom', fontsize=8)

# 축 라벨 및 제목 설정
ax.set_xlabel('월', fontsize=12)
ax.set_ylabel('합격률 (%)', fontsize=12)
ax.set_title('월별 반응기별 CNT 합격률 (A·B 등급)', fontsize=14)

# X축 눈금 설정
ax.set_xticks(index + bar_width * (n_reactors - 1) / 2)
ax.set_xticklabels(month_labels)

# Y축 범위 설정
max_val = pivot_df.max().max()
if max_val > 0:
    ax.set_ylim(0, max_val * 1.15)
else:
    ax.set_ylim(0, 100)

ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.legend(title='반응기', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
output_filename = os.path.join(OUT_DIR, "monthly_reactor_pass_rate.png")
plt.savefig(output_filename, dpi=300)
plt.close()
