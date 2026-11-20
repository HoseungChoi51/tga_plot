import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.patches as mpatches

# 설정
OUT_DIR = "out/t5"
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
    
    # 그룹별 평균 계산
    avg_1_to_13 = df_clean[df_clean['주차'] <= 13]['총생산량(kg)'].mean()
    avg_14_to_26 = df_clean[df_clean['주차'] >= 14]['총생산량(kg)'].mean()
    
    # 플롯 그리기 (16:9 비율 적용: figsize=(16, 9))
    fig, ax = plt.subplots(figsize=(16, 9))
    
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

    # 평균선 추가
    max_week = df_clean['주차'].max()
    min_week = df_clean['주차'].min()
    
    # 1~13주 평균선
    if avg_1_to_13 is not None and not pd.isna(avg_1_to_13):
        ax.hlines(y=avg_1_to_13, xmin=min_week-0.5, xmax=13.5, color='#333333', linestyle='-', linewidth=2, alpha=0.8)
        # 텍스트 라벨
        ax.text(7, avg_1_to_13, f'1~13주 평균: {avg_1_to_13:.2f} kg', 
                verticalalignment='bottom', horizontalalignment='center', 
                backgroundcolor='white', fontsize=10, fontweight='bold')
                
    # 14~26주 평균선
    if avg_14_to_26 is not None and not pd.isna(avg_14_to_26):
        ax.hlines(y=avg_14_to_26, xmin=13.5, xmax=max_week+0.5, color='#333333', linestyle='-', linewidth=2, alpha=0.8)
        # 텍스트 라벨
        ax.text((14+max_week)/2, avg_14_to_26, f'14~26주 평균: {avg_14_to_26:.2f} kg', 
                verticalalignment='bottom', horizontalalignment='center', 
                backgroundcolor='white', fontsize=10, fontweight='bold')


    # 축 레이블 및 제목
    ax.set_xlabel('주차', fontsize=12)
    ax.set_ylabel('생산량 (kg)', fontsize=12)
    ax.set_title('주간 생산량 추이 (3~8월)', fontsize=14, fontweight='bold')
    
    # x축 눈금 조정
    ax.set_xticks(df_clean['주차'].astype(int))
    ax.tick_params(axis='x', rotation=0)
    
    # 격자선 추가 (y축 기준)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)
    
    # 범례 추가 (색상 구분용)
    patch_before = mpatches.Patch(color=color_before_14, label='1~13주차')
    patch_after = mpatches.Patch(color=color_from_14, label='14주차~')
    ax.legend(handles=[patch_before, patch_after], loc='upper right', title='기간 구분')
    
    plt.tight_layout()
    
    # 저장 (200 dpi 적용)
    output_file = os.path.join(OUT_DIR, "weekly_production_volume.png")
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"그림이 저장되었습니다: {output_file}")

except Exception as e:
    print(f"오류 발생: {e}")
finally:
    plt.close(fig)
