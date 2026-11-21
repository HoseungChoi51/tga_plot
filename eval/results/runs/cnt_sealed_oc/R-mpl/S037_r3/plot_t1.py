import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

file_path = "data/L3_MES_export_202607.csv"
df = None

# 데이터 로드 시도
# 1. 일반 CSV (쉼표 구분자)
try:
    df = pd.read_csv(file_path, encoding='utf-8')
except Exception:
    pass

# 2. 세미콜론 구분자 CSV (유럽식 등)
if df is None or df.empty:
    try:
        df = pd.read_csv(file_path, encoding='utf-8', sep=';')
    except Exception:
        pass

# 3. 탭 구분자 CSV
if df is None or df.empty:
    try:
        df = pd.read_csv(file_path, encoding='utf-8', sep='\t')
    except Exception:
        pass

# 4. 엑셀 파일인 경우 (확장자가 csv라도 내용물이 xlsx일 때, 또는 미리보기의 '시트' 정보 고려)
# openpyxl 엔진을 사용하여 읽기 시도
if df is None or df.empty:
    try:
        # sheet_name=None이면 모든 시트를 dict로 반환하지만, 여기서는 첫 번째 시트를 가정하거나 이름이 있는 경우 처리 필요
        # 미리보기에 시트명이 'L3_MES_export_202607'라고 명시되어 있음
        df = pd.read_excel(file_path, sheet_name='L3_MES_export_202607', engine='openpyxl')
    except Exception:
        pass

# 만약 여전히 빈 데이터프레임이거나 읽지 못했다면, header=None으로 읽어보고 구조 파악 후 재처리 시도 가능하나
# 우선 위 방법 중 하나로 성공했다고 가정하고 진행

if df is not None and not df.empty:
    # 열 이름 정제
    df.columns = [str(c).strip() for c in df.columns]
    
    # 필요한 컬럼 찾기
    runtime_col = None
    yield_col = None
    
    for col in df.columns:
        if '가동시간' in col:
            runtime_col = col
        if 'CNT수율' in col or ('수율' in col and 'g/g-cat' in col):
            yield_col = col
            
    # 컬럼을 찾지 못한 경우 기본 헤더명으로 매칭 시도 (대소문자/공백 무시 등 유연한 처리는 이미 포함됨)
    if runtime_col is None:
        for col in df.columns:
            if 'runtime' in col.lower() or 'time' in col.lower():
                runtime_col = col
                break
                
    if yield_col is None:
        for col in df.columns:
            if 'yield' in col.lower():
                yield_col = col
                break

    if runtime_col and yield_col:
        # 수치 변환
        df[runtime_col] = pd.to_numeric(df[runtime_col], errors='coerce')
        df[yield_col] = pd.to_numeric(df[yield_col], errors='coerce')
        
        # 결측치 제거
        df_clean = df.dropna(subset=[runtime_col, yield_col])
        
        if not df_clean.empty:
            # 플롯 그리기
            fig, ax = plt.subplots(figsize=(10, 6))
            
            ax.scatter(
                df_clean[runtime_col], 
                df_clean[yield_col], 
                color='steelblue', 
                alpha=0.7, 
                edgecolors='w',
                s=50,
                label='데이터 포인트'
            )
            
            ax.set_xlabel('가동시간 (h)', fontsize=12)
            ax.set_ylabel('CNT 수율 (g/g-cat)', fontsize=12)
            ax.set_title('L3 파일럿 데이터: 가동시간 vs CNT 수율 관계', fontsize=14)
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend()
            
            plt.tight_layout()
            
            save_path = os.path.join(OUT_DIR, "runtime_vs_yield_scatter.png")
            plt.savefig(save_path, dpi=300)
            plt.close()
            print(f"Saved plot to {save_path}")
        else:
            print("No valid data points found after cleaning.")
    else:
        print(f"Columns not found. Available columns: {df.columns.tolist()}")
else:
    print("Failed to load data from the file.")
