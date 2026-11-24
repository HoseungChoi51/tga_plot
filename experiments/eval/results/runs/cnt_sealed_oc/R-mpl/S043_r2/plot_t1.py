import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/run_log.xlsx"
sheet_name = "런로그"

# 엑셀 파일 읽기
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 열 이름 정제 (공백 등 제거) 및 필요 컬럼만 선택
df.columns = df.columns.str.strip()
required_cols = ['주차', '반응기', 'IG/ID']
if not all(col in df.columns for col in required_cols):
    # 혹시 이름이 미세하게 다를 경우를 대비해 fuzzy match 또는 직접 확인이 필요하지만, 
    # 미리보기에 따라 정확히 일치한다고 가정합니다.
    raise ValueError(f"필요한 컬럼이 없습니다: {required_cols} vs {df.columns.tolist()}")

work_df = df[required_cols].copy()

# 결측치 처리 (없다고 가정하나 안전을 위해 삭제)
work_df.dropna(inplace=True)

# 주차가 수치형인지 확인
work_df['주차'] = pd.to_numeric(work_df['주차'], errors='coerce')
work_df['IG/ID'] = pd.to_numeric(work_df['IG/ID'], errors='coerce')
work_df.dropna(subset=['주차', 'IG/ID'], inplace=True)

# 반응기 정렬 (R1, R2, R3, R4 순서로)
reactors = ['R1', 'R2', 'R3', 'R4']
work_df['반응기'] = pd.Categorical(work_df['반응기'], categories=reactors, ordered=True)

# 피벗 테이블 생성: 행=주차, 열=반응기, 값=IG/ID 평균
pivot_table = work_df.pivot_table(index='주차', columns='반응기', values='IG/ID', aggfunc='mean')

# 모든 주차가 존재하는지 확인하고 없으면 채우기 (색상 표현 시 누락 방지)
all_weeks = sorted(work_df['주차'].unique())
pivot_table = pivot_table.reindex(all_weeks)

# NaN은 색상에 영향을 주므로 적절히 처리하거나, heatmap에서는 무시되도록 두는 것이 일반적입니다.
# 여기서는 데이터가 있는 곳만 그리겠습니다.

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 8))

# seaborn의 heatmap과 유사한 효과를 위해 matplotlib의 imshow 사용
im = ax.imshow(pivot_table.T.values, cmap='YlOrRd', aspect='auto', origin='lower')

# 색상 바 추가
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('평균 IG/ID 비율', rotation=-90, va="bottom", fontsize=12)

# 축 라벨 설정
ax.set_xticks(np.arange(len(all_weeks)))
ax.set_yticks(np.arange(len(reactors)))
ax.set_xticklabels([f"W{int(w)}" for w in all_weeks], rotation=90)
ax.set_yticklabels(reactors)

# 눈금 간격 조정
ax.tick_params(top=False, bottom=True, left=True, right=False, labelbottom=True, labelleft=True)

# 격자선 끄기 (Heatmap은 보통 격자선이 없음)
ax.grid(False)

# 타이틀
ax.set_title("반응기별 주당 평균 CNT IG/ID 비율 변화", fontsize=16, pad=20)
ax.set_xlabel("주차 (Week)", fontsize=12)
ax.set_ylabel("반응기 (Reactor)", fontsize=12)

# 각 셀의 값을 텍스트로 표시 (선택사항이지만 요청에 "표처럼"이라고 했으므로 도움이 될 수 있음)
# 다만 주차가 많으면 복잡해질 수 있어 조건부 또는 생략 가능. 여기서는 가독성을 위해 생략하거나, 
# 만약 사용자가 명시적으로 숫자를 원했다면 넣어야 하지만 "색으로 보여 주는" 것을 강조했으므로 색상 중심입니다.
# 너무 많은 주(26주) * 4반응기 = 104개 셀. 텍스트가 빽빽할 수 있으므로 생략하겠습니다.

# 레이아웃 정리
plt.tight_layout()

# 저장
output_file = os.path.join(OUT_DIR, "ig_id_by_reactor_week_heatmap.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"그래프가 {output_file} 에 저장되었습니다.")
