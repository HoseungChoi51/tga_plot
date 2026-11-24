"""Sub-pages for the input files: what makes each one awkward, its first bytes, the file as written (separators and
odd cells made visible), and what plotkit's reader made of it. Written into <out>/inputs/, originals into
<out>/inputs/raw/. The main report only links to them.
"""
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # experiments/
sys.path.insert(0, str(ROOT.parent))                   # the library
sys.path.insert(0, str(ROOT / "eval"))
from paths import REPO, datapath  # noqa: E402         file names as the study wrote them (tests/..., eval/...)
esc = html.escape

# files shown in evidence cards: (path, used in cards, highlight values, hand-written notes)
CARD_FILES = [
    ("tests/inputs/instrument_export.txt", ["K2"], [], [
        "UTF-16 little-endian with a byte-order mark (FF FE): most tools that assume UTF-8 read it as noise.",
        "Windows line ends (CRLF), tab-separated.",
        "Ten metadata lines (file name, instrument, sample, method) before the numbers start.",
        "No header row: the column names are given as <code>Sig1 … Sig4</code> lines, and the data begins after a "
        "<code>StartOfData</code> marker.",
        "In K2 the raw scripts read it with <code>pd.read_csv(sep=r'\\s+')</code> and got nothing usable; plotkit's "
        "reader detects all of the above."]),
    ("eval/cnt/data/L3_MES_export_202607.csv", ["K16"], [], [
        "UTF-8 with a byte-order mark, Windows line ends.",
        "Four title and metadata lines and a blank line before the header row (line 6).",
        "Semicolon separators and decimal commas (<code>10,6</code> means 10.6), so a comma-separated reader splits "
        "every number in two.",
        "Dates written <code>2026.07.01</code>, a free-text note column (비고), and a summary line "
        "<code>총 119건</code> (“119 rows in total”) after the data.",
        "In K16 the raw script tried several encodings and <code>sep=None</code> and crashed in pandas' parser."]),
    ("eval/cnt/data/run_log.xlsx", ["K4"], ["-"], [
        "A clean-looking workbook with two sheets (런로그, 주간요약).",
        "The operator column (작업자) uses <code>-</code> for “no operator recorded”, once in 998 rows (highlighted).",
        "In K4 the raw script counted <code>-</code> as an operator and drew a 0.1% pie slice; the layer's reader "
        "treats it as missing."]),
]

# the reader's own test files (tests/inputs), each with one line on why it is awkward
TEST_FILES = {
    "TGA.xlsx": "The normal layout: three sheets, one of which stops at 750 °C (no residue at 800 °C).",
    "blank_rows_on_top.xlsx": "Blank rows and sample notes above the table, which starts in column B.",
    "different_wording.xlsx": "Unusual header wording for temperature, weight and DTG.",
    "extra_columns.xlsx": "Extra and reordered columns: index, time, mg and % weight, heat flow.",
    "instrument_export.txt": "UTF-16 instrument export with metadata lines and a StartOfData marker.",
    "korean_excel.csv": "A Korean Excel CSV in cp949 (not UTF-8).",
    "korean_headers.xlsx": "Korean column names.",
    "no_header.xlsx": "No header row at all: the columns are guessed from the values.",
    "old_format.xls": "The old binary Excel format (.xls).",
    "semicolon_decimal_comma.csv": "Semicolon separators and decimal commas.",
    "space_separated.txt": "Columns separated by runs of spaces.",
    "units_row.xlsx": "A units row under the header row.",
}

CSS_EXTRA = """
.bytes{font:12px var(--f-mono);background:var(--codebg);padding:8px 10px;border-radius:6px;overflow-x:auto;white-space:pre}
table.raw{font:12px/1.4 var(--f-mono);border-collapse:collapse;width:auto}
table.raw td{border-bottom:1px solid var(--line);padding:2px 8px;white-space:pre;vertical-align:top}
table.raw td.ln{color:var(--ink3);text-align:right;user-select:none}
.sep{color:var(--accent);font-weight:600}.mark{background:color-mix(in srgb,var(--warn) 35%,transparent);border-radius:2px}
.meta-line td{color:var(--ink2)}
table.grid td,table.grid th{font-size:12.5px;padding:3px 8px;white-space:nowrap}
.back{font-size:13.5px}
"""


