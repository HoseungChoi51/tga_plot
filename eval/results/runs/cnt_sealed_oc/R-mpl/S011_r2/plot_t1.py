import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
sheet_name = "런로그"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    raise ValueError(f"Failed to read data file: {e}")

# 컬럼 이름 공백 및 특수문자 처리 (실제 Excel 헤더가 다를 수 있으므로 가장 유사한 컬럼 검색)
def find_column(df, keywords):
    for col in df.columns:
        if any(kw in str(col) for kw in keywords):
            return col
    return None

col_date = find_column(df, ['일자', 'Date'])
col_reactor = find_column(df, ['반응기', 'Reactor'])
col_prod_rate = find_column(df, ['생산속도', 'Production Rate', 'g/h'])
col_op_time = find_column(df, ['가동시간', 'Operating Time', 'h'])

if not all([col_date, col_reactor, col_prod_rate, col_op_time]):
    print("Available columns:", df.columns.tolist())
    missing = []
    if not col_date: missing.append('date')
    if not col_reactor: missing.append('reactor')
    if not col_prod_rate: missing.append('production rate')
    if not col_op_time: missing.append('operating time')
    raise KeyError(f"Could not find required columns among {missing}. Available: {df.columns.tolist()}")

# 날짜 변환
# openpyxl이 보통 datetime object를 반환하지만, 문자열인 경우를 대비해 errors='coerce'와 format=None 사용 후 NaT 확인
df[col_date] = pd.to_datetime(df[col_date], errors='coerce')

# 만약 NaT가 많다면 런ID에서 파싱 시도
if df[col_date].isna().sum() > len(df) * 0.5:
    import re
    def extract_month_from_runid(run_id):
        try:
            parts = str(run_id).split('-')
            # 예상 형식: R1-260302-1 -> index 1 is date part
            if len(parts) >= 2 and len(parts[1]) == 6:
                yy = parts[1][:2]
                mm = parts[1][2:4]
                year = '20' + yy
                return f"{year}-{mm}"
        except:
            pass
        return None
    
    # 유효한 날짜가 없는 행은 런ID로 월 추정하여 대체하거나, 일단 런ID 기반으로 그룹화 키 생성
    # 더 안전한 방법: 런ID 자체가 고유 식별자이므로 여기서 직접 파싱
    df['월'] = df['런ID'].apply(extract_month_from_runid) if '런ID' in df.columns else None
    
    if df['월'].isna().all():
         raise ValueError("Cannot determine month from date or run ID.")
else:
    # 정상적인 datetime 변환 성공 시 YYYY-MM 추출
    df['월'] = df[col_date].dt.strftime('%Y-%m')

# 유효한 월 정보 있는 행만 필터링
df_valid = df.dropna(subset=['월']).copy()

if df_valid.empty:
    raise ValueError("No valid rows with month information.")

# 생산량 계산: g -> kg
# 생산속도(g/h) * 가동시간(h) / 1000
df_valid['런별_생산량_kg'] = (df_valid[col_prod_rate] * df_valid[col_op_time]) / 1000

# 월별, 반응기별 합산
pivot_data = df_valid.pivot_table(values='런별_생산량_kg', index='월', columns=col_reactor, aggfunc='sum')

# 결측치 0으로 채움
pivot_data = pivot_data.fillna(0)

# 월 순서 정렬
pivot_data = pivot_data.sort_index()

# 플롯 생성
fig, ax = plt.subplots(figsize=(12, 7))

# 반응기 리스트 (정렬된 열 이름)
reactors = sorted(pivot_data.columns.tolist())

# 색상 팔레트
colors = ['#FF6961', '#77DD77', '#6EC5D4', '#FDFD96', '#8A2BE2', '#DEB887', '#4682B4', '#DAA520']

bottoms = None
for i, reactor in enumerate(reactors):
    values = pivot_data[reactor]
    label = f"{reactor} 반응기"
    color = colors[i % len(colors)]
    
    if bottoms is None:
        bars = ax.bar(pivot_data.index.astype(str), values, label=label, color=color, edgecolor='white', linewidth=0.5)
        bottoms = values.copy()
    else:
        bars = ax.bar(pivot_data.index.astype(str), values, bottom=bottoms, label=label, color=color, edgecolor='white', linewidth=0.5)
        bottoms += values

# 차원 설정
ax.set_title('월별 반응기별 누적 생산량 (kg)', fontsize=16, pad=20)
ax.set_xlabel('월', fontsize=12)
ax.set_ylabel('누적 생산량 (kg)', fontsize=12)

# 범례를 그래프 바깥 오른쪽에 배치
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="반응기", fontsize=10)

ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.tick_params(axis='x', rotation=45)

# 레이아웃 조정: 범례 공간 확보를 위해 tight_layout 대신 subplots_adjust 또는 savefig의 bbox_inches 사용 권장
# 여기서는 savefig 시 bbox_inches='tight'가 범례까지 포함하도록 도와줌
plt.tight_layout() 

# 저장
output_filename = os.path.join(OUT_DIR, "monthly_production_cumulative_bar.png")
# bbox_inches='tight'는 축 밖으로 나간 요소(범례 등)를 잘리지 않게 함
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close(fig)

print(f"Plot saved to {output_filename}")
