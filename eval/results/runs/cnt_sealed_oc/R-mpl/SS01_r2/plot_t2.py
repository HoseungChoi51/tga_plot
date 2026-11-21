import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
sheet_name = "주간요약"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # 필요한 컬럼 확인 및 데이터 정제
    if '주차' not in df.columns or '총생산량(kg)' not in df.columns:
        raise ValueError("필요한 컬럼('주차', '총생산량(kg)')이 없습니다.")
        
    # 결측치 제거 및 숫자 변환 (안전장치)
    df['주차'] = pd.to_numeric(df['주차'], errors='coerce')
    df['총생산량(kg)'] = pd.to_numeric(df['총생산량(kg)'], errors='coerce')
    df_clean = df.dropna(subset=['주차', '총생산량(kg)']).sort_values('주차').reset_index(drop=True)
    
    # 플롯 그리기
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 색상 정의
    color_before_14 = '#4C72B0'  # 1~13주차 기본색 (파랑 계열)
    color_from_14 = '#DD8452'    # 14주차부터 구분색 (주황/빨강 계열)
    
    # 막대 색상 리스트 생성
    colors = []
    for week in df_clean['주차']:
        if week >= 14:
            colors.append(color_from_14)
        else:
            colors.append(color_before_14)
            
    bars = ax.bar(df_clean['주차'].astype(int), df_clean['총생산량(kg)'], color=colors, edgecolor='black', linewidth=0.5)
    
    # 막대 위에 값 표시
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)

    # 축 레이블 및 제목
    ax.set_xlabel('주차', fontsize=12)
    ax.set_ylabel('총생산량 (kg)', fontsize=12)
    ax.set_title('주차별 CNT 총생산량 추이 (14주차 이후 색상 구분)', fontsize=14, fontweight='bold')
    
    # x축 눈금 조정
    ax.set_xticks(df_clean['주차'].astype(int))
    ax.tick_params(axis='x', rotation=0)
    
    # 격자선 추가 (y축 기준)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    # 범례 추가 (시각적 구분 명확화를 위해)
    import matplotlib.patches as mpatches
    patch_before = mpatches.Patch(color=color_before_14, label='1~13주차')
    patch_after = mpatches.Patch(color=color_from_14, label='14주차~')
    ax.legend(handles=[patch_before, patch_after], loc='upper right', title='기간 구분')
    
    plt.tight_layout()
    
    # 저장
    output_file = os.path.join(OUT_DIR, "weekly_production_volume.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"그림이 저장되었습니다: {output_file}")

except Exception as e:
    print(f"오류 발생: {e}")
finally:
    plt.close(fig)
