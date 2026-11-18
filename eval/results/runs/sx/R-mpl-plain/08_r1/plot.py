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
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=1)
    
    # 컬럼 이름 정리 (공백 제거 등)
    df.columns = [str(col).strip() for col in df.columns]
    
    # 필요한 컬럼 확인 및 추출
    # TGA guess에 따라 x는 Temperature, y1은 Weight(%), y2는 D.W(%/C)
    try:
        temp_col = 'Temperature'
        weight_col = 'Weight(%)'
        dw_col = 'D.W(%/C)'
        
        # 컬럼이 없으면 유사한 이름 찾기 (대소문자 무시 등)
        if temp_col not in df.columns:
            for c in df.columns:
                if 'temp' in c.lower():
                    temp_col = c
                    break
        if weight_col not in df.columns:
            for c in df.columns:
                if 'weight' in c.lower() and '%' in c:
                    weight_col = c
                    break
        if dw_col not in df.columns:
            for c in df.columns:
                if 'd.w' in c.lower() or 'dw' in c.lower():
                    dw_col = c
                    break
                    
        if temp_col not in df.columns or weight_col not in df.columns or dw_col not in df.columns:
            print(f"시트 {sheet_name}에서 필요한 컬럼을 찾을 수 없습니다.")
            continue
            
        x = df[temp_col]
        y1 = df[weight_col]
        y2 = df[dw_col]
        
    except Exception as e:
        print(f"시트 {sheet_name} 처리 중 오류 발생: {e}")
        continue
    
    # 플롯 생성
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # 첫 번째 축 (무게 %)
    color1 = 'tab:blue'
    ax1.set_xlabel('온도 (°C)', fontsize=12)
    ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
    line1 = ax1.plot(x, y1, color=color1, label='무게 (%)')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # 두 번째 축 (미분 무게 %/°C)
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('미분 무게 (%/°C)', color=color2, fontsize=12)
    line2 = ax2.plot(x, y2, color=color2, linestyle='--', label='미분 무게 (%/°C)')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # 제목
    plt.title(f'TGA 결과: {sheet_name}', fontsize=14)
    
    # 범례 추가
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='best')
    
    # 레이아웃 조정
    fig.tight_layout()
    
    # 파일 저장
    safe_sheet_name = "".join([c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sheet_name]).rstrip()
    output_filename = f"TGA_{safe_sheet_name}.png"
    output_path = os.path.join(OUT_DIR, output_filename)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"저장 완료: {output_path}")

print("모든 그래프 생성 완료")
