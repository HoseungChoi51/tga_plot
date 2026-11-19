"""Build the evaluation report page (report/index.html + report/img/) from eval/results/.

    python report/build_report.py
"""
import csv
import html
import json
import math
import random
import re
import shutil
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "eval" / "results"
OUT = ROOT / "report"
IMG = OUT / "img"

MAIN = "sx"                  # the main batch: eval/results/batch_sx.csv
ARMS = ["P-mpl", "P-ec", "R-mpl-brief", "R-ec-brief", "R-mpl-plain", "R-ec-plain"]
ARM_NAME = {"P-mpl": "Protocol · matplotlib", "P-ec": "Protocol · ECharts",
            "R-mpl-brief": "Raw code + brief · matplotlib", "R-ec-brief": "Raw code + brief · ECharts",
            "R-mpl-plain": "Raw code · matplotlib", "R-ec-plain": "Raw code · ECharts"}
FAMILY = {"P": "var(--s1)", "R-brief": "var(--s2)", "R-plain": "var(--s3)"}
GROUPS = [("A", "Set A · the 24 rehearsed requests"), ("in", "Set B · in scope, not rehearsed (7)"),
          ("messy", "Set B · unusual wording (6)"), ("out", "Set B · no spec key exists (11)")]
GROUP_SHORT = {"A": "Set A", "in": "B · in scope", "messy": "B · wording", "out": "B · no key"}
MODEL = "Qwen3.8 Flash Next (Q4, thinking off) on a Strix Halo box"
MODEL_LONG = ("The model is Qwen3.8 Flash Next, a UD-Q4_K_XL GGUF with multi-token prediction, served by llama.cpp on a "
              "Strix Halo machine with two parallel slots. Thinking was switched off for every arm "
              "(chat_template_kwargs.enable_thinking = false), as run_agent.py recommends for Qwen.")
esc = html.escape


def request_texts():
    import sys
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "eval"))
    import run_agent
    from requests_b import REQUESTS
    t = {rid: text for rid, _, _, text in run_agent.read_prompts(ROOT / "tests" / "AGENT_TEST_PROMPTS.md")}
    t.update({n.split("_")[0]: text for n, _, _, text in REQUESTS})
    return t


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


def per_request(rows, arm, key="pass_all"):
    """request -> [passes, runs] for one arm (the repeats of a request are one cluster)."""
    d = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["arm"] == arm:
            d[r["request"]][0] += r[key] == "1"
            d[r["request"]][1] += 1
    return dict(d)


def boot_ci(cells, iters=4000, seed=7):
    """Pass rate over all runs, with a 95% interval from resampling whole requests (repeats are not independent)."""
    cells = list(cells)
    if not cells:
        return 0, 0, 0
    k, n = sum(c[0] for c in cells), sum(c[1] for c in cells)
    rng = random.Random(seed)
    stats = []
    for _ in range(iters):
        s = [cells[rng.randrange(len(cells))] for _ in cells]
        stats.append(sum(c[0] for c in s) / sum(c[1] for c in s))
    stats.sort()
    return k / n, stats[int(0.025 * iters)], stats[int(0.975 * iters) - 1]


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
        parts.append(
            f'<g><title>{esc(ARM_NAME[r["arm"]])}: {r["k"]}/{r["n"]} runs ({pct(p)}), 95% interval {pct(lo)}–{pct(hi)}</title>'
            f'<rect x="0" y="{y}" width="{W}" height="{rowh}" fill="transparent"/>'
            f'<text x="{left - 8}" y="{y + 13}" class="lab" text-anchor="end">{esc(ARM_NAME[r["arm"]])}</text>'
            f'<rect x="{left}" y="{y + 3}" width="{max(0.0, x(p) - left):.1f}" height="14" rx="3" fill="{FAMILY[fam(r["arm"])]}"/>'
            f'<line x1="{x(lo):.1f}" x2="{x(hi):.1f}" y1="{y + 10}" y2="{y + 10}" class="ci"/>'
            f'<text x="{min(x(max(p, hi)) + 6, W - right + 6):.1f}" y="{y + 14}" class="val">{pct(p)}</text></g>')
    parts.append('</svg>')
    return f'<figure class="fig"><figcaption class="cap-top">{esc(title)}</figcaption>{"".join(parts)}</figure>'


Q_FILL = {3: "var(--q3)", 2: "var(--q2)", 1: "var(--q1)", 0: "var(--q0)"}
Q_NAME = {3: "every repeat", 2: "2 of 3", 1: "1 of 3", 0: "never"}


def q_class(k, n):
    """How many of a request's repeats passed, as 3/2/1/0 of 3 (scaled when a run is missing)."""
    if n == 0 or k == 0:
        return 0
    if k == n:
        return 3
    return 2 if k / n >= 0.5 else 1


def consistency_chart(rows):
    """One stacked bar per arm: how many requests passed in every repeat, in 2 of 3, in 1 of 3, never."""
    W, left, right, top, rowh = 640, 196, 16, 30, 28
    H = top + rowh * len(ARMS) + 22
    parts = [f'<div class="tw"><svg viewBox="0 0 {W} {H}" role="img" aria-label="Requests by how many repeats passed, per arm" '
             f'class="chart" style="max-width:{W}px;min-width:480px">']           # drawn at 1:1; scrolls on a phone
    lx = left
    for q in (3, 2, 1, 0):
        parts.append(f'<rect x="{lx}" y="4" width="10" height="10" rx="2" fill="{Q_FILL[q]}"/>'
                     f'<text x="{lx + 15}" y="13" class="tick">{Q_NAME[q]}</text>')
        lx += 15 + 7 * len(Q_NAME[q]) + 18
    for i, arm in enumerate(ARMS):
        cells = per_request(rows, arm)
        n = len(cells)
        if not n:
            continue
        cnt = Counter(q_class(k, m) for k, m in cells.values())
        y = top + i * rowh
        parts.append(f'<text x="{left - 8}" y="{y + 15}" class="lab" text-anchor="end">{esc(ARM_NAME[arm])}</text>')
        x0 = left
        for q in (3, 2, 1, 0):
            c = cnt.get(q, 0)
            w = (W - left - right) * c / n
            if c:
                parts.append(f'<g><title>{esc(ARM_NAME[arm])}: {c} of {n} requests passed {Q_NAME[q]}</title>'
                             f'<rect x="{x0:.1f}" y="{y + 3}" width="{max(0.0, w - 2):.1f}" height="18" rx="3" fill="{Q_FILL[q]}"/>'
                             + (f'<text x="{x0 + 5:.1f}" y="{y + 16}" class="seg q{q}">{c}</text>' if w > 22 else "") + '</g>')
            x0 += w
    parts.append(f'<text x="{left}" y="{H - 4}" class="tick">0</text><text x="{W - right}" y="{H - 4}" class="tick" text-anchor="end">48 requests</text></svg></div>')
    return ('<figure class="fig wide"><figcaption class="cap-top">Requests by how many of the 3 repeats passed</figcaption>'
            + "".join(parts) + "<figcaption>Each request ran 3 times per arm at temperature 0.7. A request that passes in every repeat "
            "is one a user can rely on; one that passes 1 or 2 times out of 3 is a coin toss.</figcaption></figure>")


