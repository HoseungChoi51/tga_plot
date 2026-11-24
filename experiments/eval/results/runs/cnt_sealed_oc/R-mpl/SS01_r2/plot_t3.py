import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t3"
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

    # 평균선 추가
    # 1~13주차 구간만 선을 그리는 것이 더 명확할 수 있으나, 요청은 단순히 가로선이므로 전체 범위에 선을 긋되 스타일로 구분하거나,
    # x축 범위 제한을 위해 각 구간별로 선을 그려주는 것이 시각적으로 더 깔끔합니다.
    # 여기서는 전체 x축 범위에 걸쳐 두 개의 평균선을 그리고, 필요시 텍스트로 위치를 명시합니다.
    
    # 방법 A: 전체 범위에 선을 그음 (단순함)
    # ax.axhline(y=avg_1_to_13, color=color_before_14, linestyle='--', linewidth=2, label=f'1~13주 평균 ({avg_1_to_13:.2f})')
    # ax.axhline(y=avg_14_to_26, color=color_from_14, linestyle='--', linewidth=2, label=f'14~26주 평균 ({avg_14_to_26:.2f})')
    
    # 방법 B: 해당 주차 구간에만 선을 그음 (더 정확한 표현)
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
    ax.set_ylabel('총생산량 (kg)', fontsize=12)
    ax.set_title('주차별 CNT 총생산량 추이 (구간별 평균 포함)', fontsize=14, fontweight='bold')
    
    # x축 눈금 조정
    ax.set_xticks(df_clean['주차'].astype(int))
    ax.tick_params(axis='x', rotation=0)
    
    # 격자선 추가 (y축 기준)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)
    
    # 범례 추가 (색상 구분용)
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
