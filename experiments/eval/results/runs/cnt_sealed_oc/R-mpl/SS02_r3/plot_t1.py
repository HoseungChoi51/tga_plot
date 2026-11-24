import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# 원인별 건수 계산
cause_counts = df['원인'].value_counts()

# 막대그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(cause_counts.index, cause_counts.values, color='steelblue', edgecolor='black')

# 그래프 스타일링
ax.set_title('설비 정지 원인별 건수', fontsize=16, fontweight='bold')
ax.set_xlabel('정지 원인', fontsize=12)
ax.set_ylabel('건수', fontsize=12)
ax.tick_params(axis='both', which='major', labelsize=10)

# 각 막대 위에 수치 표시
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=10)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "downtime_cause_count.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
