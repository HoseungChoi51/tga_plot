"""E3: one turn of a simulated analysis session, for an agent that plays the engineer.

The engineer (a Claude session) asks for plots in Korean, one request per call; this script sends the request to the
local model with the session's history, draws the plot (up to 2 retries on errors) and prints what the engineer may
see: the saved image path(s) and the assistant's fixed Korean summary (no model writes it). State lives in
eval/results/sessions/<session>/state.json, so each call continues the same conversation.

    EVAL_API_KEY_FILE=... python experiments/eval/cnt_session.py --session G01_P-ec_r1 --arm P-ec --files data/run_log.xlsx "요청"
    OC_PASS_FILE=... python experiments/eval/cnt_session.py --base-url opencode --session G01_P-ec_r1 --arm P-ec "요청"   (via opencode)
    python experiments/eval/cnt_session.py --session G01_P-ec_r1 --files data/downtime.xlsx "다른 파일로 ..."   (later turns)
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))      # the library
sys.path.insert(0, str(HERE.parent))             # experiments/
sys.path.insert(0, str(HERE))
import cnt_runs  # noqa: E402

FILES = ["data/run_log.xlsx", "data/downtime.xlsx", "data/tga_batches.xlsx", "data/raman/*.csv", "data/r2_zone_temps.csv",
         "data/doe_temp_h2.csv", "data/diameters.csv", "data/L3_MES_export_202607.csv"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--arm", default="P-ec", choices=["P-mpl", "P-ec", "P-hyb"])
    ap.add_argument("--files", help="comma-separated data files the request is about (default: all)")
    ap.add_argument("--base-url", default="http://strixhalo:8084/v1")
    ap.add_argument("--model", default="qwen3.8-flash-next")
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("request")
    a = ap.parse_args()
    if a.base_url == "opencode":                    # Qwen3.8 Flash through opencode (eval/oc_llm.py)
        import oc_llm
        cnt_runs.call_llm = oc_llm.call_llm
        a.model = oc_llm.MODEL
    key =Path(os.path.expanduser(os.environ["EVAL_API_KEY_FILE"])).read_text().strip() if os.environ.get("EVAL_API_KEY_FILE") else ""
    sd = HERE / "results" / "sessions" / a.session
    sd.mkdir(parents=True, exist_ok=True)
    if not (sd / "data").exists():
        (sd / "data").symlink_to(cnt_runs.CNT / "data", target_is_directory=True)
    st_path = sd / "state.json"
    st = json.loads(st_path.read_text(encoding="utf-8")) if st_path.exists() else \
        {"arm": a.arm, "messages": [{"role": "system", "content": cnt_runs.system_prompt(a.arm)}], "turns": [], "seen_files": []}
    arm = st["arm"]
    files = a.files.split(",") if a.files else FILES
    new_files = [f for f in files if f not in st["seen_files"]]
    turn = len(st["turns"]) + 1
    t0 = time.time()
    msg = ""
    if new_files:
        msg = cnt_runs.preview_text(new_files) + "\n\n"
        st["seen_files"] += new_files
    msg += ("사용자 요청:\n" if turn == 1 else "사용자 요청 (이어서):\n") + a.request
    st["messages"].append({"role": "user", "content": msg})
    calls, result, spec = [], {"ok": False, "error": "no reply"}, None
    for attempt in range(3):
        text, _, stats = cnt_runs.call_llm(a.base_url, a.model, key, st["messages"], a.temperature, 3000)
        calls.append(stats)
        st["messages"].append({"role": "assistant", "content": text})
        try:
            spec = cnt_runs.extract_json(text)
            engine = "matplotlib" if arm == "P-mpl" or (arm == "P-hyb" and spec.get("code")) else "echarts"
            result, facts, draw_s = cnt_runs.draw_spec(spec, engine, sd, turn)
        except Exception as e:  # noqa: BLE001
            result = {"ok": False, "error": f"reply could not be read: {e}", "hint": "reply with one ```json block"}
        if result.get("ok"):
            break
        st["messages"].append({"role": "user", "content": f"plotkit error: {result.get('error')}\nhint: {result.get('hint', '')}\n\n고쳐서 다시 보내 주세요."})
    images = sorted(str(p) for p in (sd / "out" / f"t{turn}").glob("*.png")) if result.get("ok") else []
    if result.get("ok") and not result.get("summary"):
        import run_agent                      # the curve engine's fixed Korean summary
        result["summary"] = run_agent.summary_ko(result)
    summary = result.get("summary") if result.get("ok") else f"그래프를 만들지 못했습니다: {result.get('error')}"
    if result.get("ok") and result.get("not_done"):
        summary += "\n처리하지 못한 요청: " + "; ".join(result["not_done"])
    rec = {"turn": turn, "request": a.request, "files": files, "ok": bool(result.get("ok")), "images": images, "summary": summary,
           "spec": spec, "calls": calls, "turn_s": round(time.time() - t0, 2), "error": None if result.get("ok") else result.get("error")}
    st["turns"].append(rec)
    st_path.write_text(json.dumps(st, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"turn": turn, "ok": rec["ok"], "images": images, "summary": summary, "seconds": rec["turn_s"]},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
