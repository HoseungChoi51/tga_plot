from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B19_r1/out")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(DATA_FILE, sheet_name="PVC")
    df.columns = [str(c).strip() for c in df.columns]

    temperature_col = next(c for c in df.columns if "Temperature" in c)
    weight_col = next(c for c in df.columns if "Weight" in c and "Deriv" not in c)

    data = df[[temperature_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()
    data = data.sort_values(temperature_col)

    temperature = data[temperature_col].to_numpy()
    weight = data[weight_col].to_numpy()

    t_start, t_end = 200.0, 400.0
    if temperature.min() > t_start or temperature.max() < t_end:
        raise ValueError("데이터에 200 °C 또는 400 °C가 포함된 범위가 없습니다.")

    weight_start = float(np.interp(t_start, temperature, weight))
    weight_end = float(np.interp(t_end, temperature, weight))
    mass_loss = weight_start - weight_end

    plt.rcParams["font.family"] = "Noto Sans CJK KR"
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(temperature, weight, color="#2468a2", linewidth=2, label="PVC 질량")
    ax.axvspan(t_start, t_end, color="#f2a541", alpha=0.18, label="계산 구간 (200–400 °C)")

    ax.scatter(
        [t_start, t_end],
        [weight_start, weight_end],
        color=["#d97706", "#b42318"],
        zorder=4,
        s=55,
    )
    ax.annotate(
        f"200 °C: {weight_start:.2f}%",
        (t_start, weight_start),
        xytext=(10, 12),
        textcoords="offset points",
        color="#9a5b00",
    )
    ax.annotate(
        f"400 °C: {weight_end:.2f}%",
        (t_end, weight_end),
        xytext=(10, -20),
        textcoords="offset points",
        color="#9b1c1c",
    )

    midpoint = (t_start + t_end) / 2
    ax.annotate(
        "",
        xy=(midpoint, weight_start),
        xytext=(midpoint, weight_end),
        arrowprops=dict(arrowstyle="<->", color="#333333", linewidth=1.5),
    )
    ax.text(
        midpoint + 8,
        (weight_start + weight_end) / 2,
        f"질량 감소량: {mass_loss:.2f}%p",
        va="center",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#888888", alpha=0.9),
    )

    ax.set(
        xlabel="온도 (°C)",
        ylabel="질량 (%)",
        title="PVC의 200–400 °C 구간 질량 감소",
        xlim=(temperature.min(), temperature.max()),
    )
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()

    output_path = OUT_DIR / "PVC_mass_loss_200_400C.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"200 °C 질량: {weight_start:.4f}%")
    print(f"400 °C 질량: {weight_end:.4f}%")
    print(f"200–400 °C 질량 감소량: {mass_loss:.4f}%p")
    print(f"그래프 저장: {output_path}")


if __name__ == "__main__":
    main()
