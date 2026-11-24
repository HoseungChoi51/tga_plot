import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼 이름 확인 및 공백 제거 (실제 파일의 헤더와 다를 수 있어 안전장치)
df.columns = df.columns.str.strip()

# 날짜 컬럼 처리: 'yyyy-mm-dd' 문자열이 섞여 있을 수 있으므로 errors='coerce' 사용
# 이미 datetime인 경우에도 안전하며, 파싱 실패 시 NaT로 변환되어 groupby에서 제외됨
if '일자' in df.columns:
    df['일자'] = pd.to_datetime(df['일자'], format='%Y-%m-%d', errors='coerce')
else:
    # 만약 일자 컬럼이 없다면 주차만으로도 그룹핑 가능하지만, 여기서는 존재한다고 가정하고 진행
    pass

# 유효한 날짜가 있는 행만 필터링 (선택 사항이지만 안전을 위해)
# 만약 일자 컬럼이 없거나 모두 NaT라면 원본 df를 사용
if '일자' in df.columns and not df['일자'].isna().all():
    df_valid = df.dropna(subset=['일자']).copy()
else:
    df_valid = df.copy()

# CNT수율 컬럼명 찾기 (유연하게 처리)
yield_col = None
for col in df_valid.columns:
    if 'CNT수율' in str(col):
        yield_col = col
        break

if yield_col is None:
    raise ValueError("CNT수율 컬럼을 찾을 수 없습니다.")

# 주별, 반응기별 평균 수율 계산
weekly_reactor_yield = df_valid.groupby(['주차', '반응기'])[yield_col].mean().reset_index()

# 플롯 생성
fig, ax = plt.subplots(figsize=(12, 6))

# 반응기별 색상 정의
colors = {'R1': '#1f77b4', 'R2': '#ff7f0e', 'R3': '#2ca02c', 'R4': '#d62728'}

for reactor in ['R1', 'R2', 'R3', 'R4']:
    subset = weekly_reactor_yield[weekly_reactor_yield['반응기'] == reactor]
    # 주차 순서대로 정렬하여 선 그래프가 꼬이지 않도록 함
    subset_sorted = subset.sort_values('주차')
    ax.plot(subset_sorted['주차'], subset_sorted[yield_col], marker='o', linestyle='-', label=reactor, color=colors[reactor], alpha=0.8)

# 전체 평균 수율 (참고용 점선)
overall_weekly_mean = df_valid.groupby('주차')[yield_col].mean().reset_index().sort_values('주차')
ax.plot(overall_weekly_mean['주차'], overall_weekly_mean[yield_col], linestyle='--', color='black', label='전체 평균', linewidth=2)

# 라벨링 및 제목
ax.set_title('기간(주차)에 따른 반응기별 평균 CNT 수율 추이', fontsize=14, pad=15)
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel(f'평균 {yield_col}', fontsize=12)
ax.legend(title='반응기', loc='best')
ax.grid(True, linestyle=':', alpha=0.6)

# x축 눈금 조정
max_week = int(df_valid['주차'].max())
step = 2 if max_week > 20 else 1
ax.set_xticks(np.arange(1, max_week + 1, step=step))

plt.tight_layout()

# 저장
output_filename = os.path.join(OUT_DIR, "yield_trend_by_week_and_reactor.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()

print(f"그래프가 {output_filename}에 저장되었습니다.")
