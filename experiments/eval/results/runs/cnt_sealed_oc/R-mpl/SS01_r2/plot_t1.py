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
sheet_name = "주간요약"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # 필요한 컬럼 확인 및 데이터 정제
    # 주차, 총생산량(kg)
    if '주차' not in df.columns or '총생산량(kg)' not in df.columns:
        raise ValueError("필요한 컬럼('주차', '총생산량(kg)')이 없습니다.")
        
    # 결측치 제거 및 숫자 변환 (안전장치)
    df['주차'] = pd.to_numeric(df['주차'], errors='coerce')
    df['총생산량(kg)'] = pd.to_numeric(df['총생산량(kg)'], errors='coerce')
    df_clean = df.dropna(subset=['주차', '총생산량(kg)']).sort_values('주차')
    
    # 플롯 그리기
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bars = ax.bar(df_clean['주차'].astype(int), df_clean['총생산량(kg)'], color='#4C72B0', edgecolor='black', linewidth=0.5)
    
    # 막대 위에 값 표시
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)

    # 축 레이블 및 제목
    ax.set_xlabel('주차', fontsize=12)
    ax.set_ylabel('총생산량 (kg)', fontsize=12)
    ax.set_title('주차별 CNT 총생산량 추이', fontsize=14, fontweight='bold')
    
    # x축 눈금 조정 (주차가 많을 경우 가독성 확보)
    ax.set_xticks(df_clean['주차'].astype(int))
    ax.tick_params(axis='x', rotation=0)
    
    # 격자선 추가 (y축 기준)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    # 저장
    output_file = os.path.join(OUT_DIR, "weekly_production_volume.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"그림이 저장되었습니다: {output_file}")

except Exception as e:
    print(f"오류 발생: {e}")
finally:
    plt.close(fig)
