import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/run_log.xlsx"
sheet_name = "런로그"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    raise e

# '촉매로트' 컬럼이 있는지 확인하고 그룹화하여 런 수 계산
if '촉매로트' in df.columns:
    lot_counts = df['촉매로트'].value_counts()
    
    # 그래프 그리기
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 가로 막대 차트 (barh)
    bars = ax.barh(lot_counts.index, lot_counts.values, color='steelblue', edgecolor='black')
    
    # 각 막대에 값 표시
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
                va='center', ha='left', fontsize=10)
        
    ax.set_xlabel('런 수 (Count)', fontsize=12)
    ax.set_ylabel('촉매 로트 (Catalyst Lot)', fontsize=12)
    ax.set_title('촉매 로트별 런 수 통계', fontsize=14)
    
    # y축 순서 정렬 (값이 큰 상단이 오도록 또는 오름차순 등 필요에 따라)
    # value_counts는 기본 내림차순이라 위쪽부터 많은 순으로 나옴
    
    plt.tight_layout()
    
    # 저장
    output_file = os.path.join(OUT_DIR, "catalyst_lot_run_count.png")
    plt.savefig(output_file, dpi=300)
    plt.close(fig)
else:
    print("Column '촉매로트' not found.")
