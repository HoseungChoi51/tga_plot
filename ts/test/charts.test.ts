// The chart port against the Python goldens (draw_charts): the model after layout, the static ECharts option and
// size, the live result (options, values, warnings, not_done, rows) and the SVG where Python rendered one.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { golden, decode, diff, BASES } from "./golden.ts";
import { buildModel, echartsOption, layout, liveResult, summaryValues, koreanSummary } from "../src/charts.ts";
import { echartsOptions } from "../src/api.ts";
import { normalizeChart } from "../src/chartspec.ts";
import { loadFrame } from "../src/frame.ts";
import { renderChartSvg } from "../src/chart_render.ts";
import { parseTimestamp } from "../src/chartdata.ts";
import { PlotkitError } from "../src/errors.ts";
import type { Dtype, Frame, InputFile } from "../src/types.ts";

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

// ------------------------------------------------------------------ the chart fixes (as tests/test_chart_fixes.py)
const INPUTS = BASES["tests/inputs"];
const FILES: InputFile[] = ["missing_values.csv", "run_log.csv"].map(name => ({ name, bytes: new Uint8Array(readFileSync(join(INPUTS, name))) }));
const M = "missing_values.csv";              // blanks in 날짜 (2), 일 (1), 그룹 (13), x값 (5), xu (1), y값 (9), g1 (1)

const live = (spec: object): Promise<any> => echartsOptions(spec, FILES);

async function model(spec: object): Promise<[any, any]> {
  const s = normalizeChart(spec, FILES.map(f => f.name));
  return [s, buildModel(s, await loadFrame(s as any, FILES))];
}

async function error(spec: object): Promise<PlotkitError> {
  try {
    await live(spec);
  } catch (e) {
    if (e instanceof PlotkitError) return e;
    throw e;
  }
  throw new Error(`no error for ${JSON.stringify(spec)}`);
}

test("1. layout never takes a raw spec value as a number", async () => {
  for (const [key, bad] of [["point_size", "가동시간 (h)"], ["alpha", [0.5]]] as const) {
    const [s, m] = await model({ file: M, chart: "scatter", x: "x값", y: "y값" });
    s[key] = bad;                                      // as if normalize had let it through
    assert.throws(() => layout(s, m), (e: any) => e instanceof PlotkitError && e.message.startsWith(`"${key}" must be a number`));
  }
  const [s, m] = await model({ file: M, chart: "scatter", x: "x값", y: "y값", point_size: 30, alpha: 0.5 });
  const lm = layout(s, m);
  assert.deepEqual([lm.point_size, lm.point_alpha], [30, 0.5]);
  assert.equal((await error({ file: M, chart: "line", x: { col: "x값", rotate: "abc" }, y: "y값" })).message, "\"x.rotate\" must be a number, not 'abc'");
  const zero = await live({ file: M, chart: "scatter", x: "x값", y: "y값", alpha: 0 });
  assert.equal(zero.options[0].series[0].itemStyle.opacity, 0);
  assert.equal((await live({ file: M, chart: "scatter", x: "x값", y: "y값" })).options[0].series[0].itemStyle.opacity, 0.9);
});

test("2. bins 1 is one bin; corr 1 is an error", async () => {
  assert.equal((await live({ file: M, chart: "histogram", x: "y값", bins: 1 })).values.bins, 1);
  assert.equal((await live({ file: M, chart: "histogram", x: "y값", bins: true })).values.bins, 7);
  assert.equal((await error({ file: M, chart: "histogram", x: "y값", bins: 0.5 })).message, '"bins" must be a number of bins (1 or more), not 0.5');
  const e = await error({ file: M, chart: "heatmap", corr: 1 });
  assert.equal(e.message, '"corr" must be a list of columns or "all", not 1');
  assert.ok(e.hint.includes('"all"'));
  assert.deepEqual((await live({ file: M, chart: "heatmap", corr: true })).values.cols, ["x값", "xu", "y값", "y2", "정수x"]);
  assert.equal((await error({ file: M, chart: "heatmap", corr: ["x값", "라벨"] })).message, 'corr: "라벨" is not a numeric column');
});