def heat_table(rows, reqtext):
    """Every request x arm: passes out of repeats."""
    head = "<tr><th>request</th>" + "".join(f"<th class='num'>{esc(ARM_NAME[a].replace(' · ', ' '))}</th>" for a in ARMS) + "</tr>"
    cells = {a: per_request(rows, a) for a in ARMS}
    group = {r["request"]: r["group"] for r in rows}
    body = []
    for g, label in GROUPS:
        reqs = sorted(q for q in group if group[q] == g)
        if not reqs:
            continue
        body.append(f"<tr class='grp'><td colspan='{1 + len(ARMS)}'>{esc(label)}</td></tr>")
        for q in reqs:
            tds = []
            for a in ARMS:
                k, n = cells[a].get(q, (0, 0))
                tds.append(f"<td class='num'><span class='sw' style='background:{Q_FILL[q_class(k, n)]}'></span>{k}/{n}</td>" if n else "<td class='num'>–</td>")
            body.append(f"<tr><td title='{esc(reqtext.get(q, ''))}'>{esc(q)}</td>{''.join(tds)}</tr>")
    return f"<div class='tw'><table class='heat'>{head}{''.join(body)}</table></div>"


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
<path d="M660 120 C690 120 690 65 716 65" class="edge" marker-end="url(#ar)"/><text x="686" y="70" class="small" text-anchor="end">draw</text>
<path d="M660 176 C690 176 690 238 716 238" class="edge" marker-end="url(#ar)"/><text x="712" y="266" class="small" text-anchor="end">JSON on stdin</text>
<path d="M486 186 C420 250 300 250 250 180" class="edge back" marker-end="url(#ar)"/><text x="330" y="262" class="small">error + hint (≤ 2 retries)</text>
</svg><figcaption>The spec is the only thing the model writes. File reading, column choice and the residue/peak maths run once in Python for both engines; only drawing differs. ECharts runs in a separate Node process that is started for every plot.</figcaption></figure>"""


# =================================================================== data
def load():
    D = {}
    D["runs"] = read_csv(RES / f"batch_{MAIN}.csv")
    D["think"] = read_csv(RES / f"batch_{MAIN}_think.csv")
    D["pi"] = read_csv(RES / "pi.csv")
    D["cov"] = read_csv(RES / "coverage.csv")
    D["par"] = read_csv(RES / "parity.csv")
    D["lat"] = read_csv(RES / "latency.csv")
    D["val"] = read_csv(RES / "checker_validation.csv")
    D["review"] = read_csv(RES / f"review_{MAIN}.csv")
    D["odin0"] = read_csv(ROOT / "results" / "batch_0.csv")
    D["odinS"] = read_csv(ROOT / "results" / "batch_S.csv")
    D["t06"] = read_csv(RES / "batch_t06.csv")
    D["t0ab"] = read_csv(RES / "batch_t0_aborted.csv")
    D["safety"] = json.loads((RES / "safety.json").read_text(encoding="utf-8")) if (RES / "safety.json").exists() else {}
    D["parsum"] = json.loads((RES / "parity_summary.json").read_text()) if (RES / "parity_summary.json").exists() else {}
    return D


def rate_rows(rows, arms, pred, key="pass_all"):
    out = []
    for arm in arms:
        cells = per_request([r for r in rows if pred(r)], arm, key)
        p, lo, hi = boot_ci(cells.values())
        out.append({"arm": arm, "k": sum(c[0] for c in cells.values()), "n": sum(c[1] for c in cells.values()),
                    "rate": p, "lo": lo, "hi": hi})
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
    """Per request, compare the share of repeats that passed; a sign test over the requests where the arms differ."""
    pa, pb = per_request(rows, a), per_request(rows, b)
    common = sorted(set(pa) & set(pb))
    ra = {q: pa[q][0] / pa[q][1] for q in common}
    rb = {q: pb[q][0] / pb[q][1] for q in common}
    only_a = [q for q in common if ra[q] > rb[q]]
    only_b = [q for q in common if rb[q] > ra[q]]
    diff = st.mean(ra[q] - rb[q] for q in common) if common else 0
    return len(common), only_a, only_b, sign_test(len(only_a), len(only_b)), diff


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


def record(run_dir):
    p = ROOT / "eval" / run_dir / "record.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def hit_cap(r):
    """A run where some model call stopped at the token cap."""
    return any(c.get("finish") == "length" for c in record(r["run_dir"]).get("calls", []))


def med(xs, fmt="{:.0f}"):
    xs = [float(x) for x in xs if x not in ("", None)]
    return fmt.format(st.median(xs)) if xs else "–"


def think_section(D):
    """Thinking on vs off on the same requests and arms."""
    on = D["think"]
    if not on:
        return ""
    arms = [a for a in ARMS if any(r["arm"] == a for r in on)]
    reqs = {r["request"] for r in on}
    off = [r for r in D["runs"] if r["request"] in reqs and r["arm"] in arms]
    rows = []
    for a in arms:
        f = [r for r in off if r["arm"] == a]
        o = [r for r in on if r["arm"] == a]
        rows.append(f"<tr><td><span class='sw' style='background:{FAMILY[fam(a)]}'></span>{esc(ARM_NAME[a])}</td>"
                    f"<td class='num'>{sum(r['pass_all'] == '1' for r in f)}/{len(f)} ({pct(sum(r['pass_all'] == '1' for r in f) / max(1, len(f)))})</td>"
                    f"<td class='num'>{sum(r['pass_all'] == '1' for r in o)}/{len(o)} ({pct(sum(r['pass_all'] == '1' for r in o) / max(1, len(o)))})</td>"
                    f"<td class='num'>{med([r['output_tokens'] for r in f], '{:,.0f}')}</td><td class='num'>{med([r['output_tokens'] for r in o], '{:,.0f}')}</td>"
                    f"<td class='num'>{med(r['seconds'] for r in f)} s</td><td class='num'>{med(r['seconds'] for r in o)} s</td>"
                    f"<td class='num'>{sum(hit_cap(r) for r in o)}</td><td class='num'>{sum(r['ok_run'] == '0' for r in o)}</td></tr>")
    return ("<div class='tw'><table><tr><th>arm</th><th class='num'>pass, thinking off</th><th class='num'>pass, thinking on</th>"
            "<th class='num'>output tokens off</th><th class='num'>output tokens on</th><th class='num'>time off</th><th class='num'>time on</th>"
            "<th class='num'>runs that hit the 16k cap (on)</th><th class='num'>no plot (on)</th></tr>" + "".join(rows) + "</table></div>")


def pi_section(D):
    pi = D["pi"]
    if not pi:
        return ""
    reqs = {r["request"] for r in pi}
    rows = []
    for a in [a for a in ARMS if any(r["arm"] == a for r in pi)]:
        rs = [r for r in pi if r["arm"] == a]
        b = [r for r in D["runs"] if r["arm"] == a and r["request"] in reqs]
        rows.append(f"<tr><td><span class='sw' style='background:{FAMILY[fam(a)]}'></span>{esc(ARM_NAME[a])}</td>"
                    f"<td class='num'>{sum(r['pass_all'] == '1' for r in rs)}/{len(rs)}</td>"
                    f"<td class='num'>{sum(r['pass_ask'] == '1' for r in rs)}/{len(rs)}</td>"
                    f"<td class='num'>{pct(sum(r['pass_all'] == '1' for r in b) / max(1, len(b)))}</td>"
                    f"<td class='num'>{med(r['seconds'] for r in rs)} s</td><td class='num'>{med(r['tool_calls'] for r in rs)}</td>"
                    f"<td class='num'>{med(r['plot_runs'] for r in rs)}</td>"
                    f"<td class='num'>{sum(r['rc'] == 'timeout' for r in rs)}</td></tr>")
    fails = [f"<tr><td>{esc(ARM_NAME[r['arm']])}</td><td>{esc(r['request'])}</td><td>{esc(r['note'][:90])}</td><td>{esc(r['failed'][:200])}</td></tr>"
             for r in sorted(pi, key=lambda r: (ARMS.index(r["arm"]), r["request"])) if r["pass_all"] != "1"]
    return ("<div class='tw'><table><tr><th>arm</th><th class='num'>pass</th><th class='num'>pass (asked + data)</th>"
            "<th class='num'>same requests in the batch</th><th class='num'>median time</th><th class='num'>median tool calls</th>"
            "<th class='num'>median plot runs</th><th class='num'>timeouts</th></tr>" + "".join(rows) + "</table></div>"
            + (f"<details><summary>Failed sessions ({len(fails)})</summary><div class='tw'><table><tr><th>arm</th><th>request</th>"
               f"<th>what it saved</th><th>failed checks</th></tr>{''.join(fails)}</table></div></details>" if fails else ""))


def review_section(D):
    rv = D["review"]
    if not rv:
        return ""
    rows = []
    for a in ARMS:
        rs = [r for r in rv if r["arm"] == a]
        if not rs:
            continue
        c = Counter(r["verdict"].strip() for r in rs)
        yes_in = lambda b: sum(r["verdict"].strip() == "yes" for r in rs if r["request"].startswith("B") == b)  # noqa: E731
        n_in = lambda b: sum(r["request"].startswith("B") == b for r in rs)  # noqa: E731
        defects = Counter(re.sub(r":.*", "", d) for r in rs for d in r["defects"].split())    # "missing-ask:residue" -> "missing-ask"
        rows.append(f"<tr><td><span class='sw' style='background:{FAMILY[fam(a)]}'></span>{esc(ARM_NAME[a])}</td>"
                    f"<td class='num'>{c.get('yes', 0)}</td><td class='num'>{c.get('partial', 0)}</td><td class='num'>{c.get('no', 0)}</td>"
                    f"<td class='num'>{yes_in(False)}/{n_in(False)}</td><td class='num'>{yes_in(True)}/{n_in(True)}</td>"
                    f"<td>{esc(', '.join(f'{k} ×{v}' for k, v in defects.most_common(4)))}</td></tr>")
    x = Counter((r["verdict"].strip(), r["pass_all"] == "1") for r in rv if r.get("pass_all") not in (None, ""))
    over = sum(r["pass_all"] == "1" and r["verdict"].strip() == "partial" and "overlap" in r["defects"] for r in rv)
    cross = "".join(f"<tr><td>{v}</td><td class='num'>{x[(v, True)]}</td><td class='num'>{x[(v, False)]}</td></tr>"
                    for v in ("yes", "partial", "no"))
    return (f"<div class='tw'><table><tr><th>arm</th><th class='num'>yes</th><th class='num'>partly</th><th class='num'>no</th>"
            f"<th class='num'>yes, Set A</th><th class='num'>yes, Set B</th><th>most common defects</th></tr>{''.join(rows)}</table></div>"
            f"<h4>Reviewer against checker</h4><div class='tw'><table class='narrow'><tr><th>verdict</th><th class='num'>checker passed</th>"
            f"<th class='num'>checker failed</th></tr>{cross}</table></div>"
            f"<p>The two mostly part ways on readability, which the checker does not test: {over} of the {x[('partial', True)]} plots "
            f"the checker passed and the reviewers called partly right have overlapping text.</p>")


def example_figs(D, rid, arms=("P-mpl", "P-ec", "R-mpl-brief", "R-ec-brief", "R-mpl-plain", "R-ec-plain"), rep="1"):
    figs = []
    for a in arms:
        r = next((x for x in D["runs"] if x["arm"] == a and x["request"] == rid and x["repeat"] == rep), None)
        if not r:
            continue
        png = first_png(r["run_dir"]) if r["ok_run"] == "1" else None
        verdict = "passed" if r["pass_all"] == "1" else ("no plot" if r["ok_run"] == "0" else "failed")
        why = "" if r["pass_all"] == "1" else ": " + "; ".join(p.split(":")[0].split("] ")[-1] + ":" + p.split(":", 1)[1][:70]
                                                              for p in r["failed"].split(" | ")[:2] if ":" in p)
        img = (f'<img src="{copy_img(png, f"ex_{rid}_{a}", 700)}" alt="{esc(ARM_NAME[a])} plot for request {esc(rid)}" loading="lazy">'
               if png else "<div class='noplot'>no plot</div>")
        why = why.replace("\\n", " ").replace("\n", " ")
        figs.append(f"<figure>{img}<figcaption><b>{esc(ARM_NAME[a])}</b> · {verdict}{esc(why)}</figcaption></figure>")
    return f"<div class='pair'>{''.join(figs)}</div>"


def outscope_rows(D, reqtext):
    out = [r for r in D["runs"] if r["group"] == "out"]
    reqs = sorted({r["request"] for r in out})
    body = []
    for q in reqs:
        cells = []
        for a in ARMS:
            rs = [r for r in out if r["request"] == q and r["arm"] == a]
            k = sum(r["pass_all"] == "1" for r in rs)
            routes = Counter(r["route"] for r in rs if r["route"])
            rt = (" · " + ", ".join(f"{'patch' if k2 == 'echarts' else k2}" + (f"×{v}" if v > 1 else "") for k2, v in routes.most_common())) if routes else ""
            cells.append(f"<td class='num'><span class='sw' style='background:{Q_FILL[q_class(k, len(rs))]}'></span>{k}/{len(rs)}<span class='small'>{esc(rt)}</span></td>")
        body.append(f"<tr><td>{esc(q)}</td><td lang='ko' class='small reqtext'>{esc(reqtext.get(q, '')[:110])}</td>{''.join(cells)}</tr>")
    head = "<tr><th>request</th><th>text</th>" + "".join(f"<th class='num'>{esc(ARM_NAME[a].replace(' · ', ' '))}</th>" for a in ARMS) + "</tr>"
    return f"<div class='tw'><table class='heat'>{head}{''.join(body)}</table></div>"


# Prose written after reading the results (draft until the runs finish); HTML allowed.
EXAMPLES = [                 # [(request id, note)], drawn from repeat 1
    ("02", """Set A, two turns, with tick steps, a DTG maximum and a residue label. Both protocol plots passed and were
