import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name="런로그")
df_weekly = pd.read_excel(file_path, sheet_name="주간요약")

# 데이터 전처리
# 등급이 A/B인 경우를 합격(pass), C인 경우를 불량(fail)으로 가정
# 또는 기존 주간요약 시트에 '합격률'이 있으므로 이를 활용할 수도 있지만, 
# 원본 런로그 기준으로 최신/정확한 불량을 계산하기 위해 런로그에서 직접 집계합니다.
# 주간 요약 시트가 이미 제공되므로, 사용자의 요청("불량 비율 한 장")에 가장 직관적인 것은
# 주별 추이를 보여주는 것입니다. 주간요약 시트의 '합격률'을 이용해 '불량률'을 계산합니다.

# 방법 1: 주간요약 시트 활용 (더 빠르고 정돈됨)
df_plot_data = df_weekly.copy()
df_plot_data['불량률(%)'] = 100 - df_plot_data['합격률(%)']

# 시각화
fig, ax = plt.subplots(figsize=(12, 6))

# 막대 그래프 그리기
bars = ax.bar(df_plot_data['주차'], df_plot_data['불량률(%)'], color='#d9534f', edgecolor='black')

# 평균 선 추가
avg_defect_rate = df_plot_data['불량률(%)'].mean()
ax.axhline(y=avg_defect_rate, color='blue', linestyle='--', linewidth=2, label=f'평균 불량률: {avg_defect_rate:.1f}%')

# 차트 꾸미기
ax.set_title('주별 CNT 생산 불량률 현황', fontsize=16, fontweight='bold')
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('불량률 (%)', fontsize=12)
ax.set_xticks(df_plot_data['주차'])
ax.legend(loc='upper right', fontsize=11)
ax.grid(axis='y', linestyle=':', alpha=0.7)

# 각 막대 위에 값 표시
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{height:.1f}%',
            ha='center', va='bottom', fontsize=9)

plt.tight_layout()
output_file = os.path.join(OUT_DIR, "defect_rate_by_week.png")
plt.savefig(output_file, dpi=300)
plt.close()
