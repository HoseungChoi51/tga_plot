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
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 컬럼명 확인 및 유연하게 찾기
target_col = None
for col in df.columns:
    if 'CNT수율' in str(col):
        target_col = col
        break

if target_col is None:
    for col in df.columns:
        if '수율' in str(col):
            target_col = col
            break
            
if target_col is None:
    raise ValueError("CNT 수율 컬럼을 찾을 수 없습니다.")

# 작업자 컬럼도 안전하게 찾기
worker_col = None
for col in df.columns:
    if '작업자' in str(col):
        worker_col = col
        break

if worker_col is None:
    # 미리보기에 따르면 G열이 작업자임
    worker_col = df.columns[6] 

# 타입 변환: 수율 컬럼을 숫자로 변환 (object dtype 문제 해결)
df[target_col] = pd.to_numeric(df[target_col], errors='coerce')

# NaN 값 제거
df_clean = df.dropna(subset=[target_col, worker_col])

# 작업자별 평균 CNT 수율 계산
grouped = df_clean.groupby(worker_col)[target_col].mean().reset_index()

# 높은 순으로 정렬 후 상위 5개 선택
top_5 = grouped.sort_values(by=target_col, ascending=False).head(5)

# 플롯 생성
fig, ax = plt.subplots(figsize=(10, 6))

# 가로막대 차트 (barh)
bars = ax.barh(top_5[worker_col], top_5[target_col], color='skyblue', edgecolor='black')

# 값 라벨 추가
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.1, bar.get_y() + bar.get_height()/2., f'{width:.2f}', 
            va='center', ha='left', fontsize=10)

# 레이블 및 제목 설정
ax.set_xlabel('평균 CNT 수율 (g/g-cat)', fontsize=12)
ax.set_title('작업자별 평균 CNT 수율 (상위 5명)', fontsize=14, fontweight='bold')

# y축 레이블 간격 조정 등 필요시
ax.invert_yaxis() # 막대가 위에서 아래로 정렬되도록 (높은 값이 위에 오게 하려면 역순이 아니라 정렬된 상태 그대로 두면 됨. barh는 기본이 아래->위인데, 정렬한 top_5를 넣으면 위에서부터 내려옴. 일반적으로 높은 값이 위쪽이나 왼쪽에 오길 원함. barh의 경우 첫 번째 항목이 가장 위에 그려짐.)

# x축 범위 조정
max_val = top_5[target_col].max()
ax.set_xlim(0, max_val * 1.15)

# 그리드 추가
ax.xaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

# 레이아웃 조정
plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "worker_yield_top5.png")
plt.savefig(save_path, dpi=300)
plt.close()
