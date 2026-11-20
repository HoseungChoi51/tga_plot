import pandas as pd
import matplotlib.pyplot as plt
import os

# 환경 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 경로
file_path = "data/raman/R4-260407-1.csv"

try:
    # CSV 파일 읽기 (인코딩 오류 방지 위해 utf-8-sig 시도 후 기본 utf-8 또는 euc-kr 등 필요시 조정 가능하나, 
    # 일반적으로 pandas의 기본 인코딩이나 utf-8로 잘 읽힘. 세미콜론 구분자 여부 확인이 중요하지만,
    # 미리보기에 '|' 구분자로 열 이름이 나열되어 있어 일반적인 쉼표 구분 CSV일 가능성이 높음.
    # 만약 구분자가 ';'라면 sep=';' 추가해야 함. 일단 기본 sep=',' 로 시도하고 실패하면 처리하도록 함.)
    
    # 미리보기 형식: A Raman Shift (cm-1)... | B Intensity...
    # 이것은 Excel에서 복사한 형태처럼 보이지만, 실제 파일은 CSV입니다.
    # 일반 CSV로 가정하고 읽습니다.
    df = pd.read_csv(file_path)
    
    # 열 이름 확인 및 정리 (공백 제거 등)
    df.columns = df.columns.str.strip()
    
    # 예상되는 컬럼명 찾기 (대소문자 무관, 공차 포함)
    x_col = None
    y_col = None
    
    for col in df.columns:
        if 'raman' in col.lower() or 'shift' in col.lower():
            x_col = col
        elif 'intensity' in col.lower() or 'a.u.' in col.lower():
            y_col = col
            
    # 만약 자동 인식이 안 되면 첫 번째와 두 번째 컬럼 사용
    if x_col is None and len(df.columns) >= 1:
        x_col = df.columns[0]
    if y_col is None and len(df.columns) >= 2:
        y_col = df.columns[1]
        
    if x_col is None or y_col is None:
        raise ValueError("Raman Shift 또는 Intensity 컬럼을 찾을 수 없습니다.")

    # 플롯 그리기
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df[x_col], df[y_col], color='#d62728', linewidth=1.5)
    
    # 제목 및 라벨 설정
    ax.set_title(f'Raman Spectrum: {os.path.basename(file_path)}', fontsize=14, pad=10)
    ax.set_xlabel('Raman Shift (cm⁻¹)', fontsize=12)
    ax.set_ylabel('Intensity (a.u.)', fontsize=12)
    
    # 격자 표시
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # 축 범위 자동 조절 (데이터 최소/최대 기준 약간 여유 공간)
    x_min, x_max = df[x_col].min(), df[x_col].max()
    y_min, y_max = df[y_col].min(), df[y_col].max()
    ax.set_xlim(x_min - (x_max-x_min)*0.05, x_max + (x_max-x_min)*0.05)
    ax.set_ylim(y_min - (y_max-y_min)*0.05, y_max + (y_max-y_min)*0.05)
    
    plt.tight_layout()
    
    # 저장
    output_filename = os.path.join(OUT_DIR, "R4-260407-1_raw.png")
    plt.savefig(output_filename, dpi=300)
    print(f"Plot saved to {output_filename}")
    
except Exception as e:
    print(f"Error processing file: {e}")
    # 에러 시에도 빈 이미지 생성하여 프로그램 종료되지 않게 하거나 로그만 남김
    pass
