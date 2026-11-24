"""The constrained-decoding page: free vs schema-constrained replies for the plot spec, on two servers, side by side.

Reads only result files: eval/results/cnt_cd_go.csv (OpenCode Go, 34 dev items), cnt_cd_sx.csv (Strix Halo, 15-item
subset), their *_cd_compare.json, and the run folders for replies and plots.

    python experiments/report/build_cd.py      -> report/cd/index.html + report/cd/img/
"""
import csv
import json
import math
import random
import shutil
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "eval" / "results"
sys.path.insert(0, str(ROOT / "report"))
from build_report import CSS, esc  # noqa: E402

OUT = ROOT / "report" / "cd"
IMG = OUT / "img"
SUB = "D001,D002,D004,D005,D006,D008,D010,D015,D017,D019,D022,D026,D028,DS01,DS04".split(",")
ARM = {"P-mpl": "free · matplotlib", "P-ec": "free · ECharts",
       "P-mpl+cdflat": "flat schema · matplotlib", "P-ec+cdflat": "flat schema · ECharts",
       "P-mpl+cdabc": "full schema + A–Z note · matplotlib", "P-ec+cdabc": "full schema + A–Z note · ECharts",
       "P-mpl+cd": "full schema as designed · matplotlib"}
COLOR = {"": "var(--s1)", "flat": "var(--s2)", "cdabc": "var(--s3)", "cd": "var(--s4)"}
EXTRA = """
:root{--s4:#eda100}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--s4:#c98500}}
:root[data-theme="dark"]{--s4:#c98500}
.side{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px;margin:10px 0 22px}
.side figure{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px}
.side img{width:100%;height:auto;display:block;border-radius:4px;background:#fff}
.side figcaption{font-size:12.5px;color:var(--ink2);margin-top:6px}
.side .tag{display:inline-block;font-size:11.5px;font-weight:600;padding:1px 7px;border-radius:99px;margin-right:6px;color:#fff}
.verdict{font-weight:600}.pass{color:var(--good)}.fail{color:var(--crit)}
pre.json{font-size:11.5px;line-height:1.45;white-space:pre-wrap;word-break:break-word;margin:0;max-height:330px;overflow:auto}
pre.json .lost{background:color-mix(in srgb,var(--crit) 18%,transparent);border-radius:3px}
.cols2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}
td.d-neg{color:var(--crit)}td.d-pos{color:var(--good)}
.small{font-size:13px;color:var(--ink2)}
.single .fig{max-width:620px}
"""


def rows(name):
    p = RES / name
    csv.field_size_limit(10 ** 8)
    return list(csv.DictReader(open(p, encoding="utf-8"))) if p.exists() else []


def suffix(arm):
    return arm.partition("+")[2].replace("cdflat", "flat")


def stats(rs):
    n = len(rs)
    k = sum(r["pass"] == "1" for r in rs)
    if not n:
        return None
    # bootstrap over items (turns of one item are not independent), as cd_compare does
    by = defaultdict(list)
    for r in rs:
        by[r["item"]].append(r["pass"] == "1")
    items = list(by)
    rnd = random.Random(7)
    boots = []
    for _ in range(2000):
        pick = [rnd.choice(items) for _ in items]
        tot = sum(len(by[i]) for i in pick)
        boots.append(sum(sum(by[i]) for i in pick) / tot)
    boots.sort()
    return {"n": n, "k": k, "pass": k / n, "lo": boots[50], "hi": boots[1949],
            "first": sum(r["pass"] == "1" and r["model_calls"] == "1" for r in rs) / n,
            "retry": sum(int(r["model_calls"] or 1) > 1 for r in rs) / n,
            "noplot": sum(r["ok_run"] == "0" for r in rs) / n,
            "s": st.median(float(r["llm_s"]) for r in rs if r["llm_s"]),
            "tok": st.median(float(r["output_tokens"]) for r in rs if r["output_tokens"] not in ("", "None"))}


def pct(x):
    return f"{100 * x:.0f}%"


