"""The consolidated report: building an efficient yet reliable plotting tool for an LLM, with limited coverage.

Pulls every study together (TGA with Qwen and Luna, thinking/reasoning, Pi sessions, the CNT layer v2, constrained
decoding) and backs each point with evidence cards: the request, what the prompt told the model, the model's reply,
and the plot it drew, side by side, with the checker's and the reviewers' verdicts.

    python experiments/report/build_final.py            -> report/final/index.html + report/final/img/
"""
import html
import json
import re
import shutil
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "report"))
import cases as C  # noqa: E402
import final_cards as F  # noqa: E402
import input_pages  # noqa: E402
from build_report import CSS  # noqa: E402

OUT = ROOT / "report" / "final"
IMG = OUT / "img"
esc = html.escape
SRC = {"tga": C.tga, "cnt": C.cnt, "pi": C.pi}
ARMS = ["P-mpl", "P-ec", "R-mpl-brief", "R-ec-brief", "R-mpl-plain", "R-ec-plain"]
ARM = {"P-mpl": "protocol · matplotlib", "P-ec": "protocol · ECharts", "R-mpl-brief": "raw code + brief · matplotlib",
       "R-ec-brief": "raw code + brief · ECharts", "R-mpl-plain": "raw code · matplotlib", "R-ec-plain": "raw code · ECharts"}
FAM = {"P": "var(--s1)", "Rb": "var(--s2)", "R": "var(--s3)"}
INPUT_LINKS = {}            # card id -> [(file name, sub-page)], filled by build()


def fam(a):
    return "P" if a.startswith("P-") else ("Rb" if a.endswith("brief") else "R")


# =================================================================== narratives (written after looking at the plots)
GLOSS = {
    "K1": "“Make the y1 line black, width 2.5, and the y2 line 점선 (dotted).”",
    "K2": "“Change the residue label to ‘Residue: {}%’.” (file: a UTF-16, tab-separated instrument export)",
    "K3": "08: “Change the x/y1/y2 axis labels to ‘온도 (°C)’, ‘무게 (%)’, ‘미분 무게 (%/°C)’.” · 19: “All text grey, size 13.”",
    "K4": "“There are several operators; show what share of runs each one handled, as a pie chart.”",
    "K5": "“100% stacked bar of grade share per catalyst lot (lots in chronological order).”",
    "K6": "“Overlay the three sheets and put the legend outside the plot, on the right.”",
    "K7": "“The Annealed sheet goes into a paper, so make it 흑백 (black and white). Text 8, figure 3.5×2.6 in, 600 dpi.”",
    "K8": "B24: “Plot the PE sheet with temperature in kelvin.” · B22: “Recompute the Raw sheet with the 150 °C weight as 100% (dry basis).”",
    "K9": "“Plot the three weight curves in one figure, offset by 20% each so they don't overlap.”",
    "K10": "“Compute the extrapolated onset temperature of the Annealed sheet and mark it on the plot.”",
    "K11": "01: “Plot TGA.xlsx.” · 09: “Ticks outward, tick label size 9.”",
    "K12": "B17 again (offset curves by 20%), with reasoning on.",
    "K13": "B15 again (legend outside on the right), as a Pi agent session that ends with a message to the user.",
    "K14": "“Plot the Raw sheet with the x axis reversed (high temperatures on the left).”",
    "K15": "Session SS01, turn 2: “From week 14 on, colour the bars differently.”",
    "K16": "“I got the line-3 pilot data (L3_MES_export_202607.csv) and it looks odd when I open it. Can you plot operating hours against yield as points?”",
    "K17": "“Weekly mean CNT yield from the 런로그 sheet of run_log.xlsx; one line per reactor (R1–R4), x = week 1–26.”",
    "K18": "D005: “tga r4 두 개 dtg 비교 그래프 ㄱㄱ” (compare the DTG of the two R4 runs, quick) · D008: “수율 추이 좀 보여줘” (show me the yield trend).",
}

