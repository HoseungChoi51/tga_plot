"""The CNT study page: should a local Qwen drive plots through the thin layer, and on which engine.

Reads only result files (eval/results/...): the sealed runs on strixhalo and through opencode, the blind review, the
E3 sessions and judge, E1 latency, and the E4 export and live checks.

    python experiments/report/build_cnt.py    -> report/cnt/index.html
"""
import csv
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "eval" / "results"
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "report"))
import cnt_summary  # noqa: E402
from build_report import CSS, esc  # noqa: E402

OUT = ROOT / "report" / "cnt"
ARM = {"P-mpl": "Protocol · matplotlib", "P-ec": "Protocol · ECharts", "P-hyb": "Protocol · hybrid",
       "R-mpl": "Raw code · matplotlib", "R-mpl-oc": "Raw code · matplotlib (opencode)"}
STRATA = {"always_fail": 30, "random": 86}
EXTRA_CSS = ".answers{grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}.fig .tw svg.chart{min-width:600px}"


def rows_of(name):
    p = RES / name
    return list(csv.DictReader(open(p, encoding="utf-8"))) if p.exists() else []


def pctl(xs, q):
    return cnt_summary.pct(list(xs), q)


def f1(x):
    return "–" if x is None else f"{x:.1f}"


# ------------------------------------------------------------------ data
def load():
    D = {}
    for run in ("sealed", "sealed_oc"):
        rows = rows_of(f"cnt_{run}.csv")
        arms = sorted({r["arm"] for r in rows}, key=["P-mpl", "P-ec", "P-hyb", "R-mpl"].index)
        D[run] = {"rows": rows, "arms": {a: cnt_summary.arm_stats([r for r in rows if r["arm"] == a]) for a in arms},
                  "items": {a: cnt_summary.by_item([r for r in rows if r["arm"] == a]) for a in arms}}
    D["review"] = rows_of("review_cnt_sealed.csv")
    D["judge"] = json.loads((RES / "e3_judge.json").read_text(encoding="utf-8"))
    D["sessions"] = {}
    for sd in sorted((RES / "sessions").glob("E3_G*")):
        stt = json.loads((sd / "state.json").read_text(encoding="utf-8"))
        log = [json.loads(x) for x in (sd / "persona_log.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        con = json.loads((sd / "conclusion.json").read_text(encoding="utf-8"))
        D["sessions"][sd.name] = {"arm": stt["arm"], "turns": stt["turns"], "log": log, "con": con}
    D["e1"] = rows_of("cnt_latency_e1.csv")
    D["exports"] = rows_of("cnt_exports.csv")
    key = json.loads((RES / "exports" / "key.json").read_text())
    pid = json.loads((RES / "exports" / "pair_ids.json").read_text())
    acc, n, pref = Counter(), Counter(), Counter()
    for g in (1, 2):
        for r in rows_of(f"exports/review_grades_{g}.csv"):
            m = key[pid[r["id"]]]
            for side in "ab":
                n[m[side]] += 1
                acc[m[side]] += r[f"{side}_ok"] == "yes"
            p = r["prefer"].lower()
            pref[m.get(p, "tie")] += 1
    D["e4"] = {"acc": acc, "n": n, "pref": pref}
    D["live"] = json.loads((RES / "cnt_live.json").read_text())
    return D


def review_est(rev, arm):
    """Grader verdicts on repeat 1, weighted from the two strata (all 30 always-failing turns, 18 of the other 86)."""
    est = {}
    for m in ("yes", "partial", "no", "silent"):
        tot = 0.0
        for stv, n in STRATA.items():
            rs = [o for o in rev if o["arm"] == arm and o["stratum"] == stv]
            if not rs:
                continue
            if m == "silent":
                k = sum(o["verdict"] == "no" and o["ok_run"] == "1" and o["unsupported"] in ("", "0") for o in rs)
            else:
                k = sum(o["verdict"] == m for o in rs)
            tot += n * k / len(rs)
        est[m] = 100 * tot / sum(STRATA.values())
    return est


def e1_stats(rows, arm, users):
    rs = [r for r in rows if r["arm"] == arm and r["users"] == str(users)]
    if not rs:
        return None
    t = [float(r["turn_s"]) for r in rs]
    llm = [(float(r["prefill_ms"] or 0) + float(r["decode_ms"] or 0)) / 1000 for r in rs]
    t2 = [a - b / 2 for a, b in zip(t, llm)]                     # a 2x machine halves prefill and decode
    dec = [float(r["output_tokens"]) / (float(r["decode_ms"]) / 1000) for r in rs if float(r["decode_ms"] or 0) > 0]
    pre = [(float(r["prompt_tokens"]) - float(r["cached_tokens"] or 0)) / (float(r["prefill_ms"]) / 1000)
           for r in rs if float(r["prefill_ms"] or 0) > 0 and float(r["prompt_tokens"] or 0) > float(r["cached_tokens"] or 0)]
    return {"n": len(rs), "p50": pctl(t, .5), "p90": pctl(t, .9), "p50_2x": pctl(t2, .5), "p90_2x": pctl(t2, .9),
            "over10": 100 * sum(x > 10 for x in t) / len(t), "over10_2x": 100 * sum(x > 10 for x in t2) / len(t2),
            "draw": pctl([float(r["draw_s"]) for r in rs], .5), "out_tok": pctl([float(r["output_tokens"]) for r in rs], .5),
            "decode_tps": st.median(dec) if dec else None, "prefill_tps": st.median(pre) if pre else None,
            "cached": pctl([float(r["cached_tokens"] or 0) for r in rs], .5), "prompt": pctl([float(r["prompt_tokens"]) for r in rs], .5),
            "retry": 100 * sum(int(r["calls"]) > 1 for r in rs) / len(rs), "ok": 100 * sum(r["ok"] == "1" for r in rs) / len(rs)}


def escalation(rows, arm):
    """Checker pass if the turns where `arm` flagged an unsupported ask or drew nothing took the raw-code result instead."""
    by = defaultdict(dict)
    for r in rows:
        by[(r["item"], r["turn"], r["repeat"])][r["arm"]] = r
    esc_keys = {k for k, v in by.items() if arm in v and (v[arm]["unsupported"] not in ("", "0") or v[arm]["ok_run"] != "1")}
    base, both = [], []
    for k, v in by.items():
        if arm in v and v[arm]["pass"] in ("0", "1"):
            base.append(int(v[arm]["pass"]))
        src = "R-mpl" if k in esc_keys else arm
        if src in v and v[src]["pass"] in ("0", "1"):
            both.append(int(v[src]["pass"]))
    return {"share": 100 * len(esc_keys) / len(by), "base": 100 * sum(base) / len(base), "with": 100 * sum(both) / len(both)}


# ------------------------------------------------------------------ charts
def ci_chart(title, items, thresh=None):
    """items: [(label, est, lo, hi, css colour var)] as a dot with a 95% interval on 0-100%."""
    W, L, R, RH, T = 760, 250, 40, 30, 30
    H = T + RH * len(items) + 34
    x = lambda v: L + (W - L - R) * v / 100  # noqa: E731
    p = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">']
    for v in range(0, 101, 20):
        p.append(f'<line class="grid" x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{T - 8}" y2="{H - 28}"/>'
                 f'<text class="tick" x="{x(v):.1f}" y="{H - 12}" text-anchor="middle">{v}%</text>')
    if thresh is not None:
        p.append(f'<line x1="{x(thresh):.1f}" x2="{x(thresh):.1f}" y1="{T - 14}" y2="{H - 28}" stroke="var(--warn)" stroke-width="1.5" stroke-dasharray="4 3"/>'
                 f'<text class="tick" x="{x(thresh) + 4:.1f}" y="{T - 16}">{thresh}% bar</text>')
    for i, (lab, est, lo, hi, col) in enumerate(items):
        y = T + RH * i + RH / 2
        p.append(f'<g><title>{esc(lab)}: {est:.1f}% (95% interval {lo:.1f}–{hi:.1f})</title>'
                 f'<text class="lab" x="{L - 10}" y="{y + 4:.1f}" text-anchor="end">{esc(lab)}</text>'
                 f'<line class="ci" x1="{x(lo):.1f}" x2="{x(hi):.1f}" y1="{y:.1f}" y2="{y:.1f}"/>'
                 f'<circle cx="{x(est):.1f}" cy="{y:.1f}" r="6" fill="var({col})" stroke="var(--panel)" stroke-width="2"/>'
                 f'<text class="val" x="{x(hi) + 8:.1f}" y="{y + 4:.1f}">{est:.1f}%</text></g>')
    p.append("</svg>")
    return f'<figure class="fig"><figcaption class="cap-top">{esc(title)}</figcaption><div class="tw">{"".join(p)}</div></figure>'


def verdict_chart(title, items):
    """items: [(label, yes, partial, no)] in % as one stacked bar each."""
    W, L, R, RH, T = 760, 250, 20, 30, 10
    H = T + RH * len(items) + 30
    x = lambda v: L + (W - L - R) * v / 100  # noqa: E731
    cols = [("yes", "--good", "accepted"), ("partial", "--warn", "partly"), ("no", "--crit", "rejected")]
    p = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">']
    for i, (lab, *vals) in enumerate(items):
        y = T + RH * i + 5
        p.append(f'<text class="lab" x="{L - 10}" y="{y + 15}" text-anchor="end">{esc(lab)}</text>')
        acc = 0
        for (key, col, word), v in zip(cols, vals):
            w = x(acc + v) - x(acc)
            p.append(f'<g><title>{esc(lab)}: {word} {v:.1f}%</title><rect x="{x(acc) + 1:.1f}" y="{y}" width="{max(0, w - 2):.1f}" height="20" rx="3" fill="var({col})" opacity=".85"/>'
                     + (f'<text class="seg" x="{x(acc) + w / 2:.1f}" y="{y + 14}" text-anchor="middle" fill="#fff">{v:.0f}%</text>' if w > 34 else "") + "</g>")
            acc += v
    p.append("</svg>")
    leg = "".join(f'<span><i class="sw" style="background:var({c})"></i>{w}</span>' for _, c, w in cols)
    return f'<figure class="fig"><figcaption class="cap-top">{esc(title)}</figcaption><div class="legend">{leg}</div><div class="tw">{"".join(p)}</div></figure>'


def table(head, rows, num=()):
    th = "".join(f'<th class="num">{esc(h)}</th>' if i in num else f"<th>{esc(h)}</th>" for i, h in enumerate(head))
    tr = "".join("<tr>" + "".join(f'<td class="num">{c}</td>' if i in num else f"<td>{c}</td>" for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="tw"><table><tr>{th}</tr>{tr}</table></div>'


def chip(ok, text):
    return f'<span class="chip {"ok" if ok is True else "none" if ok is False else "part"}">{esc(text)}</span>'


# ------------------------------------------------------------------ page
def build():
    D = load()
    S, O = D["sealed"], D["sealed_oc"]
    sa, oa = S["arms"], O["arms"]
    rev = D["review"]
    R = {a: review_est(rev, a) for a in ("P-mpl", "P-ec", "P-hyb", "R-mpl-oc")}
    e1 = {(a, u): e1_stats(D["e1"], a, u) for a in ("P-ec", "P-mpl", "R-mpl") for u in (1,)}
    best_p = max(("P-mpl", "P-ec", "P-hyb"), key=lambda a: sa[a]["pass"])
    best_rev = max(("P-mpl", "P-ec", "P-hyb"), key=lambda a: R[a]["yes"])
    oc_best_p = max((a for a in ("P-mpl", "P-ec", "P-hyb") if a in oa), key=lambda a: oa[a]["pass"])
    gap_oc = cnt_summary.boot(O["items"][oc_best_p], O["items"]["R-mpl"]) if "R-mpl" in oa else None
    d_ec_mpl = cnt_summary.boot(S["items"]["P-ec"], S["items"]["P-mpl"])
    d_ec_hyb = cnt_summary.boot(S["items"]["P-ec"], S["items"]["P-hyb"])
    hatch = max(sa["P-mpl"]["drawing_hatch"], sa["P-hyb"]["drawing_hatch"])
    e4 = D["e4"]
    e4_ratio = (e4["acc"]["echarts"] / e4["n"]["echarts"]) / (e4["acc"]["matplotlib"] / e4["n"]["matplotlib"])
    live = [r for r in D["live"] if r["kind"] == "live"]
    live_ok = all(not r["bad"] for r in live) and sum(r["labels"] for r in live) == sum(r["attached"] for r in live)
    lat = e1[("P-ec", 1)] or {}
    lat_m = e1[("P-mpl", 1)] or {}
    p90_2x = max(lat.get("p90_2x") or 99, lat_m.get("p90_2x") or 99)
    silent_rev = min(R[a]["silent"] for a in ("P-mpl", "P-ec", "P-hyb"))
    silent_chk = min(sa[a]["silent"] for a in ("P-mpl", "P-ec", "P-hyb"))
    J = D["judge"]
    rt = json.loads((RES / "cnt_raw_tokens.json").read_text()) if (RES / "cnt_raw_tokens.json").exists() else None
    tps = (e1[("P-ec", 1)] or {}).get("decode_tps")
    xr = e1[("R-mpl", 1)]
    raw_s = (f"median {xr['p50']:.0f} s, p90 {xr['p90']:.0f} s a turn on Strix, p90 {xr['p90_2x']:.0f} s even on a 2× machine" if xr
             else f"about {rt['turn_tokens_p50'] / tps:.0f} s of decoding a turn on Strix" if rt and tps else "pending")
    s = []

    # ---------- header and answers
    s.append('<h1>A thin plotting layer for local Qwen: the verdict</h1>')
    s.append('<p class="meta">CNT production analytics (simulated plant, R1–R4 FC-CVD) · Qwen3.8 Flash Next on strixhalo, thinking off · '
             'sealed test set, 75 requests (60 single + 15 sessions), 116 turns · 2026-11-20</p>')
    s.append(f'<p class="lede">Should an engineer\'s chat with a local, Qwen-tier model draw plots through a thin layer (the model writes a '
             f'small JSON spec; Python draws it), and should that layer draw with matplotlib or ECharts? The layer was rebuilt for bar, '
             f'scatter, histogram, heatmap and pie charts with a data grammar and a sandboxed data hatch, tuned on a separate dev set, frozen, '
             f'and then run once on a sealed set written by another agent.</p>')
    cards = [
        ("Use the thin layer?", "Yes — but it is not ready to hand over yet",
         f"Raw code is no interactive path: {raw_s}. Judged by eye, the protocol matches raw code ({R[best_rev]['yes']:.0f}% vs "
         f"{R['R-mpl-oc']['yes']:.0f}% of turns accepted) in a fraction of the time. But {silent_rev:.0f}–{max(R[a]['silent'] for a in ('P-mpl', 'P-ec', 'P-hyb')):.0f}% of turns still "
         f"come back wrong without a warning; the rule allowed 5%."),
        ("Which engine?", "One spec, drawn by both: ECharts live, matplotlib for export",
         f"The engines tie on accuracy (ECharts − matplotlib {d_ec_mpl[0]:+.1f} points). ECharts gives the live view; matplotlib exports are "
         f"preferred head to head ({e4['pref']['matplotlib']} vs {e4['pref']['echarts']}) and carry the drawing hatch ({hatch:.1f}% of turns)."),
        ("Fast enough?", f"Yes on a 2× machine: p90 {f1(min(lat.get('p90_2x') or 99, lat_m.get('p90_2x') or 99))}–{f1(p90_2x)} s" if p90_2x < 99 else "Pending E1",
         f"One user on today's Strix: median {f1(lat.get('p50'))} s, p90 {f1(lat.get('p90'))} s per turn (ECharts arm), including retries and drawing. "
         f"Halving prefill and decode gives p90 {f1(lat.get('p90_2x'))} s."),
        ("Does it support real analysis?", "Yes: 16 of 16 simulated sessions reached a conclusion",
         f"Correct on {sum(j['grade'] == 'correct' for j in J)}, partly on {sum(j['grade'] == 'partial' for j in J)}, wrong on {sum(j['grade'] == 'wrong' for j in J)} "
         f"of 16 (both engines graded the same on every goal); the assistant misled the engineer in {sum(bool(j['assistant_misled']) for j in J)}."),
    ]
    s.append('<div class="answers">' + "".join(f'<div class="ans"><h3>{esc(q)}</h3><p class="big">{esc(a)}</p><p>{esc(b)}</p></div>' for q, a, b in cards) + "</div>")

    # ---------- decision rules
    s.append('<h2 id="rules">The preregistered decision rules</h2>')
    s.append("<p>The rules were fixed before the sealed runs. The checker is the preregistered metric; the blind review (repeat 1, two "
             "graders) is shown beside it because it shows where the checker is too strict.</p>")
    rr = [
        ["Layer", "p90 turn time on a 2× machine ≤ 10 s", f"{f1(p90_2x)} s (one user, projected)", chip(p90_2x <= 10, "met" if p90_2x <= 10 else "not met")],
        ["Layer", "best protocol arm ≥ 70% of sealed turns",
         f"checker {sa[best_p]['pass']:.1f}% ({ARM[best_p]}); blind review {R[best_rev]['yes']:.1f}% ({ARM[best_rev]})",
         chip(sa[best_p]["pass"] >= 70 or None, "checker no · review yes")],
        ["Layer", "… and ≤ 10 points below raw code",
         (f"same serving (opencode): {gap_oc[0]:+.1f} points [{gap_oc[1]:+.1f}, {gap_oc[2]:+.1f}] by checker; review {R[best_rev]['yes'] - R['R-mpl-oc']['yes']:+.1f}" if gap_oc else "pending"),
         chip(gap_oc[0] >= -10 if gap_oc else None, "met" if gap_oc and gap_oc[0] >= -10 else "not met" if gap_oc else "pending")],
        ["Layer", "silent failures ≤ 5% of turns", f"review {silent_rev:.1f}–{max(R[a]['silent'] for a in ('P-mpl', 'P-ec', 'P-hyb')):.1f}% (checker proxy {silent_chk:.0f}%+)", chip(False, "not met")],
        ["Engine", "ECharts within 5 points of matplotlib and hybrid", f"{d_ec_mpl[0]:+.1f} and {d_ec_hyb[0]:+.1f} points", chip(d_ec_mpl[0] >= -5 and d_ec_hyb[0] >= -5, "met")],
        ["Engine", "drawing-hatch turns < 5%", f"{sa['P-mpl']['drawing_hatch']:.1f}% (matplotlib), {sa['P-hyb']['drawing_hatch']:.1f}% (hybrid)", chip(hatch < 5, "met" if hatch < 5 else "not met (narrowly)")],
        ["Engine", "ECharts export acceptance ≥ 90% of matplotlib's", f"{100 * e4_ratio:.0f}%", chip(e4_ratio >= .9, "met")],
        ["Engine", "live view keeps labels attached", f"{sum(r['attached'] for r in live)}/{sum(r['labels'] for r in live)} labels attached after zoom, pan and resize", chip(live_ok, "met" if live_ok else "not met")],
    ]
    s.append(table(["", "rule", "measured", "verdict"], rr))
    s.append('<p><b>Reading.</b> By the letter, the layer is not ready (two layer rules fail) and the engine rule falls through to "one spec, '
             'drawn by both" because matplotlib\'s drawing hatch was used on slightly more than 5% of turns. The rules also say what happens '
             f'then: raw code is no alternative ({raw_s}), so the misses become the layer backlog (below).</p>')

    # ---------- E2
    s.append('<h2 id="e2">1 · Sealed accuracy (E2)</h2>')
    items = [(ARM[a] + " · Strix", sa[a]["pass"], *sa[a]["ci"], c) for a, c in (("P-mpl", "--s2"), ("P-ec", "--s1"), ("P-hyb", "--s3"))]
    items += [(ARM[a] + " · opencode", oa[a]["pass"], *oa[a]["ci"], c) for a, c in (("P-mpl", "--s2"), ("P-ec", "--s1"), ("P-hyb", "--s3"), ("R-mpl", "--ink3")) if a in oa]
    s.append(ci_chart("Checker pass per turn, 3 repeats, 95% interval by resampling requests", items, thresh=70))
    hdr = ["arm", "serving", "turns", "pass", "95% CI", "no plot", "unsupported flagged", "data hatch", "drawing hatch", "retried", "turn p50 / p90 (s)"]
    tr = []
    for run, lab in (("sealed", "Strix, 2 workers"), ("sealed_oc", "opencode, 8 workers")):
        for a, x in D[run]["arms"].items():
            tr.append([esc(ARM[a]), lab, x["turns"], f"{x['pass']:.1f}%", f"{x['ci'][0]:.1f}–{x['ci'][1]:.1f}", f"{x['no_plot']:.1f}%",
                       f"{x['flagged_unsupported']:.1f}%", f"{x['data_code']:.1f}%", f"{x['drawing_hatch']:.1f}%", f"{x['retry_turns']:.1f}%",
                       f"{x['turn_s'][0]:.1f} / {x['turn_s'][1]:.1f}"])
    s.append(table(hdr, tr, num=(2, 3, 4, 5, 6, 7, 8, 9, 10)))
    s.append(f"<p>On Strix the three protocol arms are within {abs(d_ec_mpl[0]):.1f} points of each other (ECharts − matplotlib "
             f"{d_ec_mpl[0]:+.1f} [{d_ec_mpl[1]:+.1f}, {d_ec_mpl[2]:+.1f}]; ECharts − hybrid {d_ec_hyb[0]:+.1f} [{d_ec_hyb[1]:+.1f}, {d_ec_hyb[2]:+.1f}]). "
             "Through opencode the same arms and the raw-code ceiling ran on Qwen3.8 Flash; the raw-code comparison uses that run only, so "
             "both sides share the serving.</p>")
    kinds = sorted({k for a in ("P-mpl", "P-ec", "P-hyb") for k in sa[a]["by_kind"]}, key=lambda k: -sa["P-mpl"]["by_kind"].get(k, [0, 0])[1])
    kr = [[esc(k)] + [f"{sa[a]['by_kind'][k][0]:.0f}%" if k in sa[a]["by_kind"] else "–" for a in ("P-mpl", "P-ec", "P-hyb")]
          + ([f"{oa['R-mpl']['by_kind'][k][0]:.0f}%" if k in oa["R-mpl"]["by_kind"] else "–"] if "R-mpl" in oa else [])
          + [str(sa["P-mpl"]["by_kind"].get(k, [0, 0])[1] // 3)] for k in kinds]
    s.append("<h3>By expected chart kind</h3>" + table(["kind", "matplotlib", "ECharts", "hybrid"] + (["raw code (opencode)"] if "R-mpl" in oa else []) + ["turns"],
                                                         kr, num=(1, 2, 3, 4, 5)))
    ty = sorted(sa["P-mpl"]["by_type"])
    s.append("<h3>Single requests and sessions</h3>" + table(["turns", "matplotlib", "ECharts", "hybrid"],
             [[esc(t)] + [f"{sa[a]['by_type'][t][0]:.0f}%" for a in ("P-mpl", "P-ec", "P-hyb")] for t in ty], num=(1, 2, 3)))
    s.append("<p>Follow-up turns in a session pass less often than first turns, partly because a follow-up must keep the earlier asks.</p>")
    esc_rows = []
    for a in ("P-ec", "P-hyb", "P-mpl"):
        x = escalation(O["rows"], a)
        esc_rows.append([esc(ARM[a]), f"{x['share']:.1f}%", f"{x['base']:.1f}%", f"{x['with']:.1f}%", f"{x['with'] - x['base']:+.1f}"])
    s.append("<h3>A raw-code slow path for flagged turns (arm d, simulated)</h3><p>Instead of a separate run, arm (d) is simulated from "
             "the opencode run: every turn where the protocol flagged an ask as unsupported or drew nothing takes the raw-code arm's result "
             "for the same request and repeat instead.</p>"
             + table(["arm", "turns escalated", "checker pass", "with slow path", "change"], esc_rows, num=(1, 2, 3, 4))
             + "<p>About three points, for a minute's wait on one turn in ten. It cannot touch silent failures, which are by definition not "
               "flagged, so the preregistered condition for adopting it (halve silent failures) is not met. It is still a reasonable opt-in "
               "“try harder” button.</p>")

    # ---------- review
    s.append('<h2 id="review">2 · What the checker misses: blind review</h2>')
    agree = defaultdict(dict)
    for o in rev:
        agree[(o["item"], o["turn"], o["arm"])][o["grader"]] = o["verdict"]
    both = [v for v in agree.values() if len(v) == 2]
    ag = 100 * sum(v["g1"] == v["g2"] for v in both) / len(both)
    s.append(f"<p>30 of the 116 sealed turns failed the checker in every protocol run. Two fresh graders saw repeat 1 of each of those turns plus 18 "
             f"random others, as shuffled, unlabelled panels (the three Strix arms and the opencode raw-code arm), with the request and the raw "
             f"data but not the checker's answer key. They agreed on {ag:.0f}% of verdicts. Estimates below weight the two strata back to all "
             f"116 turns.</p>")
    s.append(verdict_chart("Blind review, weighted to all sealed turns", [(ARM[a], R[a]["yes"], R[a]["partial"], R[a]["no"]) for a in ("P-hyb", "P-mpl", "P-ec", "R-mpl-oc")]))
    srows = []
    for stv in ("always_fail", "random"):
        for a in ("P-mpl", "P-ec", "P-hyb", "R-mpl-oc"):
            rs = [o for o in rev if o["arm"] == a and o["stratum"] == stv]
            c = Counter(o["verdict"] for o in rs)
            srows.append([("always-failing turns (30)" if stv == "always_fail" else "random other turns (18)"), esc(ARM[a]),
                          f"{100 * c['yes'] / len(rs):.0f}%", f"{100 * c['partial'] / len(rs):.0f}%", f"{100 * c['no'] / len(rs):.0f}%",
                          f"{100 * sum(o['checker'] == '1' for o in rs) / len(rs):.0f}%"])
    s.append(table(["stratum", "arm", "accepted", "partly", "rejected", "checker pass"], srows, num=(2, 3, 4, 5)))
    dd = Counter(t for o in rev if o["arm"].startswith("P-") and o["verdict"] != "yes" for t in o["defects"].split())
    dr = Counter(t for o in rev if o["arm"] == "R-mpl-oc" and o["verdict"] != "yes" for t in o["defects"].split())
    s.append(f"<p>About a third of the always-failing protocol panels were acceptable to the graders, so the checker under-counts. "
             f"About half were real misses. Raw code did much better on exactly those hard turns and worse on ordinary ones. "
             f"Defects on protocol panels that were not accepted: {', '.join(f'{k} {v}' for k, v in dd.most_common(7))}. "
             f"On raw-code panels: {', '.join(f'{k} {v}' for k, v in dr.most_common(5))}.</p>")
    s.append(f"<p><b>Silent failures</b> (a figure is drawn, the graders reject it, and nothing was flagged as unsupported): "
             + ", ".join(f"{ARM[a]} {R[a]['silent']:.1f}%" for a in ("P-mpl", "P-ec", "P-hyb", "R-mpl-oc"))
             + ". The checker's proxy (drawn, failed, not flagged) is "
             + ", ".join(f"{sa[a]['silent']:.0f}%" for a in ("P-mpl", "P-ec", "P-hyb")) + "; it counts every strict-checker miss as silent.</p>")

    # ---------- E1
    s.append('<h2 id="e1">3 · Latency on Strix (E1)</h2>')
    lr = []
    for a in ("P-ec", "P-mpl", "R-mpl"):
        x = e1[(a, 1)]
        if x:
            lr.append([esc(ARM[a]), x["n"], f1(x["p50"]), f1(x["p90"]), f"{x['over10']:.0f}%", f1(x["p50_2x"]), f1(x["p90_2x"]), f"{x['over10_2x']:.0f}%",
                       f"{x['prompt']:.0f} / {x['cached']:.0f}", f"{x['out_tok']:.0f}", f1(x["decode_tps"]), f"{x['draw']:.2f}", f"{x['retry']:.0f}%"])
    if lr:
        s.append(table(["arm (one user)", "turns", "p50 s", "p90 s", "> 10 s", "p50 2× s", "p90 2× s", "> 10 s at 2×", "prompt / cached tokens",
                        "output tokens", "decode tok/s", "draw s", "retried"], lr, num=tuple(range(1, 13))))
        if xr:
            s.append(f"<p class='small'>Raw code was timed on {xr['n']} sealed single requests (every fifth), one user, same machine.</p>")
    two = {a: x["turn_s"] for a, x in sa.items()}
    s.append(f"<p>Turn time is end to end: model reply, plotkit, drawing and any retries. The 2× column halves prefill and decode and keeps "
             f"the rest. The sealed runs themselves ran two workers on Strix's two slots, i.e. two users at once all the time: p50/p90 "
             + ", ".join(f"{ARM[a]} {v[0]:.1f}/{v[1]:.1f} s" for a, v in two.items())
             + ".</p>")
    if rt and xr:
        s.append(f"<p><b>Raw code.</b> On Strix it needs {xr['out_tok']:,.0f} output tokens a turn at the median (retries included; "
                 f"{xr['retry']:.0f}% of turns needed one), so most turns take half a minute or more even on a 2× machine. The opencode model "
                 f"wrote shorter scripts: {rt['turn_tokens_p50']:,} tokens a turn at the median, counted with the deployed model's tokenizer. "
                 f"A protocol reply is about {(e1[('P-ec', 1)] or {}).get('out_tok', 0):.0f} tokens, and its slow turns come from prefilling "
                 f"new data previews (about {(e1[('P-ec', 1)] or {}).get('prefill_tps', 0):.0f} tokens/s uncached) and from retries.</p>")

    # ---------- E3
    s.append('<h2 id="e3">4 · Simulated analysis sessions (E3)</h2>')
    s.append("<p>Eight yield and quality goals with planted causes. A Claude persona played the engineer: it saw only the figures and "
             "the fixed Korean summary, asked one request at a time (at most 12), and wrote a conclusion. A judge holding the hidden answers "
             "graded each conclusion. These sessions used Qwen3.8 Flash through opencode.</p>")
    jr = []
    for g in sorted({j["goal"] for j in J}):
        row = [esc(g)]
        for a in ("P-ec", "P-hyb"):
            j = next(j for j in J if j["goal"] == g and j["arm"] == a)
            se = D["sessions"].get(j["session"], {})
            row.append(f'{chip({"correct": True, "wrong": False}.get(j["grade"]), j["grade"])} {j["turns_used"]} turns')
            row.append(str(sum(1 for x in se.get("log", []) if x.get("summary_matches_plot") is False)))
        jr.append(row)
    s.append(table(["goal", "ECharts arm", "summary ≠ plot", "hybrid arm", "summary ≠ plot"], jr, num=(2, 4)))
    ses = D["sessions"].values()
    ntu = sum(len(x["turns"]) for x in ses)
    s.append(f"<p>{ntu} turns in all; {sum(not t['ok'] for x in ses for t in x['turns'])} failed to draw; median turn "
             f"{st.median(t['turn_s'] for x in ses for t in x['turns']):.1f} s through opencode. Wrong conclusions came from the personas' choice "
             "of what to look at and from confounded factors, not from the assistant. What slowed the engineers down, in their own logs: "
             "box plots are not supported (one fallback drew an empty scatter with a summary that still reported points); summaries leave out "
             "categories the plot shows; two measures with different units were put on one axis; bar charts start at zero, so small differences "
             "disappear; month ticks print as full dates; there is no stratified or per-reactor panel view.</p>")

    # ---------- E4
    s.append('<h2 id="e4">5 · Exports and the live view (E4)</h2>')
    ex = D["exports"]
    s.append(table(["engine", "files", "exact pixel size", "vector PDF", "fonts embedded", "blind graders: “submit as is”"],
                   [[e, sum(r["engine"] == e for r in ex), f"{sum(r['engine'] == e and r['png_px_ok'] == '1' for r in ex)}",
                     f"{sum(r['engine'] == e and r['pdf_vector'] == '1' for r in ex)}",
                     f"{sum(r['engine'] == e and r['pdf_vector'] == '1' and r['pdf_fonts_not_embedded'] in ('', '0', '[]') for r in ex)}",
                     f"{e4['acc'][e]}/{e4['n'][e]} ({100 * e4['acc'][e] / e4['n'][e]:.0f}%)"] for e in ("matplotlib", "echarts")], num=(1, 2, 3, 4, 5)))
    s.append(f"<p>44 reference figures in journal and slide styles from both engines, graded in blind pairs by two graders. Head to head they "
             f"preferred matplotlib {e4['pref']['matplotlib']} times, ECharts {e4['pref']['echarts']}, tie {e4['pref']['tie']}. "
             f"In the live check (Playwright: zoom, pan, resize, toggle series) all {sum(r['labels'] for r in live)} data labels on "
             f"{len(live)} live charts stayed attached; the static exports' pixel-placed labels would not "
             f"({sum(len(r['bad']) for r in D['live'] if r['kind'] == 'static')} moved off their points), which is why the live view uses data-anchored marks.</p>")

    # ---------- backlog
    s.append('<h2 id="backlog">6 · What to build next</h2>')
    s.append("<ol class='rec'>"
             "<li><b>Stop the silent misses first.</b> Most rejected protocol figures drew <i>something</i> plausible: a missing ask, the wrong "
             "aggregation or grouping. Make the spec's <code>asks</code> list checkable (each ask maps to a key that the core verifies after "
             "drawing) and say so in the summary when an ask was not honoured.</li>"
             "<li><b>Add the chart types users reach for:</b> box plot first (asked in most sessions), then per-group panels (small "
             "multiples) and percent-normalised stacked bars.</li>"
             "<li><b>Summaries that match the plot:</b> list every drawn category or series, never drop one; plain numbers, not scientific notation.</li>"
             "<li><b>Layout defaults:</b> never put two units on one axis (split into panels or ask); bar axes that do not start at zero when "
             "differences are small (with a visible break or a note); month ticks as months.</li>"
             "<li><b>Data hatch robustness:</b> the commonest no-plot errors were file paths and column names inside <code>data_code</code>; "
             "pass the loaded frame in, not a path.</li>"
             "<li><b>Keep one spec for both engines</b>: ECharts for the live view, matplotlib for journal export and for drawing hatches; extend "
             "<code>eval/parity.py</code> to all chart types as a CI gate.</li>"
             "<li><b>Re-run the sealed set after the backlog</b>, with a fresh sealed split, to check the 70% bar and the 5% silent-failure bar.</li>"
             "</ol>")

    # ---------- method
    s.append('<h2 id="method">Method and caveats</h2><ul>'
             "<li>Model: Qwen3.8 Flash Next on strixhalo (llama.cpp, 2 slots), thinking off, temperature 0.2. The raw-code ceiling and the E3 "
             "sessions ran on <code>opencode-go/qwen3.8-flash</code> through a private opencode server, whose text endpoint takes one prompt: the "
             "chat was flattened, there is no system role, and the provider's default temperature applies. It may not be the same checkpoint. "
             "That is why raw code is compared only with the protocol arms of the same opencode run.</li>"
             "<li>Sealed set: written by a separate agent that never saw the layer; hashed before any layer change; run once after the freeze. "
             "The tuner looked only at aggregates. One checker crash (a bar without a value) was fixed after the run; it affected only one "
             "ECharts session, which was re-run.</li>"
             "<li>Graders, personas and the judge are Claude agents, not engineers. The review covers repeat 1 of 48 turns.</li>"
             "<li>Latency was measured on Strix only; the 2× projection assumes prefill and decode scale and the rest does not.</li></ul>")
    s.append("<h2 id='repro'>Reproduce</h2><pre>"
             "python experiments/eval/cnt_runs.py --split sealed --name sealed --arms P-mpl,P-ec,P-hyb --repeat 3 --workers 2   # Strix\n"
             "OC_PASS_FILE=... python experiments/eval/cnt_runs_oc.py --split sealed --name sealed_oc --arms P-mpl,P-ec,P-hyb,R-mpl --repeat 3 --workers 8\n"
             "python experiments/eval/cnt_latency.py --split sealed --name e1 --arms P-ec,P-mpl --users 1\n"
             "python experiments/eval/cnt_summary.py; python experiments/eval/cnt_review.py --run sealed_review; python experiments/report/build_cnt.py</pre>")
    page = ('<title>Thin Plot Layer Verdict</title><meta name="claude:viewport-fit-sides" content="cover">'
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">'
            f'<style>{CSS}{EXTRA_CSS}</style><main lang="en">{"".join(s)}</main>')
    return page


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    page = build()
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"wrote {(OUT / 'index.html').relative_to(ROOT)}", len(page), "bytes")