called usable by the blind reviewer. All four raw-code plots drew overlapping text, and the two without the brief also missed a check."""),
    ("B15", """No key puts the legend outside the plot. Both protocol arms wrote the nearest keys and the legend landed inside,
in all six runs, with no error to tell the model. All four raw-code arms placed it outside in every repeat."""),
    ("B17", """Offset curves: no key, so matplotlib's <code>code</code> hatch shifted the curves. It passed the checker, but
plotkit's residue markers stayed at the unshifted values and the top of the plot is cut off; the reviewer said no. ECharts has
no route and its spec simply left the offset out."""),
]
TEXT = {
    "think": """The four main arms on 12 of the 48 requests (five from Set A, seven from Set B), once each. These runs used
temperature 0.6, as Qwen suggests for thinking, and the same cap of 16,000 tokens per reply. Thinking helped the protocol a little and
broke raw code. Each protocol arm passed 10 of 12, against 25 and 28 of 36 thinking-off runs on the same requests. With thinking on, both
arms labelled the B02 endotherm the thinking-off runs had missed, and matplotlib wrote <code>code</code> for the B18 onset. Both still
put the B15 legend inside. Every raw-code run hit the cap on at least one reply. In 7 of 12 matplotlib runs and 9 of 12 ECharts runs the
model hit it on all three tries without writing a script, so those runs drew nothing. The protocol's replies stayed near 1,000 tokens and
never came close to the cap. Twelve single runs are too few for a firm number. The times are long partly because runs queued for the
server's two slots.""",
    "pi": """The same model as a coding agent in Pi. It looks at the data, writes <code>spec.json</code> or <code>plot.py</code>,
runs it, fixes it and answers in Korean. Each session started in a clean folder that held only that arm's files. These were 12 requests,
once each, on three arms. Thinking was off: every session log shows 0 reasoning tokens. A protocol session took a median of about 25 s
and 3 tool calls. A raw-code session took 84 s and 4 calls, and the longest (B02) took 26 calls and five minutes. Pass rates were close to the batch on
the same requests: 9, 11 and 10 of 12. Running code helped one ask no key covers. On B18 both protocol agents worked out the onset
themselves (604 and 605 °C, against 605 °C ± 8), where the batch got it 0 of 6 times. The matplotlib one counts as a fail only because
the checker reads its drawn tangent as extra data; the plot itself is right. But the agents also reported the silent drops as done. On
B15 both protocol agents told the user the legend was outside on the right, when <code>legend: right</code> puts it inside. On B21 the
matplotlib agent said it had flipped the x axis, but its code flipped the shared axis twice, which puts it back.""",
    "help": """It wins where a key covers the ask. That is every run of Set A, and 79% and 82% of the 13 new Set B requests a key
covers, against 72% for raw matplotlib with the brief. On the 11 requests no key covers it falls to 42% and 27%, while raw code keeps
58–88%. It is also steadier, writes about 50 output tokens instead of 800–2,500, and its plots were the ones blind reviewers most
often called usable as-is.""",
    "cover": """The keys cover the everyday TGA asks, and the hatches reach most of the rest on paper. In the runs, the edge is weak.
On the 11 Set B requests no key covers, 29 of the 66 protocol runs ended with keys only, and all 29 failed. In 26 of them the
model never saw an error: plotkit drew a clean plot without the ask. Runs that took the hatch passed 14 of 24 (matplotlib code)
and 9 of 13 (ECharts patch). As an agent in Pi, the model went further and told the user that two such dropped asks had been done.""",
    "outscope": """These are the requests where the protocol loses, for two reasons. Where a hatch exists but the model did not take it
(legend outside, per-sample colours on matplotlib), it wrote the nearest keys and plotkit drew a clean plot without the ask. Nothing
told the model the ask was dropped. Where the request needs a number computed from the data (onset, mass loss between two temperatures,
dry-basis normalising, kelvin), ECharts has no route and matplotlib's code hatch often got it wrong. The error hint works when it fires: in B21 every protocol run first tried <code>x.flip</code>, was told no such key exists, and
recovered through the hatch. Raw code handled the normalising and the kelvin axis in every run and the mass loss in most; onset
was hard for every arm. B05 failed on every arm for different reasons. Raw code never read Lot B's European-format file
(semicolons and decimal commas); the protocol read both files but had no way to name the legend entries.""",
    "recs": """<ol>
<li><b>Stop the silent drop.</b> When a request asks for something no key does, the model should take the hatch, or say it cannot,
instead of writing the nearest keys. Add a rule to <code>AGENT.md</code>, with the list of asks that need the hatch: legend
outside, legend names, per-sample colours, offset, two panels, onset, mass loss, normalising, unit change. Better still, plotkit
could report keys it ignored and asks it did not draw.</li>
<li><b>Add keys for the gaps this study hit.</b> <code>legend: outside right</code>; a colour list for combined sheets; legend
names per file or sheet; <code>x.flip</code> (every B21 run guessed it); and computed annotations for onset, mass loss between two
temperatures and dry-basis normalising. These go in the Python core, so both engines get them; this is the only way ECharts can
draw them at all.</li>
<li><b>Make peaks safer outside TGA weight curves.</b> On heat flow (B02), 5 of 6 protocol runs took endotherms to point up. In
this file they point down, so the low-temperature endotherm was never labelled. And asked for two maxima where the curve has one,
plotkit labelled the same peak twice. On XRD (B04) it picked the shoulders of one peak and rounded 25.3° to “25”. Offer
<code>kind: endo / exo</code> with a stated sign convention, never return the same peak twice, use prominence, and match label
decimals to the data.</li>
<li><b>Make <code>code</code> and the automatic labels agree.</b> When code changes the data (B17's offset), plotkit's residue markers
stay at the old values. Either draw the automatic labels after the code runs, or switch them off when code moves the curves.</li>
<li><b>Fix the small ECharts parity bugs</b>: the <code>--</code> and <code>점선</code> line-style aliases, and <code>inout</code>
ticks.</li>
<li><b>Prefer the protocol for ECharts.</b> Raw ECharts code was the weakest arm: 53–57% pass, and with the brief, 8% of runs gave
no plot at all. For raw matplotlib, keep the TGA brief: it added 17 points.</li>
<li><b>Teach the checker readability.</b> Overlapping text was the reviewers' main complaint, and the checker cannot see it. The
figure facts already hold the text positions, so a bounding-box overlap check is cheap.</li>
<li><b>Before relying on these numbers</b>, rerun with a second model, with thinking on, and on real instrument exports, including
a Set B written by someone other than the protocol's author.</li>
</ol>""",
    "review": """The checker reads facts, not looks, so the first repeat of every request was also judged by eye. Each request got one
sheet with its six plots in a shuffled order, labelled A–F; two fresh Claude sessions graded 24 sheets each against the request text,
without the key or any scores. The question was “could the requester use this as-is?”: <i>yes</i>, <i>partly</i> (the main plot is right but
an ask is missed, or text overlaps or is clipped) or <i>no</i>. One grader was stricter (63 vs 39 yes), but every sheet holds all six arms,
so this does not favour any arm. On Set A every protocol plot was a yes. On Set B the protocol's lead disappears: 7 and 5 yes out of 24,
against 2 to 8 for raw code. Raw code mostly lost on readability: peak and residue labels drawn over each other or over the curves,
and legends over the axis titles.""",
    "backend": """The Python core does the reading and the TGA maths for both engines, so they agree on what is drawn; the few
differences are listed below. The escape hatches are where they part. matplotlib's <code>code</code> is unrestricted Python; the
ECharts patch is checked JSON that cannot add data or panels.""",
    "backend_detail": """plotkit reads the file, picks the columns and computes the residue, the peaks and the tick values once, in Python.
matplotlib then draws in the same process; ECharts gets the finished numbers as JSON in a new Node process and renders an SVG on the server.
The 11 specs that differ do so for four reasons. Where no tick step is given, each engine picks its own ticks (5 specs). When the 800 °C
residue point lies beyond the x range, matplotlib leaves its label out and ECharts still draws it (3). ECharts ignores two line-style
aliases, <code>--</code> and <code>점선</code> (dotted). And it draws <code>inout</code> ticks as <code>out</code>. ECharts costs about 0.3 s
more per figure, mostly Node start-up, which is small next to the model's own time.""",
    "limits": """<ul>
<li><b>One model.</b> Every number here is Qwen3.8 Flash Next, quantized to 4 bits, with thinking off. A larger model may close part of
the gap between the arms. Turning thinking on did not help raw code here (it ran out of tokens), but that check covers 12 requests, once
each, not all 48.</li>
<li><b>The protocol's author wrote Set A.</b> AGENT.md was written against these 24 requests, so Set A is close to a best case
for the protocol arms. Set B was written afterwards on new data, and is the fairer test.</li>
<li><b>Made-up data.</b> Set B's files come from the gallery generator. They are clean and look like real runs, but real exports
are messier than most of them.</li>
<li><b>Batch mode, not an agent.</b> The batch gives every arm one reply and up to two retries with the error. A real agent
can inspect files, run code and look again; the Pi sessions show that case for 12 requests on three arms only.</li>
<li><b>The checker decides “pass”.</b> It reads facts from what was drawn and was validated on 233 known runs, but its expectations
encode one reading of each request. Where a request allows several readings, the checks accept any of them (any_of);
the blind visual review is the cross-check.</li>
<li><b>Raw code ran in a sandbox</b> with no network and a read-only file system, which the protocol arms did not need. No script in
this study tried to start a process, reach the network, delete files or write outside its folder (a scan of every final script), so the
sandbox changed no result here; in a real deployment the scripts would run with the user's own rights.</li>
<li><b>Graded by a model.</b> The blind visual review was done by two Claude sessions, not by the lab's users, and covers the first repeat only.
They could not see the data, so a wrong value counts only where the image itself shows it.</li>
</ul>""",
    "repro": """<p>The scripts are in the <code>eval/protocol-study</code> branch of <code>tga_plot</code>, under <code>eval/</code>; this study's CSVs are in
<code>eval/results/</code> (<code>batch_sx.csv</code>, <code>batch_sx_think.csv</code>, <code>pi.csv</code>, <code>review_sx.csv</code>).</p>
<pre>uv venv &amp;&amp; uv pip install numpy matplotlib scipy openpyxl xlrd pandas pillow
npm install --prefix echartkit &amp;&amp; npx --prefix echartkit playwright install chromium
python tests/score.py --reference              # harness check
python eval/validate_checker.py                # checker vs the old scorer: 233/233

# the main batch: 48 requests x 6 arms x 3 repeats (resumes from the CSV)
EVAL_API_KEY_FILE=... python eval/run_batch.py --name sx --base-url http://strixhalo:8084/v1 \\
    --model qwen3.8-flash-next --no-think --temperature 0.7 --repeat 3 --workers 3
python eval/rescore.py --name sx               # re-check every run from its record.json, no model calls

# thinking on, 12 requests x 4 arms
python eval/run_batch.py --name sx_think --base-url http://strixhalo:8084/v1 --model qwen3.8-flash-next \\
    --temperature 0.6 --only 02,09,12,20,23,B02,B06,B11,B15,B18,B21,B23 --arms P-mpl,P-ec,R-mpl-brief,R-ec-brief

python eval/pi_runs.py --pi-model &lt;provider&gt;/qwen3.8-flash-next --thinking off --workers 2
python eval/review_sheets.py --run sx          # blind sheets; grade, then --unblind
python eval/parity.py; python eval/coverage.py; python eval/safety.py
python report/build_report.py                  # this page</pre>
<p>Run records (<code>eval/results/runs/&lt;run&gt;/&lt;arm&gt;/&lt;request&gt;_r&lt;repeat&gt;/</code>) keep every model reply, the final spec or script,
the figure facts and the checks, so any number on this page can be traced to the runs behind it.</p>""",
}