test("3. aggregates of text", async () => {
  for (const how of ["mean", "sum", "median", "min", "max", "std"]) {
    for (const extra of [{ chart: "bar", y: { col: "라벨", agg: how } }, { chart: "pie", y: { col: "라벨", agg: how } },
                         { chart: "heatmap", y: "g1", z: { col: "라벨", agg: how } }]) {
      const e = await error({ file: M, x: "그룹", ...extra });
      assert.equal(e.message, `cannot take the ${how} of "라벨": it holds text`);
      assert.equal(e.hint, "use count or nunique, or a numeric column");
    }
  }
  assert.equal((await error({ file: M, chart: "bar", x: "그룹", y: { col: "날짜", agg: "max" } })).message, 'cannot take the max of "날짜": it holds dates');
  assert.equal((await error({ file: M, chart: "bar", x: "그룹", y: "라벨" })).message, 'cannot take the mean of "라벨": it holds text');
  assert.deepEqual((await live({ file: M, chart: "bar", x: "그룹", y: { col: "라벨", agg: "nunique" } })).values.series["라벨"], [8, 5, 5]);
  assert.deepEqual((await live({ file: M, chart: "bar", x: "그룹", y: { col: "라벨", agg: "count" } })).values.series["라벨"], [19, 14, 14]);
  const first = await live({ file: M, chart: "bar", x: "그룹", y: { col: "라벨", agg: "first" }, filter: "라벨 in [10, 2.5]" });
  assert.deepEqual(first.values.series["라벨"], [2.5, 10, 2.5]);
  assert.equal((await error({ file: M, chart: "bar", x: "그룹", y: { col: "라벨", agg: "last" } })).message, '"라벨" holds text, not numbers');
});

test("4. bins with min and max do not read the data", async () => {
  const oneRow = "y2 == 39.39";                         // the one row with y2 39.39 has no y값
  const r = await live({ file: M, chart: "histogram", x: "y값", bins: { width: 1, min: 0, max: 4 }, filter: oneRow });
  assert.deepEqual(r.values, { bins: 4, series: { "y값": { n: 0, mean: null } } });
  const [, m] = await model({ file: M, chart: "histogram", x: "y값", bins: { width: 2, min: 0, max: 6 } });
  assert.deepEqual(m.edges, [0, 2, 4, 6]);
  const e = await error({ file: M, chart: "histogram", x: "y값", bins: { width: 1 }, filter: oneRow });
  assert.deepEqual([e.message, e.hint], ["no numbers to bin", 'give "min" and "max" with the width, or check the filters']);
  assert.equal((await error({ file: M, chart: "histogram", x: "y값", bins: [3, 1, 5] })).message, '"bins" must be two or more increasing edges, not [3, 1, 5]');
  assert.equal((await error({ file: M, chart: "histogram", x: "y값", bins: { closed: "right" } })).message,
    '"bins" needs a "width" (or give a number of bins, or a list of edges)');
});

test("5. a pie legend has no dummy entry", async () => {
  for (const extra of [{ by: "반응기" }, { legend: { where: "outside right", title: "반응기" } }]) {
    const opt = (await live({ file: "run_log.csv", chart: "pie", x: "반응기", legend: "outside right", ...extra })).options[0];
    assert.ok(!JSON.stringify(opt).includes("_legend_dummy"));
    assert.deepEqual(opt.legend.data, opt.series[0].data.map((d: any) => d.name));
  }
  const bar = (await live({ file: "run_log.csv", chart: "bar", x: "등급", y: "수율", by: "반응기" })).options[0];
  const names = new Set(bar.series.map((s: any) => s.name));
  assert.ok(bar.legend.data.every((d: any) => names.has(typeof d === "string" ? d : d.name)));     // the title too
});

test("6. missing category values are left out, with a note", async () => {
  const cases: [object, string, number][] = [
    [{ chart: "bar", x: "그룹", y: "y값" }, "13 rows with no 그룹 left out", 47],
    [{ chart: "bar", x: "g1", y: "y값" }, "1 row with no g1 left out", 59],
    [{ chart: "line", x: "xu", y: "y값" }, "1 row with no xu left out", 59],
    [{ chart: "line", x: "x값", y: "y값" }, "5 rows with no x값 left out", 55],
    [{ chart: "bar", x: "날짜", y: "y값" }, "2 rows with no 날짜 left out", 58],
    [{ chart: "line", x: { col: "일", period: "week" }, y: "y2" }, "1 row with no 일 left out", 59],
    [{ chart: "pie", x: "그룹" }, "13 rows with no 그룹 left out", 47],
    [{ chart: "heatmap", x: "라벨", y: "그룹" }, "13 rows with no 그룹 left out", 47],
    [{ chart: "scatter", x: "x값", y: "y2", by: "그룹" }, "13 rows with no 그룹 left out", 47],
    [{ chart: "histogram", x: "y2", by: "그룹" }, "13 rows with no 그룹 left out", 47],
    [{ chart: "line", x: { col: "y2", bins: [40, 50, 60] }, y: "y값" }, "21 rows outside the bins of y2 left out", 39],
  ];
  for (const [spec, note, used] of cases) {
    const r = await live({ file: M, ...spec });
    assert.deepEqual([r.warnings[0], r.rows_used, r.rows_total], [note, used, 60], JSON.stringify(spec));
    const text = JSON.stringify(r.values);
    for (const bad of ['"None"', '"nan"', '"NaT"', "None–", "NaN"]) assert.ok(!text.includes(bad), `${bad} in ${JSON.stringify(spec)}`);
  }
  const e = await error({ file: M, chart: "bar", x: "그룹", y: "y2", filter: "그룹 not in [A, B, C]" });
  assert.equal(e.message, "no rows left after leaving out the rows with no 그룹");
});
