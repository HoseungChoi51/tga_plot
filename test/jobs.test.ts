import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { golden, diff, BASES } from "./golden.ts";
import { buildJobs } from "../src/jobs.ts";
import { loadFrame } from "../src/frame.ts";
import { isoFromMs } from "../src/reader.ts";
import { PlotkitError } from "../src/errors.ts";
import type { Dtype, InputFile } from "../src/types.ts";

const cache = new Map<string, Uint8Array>();

/** The files a normalized spec names (its "file" list is already expanded), from the case's data folder. */
function filesFor(base: string, names: unknown[]): InputFile[] {
  return [...new Set(names.map(String))].map(name => {
    const path = join(BASES[base], name);
    if (!cache.has(path)) cache.set(path, new Uint8Array(readFileSync(path)));
    return { name, bytes: cache.get(path)! };
  });
}

const CURVES = golden("draw_curves");
const WITH_JOBS = CURVES.filter(c => c.jobs);

test("there are curve cases with jobs", () => {
  assert.ok(WITH_JOBS.length > 300, `${WITH_JOBS.length} cases`);
});

test("build_jobs equals Python's for every drawn curve case", async () => {
  const bad: string[] = [];
  for (const c of WITH_JOBS) {
    const spec = c.norm_full;
    try {
      const [jobs, warnings] = await buildJobs(spec, filesFor(c.base, spec.file));
      const got = jobs.map(j => ({
        ...j, cols: Object.fromEntries(Object.entries(j.cols).map(([r, col]) => [r, { letter: col!.letter, index: col!.index, name: col!.name }])),
      }));
      const d = [...diff(got, c.jobs, "$jobs"), ...diff(warnings, c.job_warnings, "$warnings")];
      if (d.length) bad.push(`${c.id}: ${d.slice(0, 3).join("; ")}`);
    } catch (e) {
      bad.push(`${c.id}: threw ${(e as Error).message}`);
    }
    if (bad.length > 10) break;
  }
  assert.deepEqual(bad, []);
});

test("build_jobs raises Python's error where Python's drawing failed in build_jobs", async () => {
  const bad: string[] = [];
  let n = 0;
  for (const c of CURVES.filter(c => !c.jobs && c.draw_error && c.norm_full && !c.norm_full.data_code)) {
    try {
      await buildJobs(c.norm_full, filesFor(c.base, c.norm_full.file));
      continue;                                    // the error came from a later stage
    } catch (e) {
      n++;
      if (!(e instanceof PlotkitError) || e.message !== c.draw_error.error || e.hint !== c.draw_error.hint) {
        bad.push(`${c.id}: ${(e as Error).message} != ${c.draw_error.error}`);
      }
    }
  }
  assert.deepEqual(bad, []);
  assert.ok(n >= 5, `${n} cases`);
});

const DTYPES: Record<string, Dtype> = { float64: "float", int64: "int", bool: "bool", object: "object", str: "object" };
const dtypeOf = (t: string): Dtype => (t.startsWith("datetime64") ? "datetime" : DTYPES[t]);

test("load_frame equals pandas' for every chart case", async () => {
  const cases = golden("draw_charts").filter(c => c.frame);
  assert.ok(cases.length > 200, `${cases.length} cases`);
  const bad: string[] = [];
  for (const c of cases) {
    const spec = c.norm_full;
    try {
      const df = await loadFrame(spec, filesFor(c.base, spec.file));
      const data = Object.fromEntries(df.columns.map((name, i) => [name, df.data[i].map(v =>
        df.dtypes[i] === "datetime" ? (Number.isNaN(v) ? null : { $date: isoFromMs(v as number) })
          : typeof v === "number" && Number.isNaN(v) ? null : v)]));
      const want = c.frame;
      const d = [
        ...diff(df.columns, want.columns, "$columns"),
        ...diff(df.dtypes, want.dtypes.map(dtypeOf), "$dtypes"),
        ...diff(data, want.data, "$data"),
        ...diff(df.letters, want.letters, "$letters"),
      ];
      if (d.length) bad.push(`${c.id}: ${d.slice(0, 3).join("; ")}`);
    } catch (e) {
      bad.push(`${c.id}: threw ${(e as Error).message}`);
    }
    if (bad.length > 10) break;
  }
  assert.deepEqual(bad, []);
});

test("data_code: refused without a sandbox, run per sheet with one", async () => {
  const c = WITH_JOBS.find(c => c.jobs.length === 2)!;
  const spec = { ...c.norm_full, data_code: "y1 = y1 * 2" };
  const files = filesFor(c.base, spec.file);
  await assert.rejects(buildJobs(spec, files), (e: unknown) => e instanceof PlotkitError && /data_code/.test(e.message));
  const seen: string[] = [];
  const [jobs] = await buildJobs(spec, files, async (_s, data, sheet) => {
    seen.push(sheet);
    return { data: { ...data, y1: data.y1!.map(v => v * 2) }, marks: { mark1: { type: "vline", x: 600 } } };
  });
  assert.deepEqual(seen, c.jobs.map((j: any) => j.sheet));
  assert.deepEqual(diff(jobs[0].data.y1, c.jobs[0].data.y1.map((v: number) => v * 2)), []);
  assert.deepEqual(jobs[1].marks, { mark1: { type: "vline", x: 600 } });
});
