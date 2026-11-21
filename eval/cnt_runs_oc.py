"""cnt_runs.py with the model calls sent to Qwen3.8 Flash through opencode (eval/oc_llm.py) instead of strixhalo.

    OC_PASS_FILE=... python eval/cnt_runs_oc.py --split sealed --name sealed_oc --arms P-mpl,P-ec,P-hyb,R-mpl --repeat 3 --workers 6
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cnt_runs  # noqa: E402
import oc_llm  # noqa: E402

cnt_runs.call_llm = oc_llm.call_llm
if "--model" not in sys.argv:
    sys.argv += ["--model", oc_llm.MODEL, "--base-url", "opencode"]
cnt_runs.main()