def detect(raw):
    """(encoding, BOM description) by byte-order mark, then by trying utf-8 and cp949."""
    if raw[:2] == b"\xff\xfe":
        return "utf-16-le", "FF FE (UTF-16 little-endian)"
    if raw[:2] == b"\xfe\xff":
        return "utf-16-be", "FE FF (UTF-16 big-endian)"
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig", "EF BB BF (UTF-8)"
    for enc in ("utf-8", "cp949", "latin-1"):
        try:
            raw.decode(enc)
            return enc, "none"
        except UnicodeDecodeError:
            continue
    return "latin-1", "none"


def hexdump(raw, n=48):
    out = []
    for i in range(0, min(n, len(raw)), 16):
        chunk = raw[i:i + 16]
        hx = " ".join(f"{b:02X}" for b in chunk)
        tx = "".join(chr(b) if 32 <= b < 127 else "·" for b in chunk)
        out.append(f"{i:04X}  {hx:<47}  {tx}")
    return "\n".join(out)


def show_line(line):
    """A text line with tabs, semicolons and commas made visible."""
    s = esc(line).replace("\t", "<span class='sep'>⇥</span>")
    for ch in (";",):
        s = s.replace(ch, f"<span class='sep'>{ch}</span>")
    return s or "<span class='sep'>(blank)</span>"


def reader_summary(path):
    import plotkit
    try:
        info = plotkit.inspect_file(str(path))
    except Exception as e:  # noqa: BLE001
        return f"<p class='small'>inspect failed: {esc(str(e))}</p>"
    out = []
    for sh in info.get("sheets", []):
        cols = "".join(f"<tr><td>{esc(c['col'])}</td><td>{esc(str(c.get('name')))}</td><td class='num'>{esc(str(c.get('min', '')))}</td>"
                       f"<td class='num'>{esc(str(c.get('max', '')))}</td></tr>" for c in sh.get("columns", []))
        out.append(f"<h3>{esc(str(sh.get('name')))}</h3><p class='small'>header row(s): {esc(str(sh.get('header_rows')))} · "
                   f"first data row: {esc(str(sh.get('data_start_row')))} · data rows: {esc(str(sh.get('data_rows')))} · "
                   f"TGA columns: {esc(str(sh.get('tga_guess')))}</p>"
                   f"<div class='tw'><table class='grid'><tr><th>col</th><th>name</th><th class='num'>min</th><th class='num'>max</th></tr>{cols}</table></div>")
    return "".join(out)


def text_view(raw, enc, head=45, tail=3):
    text = raw.decode(enc)
    lines = text.splitlines()
    pick = list(enumerate(lines[:head], 1))
    rows = "".join(f"<tr><td class='ln'>{i}</td><td>{show_line(l)}</td></tr>" for i, l in pick)
    if len(lines) > head + tail:
        rows += f"<tr><td class='ln'>…</td><td class='small'>{len(lines) - head - tail} more lines</td></tr>"
        rows += "".join(f"<tr><td class='ln'>{i}</td><td>{show_line(l)}</td></tr>"
                        for i, l in enumerate(lines[-tail:], len(lines) - tail + 1))
    crlf = b"\r\n" in raw or b"\r\x00\n\x00" in raw
    return rows, len(lines), crlf


def xlsx_view(path, mark, max_rows=30):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = []
    for name in wb.sheetnames:
        ws = wb[name]
        rows = list(ws.iter_rows(values_only=True))
        body = []
        for i, r in enumerate(rows[:max_rows], 1):
            cells = "".join(f"<td class='{'mark' if v is not None and str(v) in mark else ''}'>{esc('' if v is None else str(v))}</td>" for v in r)
            body.append(f"<tr><td class='ln'>{i}</td>{cells}</tr>")
        more = f"<p class='small'>showing {min(max_rows, len(rows))} of {len(rows)} rows</p>"
        out.append(f"<h3>sheet: {esc(name)}</h3>{more}<div class='tw'><table class='grid raw'>{''.join(body)}</table></div>")
        if mark:
            hits = [(i, j) for i, r in enumerate(rows, 1) for j, v in enumerate(r) if v is not None and str(v) in mark]
            if hits:
                out.append(f"<p class='small'>cells equal to {esc(', '.join(mark))}: "
                           + ", ".join(f"row {i}, column {j + 1}" for i, j in hits[:20]) + "</p>")
    return "".join(out)


def page(css, title, body):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{esc(title)}</title><style>{css}{CSS_EXTRA}</style></head><body><main>{body}</main></body></html>")


