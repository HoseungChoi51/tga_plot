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
sheet_name = "런로그"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # 컬럼명 확인 및 매칭 (미리보기에 나온 정확한 이름 사용 시도)
    # 미리보기: B 일자, E 반응기, P 가동시간 (h), R 생산속도 (g/h)
    
    date_col = '일자'
    reactor_col = '반응기'
    rate_col = '생산속도 (g/h)'
    time_col = '가동시간 (h)'
    
    # 만약 컬럼명에 공백이 있거나 약간 다를 수 있으므로 strip 처리 후 재매칭하는 로직 추가 가능하지만,
    # openpyxl로 읽으면 보통 그대로 들어옴. 에러 방지를 위해 존재 여부 체크
    
    if date_col not in df.columns or reactor_col not in df.columns or rate_col not in df.columns or time_col not in df.columns:
        # 대안적으로 유사한 컬럼명 찾기 (예: 공백 차이 등)
        cols = df.columns.tolist()
        def find_col(key):
            for c in cols:
                if key in str(c):
                    return c
            raise ValueError(f"Column containing '{key}' not found")
        
        date_col = find_col('일자')
        reactor_col = find_col('반응기')
        rate_col = find_col('생산속도')
        time_col = find_col('가동시간')

    # 날짜 형식 변환 및 필터링 (3월 ~ 8월)
    # '2026-03-02~2026-08-30' 이므로 연도는 2026년으로 가정하거나 단순히 월만 봄
    df[date_col] = pd.to_datetime(df[date_col])
    
    # 기간 필터링: 3월부터 8월까지
    mask = (df[date_col].dt.month >= 3) & (df[date_col].dt.month <= 8)
    df_filtered = df[mask].copy()
    
    if df_filtered.empty:
        print("데이터가 비어 있습니다.")
    else:
        # 총 생산량(g) 계산: 생산속도 * 가동시간
        # 단위: g/h * h = g
        df_filtered['total_produced_g'] = df_filtered[rate_col] * df_filtered[time_col]
        
        # kg으로 환산
        df_filtered['total_produced_kg'] = df_filtered['total_produced_g'] / 1000
        
        # 반응기별 그룹화하여 합계 구하기
        group_by_reactor = df_filtered.groupby(reactor_col)['total_produced_kg'].sum().reset_index()
        
        # 그래프 그리기
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # 막대 색상 설정
        colors = ['#4C72B0', '#55A868', '#C44E52', '#8172B2']
        
        # 반응기 순서 정렬 (R1, R2, R3, R4)
        group_by_reactor[reactor_col] = pd.Categorical(group_by_reactor[reactor_col], categories=['R1', 'R2', 'R3', 'R4'], ordered=True)
        group_by_reactor = group_by_reactor.sort_values(reactor_col)
        
        bars = ax.bar(group_by_reactor[reactor_col].astype(str), group_by_reactor['total_produced_kg'], color=colors[:len(group_by_reactor)])
        
        # 막대 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=10)
            
        # 라벨 및 제목 설정
        ax.set_xlabel('반응기')
        ax.set_ylabel('누적 총 생산량 (kg)')
        ax.set_title('3~8월 누적 반응기별 총 생산량')
        
        # Y축 눈금 간격 조정 등
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 저장
        save_path = os.path.join(OUT_DIR, 'reactor_production_bar.png')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"그림을 저장했습니다: {save_path}")

except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()
