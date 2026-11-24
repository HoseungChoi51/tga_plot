import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
DATA_FILE = "data/tga_batches.xlsx"

# 폴더 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기 및 그래프 그리기
fig, ax = plt.subplots(figsize=(12, 8))

# Excel 파일의 모든 시트 이름 가져오기
xl = pd.ExcelFile(DATA_FILE)
sheet_names = xl.sheet_names

for sheet in sheet_names:
    # 각 시트 읽기
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    
    # 컬럼명 확인 (미리보기에 따라 'B 온도 (°C)'와 'C 중량 (%)' 사용 추정)
    # 일반적인 TGA 데이터 형식에 맞춰 컬럼 인덱스 또는 이름으로 접근
    # 미리보기: A 시간, B 온도, C 중량, D 미분중량
    temp_col = None
    weight_col = None
    
    for col in df.columns:
        if '온도' in str(col):
            temp_col = col
        if '중량' in str(col) and '미분' not in str(col):
            weight_col = col
            
    if temp_col is not None and weight_col is not None:
        # 결측치 제거 및 정렬 (일반적으로 온도는 증가함)
        plot_df = df[[temp_col, weight_col]].dropna()
        plot_df = plot_df.sort_values(by=temp_col)
        
        ax.plot(plot_df[temp_col], plot_df[weight_col], label=sheet, linewidth=1.5, alpha=0.8)
    else:
        print(f"시트 {sheet}에서 온도 또는 중량 컬럼을 찾지 못했습니다.")

# 그래프 스타일링
ax.set_title('TGA 곡선 비교 (모든 배치)', fontsize=16)
ax.set_xlabel('온도 (°C)', fontsize=12)
ax.set_ylabel('잔류 중량 (%)', fontsize=12)
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend(title='배치 ID', bbox_to_anchor=(1.05, 1), loc='upper left')

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "tga_all_sheets_overlay.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"그래프가 저장되었습니다: {output_path}")