def paired(rs, a, b):
    key = lambda r: (r["item"], r["turn"], r["repeat"])  # noqa: E731
    A = {key(r): r["pass"] == "1" for r in rs if r["arm"] == a}
    B = {key(r): r["pass"] == "1" for r in rs if r["arm"] == b}
    common = sorted(set(A) & set(B))
    win = sum(B[k] and not A[k] for k in common)
    loss = sum(A[k] and not B[k] for k in common)
    n = win + loss
    p = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(win, loss) + 1)) / 2 ** n)
    d = (sum(B[k] for k in common) - sum(A[k] for k in common)) / max(1, len(common))
    return {"n": len(common), "win": win, "loss": loss, "p": p, "delta": d}


# =================================================================== charts
def bar_chart(title, entries, note=""):
    """entries: [(label, suffix, stats)] -> horizontal bars with the 95% bootstrap interval."""
    W, left, right, top, rowh = 560, 250, 64, 22, 26
    H = top + rowh * len(entries) + 26
    x = lambda v: left + v * (W - left - right)  # noqa: E731
    out = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="{esc(title)}">']
    for t in (0, .25, .5, .75, 1):
        out.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top - 6}" y2="{H - 16}" class="grid"/>'
                   f'<text x="{x(t):.1f}" y="{H - 3}" class="tick" text-anchor="middle">{int(t * 100)}%</text>')
    for i, (label, suf, s) in enumerate(entries):
        y = top + i * rowh
        out.append(f'<g><title>{esc(label)}: {s["k"]}/{s["n"]} turns ({pct(s["pass"])}), 95% CI {pct(s["lo"])}–{pct(s["hi"])}</title>'
                   f'<text x="{left - 8}" y="{y + 13}" class="lab" text-anchor="end">{esc(label)}</text>'
                   f'<rect x="{left}" y="{y + 3}" width="{max(0.0, x(s["pass"]) - left):.1f}" height="14" rx="3" fill="{COLOR[suf]}"/>'
                   f'<line x1="{x(s["lo"]):.1f}" x2="{x(s["hi"]):.1f}" y1="{y + 10}" y2="{y + 10}" class="ci"/>'
                   f'<text x="{x(s["pass"]) + 6:.1f}" y="{y + 14}" class="val">{pct(s["pass"])}</text></g>')
    out.append("</svg>")
    return f'<figure class="fig"><figcaption class="cap-top">{esc(title)}</figcaption>{"".join(out)}' \
           + (f'<figcaption>{note}</figcaption>' if note else "") + "</figure>"


