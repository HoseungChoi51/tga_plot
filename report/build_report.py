"""Build the evaluation report page (report/index.html + report/img/) from eval/results/.

    python report/build_report.py
"""
import csv
import html
import json
import math
import re
import shutil
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "eval" / "results"
OUT = ROOT / "report"
IMG = OUT / "img"

ARMS = ["P-mpl", "P-ec", "R-mpl-brief", "R-ec-brief", "R-mpl-plain", "R-ec-plain"]
ARM_NAME = {"P-mpl": "Protocol · matplotlib", "P-ec": "Protocol · ECharts",
            "R-mpl-brief": "Raw code + brief · matplotlib", "R-ec-brief": "Raw code + brief · ECharts",
            "R-mpl-plain": "Raw code · matplotlib", "R-ec-plain": "Raw code · ECharts"}
FAMILY = {"P": "var(--s1)", "R-brief": "var(--s2)", "R-plain": "var(--s3)"}
GROUPS = [("A", "Set A · the 24 rehearsed requests"), ("in", "Set B · in scope, not rehearsed (7)"),
          ("messy", "Set B · unusual wording (6)"), ("out", "Set B · no spec key exists (11)")]
esc = html.escape


def fam(arm):
    return "P" if arm.startswith("P-") else ("R-brief" if arm.endswith("brief") else "R-plain")


def read_csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8"))) if p.exists() else []


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0, 0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def sign_test(b, c):
    """Two-sided exact binomial p for b vs c discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def pct(x):
    return f"{100 * x:.0f}%"


# =================================================================== charts (inline SVG)
def bars_chart(title, rows, key="pass_all"):
    """Horizontal bars: one per arm, value = pass rate, with the 95% interval as a whisker."""
    W, H, left, right, top, rowh = 520, 34 + 26 * len(rows), 196, 56, 22, 26
    x = lambda v: left + v * (W - left - right)  # noqa: E731
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}" class="chart">']
    for t in (0, .25, .5, .75, 1):
        parts.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top - 6}" y2="{H - 14}" class="grid"/>'
                     f'<text x="{x(t):.1f}" y="{H - 2}" class="tick" text-anchor="middle">{int(t * 100)}%</text>')
    for i, r in enumerate(rows):
        y = top + i * rowh
        p, lo, hi = r["rate"], r["lo"], r["hi"]
        tex = ' class="hatch"' if r["arm"].endswith("ec") or "-ec-" in r["arm"] else ""
        parts.append(
            f'<g><title>{esc(ARM_NAME[r["arm"]])}: {r["k"]}/{r["n"]} ({pct(p)}), 95% CI {pct(lo)}–{pct(hi)}</title>'
            f'<text x="{left - 8}" y="{y + 13}" class="lab" text-anchor="end">{esc(ARM_NAME[r["arm"]])}</text>'
            f'<rect x="{left}" y="{y + 3}" width="{max(0.0, x(p) - left):.1f}" height="14" rx="3" fill="{FAMILY[fam(r["arm"])]}"/>'
            + (f'<rect x="{left}" y="{y + 3}" width="{max(0.0, x(p) - left):.1f}" height="14" rx="3" fill="url(#tex)"/>' if tex else "")
            + f'<line x1="{x(lo):.1f}" x2="{x(hi):.1f}" y1="{y + 10}" y2="{y + 10}" class="ci"/>'
            f'<text x="{x(p) + 6:.1f}" y="{y + 14}" class="val">{r["k"]}/{r["n"]}</text></g>')
    parts.append('<defs><pattern id="tex" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                 '<line x1="0" y1="0" x2="0" y2="6" stroke="var(--surface)" stroke-width="2" opacity=".55"/></pattern></defs></svg>')
    return f'<figure class="fig"><figcaption class="cap-top">{esc(title)}</figcaption>{"".join(parts)}</figure>'


def arch_svg():
    return """<figure class="fig wide"><svg viewBox="0 0 980 300" role="img" class="diagram"
 aria-label="A request becomes a spec; plotkit validates it, reads the file and computes residue and peaks once in Python, then either matplotlib draws it in-process or the resolved figure goes as JSON to a Node process that builds an ECharts option and renders SVG, PNG or PDF.">
