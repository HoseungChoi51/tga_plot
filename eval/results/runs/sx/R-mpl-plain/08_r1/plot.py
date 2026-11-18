import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-plain/08_r1/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 출력 디렉토리 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기 (모든 시트)
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

# 각 시트별로 플롯 그리기
for sheet_name in sheet_names:
    # header_rows가 [1] 이므로 pandas에서는 header=0 (0-based index) 또는 skiprows를 사용해야 할 수 있음
    # 미리보기에 data_start_row: 2 라고 되어있으므로, 실제 데이터는 3번째 행부터 시작할 가능성이 높음.
    # Excel의 1행이 헤더라면 pandas header=0. 
    # 하지만 "header_rows": [1] 은 보통 1-based index로 1행을 의미하며, 이는 pandas의 header=0과 동일.
    # 그러나 sometimes complex headers require skipping. Let's try standard read first.
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
    
    # 컬럼 이름 정리 (공백 제거 등)
    df.columns = [str(col).strip() for col in df.columns]
    
    # 필요한 컬럼 확인 및 추출
    temp_col = None
    weight_col = None
    dw_col = None
    
    for c in df.columns:
        c_lower = str(c).lower()
        if 'temperature' in c_lower or 'temp' in c_lower:
            temp_col = c
        elif 'weight' in c_lower and '%' in c:
            weight_col = c
        elif ('d.w' in c_lower or 'dw' in c_lower) and '%' in c:
            dw_col = c
            
    # If specific names not found, try positional based on preview info if needed, but name matching is safer.
    # Preview says: A:Time, B:Temperature, C:Weight(%), D:D.W(%/C)
    if temp_col is None and len(df.columns) > 1:
        temp_col = df.columns[1]
    if weight_col is None and len(df.columns) > 2:
        weight_col = df.columns[2]
    if dw_col is None and len(df.columns) > 3:
        dw_col = df.columns[3]

    if temp_col is None or weight_col is None or dw_col is None:
        print(f"시트 {sheet_name}에서 필요한 컬럼을 찾을 수 없습니다. Columns: {df.columns.tolist()}")
        continue
        
    x = df[temp_col]
    y1 = df[weight_col]
    y2 = df[dw_col]
    
    # 플롯 생성
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # 첫 번째 축 (무게 %)
    color1 = 'tab:blue'
    ax1.set_xlabel('온도 (°C)', fontsize=12)
    ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
    line1, = ax1.plot(x, y1, color=color1, label='무게 (%)')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # 두 번째 축 (미분 무게 %/°C)
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('미분 무게 (%/°C)', color=color2, fontsize=12)
    line2, = ax2.plot(x, y2, color=color2, linestyle='--', label='미분 무게 (%/°C)')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # 제목
    plt.title(f'TGA 결과: {sheet_name}', fontsize=14)
    
    # 범례 추가
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='best')
    
    # 레이아웃 조정
    fig.tight_layout()
    
    # 파일 저장
    safe_sheet_name = "".join([c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sheet_name]).rstrip()
    output_filename = f"TGA_{safe_sheet_name}.png"
    output_path = os.path.join(OUT_DIR, output_filename)
    
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"저장 완료: {output_path}")

print("모든 그래프 생성 완료")