def order_svg():
    """The two servers' key-order rules on one reply."""
    return """<figure class="fig wide"><svg viewBox="0 0 980 250" class="diagram" role="img"
 aria-label="The free reply writes file, sheets, chart, x, y, by. OpenCode Go only accepts keys in alphabetical order, so after file it can no longer write by or chart. Strix Halo accepts keys in the schema's order, which the adapter sets to the model's own order.">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<text x="10" y="22" class="small">what the model writes, free (D001):</text>
<g class="box"><rect x="10" y="32" width="80" height="30" rx="6"/><text x="50" y="52" text-anchor="middle">file</text></g>
<g class="box"><rect x="100" y="32" width="80" height="30" rx="6"/><text x="140" y="52" text-anchor="middle">sheets</text></g>
<g class="box"><rect x="190" y="32" width="80" height="30" rx="6"/><text x="230" y="52" text-anchor="middle">chart</text></g>
<g class="box"><rect x="280" y="32" width="80" height="30" rx="6"/><text x="320" y="52" text-anchor="middle">x</text></g>
<g class="box"><rect x="370" y="32" width="80" height="30" rx="6"/><text x="410" y="52" text-anchor="middle">y</text></g>
<g class="box"><rect x="460" y="32" width="80" height="30" rx="6"/><text x="500" y="52" text-anchor="middle">by</text></g>
<g class="box"><rect x="550" y="32" width="80" height="30" rx="6"/><text x="590" y="52" text-anchor="middle">asks</text></g>
<text x="10" y="102" class="small">OpenCode Go accepts keys only A→Z (asks, by, chart, file, sheets, x, y):</text>
<g class="box"><rect x="10" y="112" width="80" height="30" rx="6"/><text x="50" y="132" text-anchor="middle">file</text></g>
<g class="box"><rect x="100" y="112" width="80" height="30" rx="6"/><text x="140" y="132" text-anchor="middle">sheets</text></g>
<g class="box lostbox"><rect x="190" y="112" width="80" height="30" rx="6"/><text x="230" y="132" text-anchor="middle">chart ✕</text></g>
<g class="box"><rect x="280" y="112" width="80" height="30" rx="6"/><text x="320" y="132" text-anchor="middle">x</text></g>
<g class="box"><rect x="370" y="112" width="80" height="30" rx="6"/><text x="410" y="132" text-anchor="middle">y</text></g>
<g class="box lostbox"><rect x="460" y="112" width="80" height="30" rx="6"/><text x="500" y="132" text-anchor="middle">by ✕</text></g>
<g class="box lostbox"><rect x="550" y="112" width="80" height="30" rx="6"/><text x="590" y="132" text-anchor="middle">asks ✕</text></g>
<text x="650" y="125" class="small">chart, by, asks sort before file:</text><text x="650" y="141" class="small">once file is written they can't be</text>
<text x="10" y="182" class="small">Strix Halo (gufo) accepts keys in the schema's order; the adapter puts them in the model's own order:</text>
<g class="box ok"><rect x="10" y="192" width="80" height="30" rx="6"/><text x="50" y="212" text-anchor="middle">file</text></g>
<g class="box ok"><rect x="100" y="192" width="80" height="30" rx="6"/><text x="140" y="212" text-anchor="middle">sheets</text></g>
<g class="box ok"><rect x="190" y="192" width="80" height="30" rx="6"/><text x="230" y="212" text-anchor="middle">chart</text></g>
<g class="box ok"><rect x="280" y="192" width="80" height="30" rx="6"/><text x="320" y="212" text-anchor="middle">x</text></g>
<g class="box ok"><rect x="370" y="192" width="80" height="30" rx="6"/><text x="410" y="212" text-anchor="middle">y</text></g>
<g class="box ok"><rect x="460" y="192" width="80" height="30" rx="6"/><text x="500" y="212" text-anchor="middle">by</text></g>
<g class="box ok"><rect x="550" y="192" width="80" height="30" rx="6"/><text x="590" y="212" text-anchor="middle">asks</text></g>
<text x="650" y="205" class="small">86% of free dev replies already</text><text x="650" y="221" class="small">follow that order at every level</text>
</svg><figcaption>Both servers force a key order, each a different one. On OpenCode Go a reply loses every optional key that sorts before one it has already written, and the loss is silent: the JSON is still valid. The flat profile survives because its four top-level keys are all required (required keys are reordered, not dropped).</figcaption></figure>"""


# =================================================================== examples
def run_dir(run, arm, item, rep):
    return RES / "runs" / run / arm / f"{item}_r{rep}"


def reply_of(run, arm, item, rep, turn=1):
    p = run_dir(run, arm, item, rep) / "record.json"
    if not p.exists():
        return ""
    t = json.loads(p.read_text(encoding="utf-8"))["turns"][turn - 1]
    calls = [c for c in t.get("calls", []) if c.get("reply")]
    return calls[-1]["reply"] if calls else ""


def img_of(run, arm, item, rep, turn, name):
    d = run_dir(run, arm, item, rep) / "out" / f"t{turn}"
    pngs = sorted(d.glob("*.png")) if d.exists() else []
    if not pngs:
        return None
    from PIL import Image
    im = Image.open(pngs[0]).convert("RGB")
    w = 760
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)))
    dst = IMG / f"{name}.jpg"
    im.save(dst, quality=80)
    return f"img/{dst.name}"


def verdict(rs, run_arm_item_rep_turn):
    arm, item, rep, turn = run_arm_item_rep_turn
    r = next((x for x in rs if x["arm"] == arm and x["item"] == item and x["repeat"] == str(rep)
              and x["turn"] == str(turn)), None)
    if not r:
        return "", ""
    ok = r["pass"] == "1"
    why = "" if ok else (r["failed"] or r.get("error") or "")[:150]
    return ("<span class='verdict pass'>pass</span>" if ok else "<span class='verdict fail'>fail</span>"), why


def side(title, rs, run, cells, intro=""):
    figs = []
    for arm, rep, turn in cells:
        item = title.split()[0]
        src = img_of(run, arm, item, rep, turn, f"{run}_{item}_{arm.replace('+', '_')}_r{rep}_t{turn}")
        v, why = verdict(rs, (arm, item, rep, turn))
        suf = suffix(arm)
        tag = f"<span class='tag' style='background:{COLOR[suf]}'>{esc(ARM[arm].split(' · ')[0])}</span>"
        figs.append(f"<figure>{f'<img src={src!r} alt=' + repr(esc(ARM[arm])) + '>' if src else '<p class=small>no plot was drawn</p>'}"
                    f"<figcaption>{tag}{v} {esc(ARM[arm].split(' · ')[1])}, repeat {rep}"
                    f"{'<br>' + esc(why) if why else ''}</figcaption></figure>")
    return f"<h3>{esc(title)}</h3>{intro}<div class='side'>{''.join(figs)}</div>"


