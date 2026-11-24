import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 1. 데이터 로드
# Downtime 데이터 (정지이력 시트)
downtime_df = pd.read_excel("data/downtime.xlsx", sheet_name="정지이력")

# Run Log 데이터 (주간요약 시트)
weekly_summary_df = pd.read_excel("data/run_log.xlsx", sheet_name="주간요약")

# 2. 전처리: Downtime 시간 합산 및 주차 계산
# '일자' 컬럼을 datetime으로 변환 (이미 날짜형일 수 있으나 안전을 위해 pd.to_datetime 사용)
downtime_df['일자'] = pd.to_datetime(downtime_df['일자'])

# 주차 계산 기준일: 2026-03-02 (1주차 시작)
base_date = pd.Timestamp("2026-03-02")

# 주차 산출 공식: ((날짜 - 기준일).days // 7) + 1
# 주의: ISO 주수와 다를 수 있지만 요청사항인 "3월 2일이 1주차"라는 단순 기간 기반 주차를 따름
downtime_df['주차'] = ((downtime_df['일자'] - base_date).dt.days // 7) + 1

# 주차별 총 정지시간(분) 합산 후 시간(h)으로 변환
downtime_grouped = downtime_df.groupby('주차')['정지시간(분)'].sum().reset_index()
downtime_grouped['총정지시간_h'] = downtime_grouped['정지시간(분)'] / 60.0

# 3. 데이터 병합
# 주간요약 시트의 '주차'와 downtime에서 계산된 '주차'를 기준으로 merge
merged_df = pd.merge(
    weekly_summary_df[['주차', '총생산량(kg)']], 
    downtime_grouped[['주차', '총정지시간_h']], 
    on='주차', 
    how='inner'
)

# 만약 특정 주차에 downtime 데이터가 없다면 NaN 처리 후 삭제하거나 0으로 채워야 할 수 있음
# 여기서는 inner join을 사용하여 양쪽 모두 데이터가 있는 주차만 분석 대상으로 함

# 결측치 확인 및 제거 (안전장치)
merged_df = merged_df.dropna(subset=['총정지시간_h', '총생산량(kg)'])

# 4. 시각화: 산점도
fig, ax = plt.subplots(figsize=(10, 8))

scatter = ax.scatter(
    x=merged_df['총정지시간_h'],
    y=merged_df['총생산량(kg)'],
    s=100,
    alpha=0.7,
    edgecolors='black',
    c='skyblue'
)

# 축 라벨 및 제목
ax.set_xlabel("주차별 총 정지시간 (h)", fontsize=12)
ax.set_ylabel("주차별 총생산량 (kg)", fontsize=12)
ax.set_title("주차별 총 정지시간과 총생산량의 관계", fontsize=14, pad=15)

# 그리드 표시
ax.grid(True, linestyle='--', alpha=0.6)

# 통계적 상관관계 텍스트 추가 (Pearson correlation)
if len(merged_df) > 1:
    corr_matrix = merged_df[['총정지시간_h', '총생산량(kg)']].corr()
    correlation_value = corr_matrix.loc['총정지시간_h', '총생산량(kg)']
    
    # 상관계수를 그래프 우측 상단에 표시
    ax.text(
        0.95, 0.95, f"피어슨 상관계수 (r): {correlation_value:.3f}",
        transform=ax.transAxes,
        horizontalalignment='right',
        verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8),
        fontsize=11
    )

plt.tight_layout()

# 5. 저장
output_path = os.path.join(OUT_DIR, "scatter_downtime_vs_production.png")
plt.savefig(output_path, dpi=300)
plt.close(fig)

print(f"Plot saved to {output_path}")
