"""python -m plotkit ...   (schema --json | --md: the standalone spec schema; anything else: plotkit.core's command line)"""
import sys

from .core import main


def _main(argv):
    if argv[:1] == ["schema"] and len(argv) > 1 and argv[1] in ("--json", "--md"):
        from . import schema
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(schema.dumps() if argv[1] == "--json" else schema.markdown())
        return 0
    return main(argv)


sys.exit(_main(sys.argv[1:]))
