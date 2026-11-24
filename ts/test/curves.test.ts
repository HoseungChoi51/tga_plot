import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { golden, decode, diff, REPO } from "./golden.ts";
import { resolve, curveValues, notDone, fmt, clean, rgba, axisRange, unit, sameUnit, liveResult } from "../src/curves.ts";
import type { CurveSpec, Job } from "../src/curves.ts";
import { liveOptions } from "../src/live.ts";
import { renderCurves } from "../src/render.ts";
import { findPeaksXY, findPeaks, savgolFilter, peakProminences, valueAtX } from "../src/peaks.ts";
import { PlotkitError } from "../src/errors.ts";

// Cases drawn end to end by tools/ts_golden.py; those without jobs failed earlier (the reader) or are charts.
const CASES = golden("draw_curves").filter(c => c.jobs);

/** Cases whose result is known to differ from Python's, with the reason (none so far). */
const EXPECTED: Record<string, string> = {};

/** sha256 (24 hex) of the JSON with sorted keys: equal for exactly equal results. */
function canonHash(v: unknown): string {
  const canon = (x: any): any => Array.isArray(x) ? x.map(canon)
    : x && typeof x === "object" ? Object.fromEntries(Object.keys(x).sort().map(k => [k, canon(x[k])])) : x;
  return createHash("sha256").update(JSON.stringify(canon(v))).digest("hex").slice(0, 24);
}

const sha = (s: string) => createHash("sha256").update(s).digest("hex").slice(0, 24);

function run(c: any) {
  const spec = decode(c.norm_full) as CurveSpec;
  const jobs = decode(c.jobs) as Job[];
  return { spec, jobs, figs: resolve(spec, jobs) };
}

test("draw_curves: resolve, live options, values and not_done equal Python's", () => {
  const bad: string[] = [];
  let n = 0;
  for (const c of CASES) {
    if (EXPECTED[c.id]) continue;
    n++;
    let out: string[];
    try {
      const { spec, figs } = run(c);
      out = diff(figs.map(f => ({ figure: f.figure, annotations: f.annotations })), c.figures, "$.figures");
      if (c.result) {
        out.push(...diff(liveOptions(figs.map(f => f.figure)), c.result.options, "$.options"));
        out.push(...diff(curveValues(figs.map(f => ({ annotations: f.annotations }))), c.result.values, "$.values"));
        out.push(...diff(notDone(spec), c.result.not_done, "$.not_done"));
        // the whole live result, from a fresh copy of the spec and jobs
        const again = liveResult(decode(c.norm_full), decode(c.jobs), c.job_warnings);
        out.push(...diff(again, c.result, "$.result"));
      }
    } catch (e) {
      out = [`threw ${(e as Error).stack}`];
    }
    if (out.length) bad.push(`${c.id}: ${out.slice(0, 6).join("\n    ")}`);
  }
  assert.equal(n, 356);
  assert.deepEqual(bad, []);
});

test("draw_curves: the static SVG equals Python's (render.mjs, echarts 6.1.0)", () => {
  const bad: string[] = [];
  let n = 0;
  for (const c of CASES.filter(c => c.svg)) {
    const svgs = renderCurves(decode(c.norm_full), decode(c.jobs), c.job_warnings).files.map(f => f.svg);
    n += svgs.length;
    if (svgs.length !== c.svg.length) { bad.push(`${c.id}: ${svgs.length} figures, want ${c.svg.length}`); continue; }
    svgs.forEach((s, i) => {
      if (s === c.svg[i]) return;
      let k = 0;
      while (k < s.length && s[k] === c.svg[i][k]) k++;
      bad.push(`${c.id}[${i}] differs at ${k}: ${JSON.stringify(s.slice(Math.max(0, k - 60), k + 60))}\n    want ${JSON.stringify(c.svg[i].slice(Math.max(0, k - 60), k + 60))}`);
    });
  }
  assert.equal(n, 16);
  assert.deepEqual(bad, []);
});