def file_page(css, rel, cards, mark, notes):
    path = datapath(rel)
    name = path.name
    used = " · ".join(f"<a href='../index.html#{c}'>card {c}</a>" for c in cards) if cards else "the reader's test suite"
    parts = [f"<p class='back'><a href='index.html'>← all input files</a> · <a href='../index.html'>← report</a></p>",
             f"<h1>{esc(name)}</h1><p class='meta'>{esc(rel)} · {path.stat().st_size:,} bytes · used in {used} · "
             f"<a href='raw/{esc(name)}' download>download the original</a></p>"]
    if notes:
        parts.append("<h2>What makes it awkward</h2><ul>" + "".join(f"<li>{n}</li>" for n in notes) + "</ul>")
    raw = path.read_bytes()
    if path.suffix.lower() in (".xlsx", ".xls"):
        if path.suffix.lower() == ".xlsx":
            parts.append("<h2>The workbook as written</h2>" + xlsx_view(path, mark))
        else:
            parts.append("<h2>The workbook</h2><p class='small'>Old binary .xls: download it to open; the reader uses xlrd.</p>")
    else:
        enc, bom = detect(raw)
        rows, n, crlf = text_view(raw, enc)
        parts.append(f"<h2>The file as written</h2><p class='small'>encoding {esc(enc)} · byte-order mark: {esc(bom)} · "
                     f"{n} lines · line ends: {'CRLF (Windows)' if crlf else 'LF'} · "
                     "<span class='sep'>⇥</span> = tab, <span class='sep'>;</span> = semicolon</p>"
                     f"<h3>first bytes</h3><pre class='bytes'>{esc(hexdump(raw))}</pre>"
                     f"<h3>lines</h3><div class='tw'><table class='raw'>{rows}</table></div>")
    if "eval/cnt/" in rel:      # CNT runs showed the model chartkit's preview (eval/cnt_runs.py preview_text)
        import cnt_runs
        try:
            prev = cnt_runs.preview_text([str(Path(rel).relative_to("eval/cnt"))])
        except Exception as e:  # noqa: BLE001
            prev = f"preview failed: {e}"
        parts.append("<h2>What the layer's reader made of it</h2><p class='small'>The data preview chartkit built from this file: "
                     "the protocol and raw-code arms of the CNT study were shown exactly this text instead of the file.</p>"
                     f"<pre class='bytes'>{esc(prev)}</pre>")
    else:
        parts.append("<h2>What plotkit's reader made of it</h2><p class='small'>The output of <code>python plotkit.py inspect</code>, "
                     "which the arms of the TGA study were shown instead of the file.</p>" + reader_summary(path))
    return page(css, name, "".join(parts))


def build(out_dir, css):
    inp = Path(out_dir) / "inputs"
    shutil.rmtree(inp, ignore_errors=True)
    (inp / "raw").mkdir(parents=True)
    links = {}
    listed = []
    for rel, cards, mark, notes in CARD_FILES:
        p = datapath(rel)
        shutil.copy2(p, inp / "raw" / p.name)
        stem = p.stem
        (inp / f"{stem}.html").write_text(file_page(css, rel, cards, mark, notes), encoding="utf-8")
        for c in cards:
            links.setdefault(c, []).append((p.name, f"inputs/{stem}.html"))
        listed.append((p.name, f"{stem}.html", ", ".join(cards), notes[0] if notes else ""))
    for name, why in TEST_FILES.items():
        p = REPO / "tests" / "inputs" / name
        if not p.exists() or any(name == x[0] for x in listed):
            continue
        shutil.copy2(p, inp / "raw" / name)
        (inp / f"{p.stem}.html").write_text(file_page(css, f"tests/inputs/{name}", [], [], [why]), encoding="utf-8")
        listed.append((name, f"{p.stem}.html", "", why))
    rows = "".join(f"<tr><td><a href='{h}'>{esc(n)}</a></td><td>{esc(c) or '–'}</td><td>{w}</td><td><a href='raw/{esc(n)}' download>original</a></td></tr>"
                   for n, h, c, w in listed)
    idx = ("<p class='back'><a href='../index.html'>← report</a></p><h1>Input files</h1>"
           "<p>The files behind the evidence cards, and the awkward files in plotkit's reader test suite "
           "(<code>tests/inputs/</code>). Each page shows the file as written and what the reader made of it.</p>"
           f"<div class='tw'><table><tr><th>file</th><th>card</th><th>why it is awkward</th><th></th></tr>{rows}</table></div>")
    (inp / "index.html").write_text(page(css, "Input files", idx), encoding="utf-8")
    return links
