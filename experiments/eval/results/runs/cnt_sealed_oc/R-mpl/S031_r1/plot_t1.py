import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼명 정리 (공백이나 특수문자 차이 가능성 대응)
# 미리보기에는 'CNT수율 (g/g-cat)' 라고 되어있지만, 실제 엑셀 파일에서는 공백이 없거나 단위가 괄호 없이 붙어있을 수 있음.
# 안전한 접근: 컬럼명 중 'CNT수율' 을 포함하는 컬럼 찾기
yield_col = None
for col in df_runs.columns:
    if 'CNT수율' in str(col):
        yield_col = col
        break

if yield_col is None:
    raise ValueError("Could not find CNT yield column in the dataframe.")

print(f"Using yield column: '{yield_col}'")

# 일자 컬럼 처리
date_col = None
for col in df_runs.columns:
    if '일자' in str(col):
        date_col = col
        break

if date_col is None:
    # Run ID에서 날짜 추출 시도
    def extract_date_from_runid(run_id):
        if not isinstance(run_id, str):
            return None
        parts = run_id.split('-')
        if len(parts) >= 2:
            date_str = parts[1] # e.g., 260302 -> 2026-03-02
            try:
                # YYMMDD 형식 가정
                return pd.to_datetime(date_str, format='%y%m%d')
            except:
                return None
        return None
    
    df_runs['일자'] = df_runs['런ID'].apply(extract_date_from_runid)
else:
    # 기존 일자 컬럼 사용하되 파싱 실패 시 Run ID 대체
    try:
        # format='mixed' 또는 errors='coerce'로 안전하게 변환 시도
        # 만약 문자열 'yyyy-mm-dd' 가 그대로 들어있다면 파싱 안 될 수 있으므로, 
        # 우선 datetime 객체인지 확인하고 아니라면 파싱 시도
        if not np.issubdtype(df_runs[date_col].dtype, np.datetime64):
             df_runs[date_col] = pd.to_datetime(df_runs[date_col], errors='coerce')
        
        # coerce 결과 NaT가 많으면 Run ID 기반 재시도
        if df_runs[date_col].isna().mean() > 0.5:
             def extract_date_from_runid(run_id):
                if not isinstance(run_id, str):
                    return None
                parts = run_id.split('-')
                if len(parts) >= 2:
                    date_str = parts[1] 
                    try:
                        return pd.to_datetime(date_str, format='%y%m%d')
                    except:
                        return None
                return None
             df_runs[date_col] = df_runs['런ID'].apply(extract_date_from_runid)
    except Exception:
         def extract_date_from_runid(run_id):
            if not isinstance(run_id, str):
                return None
            parts = run_id.split('-')
            if len(parts) >= 2:
                date_str = parts[1] 
                try:
                    return pd.to_datetime(date_str, format='%y%m%d')
                except:
                    return None
            return None
         df_runs[date_col] = df_runs['런ID'].apply(extract_date_from_runid)

# 정렬 및 인덱스 초기화 (날짜 순서대로)
df_runs = df_runs.sort_values(by=date_col).reset_index(drop=True)

# 이동 평균 계산
window_size = 10
# 컬럼명 공백 제거하여 참조 (안전성을 위해 변수로 저장된 컬럼명 사용)
df_runs['수율_이동평균'] = df_runs[yield_col].rolling(window=window_size).mean()

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(14, 8))

# X축: 일자
x = df_runs[date_col]

# Y축 좌측: CNT 수율
y1 = df_runs[yield_col]

ax1.set_xlabel('일자')
ax1.set_ylabel('CNT 수율 (g/g-cat)', color='tab:blue')
ax1.plot(x, y1, color='tab:blue', alpha=0.3, linestyle='-', label='개별 런 수율')
ax1.tick_params(axis='y', labelcolor='tab:blue')
ax1.grid(True, linestyle='--', alpha=0.6)

# 이동 평균 선 추가
ax1.plot(x, df_runs['수율_이동평균'], color='tab:red', linewidth=2.5, label=f'{window_size}개 런 이동 평균')

# 전역 통계 정보 텍스트로 표시
overall_mean = df_runs[yield_col].mean()
overall_std = df_runs[yield_col].std()
stats_text = f'전체 평균 수율: {overall_mean:.2f} ± {overall_std:.2f} g/g-cat\n이동 평균 윈도우: {window_size} 개 런'

# 텍스트 위치 조정 (그래프 상단 중앙이나 우상단 등)
ax1.text(0.5, 0.95, stats_text, transform=ax1.transAxes, fontsize=12,
         verticalalignment='top', horizontalalignment='center',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3))

# 범례 추가
lines, labels = ax1.get_legend_handles_labels()
ax1.legend(lines, labels, loc='lower right')

plt.title('CNT 생산 수율 추이 분석 (개별 런 및 이동 평균)')
plt.tight_layout()

# 저장
output_filename = os.path.join(OUT_DIR, 'yield_trend_analysis.png')
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()

print(f"Plots saved to {OUT_DIR}")