// =================================================================== live fixes (tests/test_live_fixes.py)
// The same specs as the Python tests, end to end through api.ts on tests/inputs/TGA.xlsx. FIX holds what the fixed
// Python plotkit returned: the live options (canonHash) and the static SVG (sha), or the error and hint.
const TGA = [{ name: "TGA.xlsx", bytes: new Uint8Array(readFileSync(join(REPO, "tests", "inputs", "TGA.xlsx"))) }];
const FIX: Record<string, { spec: any; options?: string; svgs?: string[]; error?: [string, string] }> = {
  patch: { spec: { file: "TGA.xlsx", sheets: 1, echarts: { xAxis: { inverse: true, minorTick: { show: true } }, grid: { right: 120 },
    series: [{ lineStyle: { type: "dotted" } }, {}], yAxis: [{ name: "TG" }],
    graphic: [{ type: "text", right: 10, top: 10, style: { text: "note" } }] } },
  options: "8444282337a9b07677461e8f", svgs: ["70bfb2a781ad9bd9fb20db4d"] },
  lines: { spec: { file: "TGA.xlsx", sheets: 1, annotate: { onset: { type: "vline", x: 300, text: "onset" },
    limit: { type: "hline", y: 0.3, on: "y2", text: "limit" }, mass: { type: "hline", y: 0.3, on: "y1", text: "same value" },
    quiet: { type: "hline", y: 0.5, on: "y2" } } },
  options: "bc67270bd64d290adcabc3a7", svgs: ["f09ff069cf280f2f1813b0eb"] },
  rename: { spec: { file: "TGA.xlsx", sheets: 1, echarts: { series: [{ name: "Mass" }, { name: "DTG" }] } },
    options: "08f300878a1737e6154d16c7", svgs: ["0ad8c287a008424f0b3557a9"] },
  combined: { spec: { file: "TGA.xlsx", combine: true,
    echarts: { series: [{ name: "A" }, { name: "B" }, { name: "C" }, { name: "A" }, { name: "B" }, { name: "C" }] } },
  options: "727a26cc094778bb3b2d9210", svgs: ["ec63eb88bdbbfaa31a6e1a42"] },
  too_many: { spec: { file: "TGA.xlsx", sheets: 1, echarts: { series: [{}, {}, { name: "x" }] } },
    error: ["echarts.series has 3 entries but this plot has 2", "series: 0 = y1 1006R1-V normal, 1 = y2 1006R1-V normal"] },
};

test("live fixes: the patch, line labels and renamed series equal the fixed Python's", async () => {
  const { echartsOptions, renderSvg } = await import("../src/api.ts");      // end to end (reader, spec, jobs)
  for (const [name, c] of Object.entries(FIX)) {
    if (c.error) {
      for (const run of [() => echartsOptions(c.spec, TGA), () => renderSvg(c.spec, TGA)]) {
        await assert.rejects(run, (e: unknown) => e instanceof PlotkitError && e.message === c.error![0] && e.hint === c.error![1], name);
      }
      continue;
    }
    const live = await echartsOptions(c.spec, TGA);
    assert.equal(canonHash(live.options), c.options, `${name}: live options`);
    const svg = await renderSvg(c.spec, TGA);
    assert.deepEqual(svg.files.map((f: { svg: string }) => sha(f.svg)), c.svgs, `${name}: SVG`);
  }
  // what the hashes stand for, readably
  const patch = (await echartsOptions(FIX.patch.spec, TGA)).options[0];
  assert.equal(patch.xAxis.inverse, true);
  assert.equal(patch.series[0].lineStyle.type, "dotted");
  assert.deepEqual(patch.graphic, { elements: FIX.patch.spec.echarts.graphic });
  const lines = (await echartsOptions(FIX.lines.spec, TGA)).options[0];
  const marks = (axis: string) => lines.series.find((s: any) => s.name === `__marks_${axis}`).markLine.data
    .map((d: any) => [d.xAxis ?? null, d.yAxis ?? null, d.label.formatter ?? null]);
  assert.deepEqual(marks("y1"), [[300, null, "onset"], [null, 0.3, "same value"]]);
  assert.deepEqual(marks("y2"), [[null, 0.3, "limit"], [null, 0.5, null]]);
  const rename = (await echartsOptions(FIX.rename.spec, TGA)).options[0];
  assert.deepEqual(rename.legend.data, ["Mass", "DTG"]);
});

test("live fixes: \"code\" is refused before the jobs are built", async () => {
  const spec = { ...decode(CASES[0].norm_full), code: "ax1.set_title('x')" } as CurveSpec;
  let built = false;
  const build = async (): Promise<[object[], string[]]> => { built = true; throw new PlotkitError("no such file"); };
  await assert.rejects(liveResult(spec, build), /"code" \(Python\) does not work/);
  await assert.rejects(renderCurves(spec, build), /"code" \(Python\) does not work/);
  assert.equal(built, false);
  const ok = { ...decode(CASES[0].norm_full) } as CurveSpec;
  const r = await liveResult(ok, async (): Promise<[object[], string[]]> => [decode(CASES[0].jobs), ["w"]]);
  assert.deepEqual(r.warnings, ["w"]);
  const drawn = await renderCurves(ok, (): [object[], string[]] => [decode(CASES[0].jobs), []]);
  assert.equal(drawn.files.length, CASES[0].figures.length);
});

