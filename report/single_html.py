"""Pack report/final/ (index.html, img/, inputs/) into one self-contained HTML file.

    python report/single_html.py      -> report/plotkit_report.html

Images become data URIs; each input-file page becomes a sub-page inside the same file (opened by its link, shown
in place of the report; the browser's back button returns); the original input files become embedded downloads.
"""
import base64
import mimetypes
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "report" / "final"
DST = ROOT / "report" / "plotkit_report.html"
MIME = {".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xls": "application/vnd.ms-excel",
        ".csv": "text/csv", ".txt": "text/plain", ".jpg": "image/jpeg", ".png": "image/png"}


def data_uri(path):
    mime = MIME.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def main_of(html):
    m = re.search(r"<main>(.*)</main>", html, re.S)
    return m.group(1) if m else html


def style_of(html):
    m = re.search(r"<style>(.*?)</style>", html, re.S)
    return m.group(1) if m else ""


def sub_id(stem):
    return f"input-{re.sub(r'[^A-Za-z0-9_-]+', '-', stem)}"


def build():
    index = (SRC / "index.html").read_text(encoding="utf-8")
    head = index.split("<main>", 1)[0]
    pages = sorted((SRC / "inputs").glob("*.html"))
    extra_css = style_of(pages[0].read_text(encoding="utf-8")) if pages else ""
    css = style_of(index)
    # the sub-pages' extra rules (everything after the shared stylesheet)
    if extra_css.startswith(css[:200]):
        extra_css = extra_css[len(css):] if extra_css.startswith(css) else extra_css
    body = main_of(index)

    # images -> data URIs
    def img_repl(m):
        p = SRC / m.group(2)
        return f"{m.group(1)}{data_uri(p)}{m.group(3)}" if p.exists() else m.group(0)
    body = re.sub(r"(src=')(img/[^']+)(')", img_repl, body)
    # links from the report to input pages
    body = re.sub(r"href='inputs/index\.html'", "href='#input-index'", body)
    body = re.sub(r"href='inputs/([^'#]+)\.html'", lambda m: f"href='#{sub_id(m.group(1))}'", body)

    subs = []
    for p in pages:
        sid = "input-index" if p.stem == "index" else sub_id(p.stem)
        b = main_of(p.read_text(encoding="utf-8"))
        b = re.sub(r"href='\.\./index\.html#([^']+)'", r"href='#\1'", b)
        b = re.sub(r"href='\.\./index\.html'", "href='#top'", b)
        b = re.sub(r"href='index\.html'", "href='#input-index'", b)
        b = re.sub(r"href='(?!#|https?:|data:)([^'/]+)\.html'", lambda m: f"href='#{sub_id(m.group(1))}'", b)

        def raw_repl(m):
            f = SRC / "inputs" / "raw" / m.group(1)
            return f"href='{data_uri(f)}' download='{m.group(1)}'" if f.exists() else m.group(0)
        if p.stem == "index":          # the index links each original via its own page, so each file is embedded once
            b = re.sub(r"<a href='raw/([^']+)' download>original</a>",
                       lambda m: f"<a href='#{sub_id(Path(m.group(1)).stem)}'>view and download</a>", b)
        b = re.sub(r"href='raw/([^']+)' download", raw_repl, b)
        b = re.sub(r"href='raw/([^']+)'", lambda m: raw_repl(m) if (SRC / "inputs" / "raw" / m.group(1)).exists() else m.group(0), b)
        subs.append(f"<section class='subpage' id='{sid}'>{b}</section>")

    script = """<script>
(function(){
  function show(){
    var h = decodeURIComponent(location.hash.slice(1));
    var sub = h.indexOf('input-') === 0 ? document.getElementById(h) : null;
    document.getElementById('report').style.display = sub ? 'none' : '';
    var all = document.querySelectorAll('.subpage');
    for (var i = 0; i < all.length; i++) all[i].style.display = (all[i] === sub) ? 'block' : 'none';
    if (sub) window.scrollTo(0, 0);
    else if (h && h !== 'top') { var t = document.getElementById(h); if (t) t.scrollIntoView(); }
    else window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', show);
  document.addEventListener('DOMContentLoaded', show);
})();
</script>"""
    css_all = css + extra_css + "\n.subpage{display:none}.subpage:target{display:block}"
    head = re.sub(r"<style>.*?</style>", lambda _: f"<style>{css_all}</style>", head, count=1, flags=re.S)
    page = (head + f"<main><div id='top'></div><div id='report'>{body}</div>{''.join(subs)}</main>{script}</body></html>")
    DST.write_text(page, encoding="utf-8")
    return DST, len(pages)


if __name__ == "__main__":
    dst, n = build()
    print(f"{dst.relative_to(ROOT)}: {dst.stat().st_size / 1e6:.1f} MB, {n} input sub-pages")