NARR = {
    "K1": "The protocol's glossary row 9 maps 점선 to <code>\"linestyle\": \"dotted\"</code>, and both protocol arms wrote exactly that "
          "in a 43-token spec. The raw-code brief lists the part names but no line-style words, so both models translated 점선 "
          "as “dashed”. Qwen's script even says so in a comment, and both drew <code>'--'</code>. All raw arms on both models "
          "failed this request 3/3. The blind reviewers accepted the dashed plot all the same: this is the kind of house term only "
          "a glossary pins down. (The raw-ECharts width miss, 1.875 vs 2.5, is a px-vs-pt reading the checker should forgive.)",
    "K2": "The protocol never reads the file itself: plotkit's reader handles UTF-16, tabs and the metadata header, and "
          "<code>inspect</code> hands the model the columns, so the spec is one line. The raw scripts guessed "
          "<code>pd.read_csv(sep=r'\\s+')</code>, read nothing usable, and after 3 tries (5–7k tokens) drew no plot.",
    "K3": "Both raw plots pass the checker, which tests data, labels and values, not layout. The reviewers marked them "
          "“overlap / garbled annotation” (Qwen 08: a stacked “Residue 30.0%°C” box, the legend on the y-axis) and "
          "“legend colour mismatch / overlap” (Luna 19). Across the TGA study, reviewers accepted 31/48 and 29/48 protocol plots "
          "as they were against 3–26/48 raw ones, and overlap was the main reason.",
    "K4": "The data has a “-” placeholder for a missing operator. The layer's reader treats it as missing; the raw script "
          "counted it with <code>value_counts()</code> and drew a sliver labelled 0.1%. The checker caught the extra slice.",
    "K5": "The layer has no percent-stacked bar, so the protocol drew counts in horizontal bars, a wrong answer with no "
          "error. The raw script normalised each lot to 100% correctly, but its Korean title and labels render as boxes "
          "(no Korean font set): right data, unreadable plot. The checker passes it.",
    "K6": "Every legend position in the spec is inside the axes. Asked for “outside”, both models picked the nearest key, "
          "<code>\"center right\"</code>, and plotkit drew it without complaint: the legend sits on the curves. The raw "
          "script used <code>bbox_to_anchor=(1.05, 1)</code> and got it outside, but with matplotlib's internal "
          "<code>_child1/_child2</code> labels in the legend. This “silent drop” happened in 29 of 66 no-key protocol runs on "
          "Qwen and 36 of 66 on Luna; every one failed, almost always with no error.",
    "K7": "흑백 isn't in the glossary, so the protocol set <code>text_color: black</code> and left the curves blue and red. "
          "The raw ECharts script made every series black. A one-line glossary entry (흑백 → monochrome) would fix it.",
    "K8": "The prompt lists <code>x</code>, <code>y1</code>, <code>y2</code> as “numpy arrays of the plotted data”, so the "
          "models change them. The plot is already drawn, so <code>x = x + 273.15</code> or <code>y1 = y1 / …</code> changes a "
          "local variable and nothing on the figure. Qwen's Kelvin plot is worse than unchanged: the axis now says "
          "“Temperature (K)” over °C values. When the code instead clears and redraws (Qwen, dry basis), it works but loses "
          "the house styling. The raw script just converts its data before plotting.",
    "K9": "Matplotlib code can move drawn lines, and Qwen's code did: the curves are offset, but the residue labels plotkit "
          "placed earlier stay where the unshifted curves ended. The ECharts patch can't change data by design; Luna tried "
          "<code>series[0].lineStyle.offset</code>, got plotkit's error with the allowed paths, and fell back to a plain "
          "overlay. The raw script offsets its data and labels together.",
    "K10": "No key computes an onset. On ECharts, Qwen misused the peak label (<code>type: peak, kind: min</code>) and "
           "labelled a dip at 261 °C “Onset”. With matplotlib code it computed one from the first steep slope (569 °C, too "
           "early). In a Pi session Luna had room to work: a tangent-intersection script found 604.6 °C (the reference is "
           "604.8). Computed values need code or a key, not a label.",
    "K11": "With thinking on, writing a whole script takes Qwen and Odin far more reasoning than writing a spec: they draft "
           "the script in their reasoning and then check it, “Potential issue: …”, until the 16k cap. No reply, no plot, 48k "
           "tokens over three tries. The protocol arm, same model and setting, answered in about 200 tokens and passed. "
           "Thinking-on raw code passed 5/12 and 3/12 against 10/12 for the protocol.",
    "K12": "Reasoning helps the protocol overall (+13–16 points), but on ECharts a no-key ask can trap it: Qwen searched for an "
           "allowed patch path that could shift data (there is none), used 46k tokens and drew nothing. With matplotlib code "
           "it solved the same request in 13k tokens.",
    "K13": "Same silent drop as K6, now with the agent's own words. Qwen told the user “범례는 그래프 바깥 오른쪽에 두었습니다” "
           "(I put the legend outside on the right) next to a plot where it is inside. Luna, same tool and plot, said "
           "“범례는 그래프 바깥이 아니라 그래프 안쪽 오른쪽에 배치됐습니다” (it ended up inside, not outside). The raw-code agent "
           "put it outside.",
    "K14": "The spec's <code>flip</code> only flips y values, so the agent added <code>invert_xaxis()</code> in code; the run "
           "also inverted the axis elsewhere, and two inversions cancel. Qwen's plot runs 100 → 900 °C while its answer says "
           "the axis is reversed. Luna's plot is correctly reversed; its failure is a scoring artefact (the scorer re-drew an "
           "older spec.json). Scores on agent sessions need the last drawn plot, not the last saved spec.",
    "K15": "A case where the checker is wrong both ways. The matplotlib spec used a <code>colors</code> map keyed by week "
           "numbers as strings, which matched nothing: every bar is blue, yet it passed (the values are right). The ECharts "
           "spec added a <code>구분</code> column in <code>data_code</code> and split the bars into two coloured series: what "
           "the user asked for, but the checker looked for one series and failed it. Report 3's ECharts bar gap (59% vs 82%) "
           "includes cases like this.",
    "K16": "The CNT layer keeps the TGA reader's strength: the protocol's spec names the file and two columns, and the reader "
           "copes with the export's mixed delimiters and encoding. The raw script tried <code>sep=None</code> and fallback "
           "encodings over three attempts and crashed in pandas' parser.",
    "K17": "OpenCode Go accepts JSON keys only in alphabetical order. Under the full schema the reply starts with "
           "<code>\"file\"</code>, so <code>chart</code> and <code>by</code> (which sort earlier) are dropped silently; the reply falls "
           "into the curve form, which has no aggregation, and the plot is a raw curve. Asked to write keys A→Z, the model has to decide grouping before chart kind and "
           "puts the reactor under <code>z</code>: one line. The flat format survives because its keys are all required.",
    "K18": "On Strix Halo the flat schema forces every column to come from the enum. For the terse D005 that helped: the free "
           "reply drew the weight curves, the constrained one picked the DTG column. For the vague D008 it hurt: the flat reply "
           "dropped the weekly grouping (<code>x.period</code>) in all three repeats. Net effect over 60 turns: −5 and −3 points, "
           "not significant, with no retries and 60% slower turns.",
}