// =================================================================== peaks.ts on synthetic data
// The curves use only + - * / (and an exact integer LCG), so Python and JavaScript build the same doubles. PY holds
// what the installed Python plotkit / scipy 1.18.1 returned for them (plotkit.core.find_peaks_xy, savgol_filter,
// find_peaks, peak_prominences, plotkit.core.value_at_x).
function curve(seed: number, n: number, bumps: number[][], noise: number, cap: number | null): [number[], number[]] {
  let s = seed;
  const step = 870 / (n - 1), xs: number[] = [], ys: number[] = [];
  for (let i = 0; i < n; i++) {
    const x = 30 + i * step;
    let y = 0.0;
    for (const [a, c, w] of bumps) {
      const t = (x - c) / w;
      y = y + a / (1 + t * t);
    }
    s = (s * 48271) % 2147483647;
    y = y + (s / 2147483647 - 0.5) * noise;
    if (cap !== null && y > cap) y = cap;
    xs.push(x); ys.push(y);
  }
  return [xs, ys];
}

test("peaks: find_peaks_xy, savgol_filter, find_peaks and value_at_x equal Python's", () => {
  for (const c of PY.curves) {
    const [X, Y] = curve(c.seed, c.n, c.bumps, c.noise, c.cap);
    const [count, kind, xMin, xMax, minRel] = c.args as [number, string, number | null, number | null, number];
    assert.deepEqual(findPeaksXY(X, Y, count, kind, xMin, xMax, minRel), c.peaks, `${c.name}: peaks`);
    // smoothed values: scipy's coefficients come from LAPACK (a few hundred ulps off the exact ones used here)
    const y = kind === "max" ? Y : Y.map(v => -v);
    const win = Math.max(5, Math.floor(c.n / 100) | 1);
    const sm = win < c.n ? savgolFilter(y, win, 2) : y;
    const scale = Math.max(...y.map(Math.abs));
    for (const [i, want] of c.smooth) assert.ok(Math.abs(sm[i] - want) <= 1e-12 * scale, `${c.name}: smooth[${i}] ${sm[i]} != ${want}`);
    const fp = findPeaks(Y, { height: c.height, prominence: 0.02 });
    assert.deepEqual(fp, c.find_peaks, `${c.name}: find_peaks`);
    const pr = peakProminences(Y, fp);
    assert.deepEqual([pr.prominences, pr.leftBases, pr.rightBases], [c.prominences, ...c.bases], `${c.name}: prominences`);
    assert.deepEqual([valueAtX(X, Y, 455.5, "nearest"), valueAtX(X, Y, 455.5, "interp"), valueAtX(X, Y, 1000.0, "nearest")],
      c.values, `${c.name}: value_at_x`);
  }
});

test("peaks: plateaus, edges and prominences equal scipy's", () => {
  for (const [x, peaks, prom, left, right] of PY.small as [number[], number[], number[], number[], number[]][]) {
    assert.deepEqual(findPeaks(x), peaks, `find_peaks(${x})`);
    const p = peakProminences(x, peaks);
    assert.deepEqual([p.prominences, p.leftBases, p.rightBases], [prom, left, right], `peak_prominences(${x})`);
  }
  for (const [x0, want] of PY.interp) assert.deepEqual(valueAtX(PY.xi, PY.yi, x0 as number, "interp"), want, `interp at ${x0}`);
  for (const [x0, want] of PY.nearest) assert.deepEqual(valueAtX(PY.xi, PY.yi, x0 as number, "nearest"), want, `nearest at ${x0}`);
});

