"""The six evaluation arms: one model, the same request and data preview, different ways to make the plot.

  P-mpl / P-ec           AGENT.md / AGENT_ECHARTS.md -> JSON spec -> plotkit (matplotlib / ECharts)
  R-mpl-plain / -brief   generic prompt (+ TGA brief) -> Python matplotlib script, run in a sandbox
  R-ec-plain / -brief    generic prompt (+ TGA brief) -> Python script printing ECharts options -> ECharts SSR

Every arm gets at most 2 retries with the error it caused (plotkit error+hint, or the script's traceback).
`run_arm` returns a record with the model calls, the final spec or script, the figure facts and timings.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import facts  # noqa: E402
import plotkit  # noqa: E402
import run_agent  # noqa: E402

ARMS = ("P-mpl", "P-ec", "R-mpl-plain", "R-mpl-brief", "R-ec-plain", "R-ec-brief")
PY = str(ROOT / ".venv" / "bin" / "python") if (ROOT / ".venv" / "bin" / "python").exists() else sys.executable
MPLCACHE = Path(os.environ.get("EVAL_MPLCACHE", HERE / "results" / ".mplcache"))

ENV_LINE = ("Environment: Python 3 with pandas, numpy, scipy, matplotlib, openpyxl and xlrd. "
            "Korean text needs a Korean font; \"Noto Sans CJK KR\" is installed. There is no internet.")

RAW_MPL = """You write Python scripts that draw plots with matplotlib for a lab team.
Users write in Korean.

Reply with the complete script inside one ```python block, and nothing else.
The script must:
- read the data file(s) given as DATA_FILE (or DATA_FILES) in the message (Excel, CSV or text files);
- draw what the user asks for and save the figure file(s) into OUT_DIR
  (PNG at 300 dpi unless the user asks for something else); do not call plt.show();
- run without asking anything: where the request is unclear, make a reasonable choice.
""" + ENV_LINE

RAW_EC = """You write Python scripts that turn lab data into Apache ECharts charts for a lab team.
Users write in Korean.

Reply with the complete script inside one ```python block, and nothing else.
The script reads the data file(s) given as DATA_FILE (or DATA_FILES) in the message (Excel, CSV or text files)
and prints ONE JSON document to stdout, and nothing else:
  {"figures": [{"name": "plot1", "option": {...}, "width": 614, "height": 442, "dpi": 300, "formats": ["png"]}]}
- "option": an Apache ECharts 6 option as plain JSON (no JavaScript functions); put the data in series.data.
- "width"/"height": the canvas in CSS pixels at 96 px per inch; "dpi": resolution of png/jpg/tif files;
  "formats": any of png, svg, pdf, jpg, tif. One entry per figure.
- The option is rendered server-side with ECharts 6.1 (SVG renderer) and saved as <name>.<format>.
Run without asking anything: where the request is unclear, make a reasonable choice.
""" + ENV_LINE

BRIEF = """

