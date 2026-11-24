"""Library tests: offline, no model calls. Run from the repo root: python -m pytest tests"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import importlib.util  # noqa: E402

import pytest  # noqa: E402

HAVE_MPL = importlib.util.find_spec("matplotlib") is not None
needs_mpl = pytest.mark.skipif(not HAVE_MPL, reason="the optional matplotlib engine is not installed")
ENGINES = ["echarts", pytest.param("matplotlib", marks=needs_mpl)]
