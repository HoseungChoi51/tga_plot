// End to end through the public API: the spec as the model wrote it + the folder's files as {name, bytes} ->
// the same result as the Python plotkit (api.echarts_options / api.render): options, values, warnings, not_done,
// or the same error and hint; and the same SVG where the goldens hold one.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { BASES, diff, golden } from "./golden.ts";
import { echartsOptions, renderSvg, PlotkitError } from "../src/index.ts";
import type { InputFile } from "../src/index.ts";

const FILES = new Map<string, InputFile[]>();
function filesOf(base: string): InputFile[] {
  if (!FILES.has(base)) {
    const root = BASES[base], out: InputFile[] = [];
    const walk = (d: string) => {
      for (const n of readdirSync(d)) {
        const p = join(d, n);
        if (statSync(p).isDirectory()) walk(p);
        else out.push({ name: relative(root, p).split(sep).join("/"), bytes: readFileSync(p) });
      }
    };
    walk(root);
    FILES.set(base, out);
  }
  return FILES.get(base)!;
}

const strip = (r: any) => { const { saved: _s, ...rest } = r; return rest; };

for (const name of ["draw_curves", "draw_charts"]) {
  test(`${name}: every drawn case gives Python's result`, async () => {
    const bad: string[] = [];
    let n = 0;
    for (const c of golden(name)) {
      if (!("result" in c) && !("draw_error" in c) && !("draw_crash" in c)) continue;    // data_code / code cases
      n++;
      const files = filesOf(c.base);
      try {
        const got = await echartsOptions(c.spec, files);
        if (!("result" in c)) { bad.push(`${c.id}: drew, Python said ${JSON.stringify(c.draw_error ?? c.draw_crash).slice(0, 120)}`); continue; }
        const d = diff(strip(got), strip(c.result));
        if (d.length) bad.push(`${c.id}: ${d.slice(0, 3).join("; ")}`);
      } catch (e) {
        if (!(e instanceof PlotkitError)) { bad.push(`${c.id}: crashed: ${(e as Error).stack?.split("\n").slice(0, 3).join(" ")}`); continue; }
        if (c.draw_crash) continue;                                                      // Python crashed: TS answers an error
        if (!c.draw_error) { bad.push(`${c.id}: error ${e.message} | ${e.hint}`); continue; }
        if (e.message !== c.draw_error.error || e.hint !== c.draw_error.hint) {
          bad.push(`${c.id}: error ${e.message} | ${e.hint} != ${c.draw_error.error} | ${c.draw_error.hint}`);
        }
      }
      if (bad.length > 15) break;
    }
    assert.ok(n > 200, `only ${n} cases`);
    assert.deepEqual(bad, []);
  });

  test(`${name}: SVG equals Python's`, async () => {
    const bad: string[] = [];
    for (const c of golden(name).filter((x: any) => x.svg)) {
      const r = await renderSvg(c.spec, filesOf(c.base));
      const got = r.files.map(f => f.svg);
      if (got.length !== c.svg.length || got.some((s, i) => s !== c.svg[i])) bad.push(c.id);
    }
    assert.deepEqual(bad, []);
  });
}
