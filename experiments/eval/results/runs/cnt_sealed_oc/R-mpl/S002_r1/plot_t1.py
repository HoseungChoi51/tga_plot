import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# 데이터 전처리
# '반응기'와 '정지시간(분)' 컬럼을 사용하여 반응기별 총 정지시간 계산
if '반응기' in df.columns and '정지시간(분)' in df.columns:
    # 결측치가 있는 행은 무시하고 합산
    group_total_time = df.groupby('반응기')['정지시간(분)'].sum().reset_index()
    
    # 내림차순 정렬 (제일 많은 순서대로 위에서부터)
    group_total_time = group_total_time.sort_values(by='정지시간(분)', ascending=False)
    
    reactors = group_total_time['반응기']
    times = group_total_time['정지시간(분)']
    
    # 색상 지정: 가장 높은 값(첫 번째)은 빨간색, 나머지는 회색
    colors = ['red'] + ['gray'] * (len(times) - 1)
    
    # 막대그래프 생성 (가로막대)
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # y축에 반응기 이름, x축에 시간으로 가로막대 그리기
    bars = ax.barh(reactors, times, color=colors)
    
    # y축 순서 반전 (데이터는 내림차순이지만 barh는 아래에서 위로 그라므로 위쪽이 큰 값이 되도록 반전)
    ax.invert_yaxis()
    
    # 라벨 및 제목 추가
    ax.set_xlabel('총 설비 정지시간 (분)')
    ax.set_ylabel('반응기')
    ax.set_title('반응기별 총 설비 정지시간')
    
    # 막대 끝에 값 표시
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
                va='center', ha='left', fontsize=9)
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 저장
    save_path = os.path.join(OUT_DIR, "downtime_by_reactor.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
else:
    print("필요한 컬럼을 찾을 수 없습니다.")
