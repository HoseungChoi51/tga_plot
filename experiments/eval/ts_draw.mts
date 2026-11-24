// Draw one spec with plotkit-ts (the TypeScript build, no Python) for the P-ts arm of cnt_runs.py.
//
//   node experiments/eval/ts_draw.mts <spec.json> <result.json> <dump.json> <out_dir>      (cwd: the run folder)
//
// The run folder's files (its data/ link) are handed over as {name, bytes}; data_code runs in QuickJS. Writes
// {"result": plotkit-ts's reply or {"ok": false, "error", "hint"}, "draw_s"} like cnt_draw.py, the figures' SVG to
// out_dir, and what was drawn (dump.mjs chartFacts per figure) for the figure-facts checker.
// PLOTKIT_TS: the plotkit-ts checkout, branch lib/plotkit-ts (default: .worktrees/plotkit-ts of this repo).
import { mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chartFacts } from "../../plotkit/js/dump.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const tsRoot = resolve(process.env.PLOTKIT_TS ?? join(here, "..", "..", ".worktrees", "plotkit-ts"));
const pk = await import(pathToFileURL(join(tsRoot, "src", "index.ts")).href);

const [specPath, resultPath, dumpPath, outDir] = process.argv.slice(2);
const files: { name: string; bytes: Uint8Array }[] = [];
const walk = (d: string) => {
  for (const n of readdirSync(d)) {
    const p = join(d, n);
    if (statSync(p).isDirectory()) { if (n !== "out") walk(p); }
    else if (!/^(spec|draw)_t\d+/.test(n) && n !== "record.json") files.push({ name: relative(process.cwd(), p).split(sep).join("/"), bytes: readFileSync(p) });
  }
};
walk(process.cwd());

const spec = JSON.parse(readFileSync(specPath, "utf8"));
const dump: unknown[] = [];
const t0 = performance.now();
let result: Record<string, unknown>;
try {
  const r = await pk.renderSvg(spec, files, {
    runCode: pk.quickjsRunCode(),
    onChart: (chart: unknown, info: { W: number; H: number; size_in: number[]; dpi: number }) =>
      dump.push({ ...chartFacts(chart), W: info.W, H: info.H, size_in: info.size_in, dpi: info.dpi, outputs: [] }),
  });
  mkdirSync(outDir, { recursive: true });
  const saved: string[] = [];
  r.files.forEach((f: { name: string; svg: string }, i: number) => {
    const p = join(outDir, `${f.name}.svg`);
    writeFileSync(p, f.svg);
    saved.push(p);
    const d = dump[i] as { outputs: unknown[] } | undefined;
    if (d) d.outputs.push({ format: "svg", path: p });
  });
  const { files: _f, ...rest } = r;
  result = { ...rest, saved };
} catch (e) {
  const err = e as { message?: string; hint?: string; name?: string };
  result = e instanceof pk.PlotkitError ? { ok: false, error: err.message, hint: err.hint }
    : { ok: false, error: `${err.name}: ${err.message}`, hint: "", crash: true };
}
const drawS = (performance.now() - t0) / 1000;
writeFileSync(resultPath, JSON.stringify({ result, draw_s: drawS }));
writeFileSync(dumpPath, JSON.stringify({ figures: dump }));