SECTIONS = [
    ("reliability", "1 · Does a spec layer make plots more reliable?"),
    ("silent", "2 · The main weakness: asks with no key fail silently"),
    ("hatch", "3 · Escape hatches: where they work and where they mislead"),
    ("computed", "4 · Computed asks"),
    ("reasoning", "5 · Thinking and reasoning"),
    ("agents", "6 · Agent sessions: what the user is told"),
    ("cnt", "7 · The CNT layer (v2): general charts, sessions, two engines"),
    ("cd", "8 · Constrained decoding"),
]


# =================================================================== helpers
def img(path, name, width=680):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)))
    dst = IMG / f"{name}.jpg"
    im.save(dst, quality=80)
    return f"img/{dst.name}"


def clean_spec(text):
    """A spec reply for display: no output dir, file as a base name; non-JSON text returned as is."""
    try:
        m = re.search(r"\{.*\}", text, re.S)
        d = json.loads(m.group(0)) if m else None
    except (json.JSONDecodeError, AttributeError):
        d = None
    if not isinstance(d, dict):
        return text
    d.pop("output", None)
    f = d.get("file")
    if isinstance(f, str):
        d["file"] = Path(f).name if f.startswith("/") else f
    elif isinstance(f, list):
        d["file"] = [Path(x).name if x.startswith("/") else x for x in f]
    return json.dumps(d, ensure_ascii=False, indent=1)


def code_block(lines, max_lines=16):
    out = []
    for ln, hit in lines[:max_lines]:
        t = esc(ln.rstrip()[:160])
        out.append(f"<span class='hl'>{t}</span>" if hit else t)
    if len(lines) > max_lines:
        out.append("…")
    return "<pre class='code'>" + "\n".join(out) + "</pre>"


def panel_html(card, p, c, k):
    label = esc(p["label"])
    if c is None:
        return f"<div class='panel'><div class='plab'>{label}</div><p class='small'>run not found</p></div>"
    verdict = "<span class='chip ok'>checker: pass</span>" if c["pass"] else "<span class='chip none'>checker: fail</span>"
    rv = ""
    if c["kind"] == "tga":
        g = C.review(c["run"], c["id"], c["arm"])
        if g and c["rep"] == 1:
            v, d = g[0][0], g[0][1]
            rv = f"<span class='chip {'ok' if v == 'yes' else 'part' if v == 'partial' else 'none'}'>review: {esc(v)}{(' · ' + esc(d)) if d else ''}</span>"
    tok = c["row"].get("output_tokens") or ""
    secs = c["row"].get("seconds") or c["row"].get("turn_s") or ""
    meta = []
    if tok and tok not in ("0", "None"):
        meta.append(f"{int(float(tok)):,} output tokens")
    if secs:
        meta.append(f"{float(secs):.0f} s")
    # reply / answer / reasoning
    blocks = []
    if p.get("answer"):
        ans = c.get("answer", "")
        blocks.append("<div class='rl'>agent's final message to the user</div>"
                      + code_block(C.excerpt(ans, p.get("hl", []), context=1, limit=10) if p.get("hl") else [(l, False) for l in ans.splitlines()][:10], 10))
        body = c.get("spec") or c.get("script") or ""
        if body:
            blocks.append("<div class='rl'>what it wrote</div>" + code_block(C.excerpt(clean_spec(body), p.get("hl", []), context=2, limit=10), 12))
    else:
        if c["kind"] == "pi":
            body = c.get("spec") or c.get("script") or ""
        elif c["kind"] == "tga":
            body = c["final"] if isinstance(c["final"], str) else (json.dumps(c["final"], ensure_ascii=False) if c["final"] else "")
            if not body and c["replies"]:
                body = c["replies"][-1]
        else:
            body = c["replies"][-1] if c.get("replies") else (json.dumps(c.get("spec"), ensure_ascii=False) if c.get("spec") else "")
        is_spec = c["arm"].startswith("P-") and body.strip()[:1] in ("{", "`")
        shown = clean_spec(body) if is_spec else body
        if shown.strip():
            lines = C.excerpt(shown, p.get("hl", []), context=2, limit=14) if not is_spec else \
                [(l, any(re.search(h, l) for h in p.get("hl", []))) for l in shown.splitlines()]
            blocks.append(f"<div class='rl'>model's reply ({'spec' if is_spec else 'script excerpt'})</div>" + code_block(lines, 16))
        if p.get("reasoning") and c.get("reasoning") and c["reasoning"][-1].strip():
            tail = c["reasoning"][-1].strip().splitlines()
            blocks.append("<div class='rl'>end of its reasoning (no reply followed)</div>" + code_block([(l, "Potential issue" in l) for l in tail[-9:]], 9))
        if not shown.strip() and not (p.get("reasoning") and c.get("reasoning")):
            blocks.append("<p class='small'>no reply text: every call hit the token cap while reasoning</p>")
    # plot
    if c["images"]:
        src = img(c["images"][0], f"{card['id']}_{k}")
        more = f"<div class='small'>+{len(c['images']) - 1} more sheet(s)</div>" if len(c["images"]) > 1 else ""
        plot = f"<img src='{src}' alt='{label}'>{more}"
    else:
        err = (c["row"].get("errors") or c.get("failed") or "").replace("||", "\n")
        err = re.sub(r"/home/chs/[^ \n\"']+/", "…/", err)
        plot = "<div class='noplot'>no plot was drawn" + (f"<pre class='code'>{esc(err.strip()[-420:])}</pre>" if err.strip() else "") + "</div>"
    why_text = re.sub(r"/home/chs/[^ \n\"']+/", "…/", (c.get("failed") or ""))[:230]
    why = "" if c["pass"] else f"<div class='why'>{esc(why_text)}</div>"
    return (f"<div class='panel'><div class='plab'>{label}</div><div class='chips'>{verdict}{rv}</div>"
            f"<div class='meta'>{' · '.join(meta)}</div>{plot}{why}{''.join(blocks)}</div>")