// =================================================================== helpers (values from the Python plotkit)
test("label templates, numbers and axis ranges equal Python's", () => {
  assert.equal(fmt("Residue {y:.1f}%", 800.0, 8.0117, "y"), "Residue 8.0%");
  assert.equal(fmt("{} °C", 599.4, null, "x"), "599 °C");
  assert.equal(fmt("{x} / {y}", 300.0, null, "x"), "300.0 / nan");
  assert.equal(fmt("Δ {} %", null, 2.25, "y"), "Δ 2.2 %");
  assert.equal(fmt("{{x}} {x:.3g}", 1234.5, null, "x"), "{x} 1.23e+03");
  assert.equal(fmt(null, 1.0, 1.0, "x"), "");
  const err = (f: () => unknown) => {
    try { f(); } catch (e) { if (e instanceof PlotkitError) return [e.message, e.hint]; throw e; }
    return null;
  };
  const hint = 'use {x}, {y} or {}, e.g. "Residue {y:.1f}%"';
  assert.deepEqual(err(() => fmt("{z}", 1.0, 2.0, "x")), ["label template '{z}' is invalid ('z')", hint]);
  assert.deepEqual(err(() => fmt("{x:d}", 1.0, 2.0, "x")), ["label template '{x:d}' is invalid (Unknown format code 'd' for object of type 'float')", hint]);
  assert.deepEqual(err(() => fmt("it's {0}", 1.0, 2.0, "x")), ['label template "it\'s {0}" is invalid (Replacement index 0 out of range for positional args tuple)', hint]);
  assert.deepEqual(err(() => fmt("{x", 1.0, 2.0, "x")), ["label template '{x' is invalid (expected '}' before end of string)", hint]);
  assert.deepEqual([clean(0.1 + 0.2), clean(1 / 3), clean(123456789012.5)], [0.3, 0.3333333333, 123456789000.0]);
  assert.deepEqual([rgba("navy", 0.15), rgba("#c0392b", 0.5)], ["rgba(0,0,128,0.15)", "rgba(192,57,43,0.5)"]);
  assert.deepEqual(err(() => axisRange({ min: 5.0, max: 5.0 }, 0.0, 1.0, 0, 0)), ["axis range is empty (min 5.0 >= max 5.0)", ""]);
  assert.deepEqual(err(() => axisRange({ min: null, max: null, step: 0.1 }, 0.0, 100.0, 0, 0, true)), ["step 0.1 is too small for range 0..100", "use a larger step"]);
  assert.deepEqual(axisRange({ min: 2.5, max: null, step: 10.0 }, 0.0, 100.0, 0.08, 0.12), [2.5, 112.0, [2.5, 12.5, 22.5, 32.5, 42.5, 52.5, 62.5, 72.5, 82.5, 92.5, 102.5]]);
  assert.deepEqual(axisRange({ min: null, max: null }, 3.0, 3.0, 0.08, 0.12), [2.92, 3.12, [2.925, 2.95, 2.975, 3.0, 3.025, 3.05, 3.075, 3.1]]);
  assert.deepEqual(axisRange({ log: true }, 1.0, 1000.0, 0, 0, true), [1.0, 1000.0, null]);
  assert.deepEqual(axisRange({}, 0.000123, 0.000987, 0, 0, true), [0.000123, 0.000987, [0.0002, 0.0003, 0.0004, 0.0005, 0.0006, 0.0007, 0.0008, 0.0009]]);
  assert.deepEqual([unit("Weight (mg)"), unit("D.W(%/C)"), unit("Temp"), sameUnit("°C", "℃"), sameUnit("%/°C", "% / C"), sameUnit("mg", "%")],
    ["mg", "%/C", null, true, true, false]);
});