MAPPING = [
    ("file, sheets, x/y1/y2.col", "reader: Excel/CSV/TXT, header and units rows, column letters or names", "data arrays", "series.data"),
    ("x/y1/y2 min, max, step", "tick values computed once", "set_xlim / set_ylim, MultipleLocator", "axis min/max, axisTick.customValues, axisLabel.customValues + a formatter with matplotlib's decimals"),
    ("x/y1/y2 label, label_size, label_color", "defaults per preset", "set_xlabel / set_ylabel", "axis name, nameTextStyle, nameGap from estimated text widths"),
    ("tick_direction, tick_size, tick_color", "–", "tick_params(direction=…)", "axisTick.inside, axisLabel; inout drawn as a longer outside tick"),
    ("y1 / y2 color, width, linestyle, style", "colour and style aliases (Korean names, hex)", "ax.plot(color, lw, ls)", "series.lineStyle with dash arrays in line widths"),
    ("y2 (or false), log, flip", "–", "twinx(), set_yscale('log'), invert", "a second yAxis on the right, type 'log', inverse"),
    ("legend where / show / size, <axis>.legend", "names per series", "ax1.legend(loc=…), frameless", "legend with absolute left/top from a box estimate; 'best' = a JS count of covered points"),
    ("annotate.residue, annotate.peak", "value at x and DTG peaks computed in Python", "annotate + _place_labels", "graphic text and lines placed by placeLabels, a JS port of _place_labels"),
    ("annotate vline / hline / band, text notes", "–", "axvline / axhline / axvspan / text", "markLine / markArea on helper series, graphic text"),
    ("grid, title, font, font_size, text_color", "–", "ax.grid, set_title, rcParams", "splitLine, title, textStyle"),
    ("size, dpi, output.format", "file names and folder", "figsize, savefig(dpi)", "canvas at 96 px/in → SVG (SSR) → PNG/JPG/TIF by sharp, PDF by Chromium"),
    ("combine (several sheets in one plot)", "one series per sheet, grey key entries", "one Axes", "one grid; extra legend entries as empty series"),
    ("code", "exec in plotkit's own process", "any matplotlib on fig, ax1, ax2", "not available"),
    ("echarts (patch)", "checked against an allowlist: no functions, URLs or data", "not available", "deep-merged into the option; series and yAxis by index"),
]