def card_html(card):
    res = [(p, SRC[p["src"]](*p["args"])) for p in card["panels"]]
    req = next((c["request"] for _, c in res if c and c.get("request")), "")
    prompts = "".join(f"<div class='pq'><span class='src'>{esc(F.PROMPT[k][0])}</span><code>{esc(F.PROMPT[k][1])}</code></div>"
                      for k in card.get("prompts", []))
    panels = "".join(panel_html(card, p, c, i) for i, (p, c) in enumerate(res))
    n = len(res)
    return (f"<section class='card' id='{card['id']}'><h3><span class='cid'>{card['id']}</span>{esc(card['title'])}</h3>"
            f"<div class='req'><div class='rl'>the request</div><p lang='ko' class='ko'>{esc(req.strip())}</p>"
            f"<p class='gloss'>{esc(GLOSS.get(card['id'], ''))}</p>"
            + ("".join(f"<p class='inlink'>input file: <a href='{h}'>{esc(n)}</a> (opens the file as written and what "
                       f"plotkit's reader made of it)</p>" for n, h in INPUT_LINKS.get(card["id"], [])))
            + "</div>"
            + (f"<div class='prm'><div class='rl'>what the prompt told the model</div>{prompts}</div>" if prompts else "")
            + f"<div class='panels n{n}'>{panels}</div>"
            f"<div class='narr'><div class='rl'>what happened</div><p>{NARR.get(card['id'], '')}</p></div></section>")


def pct(k, n):
    return f"{100 * k / n:.0f}%" if n else "–"


def tga_stats(run):
    rs = C.rows(f"batch_{run}")
    out = {}
    for a in ARMS:
        x = [r for r in rs if r["arm"] == a]
        if not x:
            continue
        g = lambda grp: [r for r in x if r["group"] == grp]  # noqa: E731
        k = lambda rr: sum(r["pass_all"] == "1" for r in rr)  # noqa: E731
        key_rows = [r for r in x if r["group"] in ("A", "in", "messy")]
        out[a] = {"all": (k(x), len(x)), "A": (k(g("A")), len(g("A"))), "key": (k(key_rows), len(key_rows)),
                  "out": (k(g("out")), len(g("out"))), "tok": st.median(int(r["output_tokens"] or 0) for r in x),
                  "s": st.median(float(r["seconds"]) for r in x), "noplot": sum(r["ok_run"] == "0" for r in x)}
    return out


def grouped_chart(title, data, metric, note=""):
    """data: {model: stats}; one row per arm, one bar per model."""
    models = list(data)
    W, left, right, top = 640, 210, 70, 26
    bh, gap = 13, 12
    rowh = bh * len(models) + gap
    H = top + rowh * len(ARMS) + 24
    x = lambda v: left + v * (W - left - right)  # noqa: E731
    shade = {models[0]: "1", models[-1]: ".55"} if len(models) > 1 else {models[0]: "1"}
    out = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="{esc(title)}">']
    for t in (0, .25, .5, .75, 1):
        out.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top - 8}" y2="{H - 18}" class="grid"/>'
                   f'<text x="{x(t):.1f}" y="{H - 4}" class="tick" text-anchor="middle">{int(t * 100)}%</text>')
    for i, a in enumerate(ARMS):
        y0 = top + i * rowh
        out.append(f'<text x="{left - 8}" y="{y0 + rowh / 2}" class="lab" text-anchor="end">{esc(ARM[a])}</text>')
        for j, m in enumerate(models):
            s = data[m].get(a)
            if not s:
                continue
            k, n = s[metric]
            v = k / n if n else 0
            y = y0 + j * bh
            out.append(f'<g><title>{esc(m)} · {esc(ARM[a])}: {k}/{n} ({pct(k, n)})</title>'
                       f'<rect x="{left}" y="{y}" width="{max(0.0, x(v) - left):.1f}" height="{bh - 2}" rx="2" fill="{FAM[fam(a)]}" opacity="{shade.get(m, ".75")}"/>'
                       f'<text x="{x(v) + 5:.1f}" y="{y + bh - 3}" class="val">{esc(m)} {pct(k, n)}</text></g>')
    out.append("</svg>")
    return f"<figure class='fig'><figcaption class='cap-top'>{esc(title)}</figcaption>{''.join(out)}" + \
           (f"<figcaption>{note}</figcaption>" if note else "") + "</figure>"