def json_cell(label, text, lost=()):
    t = esc(text.strip())
    for k in lost:
        t = t.replace(esc(f'"{k}"'), f"<span class='lost'>{esc(chr(34) + k + chr(34))}</span>")
    return f"<div class='fig'><figcaption class='cap-top'>{label}</figcaption><pre class='json'>{t}</pre></div>"


# =================================================================== page
def build():
    go, sx = rows("cnt_cd_go.csv"), rows("cnt_cd_sx.csv")
    shutil.rmtree(OUT, ignore_errors=True)
    IMG.mkdir(parents=True)
    goS = [r for r in go if r["item"] in SUB]
    S = lambda rs, arm: stats([r for r in rs if r["arm"] == arm])  # noqa: E731
    s = []
    n_go, n_sx = len(go), len(sx)
    g = {a: S(go, a) for a in ARM}
    gs = {a: S(goS, a) for a in ARM}
    x = {a: S(sx, a) for a in ARM}
    d_go_flat = paired(go, "P-mpl", "P-mpl+cdflat")
    d_go_abc = paired(go, "P-mpl", "P-mpl+cdabc")
    d_go_cd = paired(go, "P-mpl", "P-mpl+cd")
    d_sx_flat = paired(sx, "P-mpl", "P-mpl+cdflat")
    d_sx_ec = paired(sx, "P-ec", "P-ec+cdflat")
    d_gos_flat = paired(goS, "P-mpl", "P-mpl+cdflat")

    s.append(f"""<header><p class="meta">Qwen3.8 Flash, thinking off, temperature 0.2 · CNT dev split (no sealed items) · {n_go + n_sx} scored turns · 2026-11-23</p>
<h1>Constrained decoding for the plot spec, on two servers</h1>
<p class="lede">Does forcing the model's reply through a JSON Schema make better plots than today's free reply, which plotkit checks and answers with an error and a hint? The same model was run through two servers whose grammar engines behave differently, and every turn was scored on the plot it actually drew.</p></header>
<section class="answers">
<div class="ans"><h3>OpenCode Go (opencode's hosted Qwen3.8 Flash)</h3><p class="big">Every constrained arm was worse: {pct(g['P-mpl+cdflat']['pass'])} flat, {pct(g['P-mpl+cdabc']['pass'])} full + A–Z note, {pct(g['P-mpl+cd']['pass'])} full as designed, against {pct(g['P-mpl']['pass'])} free.</p>
<p>The gateway only accepts JSON keys in alphabetical order. An optional key that sorts before one already written is dropped without an error, so charts lose their kind, grouping and aggregation.</p></div>
<div class="ans"><h3>Strix Halo (home server, gufo)</h3><p class="big">The flat schema is within noise of free: {pct(x['P-mpl+cdflat']['pass'])} vs {pct(x['P-mpl']['pass'])} (matplotlib), {pct(x['P-ec+cdflat']['pass'])} vs {pct(x['P-ec']['pass'])} (ECharts), p ≥ {min(d_sx_flat['p'], d_sx_ec['p']):.2f}.</p>
<p>It removed every retry and "no plot", but turns took {x['P-mpl+cdflat']['s'] / x['P-mpl']['s'] - 1:.0%} longer. The full schema could not be used: once adapted to gufo's rules it hung the server.</p></div>
<div class="ans"><h3>What to do</h3><p class="big">Keep free decoding with plotkit's checks. Don't ship constrained decoding on OpenCode Go.</p>
<p>On Strix Halo the flat schema is safe but buys nothing measurable. Revisit if a server keeps schema order and handles the full schema, or if "no plot" turns become a problem with a weaker model.</p></div></section>""")

    # ---------- setup
    s.append(f"""<h2 id="setup">How it was tested</h2>
<div class="tw"><table><tr><th>arm</th><th>reply</th><th>decoding</th></tr>
<tr><td><span class="sw" style="background:var(--s1)"></span>free</td><td>JSON spec in a ```json fence, as today</td><td>free; plotkit's <code>error</code> + <code>hint</code> on failure, up to 2 retries</td></tr>
<tr><td><span class="sw" style="background:var(--s2)"></span>flat schema (<code>+cdflat</code>)</td><td>a flat settings list, converted back to the spec</td><td>JSON Schema with 4 required top-level keys</td></tr>
<tr><td><span class="sw" style="background:var(--s3)"></span>full schema + A–Z note (<code>+cdabc</code>)</td><td>the spec itself, plus one prompt line: write keys in alphabetical order</td><td>the full spec schema (OpenCode Go only; added after the first finding)</td></tr>
<tr><td><span class="sw" style="background:var(--s4)"></span>full schema as designed (<code>+cd</code>)</td><td>the spec itself</td><td>the full spec schema (OpenCode Go only)</td></tr></table></div>
<p>Same prompts (<code>prompts/v2</code>), same data preview, same retry budget, same checker for every arm. The schemas are built per request: file, sheet and column names are enums, so a constrained reply cannot name something that is not in the data.</p>
<div class="tw"><table><tr><th></th><th>OpenCode Go</th><th>Strix Halo</th></tr>
<tr><td>model</td><td><code>qwen3.8-flash</code> via the Anthropic-compatible endpoint (structured outputs)</td><td><code>qwen3.8-flash-next</code> UD-Q4_K_XL GGUF on gufo (<code>response_format</code>)</td></tr>
<tr><td>requests</td><td>all 34 dev items, 44 turns × 3 repeats</td><td>15 items covering every chart kind and every OpenCode Go failure, 20 turns × 3 repeats</td></tr>
<tr><td>arms</td><td>free (mpl, ECharts), flat, full + A–Z note (mpl, ECharts), full as designed</td><td>free and flat, matplotlib and ECharts</td></tr>
<tr><td>scored turns</td><td>{n_go}</td><td>{n_sx}</td></tr></table></div>""")

    # ---------- side by side numbers
    s.append('<h2 id="results">Results side by side</h2>')
    s.append("<div class='legend'><span><span class='sw' style='background:var(--s1)'></span>free</span><span><span class='sw' style='background:var(--s2)'></span>flat schema</span><span><span class='sw' style='background:var(--s3)'></span>full + A–Z note</span><span><span class='sw' style='background:var(--s4)'></span>full as designed</span><span>whisker = 95% interval (bootstrap over items)</span></div>")
    order = ["P-mpl", "P-mpl+cdflat", "P-mpl+cdabc", "P-mpl+cd", "P-ec", "P-ec+cdflat", "P-ec+cdabc"]
    ent = lambda d: [(ARM[a], suffix(a), d[a]) for a in order if d.get(a)]  # noqa: E731
    s.append("<div class='grid2'>" + bar_chart("Strix Halo · 15 items", ent(x))
             + bar_chart("OpenCode Go · the same 15 items", ent(gs))
             + "</div><div class='single'>" + bar_chart("OpenCode Go · all 34 dev items", ent(g)) + "</div>")

    def table(cols):
        head = "<tr><th>arm</th>" + "".join(f"<th class='num'>{esc(c)}</th>" for c, _ in cols) + "</tr>"
        body = []
        for a in order:
            cells = []
            for _, d in cols:
                v = d.get(a)
                cells.append("<td class='num'>–</td>" if not v else
                             f"<td class='num'>{pct(v['pass'])} <span class='small'>[{pct(v['lo'])}–{pct(v['hi'])}]</span></td>")
            if any(d.get(a) for _, d in cols):
                body.append(f"<tr><td><span class='sw' style='background:{COLOR[suffix(a)]}'></span>{esc(ARM[a])}</td>{''.join(cells)}</tr>")
        return f"<div class='tw'><table>{head}{''.join(body)}</table></div>"
    s.append("<h3>Pass rate per arm</h3>" + table([("Strix Halo, 15 items", x), ("OpenCode Go, same 15", gs), ("OpenCode Go, all 34", g)]))

    def cost_table(name, d):
        head = ("<tr><th>arm</th><th class='num'>turns</th><th class='num'>first try</th><th class='num'>retried</th>"
                "<th class='num'>no plot</th><th class='num'>median model time</th><th class='num'>median output tokens</th></tr>")
        b = "".join(f"<tr><td>{esc(ARM[a])}</td><td class='num'>{v['n']}</td><td class='num'>{pct(v['first'])}</td>"
                    f"<td class='num'>{pct(v['retry'])}</td><td class='num'>{pct(v['noplot'])}</td>"
                    f"<td class='num'>{v['s']:.1f} s</td><td class='num'>{v['tok']:.0f}</td></tr>"
                    for a in order if (v := d.get(a)))
        return f"<div><h3>{esc(name)}</h3><div class='tw'><table>{head}{b}</table></div></div>"
    s.append(cost_table("Strix Halo: repairs and cost (15 items)", x) + cost_table("OpenCode Go: repairs and cost (34 items)", g))

    def ptab(items):
        head = ("<tr><th>pair (same item, turn, repeat)</th><th class='num'>pairs</th><th class='num'>Δ pass</th>"
                "<th class='num'>constrained only</th><th class='num'>free only</th><th class='num'>exact p (McNemar)</th></tr>")
        b = "".join(f"<tr><td>{esc(lab)}</td><td class='num'>{p['n']}</td>"
                    f"<td class='num {'d-neg' if p['delta'] < 0 else 'd-pos' if p['delta'] > 0 else ''}'>{100 * p['delta']:+.1f} pts</td>"
                    f"<td class='num'>{p['win']}</td><td class='num'>{p['loss']}</td><td class='num'>{p['p']:.3g}</td></tr>"
                    for lab, p in items)
        return f"<div class='tw'><table>{head}{b}</table></div>"
    s.append("<h3>Paired comparisons</h3>" + ptab([
        ("Strix Halo · flat vs free · matplotlib", d_sx_flat), ("Strix Halo · flat vs free · ECharts", d_sx_ec),
        ("OpenCode Go (same 15) · flat vs free · matplotlib", d_gos_flat),
        ("OpenCode Go (34) · flat vs free · matplotlib", d_go_flat),
        ("OpenCode Go (34) · full + A–Z vs free · matplotlib", d_go_abc),
        ("OpenCode Go (34) · full + A–Z vs free · ECharts", paired(go, "P-ec", "P-ec+cdabc")),
        ("OpenCode Go (34) · full as designed vs free · matplotlib", d_go_cd)]))
    s.append("<p class='small'>Noise between repeats of the same free arm: OpenCode Go P-mpl 44, 42, 43 of 44 turns; Strix Halo P-mpl and P-ec within 1–2 turns. Pairs are not independent across turns of one item, so read p as a guide.</p>")

    # ---------- per kind
    kinds = sorted({r["kind"] for r in go + sx if r.get("kind")})
    def kind_delta(rs, a, b, k):
        sub = [r for r in rs if r.get("kind") == k]
        p = paired(sub, a, b)
        return "–" if not p["n"] else f"{100 * p['delta']:+.0f} <span class='small'>({p['n']})</span>"
    kr = "".join(f"<tr><td>{esc(k)}</td><td class='num'>{kind_delta(sx, 'P-mpl', 'P-mpl+cdflat', k)}</td>"
                 f"<td class='num'>{kind_delta(sx, 'P-ec', 'P-ec+cdflat', k)}</td>"
                 f"<td class='num'>{kind_delta(go, 'P-mpl', 'P-mpl+cdflat', k)}</td>"
                 f"<td class='num'>{kind_delta(go, 'P-mpl', 'P-mpl+cdabc', k)}</td>"
                 f"<td class='num'>{kind_delta(go, 'P-mpl', 'P-mpl+cd', k)}</td></tr>" for k in kinds)
    s.append("<h3>By chart kind (Δ pass in points, pairs in brackets)</h3><div class='tw'><table><tr><th>kind</th>"
             "<th class='num'>Strix · flat · mpl</th><th class='num'>Strix · flat · ECharts</th><th class='num'>Go · flat · mpl</th>"
             "<th class='num'>Go · full + A–Z · mpl</th><th class='num'>Go · full as designed · mpl</th></tr>" + kr + "</table></div>")

    # ---------- why: probes + order
    s.append('<h2 id="why">Why the servers differ</h2>')
    s.append(order_svg())
    s.append("""<div class='tw'><table><tr><th>probe (thinking off, temperature 0)</th><th>OpenCode Go</th><th>Strix Halo (gufo)</th></tr>
<tr><td>one required constant; does the server enforce the schema?</td><td>yes</td><td>yes, with <code>response_format</code> (gufo ignores llama.cpp's <code>json_schema</code> field)</td></tr>
<tr><td>keys a, b (both required); asked for b then a</td><td><code>{"a": …, "b": …}</code></td><td>schema order</td></tr>
<tr><td>optional keys zeta, mid, alpha (in that schema order); asked for zeta, mid, alpha</td><td><code>{"zeta": 1}</code>: mid and alpha sort before zeta and are dropped</td><td><code>{"zeta": 1, "mid": 2, "alpha": 3}</code></td></tr>
<tr><td>same, asked for alpha, zeta, mid</td><td>alphabetical</td><td><code>{"alpha": 3}</code>: alpha is last in the schema, the rest are dropped</td></tr>
<tr><td>root <code>anyOf</code> of a curve and a chart object</td><td>accepted; the branch is fixed by the first keys written</td><td>refused (400): the root must be one object</td></tr>
<tr><td>enum without <code>type</code>, open map objects, optional properties with <code>strict: true</code></td><td>accepted</td><td>refused (400): every node typed, every object closed; strict mode needs every key required</td></tr>
<tr><td>full spec schema (49–84 kB)</td><td>accepted, compiles in 2–4 s</td><td>after adapting (one root object, typed enums, closed maps, keys in the model's order): the request never finished and the server had to be restarted</td></tr></table></div>""")

    # replies side by side
    free = reply_of("cnt_cd_go", "P-mpl", "D001", 1)
    cd = reply_of("cnt_cd_go", "P-mpl+cd", "D001", 1)
    abc = reply_of("cnt_cd_go", "P-mpl+cdabc", "D001", 1)
    flat = reply_of("cnt_cd_go", "P-mpl+cdflat", "D001", 1)
    s.append("<h3>The same request, four replies (D001 on OpenCode Go, repeat 1)</h3>"
             "<p class='small' lang='ko'>“run_log.xlsx 런로그 시트로 주차별 평균 CNT수율 추이 그려줘. 반응기(R1~R4)별 line 4개, x축 주차 1~26.”</p>"
             "<div class='cols2'>" + json_cell("free: passes", free)
             + json_cell("full as designed: chart, agg and by are gone; it became a raw curve", cd, lost=("y1", "y2"))
             + json_cell("full + A–Z note: the chart is back, but by (sorts before chart) came too late and was written as z", abc, lost=("z",))
             + json_cell("flat: passes", flat) + "</div>")

    # ---------- plots side by side
    s.append('<h2 id="plots">Plots side by side</h2><p>Each row is one turn: the same request and the same repeat, drawn by each arm. Captions give the checker\'s verdict.</p>')
    s.append(side("D001 · weekly mean yield per reactor (OpenCode Go)", go, "cnt_cd_go",
                  [("P-mpl", 1, 1), ("P-mpl+cd", 1, 1), ("P-mpl+cdabc", 1, 1), ("P-mpl+cdflat", 1, 1)]))
    s.append(side("D019 · monthly downtime by cause, stacked (OpenCode Go)", go, "cnt_cd_go",
                  [("P-mpl", 1, 1), ("P-mpl+cdabc", 1, 1), ("P-ec", 1, 1), ("P-ec+cdabc", 1, 1)],
                  "<p class='small'>With the A–Z note the model writes the chart kind before it gets to the grouping key, so the stacked bar comes out as one series.</p>"))
    s.append(side("D008 · weekly yield trend: flat loses on Strix Halo", sx, "cnt_cd_sx",
                  [("P-mpl", 1, 1), ("P-mpl+cdflat", 1, 1)],
                  "<p class='small' lang='ko'>“수율 추이 좀 보여줘” (show me the yield trend). On Strix Halo the flat reply left out the weekly "
                  "grouping (<code>x.period: week</code>) in all three repeats and drew 182 raw points; the free reply kept it, and so did "
                  "OpenCode Go's flat reply, which passed all three.</p>"))
    s.append(side("D005 · DTG of two R4 batches: flat wins on Strix Halo", sx, "cnt_cd_sx",
                  [("P-mpl", 1, 1), ("P-mpl+cdflat", 1, 1), ("P-ec", 1, 1), ("P-ec+cdflat", 1, 1)],
                  "<p class='small' lang='ko'>“tga r4 두개 dtg 비교 그래프 ㄱㄱ”: the free reply drew the weight curves; the flat reply, which has to name every column from the enum, picked the DTG column.</p>"))
    s.append(side("D026 · heatmap of downtime by weekday and hour (Strix Halo)", sx, "cnt_cd_sx",
                  [("P-mpl", 2, 1), ("P-mpl+cdflat", 2, 1), ("P-ec", 2, 1), ("P-ec+cdflat", 2, 1)]))

    # ---------- caveats / recommendations / repro
    s.append("""<h2 id="caveats">Limits</h2><ul>
<li>One model (Qwen3.8 Flash), thinking off, temperature 0.2, the CNT dev split only. Strix Halo ran 15 of the 34 items, so its intervals are wide (about ±20 points).</li>
<li>The two servers do not run the same weights: OpenCode Go serves <code>qwen3.8-flash</code>, Strix Halo a 4-bit GGUF of <code>qwen3.8-flash-next</code>. Compare arms within a server, not servers' free arms with each other.</li>
<li>The full schema was not tested on Strix Halo (it hung gufo), and the order-tolerant <code>+cd2</code> variant was not run anywhere: it targets engines that keep schema order with required keys first, and OpenCode Go sorts keys anyway.</li>
<li><code>+cdabc</code> adds a prompt line, a second variable next to the grammar.</li>
<li>OpenCode Go is meant for coding agents; these scripted calls are a gray area its documentation does not settle. They identify themselves (<code>plotkit-eval/1.0</code>) and send the per-conversation session header the gateway asks for.</li></ul>
<h2 id="next">Recommendations</h2><ol class="rec">
<li><b>Keep free decoding plus plotkit's validation as the default.</b> It passed 95–98% here with 2–5% retries and no "no plot" turns.</li>
<li><b>Do not turn on constrained decoding on OpenCode Go.</b> Its alphabetical key rule silently drops keys; no prompt fixes that without making the model plan the whole spec first.</li>
<li><b>Strix Halo:</b> the flat schema is harmless but slower; keep it as an option for a weaker model, where retries and "no plot" turns cost more. Before trying the full schema again, find out why gufo hangs on it (try one chart kind's branch at a time, with a client timeout).</li>
<li><b>If a schema is kept:</b> order keys the way the model writes them (eval/cd_gufo.py measures it from free replies) and make the server's ordering rule part of the preflight. The kit's offline self-test validates replies without key order, which is exactly what both servers enforce.</li></ol>
<h2 id="repro">Reproduce</h2>
<pre>EVAL_API_KEY_FILE=~/.config/opencode_go_key python experiments/eval/cnt_runs.py --split dev --name cd_go --backend anthropic \\
  --base-url https://opencode.ai/inference/go/anthropic --model qwen3.8-flash \\
  --arms P-mpl,P-mpl+cd,P-mpl+cdabc,P-mpl+cdflat,P-ec,P-ec+cdabc --repeat 3 --workers 4
EVAL_API_KEY_FILE=~/.config/strixhalo_key python experiments/eval/cnt_runs.py --split dev --name cd_sx \\
  --base-url http://strixhalo:8084/v1 --model qwen3.8-flash-next --cd-compat gufo \\
  --arms P-mpl,P-mpl+cdflat,P-ec,P-ec+cdflat --only D001,D002,D004,D005,D006,D008,D010,D015,D017,D019,D022,D026,D028,DS01,DS04 \\
  --repeat 3 --workers 2
python experiments/eval/cd_compare.py eval/results/cnt_cd_go.csv --by kind --list
python experiments/report/build_cd.py</pre>""")

    css = CSS + EXTRA + ".diagram .lostbox rect{stroke:var(--crit);stroke-dasharray:4 3}.diagram .ok rect{stroke:var(--good)}"
    page = ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Constrained decoding for the plot spec</title><link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">'
            f'<style>{css}</style></head><body><main>{"".join(s)}</main></body></html>')
    (OUT / "index.html").write_text(page, encoding="utf-8")
    return page


if __name__ == "__main__":
    p = build()
    print(f"report/cd/index.html: {len(p) // 1024} kB, images: {len(list(IMG.glob('*.jpg')))}")
