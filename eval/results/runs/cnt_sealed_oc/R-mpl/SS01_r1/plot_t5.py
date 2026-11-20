import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t5"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기 (시트 '주간요약' 사용)
file_path = "data/run_log.xlsx"
df_weekly = pd.read_excel(file_path, sheet_name="주간요약")

# 컬럼명 확인
if "주차" not in df_weekly.columns or "총생산량(kg)" not in df_weekly.columns:
    raise ValueError("필요한 컬럼이 없습니다.")

# 정렬 및 인덱스 리셋
df_weekly_sorted = df_weekly.sort_values(by="주차").reset_index(drop=True)

# 평균 계산
avg_1_13 = df_weekly_sorted[df_weekly_sorted["주차"] <= 13]["총생산량(kg)"].mean()
avg_14_26 = df_weekly_sorted[df_weekly_sorted["주차"] >= 14]["총생산량(kg)"].mean()

# 색상 리스트 생성: 14주차 미만은 steelblue, 14주차 이상은 indianred
colors = ['steelblue' if w < 14 else 'indianred' for w in df_weekly_sorted["주차"]]

# 그래프 그리기
# 16:9 비율을 위해 figsize 조정 (예: 16 x 9 inch)
fig, ax = plt.subplots(figsize=(16, 9))

bars = ax.bar(df_weekly_sorted["주차"], df_weekly_sorted["총생산량(kg)"], color=colors, edgecolor='black')

# 가로선 추가
ax.axhline(y=avg_1_13, color='darkblue', linestyle='--', linewidth=1.5, label=f'1~13주 평균 ({avg_1_13:.2f} kg)')
ax.axhline(y=avg_14_26, color='darkred', linestyle='--', linewidth=1.5, label=f'14~26주 평균 ({avg_14_26:.2f} kg)')

# 축 라벨 및 제목 유지
ax.set_xlabel("주차", fontsize=12)
ax.set_ylabel("생산량 (kg)", fontsize=12)
ax.set_title("주간 생산량 추이 (3~8월)", fontsize=14)

# x축 눈금 조정
ax.set_xticks(df_weekly_sorted["주차"])
ax.tick_params(axis='x', rotation=45)

# 막대 위에 값 표시
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=8)

# 범례 추가
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='steelblue', label='~13주차'),
                   Patch(facecolor='indianred', label='14주차~')]

handles, labels = ax.get_legend_handles_labels()
legend_elements += handles
ax.legend(handles=legend_elements, loc='upper left')

plt.tight_layout()

# 저장: 16:9 비율, 200 dpi
output_file = os.path.join(OUT_DIR, "weekly_production_bar_slide.png")
plt.savefig(output_file, dpi=200)
plt.close(fig)

print(f"Graph saved to {output_file}")
