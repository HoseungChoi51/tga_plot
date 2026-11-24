import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t3"
DATA_FILE = "data/tga_batches.xlsx"

# 폴더 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 요청된 시트 목록 정의
selected_sheets = ['R4-260407-1', 'R4-260721-1', 'R1-260326-1']

# 데이터 읽기 및 그래프 그리기
fig, ax = plt.subplots(figsize=(12, 8))

for sheet in selected_sheets:
    try:
        # 각 시트 읽기
        df = pd.read_excel(DATA_FILE, sheet_name=sheet)
        
        temp_col = None
        weight_col = None
        
        for col in df.columns:
            if '온도' in str(col):
                temp_col = col
            if '중량' in str(col) and '미분' not in str(col):
                weight_col = col
                
        if temp_col is not None and weight_col is not None:
            plot_df = df[[temp_col, weight_col]].dropna()
            plot_df = plot_df.sort_values(by=temp_col)
            
            ax.plot(plot_df[temp_col], plot_df[weight_col], label=sheet, linewidth=1.5, alpha=0.9)
        else:
            print(f"시트 {sheet}에서 온도 또는 중량 컬럼을 찾지 못했습니다.")
    except Exception as e:
        print(f"시트 {sheet} 처리 중 오류 발생: {e}")

# 그래프 스타일링
ax.set_title('TGA (Air, 10 °C/min)', fontsize=16)
ax.set_xlabel('온도 (°C)', fontsize=12)
ax.set_ylabel('잔류 중량 (%)', fontsize=12)

# 축 범위 및 눈금 설정
ax.set_ylim(0, 105)
ax.set_xlim(left=0) # x축 시작점은 보통 0이나 최소 데이터값으로, 여기서는 자연스러운 범위를 위해 left는 자동 또는 명시적으로 설정 가능하지만 사용자 요청은 y축과 x눈금 간격이므로 y만 고정하고 x는 데이터에 맞추되 눈금만 변경합니다.
# x축 눈금 100°C 간격 설정
ax.xaxis.set_major_locator(plt.MultipleLocator(100))

ax.grid(True, linestyle='--', alpha=0.6)
ax.legend(title='배치 ID')

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "tga_selected_overlay.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"그래프가 저장되었습니다: {output_path}")
