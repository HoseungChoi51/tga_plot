#!/usr/bin/env python3
"""Independent spot-check: re-draw a few sealed requests with plain pandas + matplotlib
(no code shared with make_expectations.py), compare the numbers with sealed/requests.json,
and save the figures here. Run from experiments/eval/cnt/:   ../../../.venv/bin/python _selfcheck/selfcheck.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
plt.rcParams["font.family"] = ["Noto Sans CJK KR", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

REQ = {it["id"]: it for it in json.load(open(ROOT / "sealed/requests.json", encoding="utf-8"))["items"]}
rl = pd.read_excel(ROOT / "data/run_log.xlsx", sheet_name="런로그", skiprows=[1])
dt = pd.read_excel(ROOT / "data/downtime.xlsx", sheet_name="정지이력")
results = []


def check(name, got, want, tol):
    ok = abs(float(got) - float(want)) <= tol
    results.append((name, round(float(got), 4), want, ok))
    return ok


# 1) S008 - weekly mean yield line with a vertical marker at week 14 ------------------------
e = REQ["S008"]["turns"][0]["expect"]
s = rl.groupby("주차")["CNT수율"].mean()
pts = dict((int(a), b) for a, b in e["values"]["series"]["CNT수율"]["points"])
for w in (1, 13, 14, 26):
    check(f"S008 week{w} mean", s[w], pts[w], 0.01)
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(s.index, s.values, marker="o", color="#2b6cb0")
ax.axvline(14, ls="--", color="gray")
ax.text(14.2, s.max(), "FC-2606 투입", va="top")
ax.set(xlabel="주차", ylabel="평균 CNT수율 (g/g-cat)", title="S008 주차별 평균 수율")
fig.tight_layout(); fig.savefig(OUT / "S008_weekly_yield.png", dpi=120); plt.close(fig)

# 2) S039 - grouped bar: mean zone-2 temperature by reactor x shift ---------------------------
e = REQ["S039"]["turns"][0]["expect"]
p = rl.pivot_table(index="반응기", columns="근무조", values="2존온도", aggfunc="mean")
for r in p.index:
    for sh in p.columns:
        check(f"S039 {r}/{sh}", p.loc[r, sh], e["values"]["values"][r][sh], 0.01)
fig, ax = plt.subplots(figsize=(7, 4))
x = np.arange(len(p.index)); w = 0.38
for i, sh in enumerate(["주간", "야간"]):
    ax.bar(x + (i - 0.5) * w, p[sh], w, label=sh)
ax.set_xticks(x, p.index); ax.set_ylim(1140, 1166); ax.legend(title="근무조")
ax.set(ylabel="평균 2존온도 (°C)", title="S039 반응기별 주간/야간 2존 온도")
fig.tight_layout(); fig.savefig(OUT / "S039_zone2_by_shift.png", dpi=120); plt.close(fig)

# 3) S049 - scatter humidity vs residual metal coloured by month ------------------------------
e = REQ["S049"]["turns"][0]["expect"]["values"]
rl["월"] = rl["일자"].dt.month
check("S049 n", len(rl), e["n"], 0)
check("S049 pearson_r", rl[["외기습도", "잔류금속"]].corr().iloc[0, 1], e["pearson_r"], 0.001)
for m, n in e["series"].items():
    check(f"S049 month {m} n", (rl["월"] == int(m)).sum(), n, 0)
fig, ax = plt.subplots(figsize=(7, 4.5))
sc = ax.scatter(rl["외기습도"], rl["잔류금속"], c=rl["월"], cmap="viridis", s=10, alpha=0.7)
fig.colorbar(sc, ax=ax, label="월")
b = rl.groupby(pd.cut(rl["외기습도"], [20, 50, 60, 65, 70, 80, 90, 100]), observed=True)["잔류금속"].mean()
ax.plot([i.mid for i in b.index], b.values, "r-o", label="구간 평균")
ax.legend(); ax.set(xlabel="외기습도 (%)", ylabel="잔류금속 (wt%)", title="S049 humidity vs residual metal")
fig.tight_layout(); fig.savefig(OUT / "S049_humidity_metal.png", dpi=120); plt.close(fig)

# 4) S058 - heatmap of 노즐 막힘 counts, reactor x production week ----------------------------
e = REQ["S058"]["turns"][0]["expect"]["values"]
n = dt[dt["원인"] == "노즐 막힘"].copy()
n["주차"] = (n["일자"] - pd.Timestamp("2026-03-02")).dt.days // 7 + 1
hm = n.groupby(["반응기", "주차"]).size().unstack(fill_value=0).reindex(columns=range(1, 27), fill_value=0)
check("S058 matrix equal", int((hm.to_numpy() == np.array(e["matrix"])).all()), 1, 0)
check("S058 total weeks 1-13", hm.loc[:, 1:13].to_numpy().sum(), np.array(e["matrix"])[:, :13].sum(), 0)
check("S058 total weeks 14-26", hm.loc[:, 14:26].to_numpy().sum(), np.array(e["matrix"])[:, 13:].sum(), 0)
fig, ax = plt.subplots(figsize=(10, 2.8))
im = ax.imshow(hm.to_numpy(), cmap="Reds", aspect="auto")
ax.set_xticks(range(26), range(1, 27)); ax.set_yticks(range(4), hm.index)
fig.colorbar(im, ax=ax, label="건수"); ax.set(xlabel="주차", title="S058 노즐 막힘 건수 (반응기 × 주차)")
fig.tight_layout(); fig.savefig(OUT / "S058_nozzle_heatmap.png", dpi=120); plt.close(fig)

# 5) SS13 final turn - binned residence time, one line per lot group, argmax marked ------------
e = REQ["SS13"]["turns"][-1]["expect"]
edges = np.round(np.arange(2.5, 6.751, 0.25), 2)
rl["grp"] = np.where(rl["촉매로트"] >= "FC-2606", "new (FC-2606~2608)", "old (FC-2602~2605)")
rl["bin"] = pd.cut(rl["체류시간"], edges, right=False)
fig, ax = plt.subplots(figsize=(7, 4.5))
argmax = next(a for a in e["asks"] if a["name"].startswith("argmax"))["value"]
for g, sub in rl.groupby("grp"):
    st = sub.groupby("bin", observed=True)["CNT수율"].agg(["mean", "size"])
    st = st[st["size"] >= 10]
    mids = np.array([i.mid for i in st.index])
    check(f"SS13 {g} n bins", len(st), e["values"]["series"][g]["n"], 0)
    check(f"SS13 {g} argmax", mids[st["mean"].argmax()], argmax[g], 1e-9)
    ax.plot(mids, st["mean"], marker="o", label=g)
    ax.annotate(f"{mids[st['mean'].argmax()]:.3f} s", (mids[st["mean"].argmax()], st["mean"].max()),
                textcoords="offset points", xytext=(0, 8), ha="center")
ax.legend(); ax.set(xlabel="체류시간 bin midpoint (s)", ylabel="mean CNT수율 (g/g-cat)", title="SS13 residence-time sweet spot")
fig.tight_layout(); fig.savefig(OUT / "SS13_residence_sweetspot.png", dpi=120); plt.close(fig)

# 6) S017 - TGA onset by tangent at DTG max, baseline = W(500 °C) -------------------------------
e = REQ["S017"]["turns"][0]["expect"]
t = pd.read_excel(ROOT / "data/tga_batches.xlsx", sheet_name="R2-260616-1")
T, W, Dv = t["온도 (°C)"].to_numpy(), t["중량 (%)"].to_numpy(), t["미분중량 (%/°C)"].to_numpy()
m = (T >= 450) & (T <= 800)
i = np.flatnonzero(m)[np.argmax(Dv[m])]
w500 = np.interp(500, T, W)
onset = T[i] - (w500 - W[i]) / Dv[i]
check("S017 onset", onset, e["asks"][0]["value"], 0.5)
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot(T, W, label="TG")
tt = np.linspace(onset - 30, T[i] + 40, 50)
ax.plot(tt, W[i] - Dv[i] * (tt - T[i]), "r--", lw=1, label="tangent @ DTG max")
ax.axhline(w500, color="gray", ls=":", lw=1)
ax.plot([onset], [w500], "ko"); ax.annotate(f"onset {onset:.1f} °C", (onset, w500), xytext=(-110, -30),
                                             textcoords="offset points", arrowprops=dict(arrowstyle="->"))
ax.set(xlabel="온도 (°C)", ylabel="중량 (%)", ylim=(0, 105), title="S017 R2-260616-1 extrapolated onset")
ax.legend(); fig.tight_layout(); fig.savefig(OUT / "S017_tga_onset.png", dpi=120); plt.close(fig)

# -------------------------------------------------------------------------------------------
w = max(len(r[0]) for r in results)
for name, got, want, ok in results:
    print(f"{'OK ' if ok else 'BAD'} {name:<{w}}  got={got}  expected={want}")
nbad = sum(not r[3] for r in results)
print(f"\n{len(results) - nbad}/{len(results)} checks passed; figures in {OUT}")
raise SystemExit(1 if nbad else 0)