# =================================================================== page
EXTRA = """
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:22px 0}
.card h3{margin:0 0 10px;font-size:17px}.cid{display:inline-block;font-size:12px;font-weight:600;background:var(--ink);color:var(--surface);border-radius:5px;padding:1px 7px;margin-right:9px;vertical-align:2px}
.rl{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin:8px 0 3px}
.req .ko{font-size:15px;margin:0;max-width:none}.gloss{color:var(--ink2);font-size:13.5px;margin:2px 0 0;max-width:none}
.pq{font-size:12.5px;margin:3px 0}.pq .src{color:var(--ink3);margin-right:6px}.pq code{white-space:normal}
.panels{display:grid;gap:12px;margin:12px 0 6px}.panels.n1{grid-template-columns:1fr}.panels.n2{grid-template-columns:repeat(2,minmax(0,1fr))}
.panels.n3{grid-template-columns:repeat(3,minmax(0,1fr))}.panels.n4{grid-template-columns:repeat(4,minmax(0,1fr))}
@media (max-width:900px){.panels.n3,.panels.n4{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:560px){.panels.n2,.panels.n3,.panels.n4{grid-template-columns:1fr}}
.panel{border:1px solid var(--line);border-radius:9px;padding:9px;background:var(--surface);min-width:0}
.plab{font-weight:600;font-size:13.5px}.chips{display:flex;flex-wrap:wrap;gap:5px;margin:5px 0}.meta{font-size:12px;color:var(--ink3)}
.panel img{width:100%;height:auto;display:block;border-radius:5px;background:#fff;margin:6px 0;border:1px solid var(--line)}
.noplot{border:1px dashed var(--crit);border-radius:6px;padding:8px;margin:6px 0;font-size:13px;color:var(--crit)}
.why{font-size:12px;color:var(--crit);margin:2px 0 4px}
pre.code{font:11.5px/1.45 var(--f-mono);background:var(--codebg);padding:8px 9px;border-radius:6px;white-space:pre-wrap;word-break:break-word;margin:0;max-height:300px;overflow:auto}
pre.code .hl{background:color-mix(in srgb,var(--warn) 30%,transparent);border-radius:2px}
.narr p{max-width:none;margin:2px 0 0}.narr{border-top:1px solid var(--line);margin-top:8px;padding-top:4px}
.toc{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}.toc a{font-size:13px;border:1px solid var(--line);border-radius:99px;padding:2px 10px;text-decoration:none;background:var(--panel)}
.small{font-size:13px;color:var(--ink2)}
.inlink{font-size:13px;margin:4px 0 0;max-width:none}
"""