## The data and how plots are made here
The files are TGA (thermogravimetric analysis) runs: columns such as time, temperature (°C), weight (% or mg)
and derivative weight (DTG, %/°C, negative while mass is lost). Other x–y data can also come up.
A standard TGA plot here:
- x = temperature; left y axis (y1) = weight in % (line #1f4e9c); right y axis (y2) = DTG (line #c0392b),
  multiplied by -1 so its peaks point up; the plot title is the sheet name; legend at the center left.
- one plot per sheet; when no sheet is named, every sheet of the file.
- two labels are always drawn unless the user says otherwise:
  residue: the weight at the measured point nearest 800 °C, written like "Residue 8.0%", with a marker on the curve;
  peak: the temperature of the highest DTG peak above 150 °C, written like "600 °C", with a marker.
Part names users say (Korean -> plot part):
그림 제목 = title; x축/y1축/y2축 라벨 = axis labels (y1 = left, y2 = right; "y축" alone = y1); 틱 = tick marks;
틱 라벨 = tick numbers; 틱 간격 = tick spacing; 축 범위 = axis range; y1 선 / y2 선 = the left / right curve;
범례 = legend; 잔류량 표시 = residue label; 피크 표시 = DTG peak label; 보조선 = reference line; 격자 = grid;
시트 = sheet; 열 = column (users also say B행 / B칸 for Excel column B); 글자 색깔/크기 = text colour/size;
글꼴 = font; 그림 크기 = figure size in inches; 해상도 = dpi; 파일 형식 = file format; 겹쳐 그리기 = several sheets in one plot.
A setting that names no axis (e.g. "틱 라벨 크기 9") applies to x, y1 and y2."""


def system_prompt(arm):
    if arm == "P-mpl":
        return (ROOT / "AGENT.md").read_text(encoding="utf-8") + run_agent.SPEC_ONLY
    if arm == "P-ec":
        return (ROOT / "AGENT_ECHARTS.md").read_text(encoding="utf-8") + run_agent.SPEC_ONLY
    base = RAW_MPL if arm.startswith("R-mpl") else RAW_EC
    return base + (BRIEF if arm.endswith("brief") else "")


def inspect_text(files, protocol):
    """The same data preview for every arm (plotkit's inspect: sheets, columns, min/max, TGA column guess)."""
    parts = []
    for f in files:
        txt = plotkit.dumps(plotkit.inspect_file(f)).replace(str(f), Path(f).name)
        head = f'inspect 결과 (python plotkit.py inspect "{Path(f).name}")' if protocol else f"데이터 미리보기 ({Path(f).name})"
        parts.append(f"{head}:\n{txt}")
    return "\n\n".join(parts)


def user_message(arm, files, request, out_dir):
    if arm.startswith("P-"):
        return f"{inspect_text(files, True)}\n\n사용자 요청:\n{request}"
    loc = (f'DATA_FILE = "{files[0]}"' if len(files) == 1 else f"DATA_FILES = {json.dumps([str(f) for f in files])}")
    if arm.startswith("R-mpl"):
        loc += f'\nOUT_DIR = "{out_dir}"'
    return f"{inspect_text(files, False)}\n\n{loc}\n\n사용자 요청:\n{request}"


def extract_code(reply):
    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.S)
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", reply, flags=re.S)
    if m:
        return m.group(1)
    if "import " in reply and ("plt." in reply or "json" in reply):
        return reply.strip()
    raise ValueError("no ```python block in the reply")


# =================================================================== running code
def sandbox(cmd, run_dir, timeout=90, env_extra=None):
    """Run cmd with no network, read-only filesystem except run_dir and the matplotlib cache."""
    MPLCACHE.mkdir(parents=True, exist_ok=True)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(run_dir), "MPLBACKEND": "Agg", "MPLCONFIGDIR": str(MPLCACHE),
           "LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8", **(env_extra or {})}
    full = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
            "--bind", str(run_dir), str(run_dir), "--bind", str(MPLCACHE), str(MPLCACHE),
            "--unshare-net", "--die-with-parent", "--chdir", str(run_dir), *cmd]
    try:
        p = subprocess.run(full, capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        return -9, e.stdout or "", f"timed out after {timeout} s"


def tail(text, n=25):
    lines = [l for l in (text or "").strip().splitlines() if "Matplotlib created a temporary cache" not in l]
    return "\n".join(lines[-n:])


def run_mpl_script(code, run_dir):
    script = run_dir / "plot.py"
    script.write_text(code, encoding="utf-8")
    out = run_dir / "out"
    out.mkdir(exist_ok=True)
    fpath = run_dir / "facts.json"
    rc, so, se = sandbox([PY, "-I", str(HERE / "_runner.py"), str(script), str(fpath)], run_dir)
    figs = json.loads(fpath.read_text(encoding="utf-8"))["figures"] if fpath.exists() else []
    if rc != 0:
        return None, f"The script failed (exit {rc}):\n{tail(se)}"
    if not figs:
        return None, "The script ran but saved no figure into OUT_DIR (use fig.savefig / plt.savefig)."
    return figs, None


def run_ec_script(code, run_dir):
    script = run_dir / "make_option.py"
    script.write_text(code, encoding="utf-8")
    out = run_dir / "out"
    out.mkdir(exist_ok=True)
    rc, so, se = sandbox([PY, "-I", str(script)], run_dir)
    if rc != 0:
        return None, f"The script failed (exit {rc}):\n{tail(se)}"
    try:
        doc = json.loads(so.strip())
    except json.JSONDecodeError as e:
        start = so.find("{")
        try:
            doc = json.loads(so[start:]) if start >= 0 else None
        except json.JSONDecodeError:
            doc = None
        if doc is None:
            return None, f"stdout is not one JSON document ({e}); first 300 characters:\n{so[:300]}"
    if isinstance(doc, list):
        doc = {"figures": doc}
    if isinstance(doc, dict) and "option" in doc and "figures" not in doc:
        doc = {"figures": [doc]}
    (run_dir / "printed.json").write_text(json.dumps(doc, ensure_ascii=False)[:5_000_000], encoding="utf-8")
    dump = run_dir / "dump.json"
    try:
        p = subprocess.run(["node", str(HERE / "render_option.mjs")], input=json.dumps({"out_dir": str(out), **doc}),
                           capture_output=True, text=True, timeout=180,
                           env={**os.environ, "PLOTKIT_DUMP_OPTION": str(dump)})
        res = json.loads(p.stdout.strip().splitlines()[-1]) if p.stdout.strip() else {"ok": False, "error": tail(p.stderr, 5)}
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        res = {"ok": False, "error": str(e)}
    if not res.get("ok"):
        return None, f"ECharts could not render the printed option: {res.get('error')}"
    return facts.echarts_dump_facts(dump), None


# =================================================================== one request on one arm
def resolve_files(spec_files, files):
    """The spec's file name(s) -> real paths, as run_agent does (a name the model invented stays wrong)."""
    def pick(v):
        return str(files[0].parent / Path(str(v)).name)
    if isinstance(spec_files, list) and spec_files:
        return [pick(v) for v in spec_files]
    if spec_files:
        return pick(spec_files)
    return str(files[0]) if len(files) == 1 else [str(f) for f in files]


MAX_TOKENS = 16000          # same cap for every arm; writing a script takes Odin more thinking than a spec


EXTRA_BODY = {}             # e.g. {"chat_template_kwargs": {"enable_thinking": False}} (set by run_batch --no-think)


def call_llm(base, model, key, messages, max_tokens=MAX_TOKENS, temperature=0.6, timeout=1800):
    """run_agent.call_llm, but also returns the reasoning text (saved per call for diagnosis)."""
    import urllib.request
    body = {"model": model, "temperature": temperature, "max_tokens": max_tokens, "messages": messages, **EXTRA_BODY}
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key or 'none'}"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())
    msg = resp["choices"][0]["message"]
    u = resp.get("usage") or {}
    reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""
    think = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
    stats = {"llm_s": round(time.time() - t0, 2), "prompt_tokens": u.get("prompt_tokens"),
             "output_tokens": u.get("completion_tokens"), "thinking_tokens": think if think is not None else len(reasoning) // 3,
             "finish": resp["choices"][0].get("finish_reason")}
    return msg.get("content") or "", reasoning, stats


