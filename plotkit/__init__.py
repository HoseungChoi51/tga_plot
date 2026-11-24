"""plotkit: a language model writes a small JSON spec; plotkit checks it against the data and draws it with ECharts
(live options or files) or matplotlib.

The app-facing API:

    plotkit.system_prompt()                     the model's system prompt (plotkit/prompts)
    plotkit.preview(files, base)                the data preview the model sees instead of the files
    plotkit.first_message(request, files, base) / followup_message(request)
    plotkit.parse_reply(text)                   the spec in the model's reply
    plotkit.retry_message(err)                  the turn that sends an error + hint back
    plotkit.request_options(reasoning)          thinking off by default (local models)
    plotkit.validate(spec, base)                check without drawing
    plotkit.echarts_options(spec, base)         live ECharts options (no files)
    plotkit.render(spec, out_dir, formats)      export files
    plotkit.agent.run(request, files, llm)      the reference loop around all of the above

Errors are plotkit.PlotkitError(message, hint). See docs/INTEGRATION.md.

Modules: core (reader, curve spec, matplotlib engine, router), charts (table charts), echarts (the ECharts engine
for curves and its patch allowlist), sandbox (the data_code hatch), schema (the standalone JSON Schema), agent and
api (the above), js/ (the Node side) and prompts/.
"""
from . import agent  # noqa: F401
from .agent import (first_message, followup_message, parse_reply, preview, request_options,  # noqa: F401
                    retry_message, system_prompt)
from .api import echarts_options, render, validate  # noqa: F401
from .core import (DEFAULTS, ENGINES, SCHEMA_DOC, PlotkitError, __version__, engine_name, inspect_file,  # noqa: F401
                   normalize_spec, plot)
