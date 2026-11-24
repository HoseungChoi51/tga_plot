// The JS data hatch in QuickJS gives the same numbers as the Python data_code examples did (values from the
// Python sandbox on tests/inputs/TGA.xlsx, sheet 1, and tests/inputs/run_log.csv).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { golden, decode, BASES } from "./golden.ts";
import { runChartDataCode, runCurveDataCode } from "../src/hatch.ts";
import { quickjsRunCode } from "../src/quickjs.ts";
import type { Frame } from "../src/types.ts";

const run = quickjsRunCode();
const job = decode(golden("draw_curves").find((c: any) => c.jobs?.[0]?.sheet === "1006R1-V normal" && c.jobs[0].file === "TGA.xlsx")!.jobs[0]);
const mark = (_name: string, m: Record<string, unknown>) => ({ ...m });
const close = (a: number, b: number) => Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(b));
const pick = (a: number[]) => [a[0], a[100], a[500], a[a.length - 1]];

const PY = {
  kelvin: { x: [303.15, 403.15, 803.15, 1173.15], y1: [100.0, 97.995, 95.828, 8.0162] },
  dry: { x: [30.0, 130.0, 530.0, 900.0], y1: [102.06581203560057, 100.01939250428677, 97.80762635747531, 8.181799624397811] },
  loss: { mark: { type: "text", x: 300.0, y: 97.952, text: "Δm(200–400 °C) = -0.0%" } },
  onset: { mark: { type: "vline", x: 556.3309352517986, text: "Onset 556 °C" } },
};

test("curve examples from the prompt", async () => {
  const k = await runCurveDataCode("x = x.map(v => v + 273.15)", job.data, job.sheet, run, mark);
  assert.equal(k.data.x.length, 871);
  assert.ok(pick(k.data.x).every((v, i) => close(v, PY.kelvin.x[i])) && pick(k.data.y1).every((v, i) => close(v, PY.kelvin.y1[i])));
  const d = await runCurveDataCode("const m = interp(150, x, y1); y1 = y1.map(v => v / m * 100)", job.data, job.sheet, run, mark);
  assert.ok(pick(d.data.y1).every((v, i) => close(v, PY.dry.y1[i])), String(pick(d.data.y1)));
  const l = await runCurveDataCode("const d = interp(200, x, y1) - interp(400, x, y1); marks.push({type: 'text', x: 300, y: interp(300, x, y1), text: 'Δm(200–400 °C) = ' + d.toFixed(1) + '%'})",
    job.data, job.sheet, run, mark);
  assert.deepEqual(l.marks.mark1, PY.loss.mark);
  const o = await runCurveDataCode("const g = gradient(y1, x); const i = argmin(g); const base = median(y1.filter((v, k) => x[k] < x[i] - 100)); const t0 = x[i] + (base - y1[i]) / g[i]; marks.push({type: 'vline', x: t0, text: 'Onset ' + t0.toFixed(0) + ' °C'})",
    job.data, job.sheet, run, mark);
  assert.equal(o.marks.mark1.text, PY.onset.mark.text);
  assert.ok(close(o.marks.mark1.x as number, PY.onset.mark.x));
});

test("curve errors come back with a hint", async () => {
  await assert.rejects(runCurveDataCode("let x = 1", job.data, job.sheet, run, mark), /data_code failed/);
  await assert.rejects(runCurveDataCode("y1 = y1.slice(1)", job.data, job.sheet, run, mark), /y1 has 870 values but x has 871/);
  await assert.rejects(runCurveDataCode("x = 'a'", job.data, job.sheet, run, mark), /not numbers/);
  await assert.rejects(runCurveDataCode("x = x", job.data, job.sheet, undefined, mark), (e: any) => /no data_code/.test(e.hint));
  await assert.rejects(runCurveDataCode("while (true) {}", job.data, job.sheet, quickjsRunCode({ timeoutMs: 200 }), mark), /data_code failed/);
});

test("chart rows: names without their unit, new columns, dates as text", async () => {
  const lines = readFileSync(join(BASES["tests/inputs"], "run_log.csv"), "utf8").trim().split(/\r?\n/).map(l => l.split(","));
  const head = lines[0], body = lines.slice(1);
  const frame: Frame = {
    columns: head,
    dtypes: ["datetime", "object", "float", "float", "object"],
    data: head.map((_, j) => body.map(r => j === 0 ? Date.parse(r[0] + "T00:00:00Z") : j === 2 || j === 3 ? parseFloat(r[j]) : r[j])),
    letters: Object.fromEntries(head.map((c, j) => [c, "ABCDE"[j]])),
  };
  const out = await runChartDataCode("for (const r of rows) { r['수율_x10'] = r['수율'] * 10; r['구간'] = r['구역2온도'] >= 1150 ? '고온' : '저온'; }", frame, run);
  assert.deepEqual(out.columns, ["날짜", "반응기", "수율", "구역2 온도", "등급", "수율_x10", "구간"]);
  assert.deepEqual(out.dtypes, ["datetime", "object", "float", "float", "object", "float", "object"]);
  const x10 = out.data[5].slice(0, 5) as number[];
  [39.4, 45.199999999999996, 38.8, 40.099999999999994, 39.6].forEach((v, i) => assert.ok(close(x10[i], v)));
  assert.deepEqual(out.data[6].slice(0, 5), ["고온", "고온", "저온", "고온", "저온"]);
  assert.equal(out.data[0][0], frame.data[0][0]);                                     // dates survive the trip
  assert.deepEqual(out.letters, frame.letters);
});