def mapping_html():
    rows = "".join(f"<tr><td><code>{esc(k)}</code></td><td>{esc(c)}</td><td>{esc(m)}</td><td>{esc(e)}</td></tr>" for k, c, m, e in MAPPING)
    return ("<h3>Where each spec key ends up</h3><div class='tw'><table><tr><th>spec key</th><th>plotkit core (Python, shared)</th>"
            f"<th>matplotlib</th><th>ECharts option</th></tr>{rows}</table></div>")


# =================================================================== page
CSS = """
/* layout: one reading column (~72ch) for prose; figures and tables may use the full width */
:root{--surface:#fcfcfb;--panel:#ffffff;--ink:#16181d;--ink2:#4f5561;--ink3:#7b818c;--line:#e4e4e0;--accent:#2a78d6;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--good:#0ca30c;--warn:#c98500;--crit:#d03b3b;--codebg:#f3f3f0;
--q3:#1f5fae;--q2:#4a8fe0;--q1:#86b6ef;--q0:#cfcfc9;--q3ink:#ffffff;--q2ink:#0b1f3d;--q1ink:#0b1f3d;--q0ink:#16181d;
--f-body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--surface:#18191b;--panel:#202124;--ink:#eeeeea;--ink2:#c3c2b7;--ink3:#9a9a93;--line:#34353a;--accent:#3987e5;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--codebg:#26272b;
--q3:#93bdf2;--q2:#4f8ad6;--q1:#2f5f9e;--q0:#45464b;--q3ink:#0b1f3d;--q2ink:#0b1f3d;--q1ink:#ffffff;--q0ink:#eeeeea;color-scheme:dark}}
:root[data-theme="dark"]{--surface:#18191b;--panel:#202124;--ink:#eeeeea;--ink2:#c3c2b7;--ink3:#9a9a93;--line:#34353a;--accent:#3987e5;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--codebg:#26272b;
--q3:#93bdf2;--q2:#4f8ad6;--q1:#2f5f9e;--q0:#45464b;--q3ink:#0b1f3d;--q2ink:#0b1f3d;--q1ink:#ffffff;--q0ink:#eeeeea;color-scheme:dark}
*{box-sizing:border-box}html{background:var(--surface)}body{margin:0;background:var(--surface);color:var(--ink);font:16px/1.6 var(--f-body)}
main{max-width:1080px;margin:0 auto;padding-block:40px 80px;padding-left:max(20px,env(safe-area-inset-left,0px));padding-right:max(20px,env(safe-area-inset-right,0px))}
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
table.narrow{width:auto}
td.reqtext{min-width:240px}
p code,li code{overflow-wrap:anywhere}
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
.chart .seg{font:600 11px var(--f-body)}.chart .seg.q3{fill:var(--q3ink)}.chart .seg.q2{fill:var(--q2ink)}.chart .seg.q1{fill:var(--q1ink)}.chart .seg.q0{fill:var(--q0ink)}
.fig.wide{max-width:none}
table.heat td,table.heat th{padding:4px 8px}table.heat tr.grp td{font-weight:600;background:var(--codebg);color:var(--ink2);font-size:13px}
details{margin:12px 0}summary{cursor:pointer;color:var(--accent);font-weight:600}summary:focus-visible,a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.small{font-size:13px;color:var(--ink2)}
h4{font-size:15px;margin:22px 0 4px;font-weight:600}
.noplot{display:grid;place-items:center;aspect-ratio:4/3;max-width:100%;background:var(--codebg);color:var(--ink3);border-radius:4px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:14px 0}
.kpis div{min-width:0}
@media (max-width:520px){main{padding-block:24px 60px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}.grid2{grid-template-columns:1fr}h1{font-size:25px}}
"""


