import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기 (시트 '주간요약' 사용)
file_path = "data/run_log.xlsx"
df_weekly = pd.read_excel(file_path, sheet_name="주간요약")

# 컬럼명 확인
if "주차" not in df_weekly.columns or "총생산량(kg)" not in df_weekly.columns:
    raise ValueError("필요한 컬럼이 없습니다.")

# 정렬
df_weekly_sorted = df_weekly.sort_values(by="주차").reset_index(drop=True)

# 색상 리스트 생성: 14주차 미만은 steelblue, 14주차 이상은 indianred (또는 다른 구분 가능한 색)
colors = ['steelblue' if w < 14 else 'indianred' for w in df_weekly_sorted["주차"]]

# 그래프 그리기
fig, ax = plt.subplots(figsize=(12, 6))

bars = ax.bar(df_weekly_sorted["주차"], df_weekly_sorted["총생산량(kg)"], color=colors, edgecolor='black')

# 축 라벨 및 제목
ax.set_xlabel("주차", fontsize=12)
ax.set_ylabel("총생산량 (kg)", fontsize=12)
ax.set_title("주차별 CNT 총생산량 (14주차부터 색상 구분)", fontsize=14)

# x축 눈금 조정
ax.set_xticks(df_weekly_sorted["주차"])
ax.tick_params(axis='x', rotation=45)

# 막대 위에 값 표시
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=8)

# 범례 추가 (색상 설명)
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='steelblue', label='~13주차'),
                   Patch(facecolor='indianred', label='14주차~')]
ax.legend(handles=legend_elements, loc='upper left')

plt.tight_layout()

# 저장
output_file = os.path.join(OUT_DIR, "weekly_production_bar_colored.png")
plt.savefig(output_file, dpi=300)
plt.close(fig)

print(f"Graph saved to {output_file}")
