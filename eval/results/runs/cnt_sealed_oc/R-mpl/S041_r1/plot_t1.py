import pandas as pd
import matplotlib.pyplot as plt
import os

# 환경 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# 촉매 로트별 런 횟수 계산
lot_counts = df['촉매로트'].value_counts().sort_index()

# 막대 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(lot_counts.index, lot_counts.values, color='steelblue', edgecolor='black')

# 각 막대 위에 값 표시
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=12)

# 축 레이블 및 제목 설정
ax.set_xlabel('촉매 로트', fontsize=14)
ax.set_ylabel('런 횟수 (회)', fontsize=14)
ax.set_title('촉매 로트별 런 횟수 분포', fontsize=16, pad=15)

# y축 눈금 간격 조정 (필요시)
max_count = lot_counts.max()
ax.set_ylim(0, max_count * 1.1)

# 격자선 추가 (y축 기준)
ax.grid(axis='y', linestyle='--', alpha=0.7)

# 레이아웃 정리
plt.tight_layout()

# 저장
output_filename = "lot_run_counts.png"
output_path = os.path.join(OUT_DIR, output_filename)
plt.savefig(output_path, dpi=300)
plt.close()

print(f"Plots saved to {output_path}")
