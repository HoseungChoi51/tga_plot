"""The model side of plotkit: the prompt, the messages, reading the reply, and a reference loop.

This is the protocol the studies settled on (experiments/eval/cnt_runs.py, layer v2), as functions an app can call:

    system = system_prompt()                              # plotkit/prompts: core.md + the engine's hatch
    msg = first_message("R3 반응기만 주차별 평균 수율", ["run_log.xlsx"])   # data preview + the request
    reply = <your model>(system, msg)                     # thinking off: request_options()
    spec = parse_reply(reply)                             # the JSON spec in the reply
    try:
        options = plotkit.echarts_options(spec)           # or plotkit.render(spec, out_dir)
    except plotkit.PlotkitError as e:
        msg = retry_message(e)                            # send back, at most twice; hide it from the user

run() does exactly that with an `llm` callable you supply. The library makes no network calls.
"""
import json
import re
from pathlib import Path

from .core import PlotkitError

PROMPTS = Path(__file__).resolve().parent / "prompts"
HATCH = {"echarts": "hatch_echarts.md", "matplotlib": "hatch_matplotlib.md"}
RETRIES = 2


# =================================================================== the prompt and the messages
def system_prompt(engine="echarts"):
    """The system prompt: core.md (the spec, the asks, the examples) + the engine's escape hatch."""
    if engine not in HATCH:
        raise PlotkitError(f"unknown engine {engine!r}", "use echarts or matplotlib")
    return (PROMPTS / "core.md").read_text(encoding="utf-8") + (PROMPTS / HATCH[engine]).read_text(encoding="utf-8")


def preview(files, base=None):
    """The data preview the model sees instead of the files: per file and sheet, the rows and every column with its
    letter, type and range or values ("데이터 미리보기: ..."). files: paths (glob patterns allowed); they are shown
    relative to base (default: as given), which is also where relative paths are read from."""
    from . import charts
    base = Path(base) if base is not None else None
    parts = []
    for f in files:
        p = (base / f) if base is not None else Path(f)
        paths = sorted(p.parent.glob(p.name)) if any(c in str(f) for c in "*?") else [p]
        lines = []
        for path in paths:
            rel = path.relative_to(base).as_posix() if base is not None and path.is_relative_to(base) else path.as_posix()
            try:
                pv = charts.preview(str(path))
            except Exception as e:  # noqa: BLE001 - the model is told the file could not be read
                lines.append(f"파일 {rel}: 읽기 실패 ({e})")
                continue
            sheets = pv["sheets"]
            lines.append(f"파일 {rel}" + (f" (시트 {len(sheets)}개)" if len(sheets) > 1 else ""))
            for sh in sheets[:12]:
                if "error" in sh:
                    lines.append(f"  시트 '{sh['sheet']}': {sh['error']}")
                    continue
                cols = []
                for c in sh["columns"]:
                    if c["type"] == "number":
                        d = f"{c['col']} {c['name']} [수치 {c['min']}~{c['max']}" + (f"; 값 {c['values']}" if c.get("values") else "") + "]"
                    elif c["type"] == "date":
                        d = f"{c['col']} {c['name']} [날짜 {c['min']}~{c['max']}]"
                    else:
                        d = f"{c['col']} {c['name']} [텍스트 {c['n_values']}종: {', '.join(map(str, c['values']))}]"
                    cols.append(d)
                lines.append(f"  시트 '{sh['sheet']}' ({sh['rows']}행): " + " | ".join(cols))
            if len(sheets) > 12:
                lines.append(f"  … 시트 {len(sheets) - 12}개 더: " + ", ".join(s["sheet"] for s in sheets[12:]))
        parts.append("\n".join(lines))
    return "데이터 미리보기:\n" + "\n".join(parts)


def first_message(request, files, base=None):
    """The first user turn: the data preview, then the request."""
    return f"{preview(files, base)}\n\n사용자 요청:\n{request}"


