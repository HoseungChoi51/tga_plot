"""plotkit: an LLM writes a small JSON spec, plotkit draws it (ECharts or matplotlib).

Modules: core (reader, curve spec, matplotlib engine, router), charts (table charts), echarts (the ECharts
engine for curves and its patch allowlist), sandbox (the data_code hatch). Node scripts are in plotkit/js,
the model's system prompt in plotkit/prompts.
"""
from .core import (DEFAULTS, ENGINES, SCHEMA_DOC, PlotkitError, __version__, engine_name, inspect_file,  # noqa: F401
                   normalize_spec, plot)
