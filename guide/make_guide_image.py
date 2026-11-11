"""Draw guide_ko.png: a TGA plot with every part numbered and named in Korean.

The names here are the SAME words used in AGENT.md, so a request written with
these words maps to exactly one setting.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import logging
import numpy as np
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
from matplotlib import font_manager

for fp in font_manager.findSystemFonts():
    if "nanum" in fp.lower() or "malgun" in fp.lower():
        font_manager.fontManager.addfont(fp)
names = {f.name for f in font_manager.fontManager.ttflist}
for f in ("Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"):
    if f in names:
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]
        break
plt.rcParams["axes.unicode_minus"] = False

# ---------------------------------------------------------------- data
T = np.arange(30, 901, 1.0)
rate = (4 * np.exp(-0.5 * ((T - 95) / 20) ** 2) / (20 * 2.5066)
        + 12 * np.exp(-0.5 * ((T - 400) / 30) ** 2) / (30 * 2.5066)
        + 80 * np.exp(-0.5 * ((T - 560) / 40) ** 2) / (40 * 2.5066))
W = 100 - np.cumsum(rate) * 97 / rate.sum()
D = -np.gradient(W, T)

BLUE, RED, INK, MARK = "#1f4e9c", "#c0392b", "#222222", "#e8710a"

fig = plt.figure(figsize=(16, 9), dpi=150)
ax1 = fig.add_axes([0.075, 0.17, 0.50, 0.70])
ax2 = ax1.twinx()
l1, = ax1.plot(T, W, color=BLUE, lw=2, label="Weight (%)")
l2, = ax2.plot(T, D, color=RED, lw=1.6, label="Deriv. weight (%/°C)")
ax1.set_xlim(0, 900); ax1.set_ylim(-5, 112); ax2.set_ylim(-0.1, 1.0)
ax1.set_xticks(range(0, 901, 200))
ax1.set_xlabel("Temperature (°C)", fontsize=13)
ax1.set_ylabel("Weight (%)", color=BLUE, fontsize=13)
ax2.set_ylabel("Deriv. weight (%/°C)", color=RED, fontsize=13)
ax1.tick_params(axis="y", colors=BLUE, direction="in", labelsize=11)
ax2.tick_params(axis="y", colors=RED, direction="in", labelsize=11)
ax1.tick_params(axis="x", direction="in", labelsize=11, length=7)
ax2.spines["left"].set_color(BLUE); ax2.spines["right"].set_color(RED)
ax1.grid(True, alpha=0.25)
ax1.set_title("1006R1-V normal", fontsize=15, pad=12)
leg = ax1.legend(handles=[l1, l2], loc="center left", frameon=False, fontsize=11)

# residue + peak + vertical guide line
i8 = np.argmin(abs(T - 800))
ax1.plot([800], [W[i8]], "o", ms=7, mfc="white", mec=BLUE, mew=1.8, zorder=5)
res = ax1.annotate(f"Residue {W[i8]:.1f}%", xy=(800, W[i8]), xytext=(8, 45),
                   textcoords="offset points", ha="right", fontsize=11, color=BLUE,
                   arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.8))
ip = np.argmax(D)
ax2.plot([T[ip]], [D[ip]], "^", ms=7, color=RED)
pk = ax2.annotate(f"{T[ip]:.0f} °C", xy=(T[ip], D[ip]), xytext=(0, 9), textcoords="offset points",
                  ha="center", fontsize=11, color=RED, fontweight="bold")
ax1.axvline(450, color="gray", lw=1, ls="--")
ax1.text(455, 108, "450 °C", color="gray", fontsize=10, va="top")

fig.canvas.draw()
rend = fig.canvas.get_renderer()
inv = fig.transFigure.inverted()


def bbox(artist):
    b = artist.get_window_extent(rend)
    (x0, y0), (x1, y1) = inv.transform([(b.x0, b.y0), (b.x1, b.y1)])
    return x0, y0, x1, y1


def badge(n, x, y, target=None, coords="figure fraction"):
    """Numbered circle at figure coords (x, y), optionally with a line to target."""
    kw = dict(arrowprops=dict(arrowstyle="-", color=MARK, lw=1.4, shrinkA=9, shrinkB=2)) if target else {}
    fig.add_artist(matplotlib.text.Annotation(
        str(n), xy=target if target else (x, y), xycoords=coords if target else "figure fraction",
        xytext=(x, y), textcoords="figure fraction", ha="center", va="center",
        fontsize=11, fontweight="bold", color="white", zorder=20,
        bbox=dict(boxstyle="circle,pad=0.25", fc=MARK, ec="none"), **kw))


def data_to_fig(ax, x, y):
    return tuple(inv.transform(ax.transData.transform((x, y))))


x0, y0, x1, y1 = bbox(ax1.title);          badge(1, x0 - 0.018, (y0 + y1) / 2)
x0, y0, x1, y1 = bbox(ax1.xaxis.label);    badge(2, x0 - 0.018, (y0 + y1) / 2)
x0, y0, x1, y1 = bbox(ax1.yaxis.label);    badge(3, (x0 + x1) / 2, y1 + 0.025)
x0, y0, x1, y1 = bbox(ax2.yaxis.label);    badge(4, (x0 + x1) / 2, y1 + 0.025)
# 5 tick mark, 6 tick label, 7 tick spacing
badge(5, *[a + b for a, b in zip(data_to_fig(ax1, 400, -5), (0.03, 0.06))], target=data_to_fig(ax1, 400, -2.5))
lab600 = [t for t in ax1.get_xticklabels() if t.get_text() == "600"][0]
x0, y0, x1, y1 = bbox(lab600);             badge(6, x1 + 0.02, y0 - 0.012, target=((x0 + x1) / 2 + 0.006, y0 + 0.004))
p200, p400 = data_to_fig(ax1, 200, 2.5), data_to_fig(ax1, 400, 2.5)
fig.add_artist(matplotlib.patches.FancyArrowPatch(p200, p400, transform=fig.transFigure,
                                                  arrowstyle="<->", mutation_scale=12, color=MARK, lw=1.4))
badge(7, (p200[0] + p400[0]) / 2, p200[1] + 0.03)
# 8 axis range (x)
xa, _ = data_to_fig(ax1, 0, 0); xb, _ = data_to_fig(ax1, 900, 0)
yb = bbox(ax1.xaxis.label)[1] - 0.035
fig.add_artist(matplotlib.patches.FancyArrowPatch((xa, yb), (xb, yb), transform=fig.transFigure,
                                                  arrowstyle="|-|", mutation_scale=6, color=MARK, lw=1.4))
badge(8, xa - 0.018, yb)
# 9 y1 line, 10 y2 line
badge(9, *[a + b for a, b in zip(data_to_fig(ax1, 230, W[200]), (0, 0.07))], target=data_to_fig(ax1, 230, W[200]))
pt = (T[ip] + 45, D[ip + 45])
badge(10, *[a + b for a, b in zip(data_to_fig(ax2, *pt), (0.045, 0.02))], target=data_to_fig(ax2, *pt))
x0, y0, x1, y1 = bbox(leg);                badge(11, x1 + 0.012, (y0 + y1) / 2)
tb = res.get_window_extent(rend)             # text only, not the arrow
(x0, y0), (x1, y1) = inv.transform([(tb.x0, tb.y0), (tb.x1, tb.y1)])
pr = data_to_fig(ax1, 800, W[i8])
badge(12, pr[0] + 0.035, pr[1] + 0.045, target=pr)
x0, y0, x1, y1 = bbox(pk);                 badge(13, x0 - 0.018, (y0 + y1) / 2)
badge(14, *data_to_fig(ax1, 450, 60))
badge(15, *[a + b for a, b in zip(data_to_fig(ax1, 700, 60), (0.03, 0.04))], target=data_to_fig(ax1, 700, 60))

# ---------------------------------------------------------------- legend panel
items = [
    ("그림 제목", "맨 위 제목 (기본: 시트 이름)", "그림 제목을 'CNT 산화'로, 글자 크기 16"),
    ("x축 라벨", "가로축 이름", "x축 라벨을 '온도 (°C)'로"),
    ("y1축 라벨", "왼쪽 세로축 이름 (무게)", "y1축 라벨 글자 색깔 검정"),
    ("y2축 라벨", "오른쪽 세로축 이름 (미분 무게)", "y2축 라벨을 'DTG (%/°C)'로"),
    ("틱", "축 위의 눈금 표시", "틱 방향 바깥쪽"),
    ("틱 라벨", "눈금 숫자", "x축 틱 라벨 크기 9"),
    ("틱 간격", "눈금 사이 거리", "x축 틱 간격 200, y1축 틱 간격 20"),
    ("축 범위", "축의 시작~끝 (y축도 같음)", "x축 범위 0~900, y2축 범위 -0.1~1"),
    ("y1 선", "왼쪽 축 곡선 (무게)", "y1 선 색깔 초록, 선 굵기 2, 점선"),
    ("y2 선", "오른쪽 축 곡선 (미분 무게)", "y2 선 색깔 빨강"),
    ("범례", "선 이름 상자", "범례 오른쪽 위 / 범례 없애줘"),
    ("잔류량 표시", "800 °C의 무게 값", "잔류량 표시 'Residue {}%', 가장 가까운 점"),
    ("피크 표시", "y2 선 최고점의 온도", "피크 표시 2개, 150 °C 이상만"),
    ("보조선", "세로/가로 점선", "450 °C에 세로 보조선"),
    ("격자", "배경 격자선", "격자 켜줘 / 꺼줘"),
]
px, py = 0.655, 0.905
fig.text(px, py + 0.04, "그래프 요소 이름 (요청할 때 이 이름을 써 주세요)", fontsize=15, fontweight="bold", color=INK)
dy = 0.0535
for k, (name, what, ex) in enumerate(items, 1):
    y = py - (k - 1) * dy
    fig.text(px, y, str(k), fontsize=10.5, fontweight="bold", color="white", ha="center", va="center",
             bbox=dict(boxstyle="circle,pad=0.25", fc=MARK, ec="none"))
    fig.text(px + 0.018, y + 0.006, name, fontsize=12.5, fontweight="bold", color=INK, va="center")
    fig.text(px + 0.105, y + 0.006, what, fontsize=11, color="#555555", va="center")
    fig.text(px + 0.018, y - 0.017, "예: " + ex, fontsize=10.5, color="#1a6b3c", va="center")

fig.text(0.075, 0.035,
         "그 밖의 용어:  시트 (엑셀 아래 탭)  ·  열 = 세로줄 (B열, C열)  ·  글자 색깔 / 글자 크기 (전체 또는 요소별)  ·  "
         "글꼴  ·  그림 크기  ·  해상도 (dpi)  ·  파일 형식 (png, pdf, svg)  ·  여러 시트를 한 그림에 (겹쳐 그리기)",
         fontsize=11.5, color=INK)

out = Path(__file__).with_name("guide_ko.png")
fig.savefig(out, dpi=150)
print("wrote", out)
