import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 열 이름 확인: 'CNT'와 '수율'이 포함된 컬럼 찾기
col_yield = None
for col in df.columns:
    if isinstance(col, str) and ('CNT' in col and '수율' in col):
        col_yield = col
        break

if col_yield is None:
    raise ValueError("CNT 수율 컬럼을 찾을 수 없습니다.")

# 반응기 컬럼 확인
col_reactor = "반응기"
if col_reactor not in df.columns:
    # 혹시 다른 이름일 경우 검색
    for col in df.columns:
        if "반응기" in str(col):
            col_reactor = col
            break

# 데이터 정제: 수율 컬럼을 숫자형으로 변환 (object dtype 에러 방지)
df[col_yield] = pd.to_numeric(df[col_yield], errors='coerce')
df = df.dropna(subset=[col_yield])

# 반응기별 수율 비교를 위한 그룹화 및 통계 계산
reactor_stats = df.groupby(col_reactor)[col_yield].agg(['mean', 'std', 'count']).reset_index()
reactor_stats.columns = ['반응기', '평균_수율', '표준편차', '개수']

# 박스 플롯용 데이터 준비 (반응기별로 리스트로 묶음)
box_data = [df[df[col_reactor] == r][col_yield].dropna().values for r in sorted(df[col_reactor].unique())]
labels = sorted(df[col_reactor].unique())

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 박스 플롯 생성
bp = ax.boxplot(box_data, labels=labels, patch_artist=True, showmeans=True)

# 색상 지정
colors = ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)

# 축 라벨 및 제목
ax.set_title('반응기별 CNT 수율 분포 비교', fontsize=14, pad=15)
ax.set_xlabel('반응기', fontsize=12)
ax.set_ylabel('CNT 수율 (g/g-cat)', fontsize=12)
ax.grid(True, linestyle='--', alpha=0.7)

# 통계 정보 텍스트로 추가
stats_text = "\n".join([f"{row['반응기']}: 평균 {row['평균_수율']:.2f} ± {row['표준편차']:.2f} (N={int(row['개수'])})" 
                        for _, row in reactor_stats.iterrows()])
ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, va='top', ha='right', 
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8), fontsize=9)

# 저장
output_file = os.path.join(OUT_DIR, "reactor_yield_comparison.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"Plot saved to {output_file}")
