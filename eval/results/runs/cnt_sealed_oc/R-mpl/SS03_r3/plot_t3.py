import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# 설정
OUT_DIR = "out/t3"
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
if date_col not in df.columns:
    date_cols = [c for c in df.columns if '일자' in str(c)]
    if date_cols:
        date_col = date_cols[0]

try:
    df['날짜_변환'] = pd.to_datetime(df[date_col], format='%Y-%m-%d', errors='coerce')
except ValueError:
    df['날짜_변환'] = pd.to_datetime(df[date_col], errors='coerce')

# 변환된 날짜에서 월 추출
df['월'] = df['날짜_변환'].dt.month
df['월라벨'] = df['월'].apply(lambda x: f"{x}월" if pd.notna(x) else "")

# 합격 여부 계산 (A 또는 B 등급)
df['is_pass'] = df[grade_col].isin(['A', 'B']).astype(int)

# 반응기별, 월별 평균 합격률 계산
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

# Y축 범위 설정: 요청대로 40~100으로 고정
ax.set_ylim(40, 100)

# 목표선 90% 점선 추가
ax.axhline(y=90, color='red', linestyle='--', linewidth=1.5, label='목표 (90%)')

ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.legend(title='구분', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
output_filename = os.path.join(OUT_DIR, "monthly_reactor_pass_rate.png")
plt.savefig(output_filename, dpi=300)
plt.close()