<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g class="box"><rect x="10" y="120" width="120" height="56" rx="8"/><text x="70" y="143" text-anchor="middle">Korean request</text><text x="70" y="161" text-anchor="middle" class="small">+ inspect output</text></g>
<g class="box acc"><rect x="170" y="120" width="120" height="56" rx="8"/><text x="230" y="143" text-anchor="middle">LLM</text><text x="230" y="161" text-anchor="middle" class="small">AGENT.md</text></g>
<g class="box"><rect x="330" y="120" width="120" height="56" rx="8"/><text x="390" y="143" text-anchor="middle">JSON spec</text><text x="390" y="161" text-anchor="middle" class="small">5–15 lines</text></g>
<g class="box"><rect x="490" y="96" width="170" height="104" rx="8"/><text x="575" y="118" text-anchor="middle">plotkit (Python, shared)</text>
<text x="575" y="140" text-anchor="middle" class="small">normalize: aliases, checks</text><text x="575" y="157" text-anchor="middle" class="small">read file, pick columns</text><text x="575" y="174" text-anchor="middle" class="small">residue, peaks, ticks</text><text x="575" y="191" text-anchor="middle" class="small">echarts-patch allowlist</text></g>
<g class="box"><rect x="720" y="30" width="250" height="70" rx="8"/><text x="845" y="56" text-anchor="middle">matplotlib (in-process)</text><text x="845" y="76" text-anchor="middle" class="small">twinx, annotate, _place_labels</text><text x="845" y="92" text-anchor="middle" class="small">"code": exec, no sandbox</text></g>
<g class="box"><rect x="720" y="196" width="250" height="84" rx="8"/><text x="845" y="220" text-anchor="middle">Node: echartkit (new process per plot)</text><text x="845" y="240" text-anchor="middle" class="small">translate.mjs → ECharts option</text><text x="845" y="256" text-anchor="middle" class="small">SSR SVG → sharp PNG / Chromium PDF</text><text x="845" y="272" text-anchor="middle" class="small">placeLabels: JS port of the label layout</text></g>
<path d="M130 148 H166" class="edge" marker-end="url(#ar)"/><path d="M290 148 H326" class="edge" marker-end="url(#ar)"/><path d="M450 148 H486" class="edge" marker-end="url(#ar)"/>
<path d="M660 120 C690 120 690 65 716 65" class="edge" marker-end="url(#ar)"/><text x="672" y="84" class="small">draw</text>
<path d="M660 176 C690 176 690 238 716 238" class="edge" marker-end="url(#ar)"/><text x="664" y="222" class="small">JSON on stdin</text>
<path d="M486 186 C420 250 300 250 250 180" class="edge back" marker-end="url(#ar)"/><text x="330" y="262" class="small">error + hint (≤ 2 retries)</text>
</svg><figcaption>The spec is the only thing the model writes. File reading, column choice and the residue/peak maths run once in Python for both engines; only drawing differs. ECharts runs in a separate Node process that is started for every plot.</figcaption></figure>"""


# =================================================================== data
def load():
    D = {}
    D["t0"] = read_csv(RES / "batch_t0.csv")
    D["t07"] = read_csv(RES / "batch_t07.csv")
    D["pi"] = read_csv(RES / "pi.csv")
    D["cov"] = read_csv(RES / "coverage.csv")
    D["par"] = read_csv(RES / "parity.csv")
    D["lat"] = read_csv(RES / "latency.csv")
    D["val"] = read_csv(RES / "checker_validation.csv")
    D["review"] = read_csv(RES / "review_t0.csv")
    D["safety"] = json.loads((RES / "safety.json").read_text(encoding="utf-8")) if (RES / "safety.json").exists() else {}
    D["parsum"] = json.loads((RES / "parity_summary.json").read_text()) if (RES / "parity_summary.json").exists() else {}
    return D


def rate_rows(rows, arms, pred, key="pass_all"):
    out = []
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm and pred(r)]
        k = sum(r[key] == "1" for r in rs)
        p, lo, hi = wilson(k, len(rs))
        out.append({"arm": arm, "k": k, "n": len(rs), "rate": p, "lo": lo, "hi": hi})
    return out


def arm_table(rows):
    head = ("<tr><th>arm</th><th>pass (all checks)</th><th>pass (asked + data)</th><th>first try</th>"
            "<th>no plot at all</th><th>model calls / run</th><th>median time / run</th><th>median output tokens / run</th></tr>")
    body = []
    for arm in ARMS:
        rs = [r for r in rows if r["arm"] == arm]
        if not rs:
            continue
        n = len(rs)
        f = lambda k: sum(r[k] == "1" for r in rs)  # noqa: E731
        body.append(f"<tr><td><span class='sw' style='background:{FAMILY[fam(arm)]}'></span>{esc(ARM_NAME[arm])}</td>"
                    f"<td class='num'>{f('pass_all')}/{n} ({pct(f('pass_all') / n)})</td>"
                    f"<td class='num'>{pct(f('pass_ask') / n)}</td><td class='num'>{pct(f('first_try') / n)}</td>"
                    f"<td class='num'>{pct(sum(r['ok_run'] == '0' for r in rs) / n)}</td>"
                    f"<td class='num'>{st.mean(int(r['model_calls']) for r in rs):.2f}</td>"
                    f"<td class='num'>{st.median(float(r['seconds']) for r in rs):.0f} s</td>"
                    f"<td class='num'>{st.median(int(r['output_tokens']) for r in rs):,.0f}</td></tr>")
    return f"<div class='tw'><table>{head}{''.join(body)}</table></div>"


def paired(rows, a, b):
    pa = {r["request"]: r["pass_all"] == "1" for r in rows if r["arm"] == a}
    pb = {r["request"]: r["pass_all"] == "1" for r in rows if r["arm"] == b}
    common = sorted(set(pa) & set(pb))
    only_a = [q for q in common if pa[q] and not pb[q]]
    only_b = [q for q in common if pb[q] and not pa[q]]
    return len(common), only_a, only_b, sign_test(len(only_a), len(only_b))


def fail_kinds(rows, arm):
    c = Counter()
    for r in rows:
        if r["arm"] != arm or r["pass_all"] == "1":
            continue
        if r["ok_run"] == "0":
            err = r["errors"].split("||")[-1]
            m = re.search(r"(\w+Error|\w+Exception|timed out|no ```python block|not valid JSON|not one JSON|could not render|saved no figure|plotkit error)", err)
            c["no plot: " + (m.group(1) if m else "other")] += 1
            continue
        for part in r["failed"].split(" | "):
            m = re.match(r"\[(\w+)\] (\w+)", part.strip())
            if m:
                c[f"{m.group(2)} ({m.group(1)})"] += 1
    return c


def chip(status):
    cls = {"key": "ok", "code": "hatch", "echarts": "hatch", "partial": "part", "none": "none"}.get(status.split(":")[0], "none")
    label = {"key": "key", "code": "code", "echarts": "patch", "partial": "partial", "none": "no route"}.get(status.split(":")[0], status)
    return f"<span class='chip {cls}'>{esc(label)}</span>"


def copy_img(src, name, width=900):
    from PIL import Image
    IMG.mkdir(parents=True, exist_ok=True)
    dst = IMG / name
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)))
    im.save(dst.with_suffix(".jpg"), quality=82)
    return f"img/{dst.with_suffix('.jpg').name}"


def first_png(run_dir):
    p = sorted((ROOT / "eval" / run_dir / "out").rglob("*.png")) if run_dir else []
    return p[0] if p else None


# =================================================================== page
CSS = """
:root{--surface:#fcfcfb;--panel:#ffffff;--ink:#16181d;--ink2:#4f5561;--ink3:#7b818c;--line:#e4e4e0;--accent:#2a78d6;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--good:#0ca30c;--warn:#c98500;--crit:#d03b3b;--codebg:#f3f3f0;
--f-body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;color-scheme:light}
/* layout: one reading column (~72ch) for prose; figures and tables may use the full width */
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--surface:#18191b;--panel:#202124;--ink:#eeeeea;--ink2:#c3c2b7;--ink3:#9a9a93;--line:#34353a;--accent:#3987e5;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--codebg:#26272b;color-scheme:dark}}
:root[data-theme="dark"]{--surface:#18191b;--panel:#202124;--ink:#eeeeea;--ink2:#c3c2b7;--ink3:#9a9a93;--line:#34353a;--accent:#3987e5;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--codebg:#26272b;color-scheme:dark}
*{box-sizing:border-box}html{background:var(--surface)}body{margin:0;background:var(--surface);color:var(--ink);font:16px/1.6 var(--f-body)}
main{max-width:1080px;margin:0 auto;padding:40px 20px 80px}
h1{font-size:30px;line-height:1.2;margin:0 0 8px;text-wrap:balance;letter-spacing:-.01em}
h2{font-size:22px;margin:56px 0 12px;text-wrap:balance;padding-top:16px;border-top:1px solid var(--line)}
h3{font-size:17px;margin:28px 0 8px}
p,li{max-width:74ch}p{margin:8px 0}.lede{color:var(--ink2);font-size:17px}
.meta{color:var(--ink3);font-size:14px}
a{color:var(--accent)}code{font:13px var(--f-mono);background:var(--codebg);padding:1px 5px;border-radius:4px}
.answers{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px;margin:24px 0}
.ans{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 18px;border-top:3px solid var(--accent)}
.ans h3{margin:0 0 6px;font-size:15px;color:var(--ink2);font-weight:600}.ans .big{font-size:19px;font-weight:600;margin:0 0 6px;line-height:1.35}
.ans p{font-size:14.5px;color:var(--ink2);margin:4px 0}
.tw{overflow-x:auto;margin:12px 0}table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--ink2);font-weight:600;font-size:13px}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:7px;vertical-align:0}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:18px}
.fig{margin:12px 0;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.fig figcaption{color:var(--ink2);font-size:13.5px;margin-top:6px}.cap-top{font-weight:600;color:var(--ink)!important;font-size:14px!important;margin:0 0 4px!important}
svg.chart,svg.diagram{width:100%;height:auto;display:block}
.chart .grid{stroke:var(--line);stroke-width:1}.chart .tick,.chart .val{font:11px var(--f-body);fill:var(--ink2)}
.chart .lab{font:12px var(--f-body);fill:var(--ink)}.chart .ci{stroke:var(--ink);stroke-width:1.4;opacity:.7}
.diagram{color:var(--ink)}.diagram .box rect{fill:var(--panel);stroke:currentColor;stroke-width:1.2}.diagram .box.acc rect{stroke:var(--accent);stroke-width:2}
.diagram text{font:13px var(--f-body);fill:currentColor}.diagram .small{font-size:11px;fill:var(--ink2)}
.diagram .edge{fill:none;stroke:currentColor;stroke-width:1.3}.diagram .back{stroke-dasharray:4 3;stroke:var(--accent)}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;color:var(--ink2);margin:6px 0}
.chip{display:inline-block;font-size:12px;padding:1px 8px;border-radius:99px;border:1px solid var(--line);white-space:nowrap}
.chip.ok{background:color-mix(in srgb,var(--good) 16%,transparent);border-color:color-mix(in srgb,var(--good) 45%,transparent)}
.chip.hatch{background:color-mix(in srgb,var(--accent) 12%,transparent);border-color:color-mix(in srgb,var(--accent) 40%,transparent)}
.chip.part{background:color-mix(in srgb,var(--warn) 16%,transparent);border-color:color-mix(in srgb,var(--warn) 45%,transparent)}
.chip.none{background:color-mix(in srgb,var(--crit) 12%,transparent);border-color:color-mix(in srgb,var(--crit) 40%,transparent)}
.pair{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.pair figure{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px}
.pair img{width:100%;height:auto;display:block;border-radius:4px;background:#fff}
.pair figcaption{font-size:13px;color:var(--ink2);margin-top:6px}
.note{border-left:3px solid var(--warn);padding:6px 12px;background:color-mix(in srgb,var(--warn) 7%,transparent);border-radius:0 6px 6px 0;margin:12px 0}
pre{background:var(--codebg);padding:12px 14px;border-radius:8px;overflow-x:auto;font:12.5px/1.5 var(--f-mono)}
ol.rec li{margin:6px 0}
@media (max-width:520px){main{padding:24px 16px 60px}.grid2{grid-template-columns:1fr}h1{font-size:25px}}
"""


def build():
    D = load()
    t0 = D["t0"]
    shutil.rmtree(IMG, ignore_errors=True)
    IMG.mkdir(parents=True)
    s = []
    n_runs = len(t0)
    reqs = sorted({r["request"] for r in t0})
    overall = {arm: rate_rows(t0, [arm], lambda r: True)[0] for arm in ARMS}

    def ov(arm, key="pass_all"):
        return rate_rows(t0, [arm], lambda r: True, key)[0]

    # ---------- answers
    pm, pe = ov("P-mpl"), ov("P-ec")
    rb = max((ov(a) for a in ("R-mpl-brief", "R-ec-brief")), key=lambda x: x["rate"])
    rp = max((ov(a) for a in ("R-mpl-plain", "R-ec-plain")), key=lambda x: x["rate"])
    cov = D["cov"]
    nkey = sum(r["matplotlib"] == "key" for r in cov)
    ncode = sum(r["matplotlib"] == "code" for r in cov)
    nec = sum(r["echarts"] in ("echarts",) for r in cov)
    necp = sum(r["echarts"] == "partial" for r in cov)
    necn = sum(r["echarts"] == "none" for r in cov)
    psum = D["parsum"]
    s.append(f"""<header><p class="meta">plotkit evaluation · model: Odin (Qwen3.8 flash next) on centinels · {len(reqs)} requests × {len(ARMS)} arms = {n_runs} runs at temperature 0 · scored on what was drawn</p>
<h1>Does the plotkit spec protocol help an LLM make plots?</h1>
<p class="lede">The same model got the same requests and the same data preview six ways: with the protocol (spec → plotkit) on matplotlib or ECharts, or writing plotting code itself, with and without a short TGA brief. Every plot was scored by one checker on the figure it actually drew.</p></header>""")
    s.append(f"""<section class="answers">
<div class="ans"><h3>1 · Does it help?</h3><p class="big">{pct(pm['rate'])} (matplotlib) and {pct(pe['rate'])} (ECharts) of requests fully right with the protocol, against {pct(rb['rate'])} at best when the model writes the code itself with the brief, and {pct(rp['rate'])} without it.</p>
<p>__HELP_DETAIL__</p></div>
<div class="ans"><h3>2 · Does it cover reasonable variety?</h3><p class="big">{nkey} of {len(cov)} plausible wishes have a key on both engines; the matplotlib <code>code</code> hatch reaches {ncode} more, the ECharts patch {nec} (+{necp} partly).</p>
<p>__COVER_DETAIL__</p></div>
<div class="ans"><h3>3 · How does it connect to the libraries?</h3><p class="big">One spec, one Python core, two thin drawing back ends; {psum.get('specs', 0) - psum.get('specs_with_differences', 0)} of {psum.get('specs', 0)} test specs draw the same on both.</p>
<p>__BACKEND_DETAIL__</p></div></section>""")

    # ---------- setup
    val = D["val"]
    agree = sum(r["spec_ok"] == r["fact_ok"] for r in val)
    s.append(f"""<h2 id="setup">How it was tested</h2>
<div class="tw"><table><tr><th>arm</th><th>what the model gets</th><th>what it writes</th><th>who draws</th></tr>
<tr><td><span class="sw" style="background:var(--s1)"></span>Protocol · matplotlib / ECharts</td><td><code>AGENT.md</code> / <code>AGENT_ECHARTS.md</code> (glossary, rules, examples)</td><td>a JSON spec</td><td>plotkit, either engine</td></tr>
<tr><td><span class="sw" style="background:var(--s2)"></span>Raw code + brief</td><td>a short prompt + a TGA brief: what residue and DTG peak mean, the house defaults, the Korean part names (no spec)</td><td>a Python script</td><td>the script (matplotlib) or the printed ECharts option (ECharts 6.1 SSR)</td></tr>
<tr><td><span class="sw" style="background:var(--s3)"></span>Raw code</td><td>the short prompt only</td><td>a Python script</td><td>as above</td></tr></table></div>
<p>All six arms got the same data preview (sheets, columns, ranges), the same 16k-token budget and up to two retries with the error they caused: plotkit's <code>error</code> + <code>hint</code>, or the script's traceback. Scripts ran in a sandbox (bubblewrap: no network, read-only system).</p>
<p><b>Requests.</b> Set A is the 24 Korean test requests the protocol was written for. Set B is 24 new ones on new made-up data (polymers, calcium oxalate with heat flow, CNT batches, an isothermal hold, XRD, rheology): 7 that a key covers but no example shows, 6 in unusual wording, and 11 that no key covers.</p>
<p><b>Scoring.</b> A figure-facts extractor reads what was actually drawn (matplotlib figure objects; the final ECharts option plus the axis extents and texts ECharts computed) and one checker tests each request's facts: the right data, what was asked, and the lab's conventions (residue and peak labels) where the request leaves them implicit. Before the runs, the checker agreed with the old spec-based scorer on {agree}/{len(val)} known-good and deliberately-wrong runs, and every Set B expectation was met by a hand-written answer wherever a route exists.</p>""")

    # ---------- Q1
    s.append('<h2 id="help">1 · Does the protocol help?</h2>')
    s.append('<div class="legend"><span><span class="sw" style="background:var(--s1)"></span>protocol</span><span><span class="sw" style="background:var(--s2)"></span>raw code + brief</span><span><span class="sw" style="background:var(--s3)"></span>raw code</span><span>hatched = ECharts · whisker = 95% interval</span></div>')
    charts = []
    for g, label in GROUPS:
        rows = rate_rows(t0, ARMS, lambda r, g=g: r["group"] == g)
        if any(r["n"] for r in rows):
            charts.append(bars_chart(label, rows))
    s.append(f'<div class="grid2">{"".join(charts)}</div>')
    s.append("<h3>All 48 requests</h3>" + arm_table(t0))
    pairs = [("P-mpl", "R-mpl-brief"), ("P-ec", "R-ec-brief"), ("R-mpl-brief", "R-mpl-plain"), ("P-mpl", "P-ec")]
    prow = []
    for a, b in pairs:
        n, oa, ob, p = paired(t0, a, b)
        if n:
            prow.append(f"<tr><td>{esc(ARM_NAME[a])} vs {esc(ARM_NAME[b])}</td><td class='num'>{n}</td><td class='num'>{len(oa)}</td>"
                        f"<td class='num'>{len(ob)}</td><td class='num'>{p:.3g}</td><td>{esc(', '.join(oa[:8]))}{'…' if len(oa) > 8 else ''}</td><td>{esc(', '.join(ob[:8]))}</td></tr>")
    s.append("<h3>Same request, two arms</h3><div class='tw'><table><tr><th>pair</th><th class='num'>requests</th><th class='num'>only first passes</th>"
             "<th class='num'>only second passes</th><th class='num'>sign test p</th><th>only first</th><th>only second</th></tr>" + "".join(prow) + "</table></div>")
    fk = []
    for arm in ARMS:
        c = fail_kinds(t0, arm)
        if c:
            fk.append(f"<tr><td>{esc(ARM_NAME[arm])}</td><td>{esc('; '.join(f'{k} ×{v}' for k, v in c.most_common(6)))}</td></tr>")
    s.append("<h3>Why runs failed</h3><div class='tw'><table><tr><th>arm</th><th>most common failed checks (category)</th></tr>" + "".join(fk) + "</table></div>")
    s.append("__EXAMPLES__")
    s.append("__T07__")
    s.append("__PI__")
    s.append("__REVIEW__")

    # ---------- Q2 coverage
    s.append('<h2 id="variety">2 · Does it cover reasonable variety?</h2>')
    s.append(f"<p>{len(cov)} plot changes a TGA user might plausibly ask for, drawn from the guide's 15 parts, TGA practice, journal and slide habits, and commonly used library options. Each claimed route was drawn once on its engine; each “no route” on ECharts was tried and refused by plotkit.</p>")
    groups = list(dict.fromkeys(r["group"] for r in cov))
    gr = []
    for g in groups:
        rs = [r for r in cov if r["group"] == g]
        gr.append(f"<tr><td>{esc(g)}</td><td class='num'>{len(rs)}</td><td class='num'>{sum(r['matplotlib'] == 'key' for r in rs)}</td>"
                  f"<td class='num'>{sum(r['matplotlib'] == 'code' for r in rs)}</td><td class='num'>{sum(r['echarts'] == 'echarts' for r in rs)}</td>"
                  f"<td class='num'>{sum(r['echarts'] == 'partial' for r in rs)}</td><td class='num'>{sum(r['echarts'] == 'none' for r in rs)}</td></tr>")
    s.append("<div class='tw'><table><tr><th>group</th><th class='num'>wishes</th><th class='num'>key (both)</th><th class='num'>+ matplotlib code</th>"
             "<th class='num'>+ ECharts patch</th><th class='num'>ECharts partial</th><th class='num'>ECharts no route</th></tr>" + "".join(gr) + "</table></div>")
    rows = []
    for r in cov:
        rows.append(f"<tr><td>{esc(r['id'])}</td><td>{esc(r['wish'])}</td><td lang='ko'>{esc(r['example'])}</td><td>{chip(r['matplotlib'])}</td>"
                    f"<td>{chip(r['echarts'])}</td><td class='small'>{esc(r['note'])}</td></tr>")
    s.append("<details><summary>All wishes and routes</summary><div class='tw'><table><tr><th>id</th><th>wish</th><th>example</th><th>matplotlib</th><th>ECharts</th><th>note</th></tr>"
             + "".join(rows) + "</table></div></details>")
    s.append("__OUTSCOPE__")

    # ---------- Q3 backends
    s.append('<h2 id="backends">3 · How does it connect to the back ends?</h2>')
    s.append(arch_svg())
    s.append("__MAPPING__")
    par = D["par"]
    kinds = Counter(r["kind"] for r in par)
    prs = []
    seen = set()
    for r in par:
        key = (r["kind"], r["field"].split(".")[-1])
        if key in seen:
            continue
        seen.add(key)
        prs.append(f"<tr><td>{esc(r['kind'])}</td><td>{esc(r['spec'])}</td><td><code>{esc(r['field'])}</code></td><td>{esc(r['matplotlib'][:70])}</td><td>{esc(r['echarts'][:70])}</td></tr>")
    s.append(f"<h3>Parity: the same spec on both engines</h3><p>{psum.get('specs', 0)} specs (gallery, the 24 reference answers, Set B answers and 8 probes) were drawn on both engines and their figure facts compared: axis ranges and ticks, labels, line styles, annotations, texts, legend, sizes. {psum.get('specs_with_differences', 0)} differ ({', '.join(f'{k} ×{v}' for k, v in kinds.most_common())}).</p>"
             "<div class='tw'><table><tr><th>kind</th><th>first spec</th><th>field</th><th>matplotlib</th><th>ECharts</th></tr>" + "".join(prs) + "</table></div>")
    lat = D["lat"]
    if lat:
        med = lambda e, pdf=False: st.median(float(r["seconds"]) / max(1, int(r["figures"])) for r in lat if r["engine"] == e and (("pdf" in r["formats"]) == pdf))  # noqa: E731
        pdf = {e: [float(r["seconds"]) for r in lat if r["engine"] == e and "pdf" in r["formats"]] for e in ("matplotlib", "echarts")}
        s.append(f"<h3>Speed</h3><p>Median draw time per figure (PNG): matplotlib {med('matplotlib'):.2f} s, ECharts {med('echarts'):.2f} s, of which about 0.34 s is starting Node and loading ECharts, which happens for every plot. A PDF took {pdf['matplotlib'][0]:.2f} s vs {pdf['echarts'][0]:.2f} s (Chromium). Both are small next to the model: a spec reply took a median of __SPEC_S__ s in this run.</p>" if pdf["matplotlib"] and pdf["echarts"] else "")
    sf = D["safety"]
    if sf:
        srows = "".join(f"<tr><td>{esc(k.replace('_', ' '))}</td><td>{esc(v['engine'])}</td><td>{esc(v['result'])}</td><td>{esc(v.get('error', ''))}</td></tr>" for k, v in sf.items())
        s.append("<h3>Escape hatches and safety</h3><p>The two hatches are not equivalent. <code>code</code> is Python run with <code>exec</code> in plotkit's own process; the ECharts patch is JSON checked against an allowlist. Harmless probes:</p>"
                 f"<div class='tw'><table><tr><th>probe</th><th>engine</th><th>result</th><th>plotkit's answer</th></tr>{srows}</table></div>")
    s.append("__RECS__")
    s.append("__REPRO__")
    page = (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>plotkit protocol evaluation</title><link rel="preconnect" href="https://fonts.googleapis.com">'
            f'<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">'
            f'<style>{CSS}</style></head><body><main>{"".join(s)}</main></body></html>')
    return page, D


if __name__ == "__main__":
    page, D = build()
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print("wrote report/index.html", len(page), "bytes")
