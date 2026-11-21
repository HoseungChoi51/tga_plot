import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t4"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# R2만 필터링
df_r2 = df[df['반응기'] == 'R2']

# 원인별 정지시간 합계 계산
cause_sums = df_r2.groupby('원인')['정지시간(분)'].sum()

# 파이 차트 그리기
fig, ax = plt.subplots(figsize=(10, 8))

# 색상 팔레트 지정 (가독성을 위해)
# 원인 종류 수에 맞춰 색상 할당
colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99', '#c2c2f0', '#ffb3e6', '#d4a5a5']
selected_colors = colors[:len(cause_sums)] if len(cause_sums) <= len(colors) else colors * ((len(cause_sums)//len(colors))+1)

wedges, texts, autotexts = ax.pie(
    cause_sums.values, 
    labels=cause_sums.index, 
    autopct='%1.1f%%',
    startangle=140,
    colors=selected_colors,
    pctdistance=0.85,
    textprops={'fontsize': 12}
)

# 비율 텍스트 굵게 및 검은색으로 변경
for autotext in autotexts:
    autotext.set_color('black')
    autotext.set_fontweight('bold')

ax.set_title('R2 반응기 설비 정지 원인별 정지시간 분포', fontsize=16, fontweight='bold')

# 원형 유지
ax.axis('equal')

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "downtime_cause_time_pie_R2.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
