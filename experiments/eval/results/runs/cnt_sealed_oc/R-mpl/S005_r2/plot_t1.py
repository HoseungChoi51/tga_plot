import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 등급 컬럼 이름 확인 및 정규화
grade_col = '등급 (A/B/C)'
if grade_col not in df.columns:
    cols = [c for c in df.columns if '등급' in str(c)]
    if cols:
        grade_col = cols[0]

# 날짜 변환 처리 강화
# 미리보기에 헤더가 '일자 (yyyy-mm-dd)' 형태로 되어 있을 가능성이 높음.
# pandas read_excel이 헤더를 읽을 때 괄호 안 내용까지 포함할 수 있음.
date_col = None
for col in df.columns:
    if '일자' in str(col):
        date_col = col
        break

if date_col is None:
    raise ValueError("날짜 컬럼을 찾을 수 없습니다.")

# 문자열로 변환 후 파싱 시도, 실패 시 오류 무시하고 NaT로 처리하거나 다른 포맷 시도
try:
    df['일자_dt'] = pd.to_datetime(df[date_col], format='mixed', errors='coerce')
except:
    # 만약 'mixed'가 지원되지 않거나 문제가 있으면, 각 값을 개별 파싱하거나 표준 형식 강제 변환
    def parse_date(x):
        if pd.isna(x): return pd.NaT
        try:
            # 이미 datetime 객체일 경우
            if isinstance(x, pd.Timestamp): return x
            # 문자열일 경우 기본 파싱 시도
            return pd.to_datetime(str(x))
        except:
            return pd.NaT
    
    df['일자_dt'] = df[date_col].apply(parse_date)

# 유효한 날짜만 필터링하여 정렬
df_valid = df.dropna(subset=['일자_dt']).copy()
df_valid.sort_values('일자_dt', inplace=True)

# 불량 정의 (C등급 = 불량으로 가정 - 임원 보고용 핵심 지표 선정 기준)
# 참고: 주간요약의 합격률과 비교하기 위해 B+C를 불용으로 할 수도 있으나, 
# 일반적으로 Grade C가 가장 심각한 불량으로 간주되므로 이를 우선시함.
# 만약 데이터상 B도 불량률이 매우 낮다면 C 만으로 충분하지만, 여기서는 C를 기준으로 함.
df_valid['is_defect'] = (df_valid[grade_col] == 'C').astype(int)

# 일별 통계 계산
daily_stats = df_valid.groupby('일자_dt').agg(
    total_runs=('is_defect', 'count'),
    defect_count=('is_defect', 'sum')
).reset_index()

daily_stats['defect_rate'] = (daily_stats['defect_count'] / daily_stats['total_runs']) * 100

# 이동평균 (7일)
daily_stats['moving_avg_defect_rate'] = daily_stats['defect_rate'].rolling(window=7, min_periods=1).mean()

# 최신 데이터 확인 (이번 주)
latest_date = daily_stats['일자_dt'].max()
# 최근 7일을 "이번 주"로 간주
recent_week_mask = daily_stats['일자_dt'] >= (latest_date - pd.Timedelta(days=6))
recent_week_data = daily_stats[recent_week_mask]

current_week_defect_rate = recent_week_data['defect_rate'].mean()
overall_defect_rate = (df_valid['is_defect'].sum() / len(df_valid)) * 100

# 플롯 그리기
fig, ax1 = plt.subplots(figsize=(14, 8))

x = daily_stats['일자_dt']
y_bar = daily_stats['defect_rate']
y_line = daily_stats['moving_avg_defect_rate']

# 일별 불량률 막대 그래프
bars = ax1.bar(x, y_bar, color='lightcoral', alpha=0.6, label='일별 불량률 (%)')
ax1.set_xlabel('날짜')
ax1.set_ylabel('일별 불량률 (%)', color='tab:red')
ax1.tick_params(axis='y', labelcolor='tab:red')

# Y축 범위 설정: 최대값보다 조금 더 크게
max_val = max(daily_stats['defect_rate'].max(), 50)
ax1.set_ylim(0, max_val * 1.1) 

# 이동평균선
ax2 = ax1.twinx()
line = ax2.plot(x, y_line, color='darkblue', linewidth=2.5, label='7일 이동평균 불량률 (%)')
ax2.set_ylabel('이동평균 불량률 (%)', color='tab:blue')
ax2.tick_params(axis='y', labelcolor='tab:blue')
ax2.set_ylim(ax1.get_ylim()) # 동일한 스케일 유지

# 제목 및 레전드
ax1.set_title(f'CNT 생산 불량률 분석 (기준: Grade C)\n전체 평균: {overall_defect_rate:.1f}% | 최근 1주일 평균: {current_week_defect_rate:.1f}%', fontsize=16, fontweight='bold')

# 범례 통합
lines_labels = ax1.get_legend_handles_labels()
by_lines_labels = ax2.get_legend_handles_labels()
ax1.legend(lines_labels[0] + by_lines_labels[0], lines_labels[1] + by_lines_labels[1], loc='upper right')

# 그리드
ax1.grid(True, linestyle='--', alpha=0.3)

# x축 날짜 포맷팅
fig.autofmt_xdate(rotation=45)

# 텍스트 애노테이션으로 핵심 수치 강조
textstr = f'최근 1주일\n불량률: {current_week_defect_rate:.2f}%'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax1.text(0.02, 0.95, textstr, transform=ax1.transAxes, fontsize=12,
         verticalalignment='top', bbox=props)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "defect_rate_report.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
