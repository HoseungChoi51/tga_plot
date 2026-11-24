// The chart port against the Python goldens (draw_charts): the model after layout, the static ECharts option and
// size, the live result (options, values, warnings, not_done, rows) and the SVG where Python rendered one.
import { test } from "node:test";
import assert from "node:assert/strict";
import { golden, decode, diff } from "./golden.ts";
import { buildModel, echartsOption, layout, liveResult, summaryValues, koreanSummary } from "../src/charts.ts";
import { renderChartSvg } from "../src/chart_render.ts";
import { parseTimestamp } from "../src/chartdata.ts";
import { PlotkitError } from "../src/errors.ts";
import type { Dtype, Frame } from "../src/types.ts";

/** Cases whose Python result the port can not reproduce, with the reason. */
const EXPECTED: Record<string, string> = {};

const DTYPES: Record<string, Dtype> = { float64: "float", int64: "int", bool: "bool", object: "object", str: "object" };

function toFrame(f: any): Frame {
  const dtypes = (f.dtypes as string[]).map(d => d.startsWith("datetime64") ? "datetime" : DTYPES[d]);
  const data = (f.columns as string[]).map((c, j) => (f.data[c] as any[]).map(v => {
    const d = dtypes[j];
    if (d === "datetime") return v === null ? NaN : parseTimestamp(v.$date);
    if (d === "float" || d === "int") return v === null ? NaN : v;
    return v;
  }));
  return { columns: f.columns, dtypes, data, letters: f.letters };
}

const cases = golden("draw_charts").filter((c: any) => c.frame);

function run(c: any): string[] {
  const spec = decode(c.norm_full);
  const frame = toFrame(c.frame);
  if (c.draw_error || c.draw_crash) {
    try {
      const model = layout(spec, buildModel(spec, frame));
      echartsOption(spec, model);
      liveResult(spec, frame);
    } catch (e) {
      if (!(e instanceof PlotkitError)) return [`threw ${e}`];
      if (c.draw_crash) return [];
      const out: string[] = [];
      if (e.message !== c.draw_error.error) out.push(`error: ${e.message} != ${c.draw_error.error}`);
      if (e.hint !== c.draw_error.hint) out.push(`hint: ${e.hint} != ${c.draw_error.hint}`);
      return out;
    }
    return ["no error raised"];
  }
  const out: string[] = [];
  const model = layout(spec, buildModel(spec, frame));
  out.push(...diff(model, c.model, "model"));
  const [opt, size] = echartsOption(spec, model);
  out.push(...diff(opt, c.static_option, "static_option"));
  out.push(...diff(size, c.size_px, "size_px"));
  const res = liveResult(spec, frame);
  const want = { ...c.result };
  out.push(...diff(res, want, "result"));
  out.push(...diff(summaryValues(model), c.result.values, "values"));
  koreanSummary(model, res.values, ["chart.png"], res.not_done, res.warnings);
  if (c.svg) {
    const svg = renderChartSvg(spec, model);
    if (svg !== c.svg[0]) {
      let i = 0;
      while (i < svg.length && svg[i] === c.svg[0][i]) i++;
      out.push(`svg differs at ${i}: ${JSON.stringify(svg.slice(i - 40, i + 80))} != ${JSON.stringify(c.svg[0].slice(i - 40, i + 80))}`);
    }
  }
  return out;
}

test("draw_charts goldens", async t => {
  for (const c of cases) {
    await t.test(c.id, () => {
      let problems: string[];
      try {
        problems = run(c);
      } catch (e) {
        problems = [`threw ${e instanceof PlotkitError ? `PlotkitError: ${e.message} / ${e.hint}` : (e as Error)?.stack ?? e}`];
      }
      if (EXPECTED[c.id]) {
        assert.ok(problems.length > 0, `${c.id} is marked as an expected difference but now matches`);
        return;
      }
      assert.deepEqual(problems, []);
    });
  }
});