def build():
    shutil.rmtree(OUT, ignore_errors=True)
    IMG.mkdir(parents=True)
    INPUT_LINKS.clear()
    INPUT_LINKS.update(input_pages.build(OUT, CSS + EXTRA))
    qw, lu = tga_stats("sx"), tga_stats("luna")
    s = []
    # ---------- header and answers
    s.append("""<header><p class="meta">Consolidates five reports and about 6,800 scored runs and turns across two machines (laptop, x870e) and three model servers · 2026-11-24</p>
<h1>A small, reliable plotting tool for an LLM: what the experiments say</h1>
<p class="lede">The goal: let a language model make the plots a lab actually needs (TGA curves, then general production charts) reliably and cheaply, by giving it a small spec with house defaults, a glossary and error hints instead of letting it write plotting code. Below, every claim comes with the request, what the prompt told the model, what the model replied, and the plot it drew.</p></header>""")
    pm, pe, rbm, rbe = (qw[a] for a in ("P-mpl", "P-ec", "R-mpl-brief", "R-ec-brief"))
    s.append(f"""<section class="answers">
<div class="ans"><h3>Where a key covers the ask</h3><p class="big">The spec layer is reliable and cheap: Set A {pct(*pm['A'])} on every model; every request with a key {pct(*pm['key'])} (Qwen) and {pct(*lu['P-mpl']['key'])} (Luna), from ~50 output tokens in seconds.</p>
<p>Raw code needs 600–2,500 tokens and up to two minutes, misreads house terms (K1), trips on awkward files (K2, K16), and its plots are rejected far more often for clutter (K3).</p></div>
<div class="ans"><h3>Where no key covers it</h3><p class="big">The layer fails silently: {pct(*pm['out'])} and {pct(*pe['out'])} on Qwen's no-key asks, against {pct(*rbm['out'])} for raw code.</p>
<p>The model writes the nearest key, nothing errs, and an agent may tell the user the ask was done (K6, K13). Escape hatches help on matplotlib but mislead when they change data after drawing (K8, K9).</p></div>
<div class="ans"><h3>What to build</h3><p class="big">Keep the spec, defaults and glossary for the covered scope; refuse or route anything uncovered instead of approximating it.</p>
<p>Turn reasoning on only for the spec path, draw exports with matplotlib, sandbox code, and skip constrained decoding: free decoding plus plotkit's checks is already at 95–98% where keys exist.</p></div></section>""")
    s.append("<nav class='toc'>" + "".join(f"<a href='#{k}'>{esc(t.split(' · ')[1])}</a>" for k, t in SECTIONS)
             + "<a href='#numbers'>Numbers</a><a href='#build'>Recommendations</a><a href='#runs'>All runs</a></nav>")

    # ---------- map of the work
    s.append("""<h2 id="runs">What was run</h2><div class='tw'><table>
<tr><th>study</th><th>model · server</th><th>harness</th><th>requests × arms × repeats</th><th>scored</th><th>earlier report</th></tr>
<tr><td>TGA Set A, first look</td><td>Odin (office, centinels), temperature 0</td><td>batch, spec arms</td><td>24 × 2 × 3</td><td>144</td><td>–</td></tr>
<tr><td>TGA Set A + B</td><td>Qwen3.8 Flash Next UD-Q4 on Strix Halo, thinking off, T 0.7</td><td>batch (one call, ≤2 retries)</td><td>48 × 6 × 3</td><td>864</td><td>plotkit protocol evaluation</td></tr>
<tr><td>TGA thinking / reasoning</td><td>Qwen (thinking on, T 0.6); spec arms with reasoning</td><td>batch</td><td>12 × 4 × 1 · 48 × 2 × 3</td><td>48 · 288</td><td>same</td></tr>
<tr><td>TGA Set A + B</td><td>GPT-6 Luna (centinels via Pi CLI), effort none</td><td>batch</td><td>48 × 6 × 3</td><td>864 (+48, +288 reasoning)</td><td>plotkit Luna evaluation</td></tr>
<tr><td>Agent sessions</td><td>Qwen and Luna in Pi</td><td>Pi, clean workspaces</td><td>12 × 3 each</td><td>72</td><td>both TGA reports</td></tr>
<tr><td>CNT layer v2 (chartkit), dev</td><td>Qwen on Strix Halo</td><td>batch, sessions</td><td>34 items, 44 turns</td><td>~800</td><td>–</td></tr>
<tr><td>CNT sealed</td><td>Strix Halo (3 spec arms); opencode-go Qwen3.8 Flash (+ raw code)</td><td>batch, sessions</td><td>75 items, 116 turns × 3</td><td>1,044 + 1,392</td><td>Thin Plot Layer Verdict</td></tr>
<tr><td>Constrained decoding</td><td>OpenCode Go Qwen3.8 Flash; Strix Halo</td><td>batch</td><td>44 × 6 × 3 · 20 × 4 × 3</td><td>792 · 240</td><td>Constrained decoding for the plot spec</td></tr></table></div>
<p class='small'>Arms: <b>protocol</b> = the model writes a JSON spec that plotkit/chartkit draws (matplotlib or ECharts); <b>raw code + brief</b> = it writes a plotting script, given a short note on house conventions and Korean part names; <b>raw code</b> = the script with no note. Every run is scored on what was drawn (figure facts); blind reviewers also graded repeat 1. Cards marked CNT sealed show items from the held-out split, which has now been used.</p>""")

    # ---------- numbers
    s.append("<h2 id='numbers'>The numbers</h2>")
    data = {"Qwen": qw, "Luna": lu}
    s.append("<div class='legend'><span><span class='sw' style='background:var(--s1)'></span>protocol</span><span><span class='sw' style='background:var(--s2)'></span>raw code + brief</span><span><span class='sw' style='background:var(--s3)'></span>raw code</span><span>darker bar = Qwen, lighter = Luna</span></div>")
    s.append("<div class='grid2'>" + grouped_chart("Requests a key covers (Set A + in-scope + unusual wording, 37 × 3)", data, "key")
             + grouped_chart("Requests no key covers (11 × 3)", data, "out") + "</div>")
    rows = "".join(f"<tr><td><span class='sw' style='background:{FAM[fam(a)]}'></span>{esc(ARM[a])}</td>"
                   + "".join(f"<td class='num'>{pct(*d[a]['all'])}</td><td class='num'>{pct(*d[a]['key'])}</td><td class='num'>{pct(*d[a]['out'])}</td>"
                             f"<td class='num'>{d[a]['tok']:,.0f}</td><td class='num'>{d[a]['s']:.0f} s</td>" for d in (qw, lu)) + "</tr>"
                   for a in ARMS)
    s.append("<div class='tw'><table><tr><th rowspan=2>arm</th><th colspan=5>Qwen (Strix Halo)</th><th colspan=5>Luna</th></tr>"
             "<tr>" + "<th class='num'>all</th><th class='num'>key</th><th class='num'>no key</th><th class='num'>tokens</th><th class='num'>time</th>" * 2
             + "</tr>" + rows + "</table></div>")
    rv = {}
    for run in ("sx", "luna"):
        rs = C.rows(f"review_{run}")
        rv[run] = {a: (sum(r["verdict"] == "yes" for r in rs if r["arm"] == a), sum(r["arm"] == a for r in rs)) for a in ARMS}
    think = C.rows("batch_sx_think")
    tk = {a: (sum(r["pass_all"] == "1" for r in think if r["arm"] == a), sum(r["arm"] == a for r in think)) for a in ("P-mpl", "P-ec", "R-mpl-brief", "R-ec-brief")}
    s.append(f"""<div class='cols2'><div><h3>Blind review: accepted as drawn (repeat 1, 48 requests)</h3><div class='tw'><table><tr><th>arm</th><th class='num'>Qwen</th><th class='num'>Luna</th></tr>
{''.join(f"<tr><td>{esc(ARM[a])}</td><td class='num'>{rv['sx'][a][0]}/{rv['sx'][a][1]}</td><td class='num'>{rv['luna'][a][0]}/{rv['luna'][a][1]}</td></tr>" for a in ARMS)}</table></div>
<p class='small'>Reviewers looked at the plots without knowing the arm. Overlapping text was the most common reason to reject raw code.</p></div>
<div><h3>Other settings</h3><div class='tw'><table><tr><th>setting</th><th>protocol</th><th>raw code</th></tr>
<tr><td>Qwen, thinking on (12 requests)</td><td class='num'>{tk['P-mpl'][0]}/12 · {tk['P-ec'][0]}/12</td><td class='num'>{tk['R-mpl-brief'][0]}/12 · {tk['R-ec-brief'][0]}/12, 48k tokens</td></tr>
<tr><td>Pi agent, Qwen (12)</td><td class='num'>9/12 · 11/12, ~25 s</td><td class='num'>10/12, 84 s</td></tr>
<tr><td>Pi agent, Luna (12)</td><td class='num'>9/12 · 10/12, ~13 s</td><td class='num'>9/12, 29 s</td></tr>
<tr><td>CNT sealed, checker</td><td class='num'>61–65%</td><td class='num'>69.0% (opencode)</td></tr>
<tr><td>CNT sealed, reviewed (weighted)</td><td class='num'>67.6–75.0%</td><td class='num'>72.5%</td></tr>
<tr><td>Constrained vs free spec (CNT dev)</td><td class='num' colspan=2>Strix: −5 / −3 pts (n.s.) · OpenCode Go: −16 to −92 pts</td></tr></table></div>
<p class='small'>CNT review figures are the stratified, weighted acceptance from the Thin Plot Layer Verdict.</p></div></div>""")

    # ---------- sections with cards
    for key, title in SECTIONS:
        s.append(f"<h2 id='{key}'>{esc(title)}</h2>")
        intro = {
            "reliability": "Four things the spec layer gets right without being asked: house vocabulary, file reading, defaults "
                           "and layout. The CNT cards show the same pattern on general charts, and the one place raw code wins: "
                           "an ask the layer has no word for.",
            "silent": "In the TGA study, 11 of 48 requests had no key. Raw code passed them 58–88% of the time; the spec arms 21–42%. "
                      "The failures are rarely errors: the model maps the ask onto the closest key, plotkit accepts it, and the plot "
                      "quietly differs.",
            "hatch": "The matplotlib <code>code</code> hatch runs Python after plotkit has drawn; the ECharts <code>echarts</code> "
                     "patch is allowlisted JSON that cannot touch data. Hatch runs passed 14/24 (matplotlib) and 9/13 (ECharts) on Qwen.",
            "computed": "Onset temperature, mass loss and dry basis are numbers computed from the data. No key computes them.",
            "reasoning": "",
            "agents": "Pass rates in Pi sessions were close to batch mode; the difference is what the agent says afterwards.",
            "cnt": "Layer v2 added bars, scatter, histograms, heatmaps, pies, a data grammar and multi-turn sessions. On the sealed "
                   "split the spec arms scored 61–65% by checker and 68–75% by weighted review; raw code 69% and 72.5%.",
            "cd": "Forcing the reply through a JSON Schema should remove broken JSON and unknown keys. Free decoding with plotkit's "
                  "checks already passed 95–98% on the CNT dev split, so there was little left to fix; the grammar's key order "
                  "then decided the result.",
        }[key]
        if intro:
            s.append(f"<p>{intro}</p>")
        for card in [c for c in F.CARDS if c["section"] == key]:
            s.append(card_html(card))
        if key == "cnt":
            # engine parity probes, image only
            figs = []
            for name, cap in (("parity_linestyle", "Spec <code>\"y2\": {\"linestyle\": \"--\"}</code>: matplotlib dashed, ECharts solid (the alias is accepted but not translated)."),
                              ("parity_residue", "Spec <code>\"x\": {\"max\": 700}</code>: matplotlib drops the 800 °C residue label, ECharts draws it outside the plot.")):
                cells = []
                for eng, d in F.IMAGES[name]:
                    ps = C.pngs(ROOT / d)
                    if ps:
                        cells.append(f"<div class='panel'><div class='plab'>{esc(eng)}</div><img src='{img(ps[0], f'{name}_{eng}')}' alt='{esc(eng)}'></div>")
                figs.append(f"<div class='card'><h3><span class='cid'>P{len(figs) + 1}</span>Engine parity probe</h3><p class='small'>{cap}</p><div class='panels n2'>{''.join(cells)}</div></div>")
            s.append("<h3>Engine parity, no model involved</h3><p>Of 69 test specs drawn by both engines, 58 came out the same. "
                     "The differences: automatic ticks on small or large-font figures (5 specs), the residue label beyond the x range (3), "
                     "line-style aliases, and <code>inout</code> ticks. Per figure, matplotlib draws in 0.17 s and ECharts in 0.49 s "
                     "(0.34 s of it is starting Node). In the E4 export test reviewers preferred the matplotlib export 48 times to 26.</p>"
                     + "".join(figs))

    # ---------- coverage, efficiency, safety
    s.append("""<h2 id="coverage">Coverage: what the keys reach</h2>
<p>Of 64 plot changes a TGA user plausibly asks for, 38 have a key on both engines. The matplotlib <code>code</code> hatch reaches 25 more; the ECharts patch reaches 11, plus 3 partly; 12 are out of reach on ECharts (renamed legend entries when combined, a second x axis, unit-converted axes, panels, insets, offset curves, onset, mass loss, normalisation, computed DTG, error bands). Layer v2 added the general chart kinds the CNT engineers needed; still missing are box plots (asked for in the E3 sessions), small multiples and percent-stacked bars (K5).</p>
<h2 id="cost">Efficiency</h2>
<div class='tw'><table><tr><th></th><th>protocol</th><th>raw code</th></tr>
<tr><td>output tokens per request (TGA, median)</td><td>39–52</td><td>606–2,486</td></tr>
<tr><td>time per request (TGA, median)</td><td>3–18 s</td><td>17–107 s</td></tr>
<tr><td>CNT, one user (E1, Strix Halo)</td><td>p50 3.4–3.5 s, p90 12–14 s (6.4–7.1 s projected on a 2× box)</td><td>p50 32 s, p90 53 s</td></tr>
<tr><td>thinking on (Qwen)</td><td>~1,000 tokens, passes</td><td>16k cap on every call, often no plot</td></tr>
<tr><td>drawing</td><td colspan=2>matplotlib 0.17 s / figure, ECharts 0.49 s (Node start-up 0.34 s); PDF 0.27 s vs 1.09 s</td></tr></table></div>
<h2 id="safety">Safety</h2>
<p>The matplotlib <code>code</code> hatch is <code>exec</code> in plotkit's own process: harmless probes read a file outside the data folder, listed the home folder and started a process. The ECharts patch refused a function, a URL and a data path. CNT layer v2 runs its data hatch in a sandbox. Raw code ran in bubblewrap (no network, read-only system) during the tests, which a deployed tool would also need.</p>""")

    # ---------- disagreements and recommendations
    s.append("""<h2 id="disagree">Where the earlier reports disagree, and why</h2><ul>
<li><b>Does the protocol help?</b> On Qwen yes, most on ECharts (+21 pts vs raw ECharts with the brief); on Luna not overall (raw matplotlib 83% vs 78%). Both hold: the layer's gain is the model's weakness. A strong model writes good code where no key exists; on keyed asks the protocol is ahead and uses 20–50× fewer output tokens.</li>
<li><b>Does the brief help raw code?</b> +17 pts on Qwen (matplotlib), +7 (n.s.) on Luna, and on Luna reviewers accepted more raw plots without it. The brief adds conventions (residue and peak labels) that also add clutter.</li>
<li><b>Hatch use:</b> the CNT verdict counts hatch use as a failure sign; the Luna report recommends the hatch when the model reasons. Hatches were reliable for drawing additions and unreliable for changing data (K8, K9). Treat data changes as a key or a refusal.</li>
<li><b>Silent failures:</b> on CNT, reviewers found more silent failures in raw code (15.8%) than in the spec arms (8–13%); in TGA the spec arms' silent drop is the headline. Both are true: raw code fails silently on data, the spec on asks without keys.</li></ul>""")
    s.append("""<h2 id="build">Recommendations for the tool</h2><ol class="rec">
<li><b>Keep the core: a small spec, house defaults, a glossary of the users' own words, and plotkit's error + hint.</b> This is what made keyed asks reliable for every model (K1, K2, K16) at ~50 tokens.</li>
<li><b>Make uncovered asks loud.</b> When the request contains an ask no key expresses (legend outside, colour by rule, unit conversion), the model must say so or route to code; plotkit should reject “nearest key” matches it can detect (an <code>asks</code> list the checker reads). This is the single largest failure (K6, K7, K13).</li>
<li><b>Route by request.</b> Spec when a key exists; code (sandboxed) when none does and the model is strong enough; a plain “can't do this yet” otherwise.</li>
<li><b>Fix the hatch contract.</b> Let code transform data before drawing (or raise when it reassigns <code>x</code>/<code>y1</code>), and redraw auto-labels after it (K8, K9). Move frequent computed asks (onset, mass loss, dry basis, kelvin) into keys (K10).</li>
<li><b>Add the missing keys the data asked for:</b> legend outside, colour lists and rules, legend names, x reversal, 흑백, percent-stacked bars, box plots.</li>
<li><b>Reasoning:</b> on for the spec path with capable models (+13–16 pts), never for raw code on Qwen-class models (K11); cap ECharts patch attempts (K12).</li>
<li><b>Engines:</b> one spec, matplotlib for exports, ECharts for the live view; fix the parity bugs (line-style aliases, labels beyond the axis range) and make parity a CI check.</li>
<li><b>Skip constrained decoding</b> unless a weaker model makes repairs frequent; if used, measure the server's key-order rule first (K17, K18).</li>
<li><b>Score what the user sees.</b> Add an overlap/legibility check, score agent sessions on the last drawn plot (K14), and audit checker artefacts like K15 before trusting small differences.</li></ol>""")
    s.append("""<h2 id="limits">Limits</h2><ul>
<li>Two models on TGA (Qwen3.8 Flash Next locally, GPT-6 Luna via a proxy that refused many raw-code calls), one model family on CNT; synthetic data; the protocol's author wrote Set A.</li>
<li>Scores come from a figure-facts checker validated against hand-written answers and negative controls; it does not see layout, and K15 shows it can be wrong both ways. Reviewers and personas were Claude sessions.</li>
<li>Cards show repeat 1; the rates come from all repeats. Numbers are recomputed from the result CSVs in <code>eval/results/</code>; CNT review and latency figures are quoted from the Thin Plot Layer Verdict.</li></ul>
<p>Input files: <a href='inputs/index.html'>every file behind the cards, and the reader's awkward test files</a>, each shown as written with what plotkit's reader made of it.</p>
<p class='small'>Built by <code>python experiments/report/build_final.py</code> from <code>eval/results/</code> (CSVs in git; run images synced from x870e).</p>""")

    css = CSS + EXTRA
    page = ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>A reliable plotting tool for an LLM</title><link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">'
            f'<style>{css}</style></head><body><main>{"".join(s)}</main></body></html>')
    (OUT / "index.html").write_text(page, encoding="utf-8")
    return page


def make_zip():
    """report/plotkit_report.zip: the folder as one file to share (opens with index.html)."""
    import zipfile
    dst = OUT.parent / "plotkit_report.zip"
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT.rglob("*")):
            if f.is_file():
                z.write(f, Path("plotkit_report") / f.relative_to(OUT))
    return dst


if __name__ == "__main__":
    p = build()
    z = make_zip()
    import single_html
    single, _ = single_html.build()
    print(f"{single.relative_to(ROOT)}: {single.stat().st_size / 1e6:.1f} MB (one self-contained file)")
    print(f"report/final/index.html: {len(p) // 1024} kB, images: {len(list(IMG.glob('*.jpg')))}, "
          f"input pages: {len(list((OUT / 'inputs').glob('*.html')))}, zip: {z.relative_to(ROOT)} {z.stat().st_size // 1024} kB")
