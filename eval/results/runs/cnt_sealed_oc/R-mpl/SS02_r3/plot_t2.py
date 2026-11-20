import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# 원인별 건수 계산
cause_counts = df['원인'].value_counts()

# 파이 차트 그리기
fig, ax = plt.subplots(figsize=(10, 8))

# 색상 팔레트 지정 (가독성을 위해)
colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99', '#c2c2f0']

wedges, texts, autotexts = ax.pie(
    cause_counts.values, 
    labels=cause_counts.index, 
    autopct='%1.1f%%',
    startangle=140,
    colors=colors,
    pctdistance=0.85,
    textprops={'fontsize': 12}
)

# 비율 텍스트 굵게 및 검은색으로 변경
for autotext in autotexts:
    autotext.set_color('black')
    autotext.set_fontweight('bold')

ax.set_title('설비 정지 원인별 분포', fontsize=16, fontweight='bold')

# 원형 유지
ax.axis('equal')

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "downtime_cause_pie.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