def followup_message(request, last_spec=None):
    """A later turn on the same plot. The reference loop keeps the chat history, so the model sees its last spec
    there; pass last_spec only when your app does not send the history (the spec then goes in this turn)."""
    head = "" if last_spec is None else \
        "지금 그림의 spec:\n```json\n" + json.dumps(last_spec, ensure_ascii=False, indent=1) + "\n```\n\n"
    return f"{head}사용자 요청 (이어서):\n{request}"


def reply_json(text):
    """The JSON text in a model reply: <think> blocks dropped, the first ```json block, else the outermost {...}."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    m = re.search(r"```(?:json)?\s*\n(.*?)```", text, flags=re.S)
    return m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]


def parse_reply(text):
    """The spec in a model reply (see reply_json). Raises PlotkitError, to send back with retry_message, when the
    reply holds no JSON object."""
    try:
        spec = json.loads(reply_json(text))
    except json.JSONDecodeError as e:
        raise PlotkitError(f"your reply could not be read: {e}", "reply with one ```json block")
    if not isinstance(spec, dict):
        raise PlotkitError("your reply could not be read: the JSON is not an object", "reply with one ```json block")
    return spec


def retry_message(err):
    """The turn that sends an error back to the model: plotkit's message and hint, and a request to fix it.
    err: a PlotkitError, or a dict with "error" and "hint" (a result with ok false)."""
    msg, hint = (err.message, err.hint) if isinstance(err, PlotkitError) else (err.get("error", ""), err.get("hint", ""))
    return f"plotkit error: {msg}" + (f"\nhint: {hint}" if hint else "") + "\n\n고쳐서 다시 보내 주세요."


def request_options(reasoning=False):
    """Extra request-body fields for a locally served model (llama.cpp, vLLM, SGLang; Qwen-style chat templates):
    thinking off unless the user asks for it (the app's "think harder" toggle passes reasoning=True). Merge them into
    the request; "/no_think" in the prompt does not switch Qwen's thinking off, this flag does."""
    return {"chat_template_kwargs": {"enable_thinking": bool(reasoning)}}


# =================================================================== the reference loop
def run(request, files, llm, reasoning=False, history=None, engine="echarts", base=None, retries=RETRIES,
        allow_unsandboxed=None):
    """One user request -> the spec and its live ECharts options (nothing is written to disk).

    llm(messages, **options) -> the reply text. messages are chat messages ({"role", "content"}: system, user,
        assistant); options are request_options(reasoning), to merge into your request. Your
        function adds the model name, the endpoint and the rest.
    files: the data files, as the user named them; base: the folder they are in (default: the current one).
    history: the "transcript" of an earlier run() on the same plot; the request is then a follow-up turn.
    engine: the escape hatch the model is shown, "echarts" (recommended) or "matplotlib". The options are ECharts
        either way; render() draws files with either engine.

    Returns {"ok", "spec", "options", "warnings", "not_done", "values", "error", "hint", "attempts", "transcript"}.
    The spec is as the model wrote it. When every attempt fails, ok is false and error/hint say why."""
    from . import api
    opts = request_options(reasoning)
    if history:
        messages = list(history) + [{"role": "user", "content": followup_message(request)}]
    else:
        messages = [{"role": "system", "content": system_prompt(engine)},
                    {"role": "user", "content": first_message(request, files, base)}]
    spec, err = None, None
    for attempt in range(1, retries + 2):
        reply = llm(messages, **opts)
        messages.append({"role": "assistant", "content": reply})
        try:
            spec = parse_reply(reply)
            res = api.echarts_options(spec, base, full=True, allow_unsandboxed=allow_unsandboxed)
        except PlotkitError as e:
            err = e
            if attempt <= retries:
                messages.append({"role": "user", "content": retry_message(e)})
            continue
        return {"ok": True, "spec": spec, "options": res["options"], "warnings": res["warnings"],
                "not_done": res["not_done"], "values": res["values"], "error": None, "hint": None,
                "attempts": attempt, "transcript": messages}
    return {"ok": False, "spec": spec, "options": [], "warnings": [], "not_done": [], "values": {},
            "error": err.message, "hint": err.hint, "attempts": retries + 1, "transcript": messages}