const PY = {
  curves: [
    {"name": "one peak", "seed": 7, "n": 871, "bumps": [[1.0, 600, 40]], "noise": 0.02, "cap": null, "args": [1, "max", 150, null, 0.1], "peaks": [[599.0, 1.0044578372276955]], "smooth": [[0, -0.0014752304171121618], [1, -8.184650085110799e-05], [4, 0.00448846768433189], [290, 0.018356932533472606], [435, 0.08436407235725958], [869, 0.020422306327687042], [870, 0.022429478608788626]], "height": 0.03309850908341059, "find_peaks": [569], "prominences": [0.9940391878827172], "bases": [[0], [857]], "values": [[455.0, 0.07752164677120288], [455.5, 0.07839358590115171], [null, null]]},
    {"name": "three peaks", "seed": 11, "n": 1500, "bumps": [[0.8, 320, 25], [1.2, 480, 30], [0.5, 700, 20]], "noise": 0.03, "cap": null, "args": [3, "max", 150, null, 0.1], "peaks": [[319.03268845897264, 0.8383026806771965], [479.2194796531021, 1.236730130088234], [699.7665110073382, 0.5353084724015752]], "smooth": [[0, 0.011461819332762706], [1, 0.011906693566166734], [7, 0.013678655701252141], [500, 0.8384296966689705], [750, 0.9899363391310578], [1498, 0.020771890497827086], [1499, 0.0237606986327596]], "height": 0.10828162954803941, "find_peaks": [380, 383, 395, 420, 447, 497, 564, 598, 606, 632, 660, 774, 892, 928, 933, 936, 943, 954, 958, 964, 971, 973, 976, 983, 1057, 1067, 1080, 1084, 1154, 1158, 1167, 1217], "prominences": [0.02475238611128122, 0.0216622849233066, 0.02246090880620938, 0.024496468929461612, 0.020949438460517555, 0.6496966358044464, 0.020300215652364617, 0.022753957076439124, 0.027892724098117355, 0.02035295852412053, 0.02276808757878454, 1.2373910976805593, 0.023305368796105258, 0.02243835942826275, 0.02519426257947807, 0.021945727064494838, 0.023077547617524563, 0.020845359766756402, 0.02892962039006934, 0.02049448120237178, 0.02030149732303188, 0.021765776019749758, 0.021256948051887284, 0.024466665047344252, 0.025165717427113724, 0.022839304796256066, 0.02158644449919414, 0.02233355333687287, 0.4608926979563903, 0.02257445414935899, 0.020621388639662952, 0.02425088246929255], "bases": [[0, 0, 0, 0, 0, 0, 563, 596, 604, 619, 619, 0, 891, 925, 932, 934, 942, 952, 957, 961, 969, 972, 974, 977, 1007, 1007, 1007, 1007, 1007, 1157, 1166, 1216], [381, 384, 396, 421, 448, 619, 619, 619, 619, 634, 661, 1492, 1007, 1007, 1007, 1007, 1007, 957, 1007, 1007, 972, 1007, 1007, 1007, 1058, 1068, 1081, 1085, 1492, 1492, 1492, 1492]], "values": [[455.4236157438292, 0.7594796837655337], [455.5, 0.7598940230744904], [null, null]]},
    {"name": "dips", "seed": 5, "n": 450, "bumps": [[-0.6, 250, 30], [-0.9, 520, 50]], "noise": 0.01, "cap": null, "args": [2, "min", null, null, 0.1], "peaks": [[250.89086859688197, -0.6287530575082115], [520.2227171492204, -0.9118799754005964]], "smooth": [[0, 0.024073995005859102], [1, 0.024304498830297155], [2, 0.02342248877927399], [150, 0.14458484460273785], [225, 0.4255776214364888], [448, 0.019782400641785335], [449, 0.01718898859786646]], "height": -0.12505241177390958, "find_peaks": [165], "prominences": [0.5128926434376087], "bases": [[115], [253]], "values": [[456.28062360801783, -0.35782969811314286], [455.5, -0.34995625399101227], [null, null]]},
    {"name": "flat top", "seed": 3, "n": 300, "bumps": [[2.0, 450, 60]], "noise": 0.0, "cap": 1.5, "args": [1, "max", null, null, 0.1], "peaks": [[481.0033444816053, 1.5]], "smooth": [[0, 0.04000006280301357], [1, 0.040548561689752204], [2, 0.041108660621890614], [100, 0.35557696048763543], [150, 1.499999999999999], [298, 0.03538253021033453], [299, 0.034934542697226484]], "height": 0.1405687947427304, "find_peaks": [144], "prominences": [1.46], "bases": [[0], [299]], "values": [[454.81605351170566, 1.5], [455.5, 1.5], [null, null]]},
    {"name": "short", "seed": 9, "n": 40, "bumps": [[1.0, 400, 80]], "noise": 0.05, "cap": null, "args": [2, "max", null, null, 0.1], "peaks": [[409.2307692307692, 1.0096493604241081]], "smooth": [[0, 0.03068804767993339], [1, 0.04155049682155884], [2, 0.05249224966143891], [13, 0.4906939224023315], [20, 0.5417407858977449], [38, 0.0356100993012486], [39, 0.03672620530413857]], "height": 0.12148311172351531, "find_peaks": [17], "prominences": [0.9899776961554158], "bases": [[0], [35]], "values": [[453.8461538461538, 0.6981909443404309], [455.5, 0.685967134745163], [null, null]]},
    {"name": "window 33", "seed": 13, "n": 3200, "bumps": [[1.0, 300, 30], [0.7, 650, 25]], "noise": 0.02, "cap": null, "args": [2, "max", null, 800, 0.05], "peaks": [[300.8721475461081, 0.9990165964934117], [649.7968115035949, 0.7120023876172873]], "smooth": [[0, 0.008669861358372395], [1, 0.00949503614490746], [16, 0.015767732392348455], [1066, 0.697136739392198], [1600, 0.04517819950758254], [3198, 0.007747869693266639], [3199, 0.007322653234058197]], "height": 0.05913804158135884, "find_peaks": [998, 2282], "prominences": [1.006818765102806, 0.6846749901345732], "bases": [[0, 1757], [3174, 3174]], "values": [[455.6173804313848, 0.046742779473511735], [455.5, 0.046203383539566545], [null, null]]},
    {"name": "window 75", "seed": 17, "n": 7450, "bumps": [[0.9, 500, 35], [0.4, 820, 10]], "noise": 0.01, "cap": null, "args": [2, "max", 200, null, 0.1], "peaks": [[500.09665726943217, 0.9006320159293919], [820.1127668143375, 0.41176797249219227]], "smooth": [[0, 0.004971060664542444], [1, 0.004927633740871135], [37, 0.004601992845783995], [2483, 0.033289946036857455], [3725, 0.45151425423005637], [7448, 0.01391326281233458], [7449, 0.013985393630583447]], "height": 0.035133656005849334, "find_peaks": [4030, 6763], "prominences": [0.896363284337851, 0.3949446197647696], "bases": [[0, 6107], [7425, 7425]], "values": [[455.48127265404753, 0.34823011746369187], [455.5, 0.3476086614158815], [null, null]]},
    {"name": "nothing qualifies", "seed": 19, "n": 200, "bumps": [[0.3, 100, 20]], "noise": 0.001, "cap": null, "args": [1, "max", 600, null, 0.1], "peaks": [[830.0502512562813, 0.0006916272314564325]], "smooth": [[0, 0.022196183432201592], [1, 0.02540846982722661], [2, 0.02910205810046463], [66, 0.002380494589332538], [100, 0.0007905881033196254], [198, 0.00022293807401416773], [199, 0.0003653735013023053]], "height": 0.0009580302164055576, "find_peaks": [16], "prominences": [0.2780122137440765], "bases": [[0], [179]], "values": [[454.07035175879395, 0.0012768287126237155], [455.5, 0.001102808950568336], [null, null]]},
    {"name": "no range", "seed": 23, "n": 120, "bumps": [[1.0, 400, 40]], "noise": 0.01, "cap": null, "args": [1, "max", 950, null, 0.1], "peaks": [], "smooth": [[0, 0.007803716007947489], [1, 0.013910460013124654], [2, 0.016336672790325794], [40, 0.20768286592159296], [60, 0.25434169917089877], [118, 0.005021523394095473], [119, 0.0049087953397086315]], "height": 0.03362741085956456, "find_peaks": [50], "prominences": [0.9855091548659776], "bases": [[0], [117]], "values": [[454.03361344537814, 0.3580556956924482], [455.5, 0.34672454198538993], [null, null]]},
  ],
  small: [[[0, 1, 1, 1, 0, 2, 2, 0, 3, 3, 3, 3, 1], [2, 5, 9], [1.0, 2.0, 2.0], [0, 4, 7], [4, 7, 12]], [[1, 2, 2, 2], [], [], [], []], [[0, 1, 0, 1, 0], [1, 3], [1.0, 1.0], [0, 2], [2, 4]], [[5, 4, 3, 2, 1], [], [], [], []], [[0, 2, 1, 3, 1, 2, 0], [1, 3, 5], [1.0, 3.0, 1.0], [0, 0, 4], [2, 6, 6]]],
  xi: [10.0, 20.0, 30.0, 25.0, 40.0, 50.0], yi: [1.0, 2.0, 4.0, 9.0, 5.0, 3.0],
  interp: [[10.0, [10.0, 1.0]], [22.5, [22.5, 2.5]], [27.5, [27.5, 3.5]], [35.0, [35.0, 4.5]], [50.0, [50.0, 3.0]], [5.0, [null, null]], [50.0000000001, [50.0000000001, 3.0]]],
  nearest: [[22.5, [20.0, 2.0]], [27.0, [25.0, 9.0]], [45.0, [40.0, 5.0]]],
};