def run_arm(arm, files, request, run_dir, base, model, key, temperature=0.0, retries=2):
    run_dir = Path(run_dir)
    shutil.rmtree(run_dir, ignore_errors=True)
    run_dir.mkdir(parents=True)
    files = [Path(f) for f in files]
    out_dir = run_dir / "out"
    messages = [{"role": "system", "content": system_prompt(arm)},
                {"role": "user", "content": user_message(arm, files, request, out_dir)}]
    calls, errors, figs, final = [], [], None, None
    t0 = time.time()
    exec_s = 0.0
    for attempt in range(retries + 1):
        try:
            reply, reasoning, stats = call_llm(base, model, key, messages, temperature=temperature)
        except Exception as e:                       # network / server trouble: record and stop this run
            errors.append(f"model call failed: {e!r}")
            break
        calls.append(stats)
        (run_dir / f"reply_{attempt + 1}.txt").write_text(reply, encoding="utf-8")
        if reasoning:
            r = reasoning if len(reasoning) < 8000 else reasoning[:3000] + "\n[...]\n" + reasoning[-4000:]
            (run_dir / f"reasoning_{attempt + 1}.txt").write_text(r, encoding="utf-8")
        t1 = time.time()
        if arm.startswith("P-"):
            engine = "matplotlib" if arm == "P-mpl" else "echarts"
            try:
                spec = run_agent.extract_json(reply)
                spec["file"] = resolve_files(spec.get("file"), files)
                if isinstance(spec.get("output"), (dict, type(None))):
                    spec["output"] = {**(spec.get("output") or {}), "dir": str(out_dir)}
                final = spec
                _, figs = facts.plotkit_facts(spec, engine, run_dir / "dump.json")
                err = None
            except plotkit.PlotkitError as e:
                err = f"plotkit error: {e.message} | hint: {e.hint}"
            except (json.JSONDecodeError, ValueError) as e:
                err = f"your reply was not valid JSON: {e}"
            except Exception as e:                    # a plotkit crash is the protocol's failure too
                err = f"plotkit crashed: {e!r}"
            follow = "Reply with the corrected JSON spec only."
        else:
            try:
                code = extract_code(reply)
                final = code
                figs, err = (run_mpl_script if arm.startswith("R-mpl") else run_ec_script)(code, run_dir)
            except ValueError as e:
                err = str(e)
            follow = "Reply with the corrected complete script only, inside one ```python block."
        exec_s += time.time() - t1
        if err is None:
            break
        errors.append(err)
        figs = None
        messages += [{"role": "assistant", "content": reply}, {"role": "user", "content": f"{err}\n{follow}"}]
    rec = {"arm": arm, "ok_run": figs is not None, "calls": calls, "errors": errors, "final": final,
           "seconds": round(time.time() - t0, 2), "exec_seconds": round(exec_s, 2), "figures": figs or []}
    (run_dir / "record.json").write_text(json.dumps(rec, ensure_ascii=False, default=str), encoding="utf-8")
    return rec


# =================================================================== static look at raw scripts
RISKY = {"subprocess": r"\bsubprocess\b|os\.system|os\.popen", "network": r"\b(requests|urllib|socket|http\.client)\b",
         "delete": r"os\.remove|os\.unlink|shutil\.rmtree|\.unlink\(", "exec": r"\bexec\(|\beval\(",
         "write_outside": r"open\([^)]*['\"]w"}


def code_stats(code):
    if not isinstance(code, str):
        return {}
    lines = [l for l in code.splitlines() if l.strip() and not l.strip().startswith("#")]
    return {"loc": len(lines), **{k: int(bool(re.search(v, code))) for k, v in RISKY.items()}}
