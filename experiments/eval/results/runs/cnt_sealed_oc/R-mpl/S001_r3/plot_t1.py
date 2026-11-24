import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# 데이터 경로
FILE_PATH = "data/run_log.xlsx"
SHEET_NAME = "런로그"

# 데이터 읽기
df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)

# 컬럼명 정리: 앞뒤 공백 제거 및 내부 공백 정규화 (다중 공백을 단일로)
df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

# 날짜 변환 및 필터링 (3월~8월)
if not pd.api.types.is_datetime64_any_dtype(df['일자']):
    df['일자'] = pd.to_datetime(df['일자'], errors='coerce')
    df = df.dropna(subset=['일자'])

mask_date = (df['일자'].dt.month >= 3) & (df['일자'].dt.month <= 8)
df_filtered = df[mask_date].copy()

# 필요한 컬럼명 확인 및 안전한 접근
# 미리보기에 따르면 '생산속도 (g/h)'와 '가동시간 (h)'가 존재해야 함
col_speed = '생산속도 (g/h)'
col_time = '가동시간 (h)'

# 만약 컬럼명이 미세하게 다르다면(예: 전각/반각 괄호 등) 처리할 수 있도록 로깅하거나 자동 교정 시도 가능하나,
# 여기서는 str.replace로 정규화된 이름이 맞다고 가정하고 진행.
if col_speed not in df_filtered.columns or col_time not in df_filtered.columns:
    # 디버깅용 출력 생략, 실제 실행 시 에러 발생 방지를 위해 존재하는지 체크하고 없으면 유사 컬럼 찾기 시도
    # 간단한 대응: 컬럼명 매핑을 다시 한번 확인
    print("Warning: Column names might differ slightly.")
    # 실제로는 위 정규화가 잘 작동했으므로 이 블록은 통과될 가능성이 높음.

# 생산량 계산: 생산속도(g/h) * 가동시간(h) -> g, 그리고 kg으로 환산 (/1000)
df_filtered[col_speed] = pd.to_numeric(df_filtered[col_speed], errors='coerce')
df_filtered[col_time] = pd.to_numeric(df_filtered[col_time], errors='coerce')

# 유효한 데이터만 남기기
df_valid = df_filtered.dropna(subset=[col_speed, col_time])

# 계산용 임시 컬럼 생성
df_valid['총생산량_kg'] = (df_valid[col_speed] * df_valid[col_time]) / 1000

# 반응기별 총 생산량 집계
grouped = df_valid.groupby('반응기')['총생산량_kg'].sum().reset_index()

# 정렬 (R1, R2, R3, R4 순서대로 나오도록 categorical 설정 또는 정렬)
reactors_order = ['R1', 'R2', 'R3', 'R4']
grouped['반응기'] = pd.Categorical(grouped['반응기'], categories=reactors_order, ordered=True)
grouped = grouped.sort_values('반응기')

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 6))

bars = ax.bar(grouped['반응기'], grouped['총생산량_kg'], color=['#4E79A7', '#F28E2B', '#E15759', '#76B7B2'])

# 막대 위에 수치 표시
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=12)

ax.set_xlabel('반응기', fontsize=14)
ax.set_ylabel('누적 총 생산량 (kg)', fontsize=14)
ax.set_title('2026년 3월~8월 반응기별 누적 총 생산량', fontsize=16)
ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.set_ylim(0, max(grouped['총생산량_kg']) * 1.15 if not grouped.empty else 100) # 상단 여백 확보, 빈 경우 대비

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "reactor_production_total.png"), dpi=300)
plt.close()
