import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
try:
    df = pd.read_excel(file_path, sheet_name='런로그')
except Exception as e:
    print(f"Error reading excel file: {e}")
    df = pd.DataFrame()

if not df.empty and '등급' in df.columns:
    # 주차 컬럼을 숫자로 강제 변환 (문자열이나 하이픈 등이 들어있는 경우 방지)
    # errors='coerce'를 사용하여 변환 불가능한 값은 NaN으로 만들고 삭제
    df['주차'] = pd.to_numeric(df['주차'], errors='coerce')
    df = df.dropna(subset=['주차'])
    df['주차'] = df['주차'].astype(int)

    # 전체 기간의 평균 불량률 계산
    total_runs = len(df)
    defective_runs = len(df[df['등급'] == 'C'])
    overall_defect_rate = (defective_runs / total_runs) * 100
    
    # 주간별 불량률 계산
    weekly_stats = df.groupby('주차').apply(lambda x: (len(x[x['등급']=='C']) / len(x)) * 100).reset_index(name='불량률 (%)')
    
    # 그래프 작성
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # 라인 플롯으로 주간 추세 표시
    ax.plot(weekly_stats['주차'], weekly_stats['불량률 (%)'], marker='o', linestyle='-', color='#D62828', linewidth=2, markersize=6, label='주간 불량률 (C등급 비중)')
    
    # 전체 평균 불량률 점선으로 표시
    ax.axhline(y=overall_defect_rate, color='#540B0E', linestyle='--', linewidth=1.5, label=f'전체 평균 불량률 ({overall_defect_rate:.2f}%)')
    
    # 스타일링
    ax.set_title('CNT 생산 공정 주간별 불량률 추이', fontsize=16, fontweight='bold')
    ax.set_xlabel('주차', fontsize=12)
    ax.set_ylabel('불량률 (%)', fontsize=12)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='best', fontsize=10)
    
    # Y축 범위 설정
    if not weekly_stats.empty:
        max_val = weekly_stats['불량률 (%)'].max()
        min_val = weekly_stats['불량률 (%)'].min()
        padding = (max_val - min_val) * 0.1 + 1
        ax.set_ylim(max(0, min_val - padding), max_val + padding)
        
        # X축 눈금 정수화
        min_week = int(weekly_stats['주차'].min())
        max_week = int(weekly_stats['주차'].max())
        ax.set_xticks(np.arange(min_week, max_week + 1, 1))
    
    plt.tight_layout()
    
    # 저장
    output_filename = os.path.join(OUT_DIR, "defect_rate_trend.png")
    plt.savefig(output_filename, dpi=300)
    plt.close()
    print(f"Saved plot to {output_filename}")
else:
    print("Data is empty or column '등급' not found.")