def build():
    D = load()
    t0 = D["runs"]
    shutil.rmtree(IMG, ignore_errors=True)
    IMG.mkdir(parents=True)
    s = []
    n_runs = len(t0)
    reqs = sorted({r["request"] for r in t0})
    n_rep = max(int(r["repeat"]) for r in t0)
    reqtext = request_texts()

    def ov(arm, key="pass_all"):
        return rate_rows(t0, [arm], lambda r: True, key)[0]

    # ---------- answers
    pm, pe = ov("P-mpl"), ov("P-ec")
    rbm, rbe = ov("R-mpl-brief"), ov("R-ec-brief")
    cov = D["cov"]
    nkey = sum(r["matplotlib"] == "key" for r in cov)
    ncode = sum(r["matplotlib"] == "code" for r in cov)
    nec = sum(r["echarts"] in ("echarts",) for r in cov)
    necp = sum(r["echarts"] == "partial" for r in cov)
    necn = sum(r["echarts"] == "none" for r in cov)
    psum = D["parsum"]
    s.append(f"""<header><p class="meta">plotkit evaluation · {esc(MODEL)} · {len(reqs)} requests × {len(ARMS)} arms × {n_rep} repeats = {n_runs} runs at temperature 0.7 · scored on what was drawn</p>
<h1>Does the plotkit spec protocol help an LLM make plots?</h1>
<p class="lede">The same model got the same requests and the same data preview six ways: with the protocol (spec → plotkit) on matplotlib or ECharts, or writing plotting code itself, with and without a short TGA brief. Every plot was scored by one checker on the figure it actually drew.</p></header>""")
    s.append(f"""<section class="answers">
<div class="ans"><h3>1 · Does it help?</h3><p class="big">Where a key covers the ask, yes; where none does, it hurts. Overall {pct(pm['rate'])} vs {pct(rbm['rate'])} of runs fully right on matplotlib (raw code + brief), {pct(pe['rate'])} vs {pct(rbe['rate'])} on ECharts.</p>
<p>{TEXT['help']}</p></div>
<div class="ans"><h3>2 · Does it cover reasonable variety?</h3><p class="big">{nkey} of {len(cov)} plausible wishes have a key on both engines; the matplotlib <code>code</code> hatch reaches {ncode} more, the ECharts patch {nec} (+{necp} partly).</p>
<p>{TEXT['cover']}</p></div>
<div class="ans"><h3>3 · How does it connect to the libraries?</h3><p class="big">One spec, one Python core, two thin drawing back ends; {psum.get('specs', 0) - psum.get('specs_with_differences', 0)} of {psum.get('specs', 0)} test specs draw the same on both.</p>
<p>{TEXT['backend']}</p></div></section>""")

    # ---------- setup
    val = D["val"]
    agree = sum(r["spec_ok"] == r["fact_ok"] for r in val)
    s.append(f"""<h2 id="setup">How it was tested</h2>
<div class="tw"><table><tr><th>arm</th><th>what the model gets</th><th>what it writes</th><th>who draws</th></tr>
<tr><td><span class="sw" style="background:var(--s1)"></span>Protocol · matplotlib / ECharts</td><td><code>AGENT.md</code> / <code>AGENT_ECHARTS.md</code> (glossary, rules, examples)</td><td>a JSON spec</td><td>plotkit, either engine</td></tr>
<tr><td><span class="sw" style="background:var(--s2)"></span>Raw code + brief</td><td>a short prompt + a TGA brief: what residue and DTG peak mean, the house defaults, the Korean part names (no spec)</td><td>a Python script</td><td>the script (matplotlib) or the printed ECharts option (ECharts 6.1 SSR)</td></tr>
<tr><td><span class="sw" style="background:var(--s3)"></span>Raw code</td><td>the short prompt only</td><td>a Python script</td><td>as above</td></tr></table></div>
<p>All six arms got the same data preview (sheets, columns, ranges), the same 16k-token budget and up to two retries with the error they caused: plotkit's <code>error</code> + <code>hint</code>, or the script's traceback. Scripts ran in a sandbox (bubblewrap: no network, read-only system).</p>
<p><b>Model and runs.</b> {esc(MODEL_LONG)} Every request ran {n_rep} times per arm at temperature 0.7, so each arm has {n_rep * len(reqs)} runs. Pass rates below count runs; their 95% intervals come from resampling whole requests, because the repeats of one request are not independent.</p>
<p><b>Requests.</b> Set A is the 24 Korean test requests the protocol was written for. Set B is 24 new ones on new made-up data (polymers, calcium oxalate with heat flow, CNT batches, an isothermal hold, XRD, rheology): 7 that a key covers but no example shows, 6 in unusual wording, and 11 that no key covers.</p>
<p><b>Scoring.</b> A figure-facts extractor reads what was actually drawn (matplotlib figure objects; the final ECharts option plus the axis extents and texts ECharts computed) and one checker tests each request's facts: the right data, what was asked, and the lab's conventions (residue and peak labels) where the request leaves them implicit. Before the runs, the checker agreed with the old spec-based scorer on {agree}/{len(val)} known-good and deliberately-wrong runs, and every Set B expectation was met by a hand-written answer wherever a route exists.</p>""")

    # ---------- Q1
    s.append('<h2 id="help">1 · Does the protocol help?</h2>')
    s.append('<div class="legend"><span><span class="sw" style="background:var(--s1)"></span>protocol</span><span><span class="sw" style="background:var(--s2)"></span>raw code + brief</span><span><span class="sw" style="background:var(--s3)"></span>raw code</span><span>bar = share of runs that passed every check · whisker = 95% interval</span></div>')
    charts = [bars_chart(f"All {len(reqs)} requests", rate_rows(t0, ARMS, lambda r: True))]
    for g, label in GROUPS:
        rows = rate_rows(t0, ARMS, lambda r, g=g: r["group"] == g)
        if any(r["n"] for r in rows):
            charts.append(bars_chart(label, rows))
    s.append(f'<div class="grid2">{"".join(charts)}</div>')
    s.append(f"<h3>All {len(reqs)} requests, {n_rep} repeats</h3>" + arm_table(t0)
             + "<p class='small'>Times include waiting for one of the server's two slots (three runs at a time) and depend on prompt "
             "caching, so they compare arms only roughly; output tokens are the steadier measure of the model's work. A protocol spec "
             "comes with a prompt of about 5,000 tokens (the glossary), raw code with 1,200–1,800.</p>")
    s.append("<h3>Repeat to repeat</h3>" + consistency_chart(t0))
    s.append(f"<details><summary>Every request on every arm (passes out of {n_rep})</summary>{heat_table(t0, reqtext)}</details>")
    pairs = [("P-mpl", "R-mpl-brief"), ("P-ec", "R-ec-brief"), ("P-mpl", "R-mpl-plain"), ("P-ec", "R-ec-plain"),
             ("R-mpl-brief", "R-mpl-plain"), ("R-ec-brief", "R-ec-plain"), ("P-mpl", "P-ec")]
    prow = []
    for a, b in pairs:
        n, oa, ob, p, diff = paired(t0, a, b)
        if n:
            prow.append(f"<tr><td>{esc(ARM_NAME[a])} vs {esc(ARM_NAME[b])}</td><td class='num'>{n}</td><td class='num'>{100 * diff:+.0f} pts</td>"
                        f"<td class='num'>{len(oa)}</td><td class='num'>{len(ob)}</td><td class='num'>{p:.2g}</td>"
                        f"<td>{esc(', '.join(oa[:10]))}{'…' if len(oa) > 10 else ''}</td><td>{esc(', '.join(ob[:10]))}{'…' if len(ob) > 10 else ''}</td></tr>")
    s.append("<h3>Same request, two arms</h3><p>For each request, the share of its repeats that passed on each arm. "
             "“Better” counts the requests where one arm passed more of its repeats; the sign test ignores ties.</p>"
             "<div class='tw'><table><tr><th>pair</th><th class='num'>requests</th><th class='num'>mean difference</th><th class='num'>first better</th>"
             "<th class='num'>second better</th><th class='num'>sign test p</th><th>first better on</th><th>second better on</th></tr>" + "".join(prow) + "</table></div>")
    fk = []
    for arm in ARMS:
        c = fail_kinds(t0, arm)
        if c:
            fk.append(f"<tr><td>{esc(ARM_NAME[arm])}</td><td>{esc('; '.join(f'{k} ×{v}' for k, v in c.most_common(6)))}</td></tr>")
    s.append("<h3>Why runs failed</h3><div class='tw'><table><tr><th>arm</th><th>most common failed checks (category)</th></tr>" + "".join(fk) + "</table></div>")
    if EXAMPLES:
        s.append("<h3>What the arms drew</h3><p>The first repeat of a few requests on every arm, with the checker's verdict.</p>")
        for rid, note in EXAMPLES:
            s.append(f"<h4>{esc(rid)} · <span lang='ko'>{esc(reqtext.get(rid, '')[:160])}</span></h4><p>{note}</p>{example_figs(D, rid)}")
    if D["think"]:
        s.append(f"<h3>With thinking on</h3><p>{TEXT['think']}</p>{think_section(D)}")
    if D["pi"]:
        s.append(f"<h3>In a real agent session (Pi)</h3><p>{TEXT['pi']}</p>{pi_section(D)}")
    if D["review"]:
        s.append(f"<h3>Blind visual review</h3><p>{TEXT['review']}</p>{review_section(D)}")

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
    s.append(f"<h3>The 11 requests no key covers</h3><p>{TEXT['outscope']}</p>{outscope_rows(D, reqtext)}"
             "<p class='small'>Cells: passes out of 3 repeats; for the protocol arms, the route each run took "
             "(keys = only spec keys, code = the matplotlib hatch, patch = the ECharts patch).</p>")

    # ---------- Q3 backends
    s.append('<h2 id="backends">3 · How does it connect to the back ends?</h2>')
    s.append(arch_svg())
    s.append(f"<p>{TEXT['backend_detail']}</p>")
    s.append(mapping_html())
    par = D["par"]
    kinds = Counter(k for k, _ in {(r["kind"], r["spec"]) for r in par})     # specs per kind of difference
    prs = []
    seen = set()
    for r in par:
        key = (r["kind"], r["field"].split(".")[-1])
        if key in seen:
            continue
        seen.add(key)
        prs.append(f"<tr><td>{esc(r['kind'])}</td><td>{esc(r['spec'])}</td><td><code>{esc(r['field'])}</code></td><td>{esc(r['matplotlib'][:70])}</td><td>{esc(r['echarts'][:70])}</td></tr>")
    s.append(f"<h3>Parity: the same spec on both engines</h3><p>{psum.get('specs', 0)} specs (gallery, the 24 reference answers, Set B answers and 8 probes) were drawn on both engines and their figure facts compared: axis ranges and ticks, labels, line styles, annotations, texts, legend, sizes. {psum.get('specs_with_differences', 0)} differ (specs per kind: {', '.join(f'{k} {v}' for k, v in kinds.most_common())}).</p>"
             "<div class='tw'><table><tr><th>kind</th><th>first spec</th><th>field</th><th>matplotlib</th><th>ECharts</th></tr>" + "".join(prs) + "</table></div>")
    lat = D["lat"]
    if lat:
        med_lat = lambda e, pdf=False: st.median(float(r["seconds"]) / max(1, int(r["figures"])) for r in lat if r["engine"] == e and (("pdf" in r["formats"]) == pdf))  # noqa: E731
        pdf = {e: [float(r["seconds"]) for r in lat if r["engine"] == e and "pdf" in r["formats"]] for e in ("matplotlib", "echarts")}
        s.append(f"<h3>Speed</h3><p>Median draw time per figure (PNG): matplotlib {med_lat('matplotlib'):.2f} s, ECharts {med_lat('echarts'):.2f} s, of which about 0.34 s is starting Node and loading ECharts, which happens for every plot. A PDF took {pdf['matplotlib'][0]:.2f} s vs {pdf['echarts'][0]:.2f} s (Chromium). Both are small next to the model: a protocol run (model reply, plotkit and any retries) took a median of {med(r['seconds'] for r in t0 if r['arm'].startswith('P-'))} s in this study.</p>" if pdf["matplotlib"] and pdf["echarts"] else "")
    sf = D["safety"]
    if sf:
        srows = "".join(f"<tr><td>{esc(k.replace('_', ' '))}</td><td>{esc(v['engine'])}</td><td>{esc(v['result'])}</td><td>{esc(v.get('error', ''))}</td></tr>" for k, v in sf.items())
        s.append("<h3>Escape hatches and safety</h3><p>The two hatches are not equivalent. <code>code</code> is Python run with <code>exec</code> in plotkit's own process; the ECharts patch is JSON checked against an allowlist. Harmless probes:</p>"
                 f"<div class='tw'><table><tr><th>probe</th><th>engine</th><th>result</th><th>plotkit's answer</th></tr>{srows}</table></div>")
    s.append(f"<h2 id='limits'>Limits of this study</h2>{TEXT['limits']}")
    s.append(f"<h2 id='recs'>Recommendations</h2>{TEXT['recs']}")
    s.append(f"<h2 id='repro'>Reproduce</h2>{TEXT['repro']}")
    # the artifact host wraps this in its own <!doctype html><head><body> skeleton
    page = (f'<title>plotkit protocol evaluation</title><meta name="claude:viewport-fit-sides" content="cover">'
            f'<link rel="preconnect" href="https://fonts.googleapis.com">'
            f'<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">'
            f'<style>{CSS}</style><main lang="en">{"".join(s)}</main>')
    return page, D


if __name__ == "__main__":
    page, D = build()
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print("wrote report/index.html", len(page), "bytes")
