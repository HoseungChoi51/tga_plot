// What the chart port needs of pandas, numpy and Python, on plain arrays: the loaded table as typed columns,
// Python str()/repr()/float(), numpy's pairwise sums, linspace/arange/around/histogram, pandas' rolling mean,
// group variance, Pearson correlation, pd.cut labels, and datetimes held as epoch milliseconds (naive, read as UTC).
import type { Dtype, Frame } from "./types.ts";
import { PlotkitError } from "./errors.ts";
import { pyRepr, pow10 } from "./pyfmt.ts";

export type Val = number | string | boolean | null;
/** numpy dtype.kind: f float64 (NaN missing), i int64, b bool, M datetime64 (epoch ms, NaN = NaT), O object (null missing). */
export type Kind = "f" | "i" | "b" | "M" | "O";

/** A column as pandas holds it: its kind and its values. */
export interface Ser {
  kind: Kind;
  v: Val[];
}

/** The chart table: Frame with the dtype kinds, a row count, and the column letters (df.attrs["letters"]). */
export interface Table {
  columns: string[];
  kinds: Kind[];
  data: Val[][];
  letters: Record<string, string>;
  nrows: number;
}

const KINDS: Record<Dtype, Kind> = { float: "f", int: "i", bool: "b", datetime: "M", object: "O" };

export function fromFrame(f: Frame): Table {
  return { columns: [...f.columns], kinds: f.dtypes.map(d => KINDS[d]), data: f.data.map(c => [...c]),
           letters: { ...f.letters }, nrows: f.data.length ? f.data[0].length : 0 };
}

/** df.iloc[idx] */
export function take(t: Table, idx: number[]): Table {
  return { ...t, data: t.data.map(c => idx.map(i => c[i])), nrows: idx.length };
}

/** df[name] (the first column of that name, as find_col returns names). */
export function col(t: Table, name: string): Ser {
  const j = t.columns.indexOf(name);
  if (j < 0) throw new PlotkitError(`no column "${name}"`);
  return { kind: t.kinds[j], v: t.data[j] };
}

export function setCol(t: Table, name: string, s: Ser): Table {
  const j = t.columns.indexOf(name);
  if (j >= 0) {
    const data = [...t.data], kinds = [...t.kinds];
    data[j] = s.v; kinds[j] = s.kind;
    return { ...t, data, kinds };
  }
  return { ...t, columns: [...t.columns, name], kinds: [...t.kinds, s.kind], data: [...t.data, s.v] };
}

export function isNA(kind: Kind, v: Val): boolean {
  if (v === null) return true;
  return typeof v === "number" && Number.isNaN(v) && kind !== "b";
}

export function sub(s: Ser, idx: number[]): Ser {
  return { kind: s.kind, v: idx.map(i => s.v[i]) };
}

// =================================================================== Python
/** str(int(v)) for an integral float. */
export function intStr(v: number): string {
  return Object.is(v, -0) ? "0" : Math.abs(v) < 1e21 ? String(v) : BigInt(v).toString();
}

/** Python str() of a JSON value from the spec (JSON has no int/float: integral numbers are taken as ints). */
export function specStr(v: unknown): string {
  if (typeof v === "string") return v;
  if (typeof v === "number") return Number.isInteger(v) ? intStr(v) : pyRepr(v);
  if (typeof v === "boolean") return v ? "True" : "False";
  if (v === null || v === undefined) return "None";
  return specRepr(v);
}

/** Python repr() of a JSON value from the spec. */
export function specRepr(v: unknown): string {
  if (typeof v === "string") return strRepr(v);
  if (Array.isArray(v)) return "[" + v.map(specRepr).join(", ") + "]";
  if (v && typeof v === "object") return "{" + Object.entries(v).map(([k, x]) => `${strRepr(k)}: ${specRepr(x)}`).join(", ") + "}";
  return specStr(v);
}

/** Python repr() of a str. */
export function strRepr(s: string): string {
  const q = s.includes("'") && !s.includes('"') ? '"' : "'";
  let out = "";
  for (const ch of s) {
    const c = ch.codePointAt(0)!;
    if (ch === "\\") out += "\\\\";
    else if (ch === q) out += "\\" + q;
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else if (c < 0x20 || c === 0x7f) out += "\\x" + c.toString(16).padStart(2, "0");
    else out += ch;
  }
  return q + out + q;
}

const DIGITS = "\\d(?:_?\\d)*";
const FLOAT_RE = new RegExp(`^[+-]?(?:(?:${DIGITS}(?:\\.(?:${DIGITS})?)?|\\.${DIGITS})(?:[eE][+-]?${DIGITS})?|inf|infinity|nan)$`, "i");

/** Python float(text), or null where Python raises ValueError. */
export function floatText(v: string): number | null {
  const s = v.trim();
  if (!FLOAT_RE.test(s)) return null;
  const t = s.replace(/_/g, "").toLowerCase();
  if (/^[+-]?nan$/.test(t)) return NaN;
  if (/^[+-]?inf(inity)?$/.test(t)) return t.startsWith("-") ? -Infinity : Infinity;
  return parseFloat(t);
}

/** Python float(x) of a number, true/false or text (ValueError -> PlotkitError). */
export function pyFloat(v: unknown): number {
  if (typeof v === "number") return v;
  if (typeof v === "boolean") return v ? 1 : 0;
  const x = typeof v === "string" ? floatText(v) : null;
  if (x === null) throw new PlotkitError(`could not convert ${specRepr(v)} to a number`, "give a number");
  return x;
}

/** _num: a finite number the spec gives (a number or numeric text); anything else is a PlotkitError naming the key. */
export function specNum(v: unknown, where: string): number {
  const x = typeof v === "number" ? v : typeof v === "string" ? floatText(v) : null;
  if (x === null || !Number.isFinite(x)) throw new PlotkitError(`"${where}" must be a number, not ${specRepr(v)}`, "write a number, e.g. 2.5");
  return x;
}

/** str.strip("'\"") */
export function stripQuotes(s: string): string {
  return s.replace(/^['"]+|['"]+$/g, "");
}

/** Python's str ordering (by code point; JS compares UTF-16 units). */
export function cmpStr(a: string, b: string): number {
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) {
    let x = a.charCodeAt(i), y = b.charCodeAt(i);
    if (x !== y) {
      if (x >= 0xd800 && y >= 0xd800) {
        x = x < 0xe000 ? x + 0x2000 : x - 0x800;
        y = y < 0xe000 ? y + 0x2000 : y - 0x800;
      }
      return x - y;
    }
  }
  return a.length - b.length;
}

/** Number of code points (Python len of a str). */
export function pyLen(s: string): number {
  let n = 0;
  for (const _ of s) n++;
  return n;
}

/** np.min / np.max of an array (NaN propagates), without spreading it into arguments (large tables). */
export function amin(a: ArrayLike<number>): number {
  let m = Infinity;
  for (let i = 0; i < a.length; i++) { const x = a[i]; if (Number.isNaN(x)) return NaN; if (x < m) m = x; }
  return m;
}

export function amax(a: ArrayLike<number>): number {
  let m = -Infinity;
  for (let i = 0; i < a.length; i++) { const x = a[i]; if (Number.isNaN(x)) return NaN; if (x > m) m = x; }
  return m;
}

/** Python's min(a, b) / max(a, b) (NaN handling as Python's comparisons give it). */
export function pyMin(a: number, b: number): number {
  return b < a ? b : a;
}

export function pyMax(a: number, b: number): number {
  return b > a ? b : a;
}

/** Python truthiness of a JSON value. */
export function truthy(v: unknown): boolean {
  if (v === null || v === undefined || v === false || v === 0 || v === "") return false;
  if (typeof v === "number" && Number.isNaN(v)) return true;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === "object") return Object.keys(v as object).length > 0;
  return true;
}

// =================================================================== numpy
/** numpy's pairwise summation of a[lo, lo + n). */
function pairwise(a: ArrayLike<number>, lo: number, n: number): number {
  if (n < 8) {
    let res = -0.0;
    for (let i = 0; i < n; i++) res += a[lo + i];
    return res;
  }
  if (n <= 128) {
    const r = [a[lo], a[lo + 1], a[lo + 2], a[lo + 3], a[lo + 4], a[lo + 5], a[lo + 6], a[lo + 7]];
    let i = 8;
    for (; i < n - (n % 8); i += 8) for (let j = 0; j < 8; j++) r[j] += a[lo + i + j];
    let res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
    for (; i < n; i++) res += a[lo + i];
    return res;
  }
  let n2 = Math.floor(n / 2);
  n2 -= n2 % 8;
  return pairwise(a, lo, n2) + pairwise(a, lo + n2, n - n2);
}

/** np.sum of a float64 array (the add identity, then numpy's pairwise sum). */
export function npSum(a: ArrayLike<number>): number {
  return 0.0 + pairwise(a, 0, a.length);
}

export function npMean(a: ArrayLike<number>): number {
  return npSum(a) / a.length;
}

/** pandas Series.var/std (two-pass, ddof 1) of values without NaN. */
export function npStd(a: number[], ddof = 1): number {
  const n = a.length;
  if (n - ddof <= 0) return NaN;
  const avg = npSum(a) / n;
  const sq = a.map(x => { const d = avg - x; return d * d; });
  return Math.sqrt(npSum(sq) / (n - ddof));
}

/** np.median of values without NaN. */
export function npMedian(a: number[]): number {
  const s = [...a].sort((x, y) => x - y);
  const n = s.length, h = Math.floor(n / 2);
  return n % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
}

/** pandas' groupby var/std/sem (Welford, in row order; NaN skipped). */
export function groupVar(a: number[], how: "std" | "sem", ddof = 1): number {
  let nobs = 0, mean = 0, out = 0;
  for (const val of a) {
    if (Number.isNaN(val)) continue;
    nobs += 1;
    const old = mean;
    mean += (val - old) / nobs;
    out += (val - mean) * (val - old);
  }
  if (nobs <= ddof) return NaN;
  return how === "std" ? Math.sqrt(out / (nobs - ddof)) : Math.sqrt(out / (nobs - ddof) / nobs);
}

/** pd.Series(y).rolling(w, min_periods=1).mean() (pandas' online mean with Kahan compensation). */
export function rollingMean(values: number[], w: number): number[] {
  const N = values.length;
  if (w < 1) throw new PlotkitError(`min_periods 1 must be <= window ${w}`, "smooth needs a window of 1 or more points");
  const out: number[] = [];
  let nobs = 0, negCt = 0, sumX = 0, compAdd = 0, compRemove = 0, same = 0, prev = 0;
  const add = (val: number) => {
    if (val !== val) return;
    nobs += 1;
    const y = val - compAdd, t = sumX + y;
    compAdd = t - sumX - y;
    sumX = t;
    if (val < 0 || Object.is(val, -0)) negCt += 1;
    if (val === prev) same += 1;
    else same = 1;
    prev = val;
  };
  const remove = (val: number) => {
    if (val !== val) return;
    nobs -= 1;
    const y = -val - compRemove, t = sumX + y;
    compRemove = t - sumX - y;
    sumX = t;
    if (val < 0 || Object.is(val, -0)) negCt -= 1;
  };
  for (let i = 0; i < N; i++) {
    const s = Math.max(0, i - w + 1), e = i + 1;
    if (i === 0 || s >= i) {                        // setup (also each step of a window of 1)
      compAdd = compRemove = sumX = 0;
      nobs = negCt = 0;
      prev = values[s];
      same = 0;
      for (let j = s; j < e; j++) add(values[j]);
    } else {
      const s0 = Math.max(0, i - w);
      for (let j = s0; j < s; j++) remove(values[j]);
      add(values[i]);
    }
    let r: number;
    if (nobs >= 1) {
      r = sumX / nobs;
      if (same >= nobs) r = prev;
      else if (negCt === 0 && r < 0) r = 0;
      else if (negCt === nobs && r > 0) r = 0;
    } else r = NaN;
    out.push(r);
  }
  return out;
}

/** np.linspace(start, stop, num) */
export function linspace(start: number, stop: number, num: number): number[] {
  const div = num - 1;
  const delta = stop - start;
  const y: number[] = [];
  for (let i = 0; i < num; i++) y.push(i);
  if (div > 0) {
    const step = delta / div;
    if (step === 0) for (let i = 0; i < num; i++) y[i] = (y[i] / div) * delta;
    else for (let i = 0; i < num; i++) y[i] = y[i] * step;
  } else for (let i = 0; i < num; i++) y[i] = y[i] * delta;
  for (let i = 0; i < num; i++) y[i] += start;
  if (num > 1) y[num - 1] = stop;
  return y;
}

/** np.arange(start, stop, step) for floats. */
export function arange(start: number, stop: number, step: number): number[] {
  const len = Math.ceil((stop - start) / step);
  if (!(len > 0)) return [];
  const out = [start];
  if (len === 1) return out;
  const next = start + step;
  out.push(next);
  const delta = next - start;
  for (let i = 2; i < len; i++) out.push(start + i * delta);
  return out;
}

/** np.rint: round half to even. */
export function rint(x: number): number {
  if (!Number.isFinite(x) || Math.abs(x) >= 4503599627370496) return x;
  const f = Math.floor(x), d = x - f;
  const r = d < 0.5 ? f : d > 0.5 ? f + 1 : (f % 2 === 0 ? f : f + 1);
  return r === 0 && (x < 0 || Object.is(x, -0)) ? -0 : r;
}

function powerOfTen(n: number): number {
  const p = [1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8];
  if (n < 9) return p[n];
  let r = 1e9;
  while (n-- > 9) r *= 10;
  return r;
}

/** np.around(x, decimals) (and round() of a numpy float): multiply, round half even, divide. */
export function npAround(x: number, decimals: number): number {
  if (decimals >= 0) {
    const f = powerOfTen(decimals);
    return rint(x * f) / f;
  }
  const f = powerOfTen(-decimals);
  return rint(x / f) * f;
}

/** np.allclose(a, b) */
export function allclose(a: number[], b: number[]): boolean {
  return a.every((x, i) => Math.abs(x - b[i]) <= 1e-8 + 1e-5 * Math.abs(b[i]));
}

/** np.histogram_bin_edges(v, bins=n) for finite v. */
export function histogramBinEdges(v: number[], n: number): number[] {
  if (n < 1) throw new PlotkitError("`bins` must be positive, when an integer", "bins: a number of bins (1 or more)");
  let first: number, last: number;
  if (!v.length) { first = 0; last = 1; } else { first = amin(v); last = amax(v); }
  if (first === last) { first -= 0.5; last += 0.5; }
  return linspace(first, last, n + 1);
}

/** np.histogram(v, bins=edges, density)[0] for an array of edges. */
export function histogram(v: number[], edges: number[], density: boolean): number[] {
  for (let i = 1; i < edges.length; i++) {
    if (edges[i - 1] > edges[i]) throw new PlotkitError("`bins` must increase monotonically, when an array", "give the bin edges in increasing order");
  }
  const s = [...v].sort((a, b) => a - b);
  const left = (x: number) => { let lo = 0, hi = s.length; while (lo < hi) { const m = (lo + hi) >> 1; if (s[m] < x) lo = m + 1; else hi = m; } return lo; };
  const right = (x: number) => { let lo = 0, hi = s.length; while (lo < hi) { const m = (lo + hi) >> 1; if (s[m] <= x) lo = m + 1; else hi = m; } return lo; };
  const cum = edges.map((e, i) => i < edges.length - 1 ? left(e) : right(e));
  const n = cum.slice(1).map((c, i) => c - cum[i]);
  if (!density) return n;
  const total = n.reduce((a, b) => a + b, 0);
  return n.map((c, i) => c / (edges[i + 1] - edges[i]) / total);
}

/** np.polyfit(x, y, 1) -> [slope, intercept] (the least-squares line; numpy solves it by SVD). */
export function polyfit1(x: number[], y: number[]): [number, number] {
  const n = x.length;
  const xm = npMean(x), ym = npMean(y);
  let sxx = 0, sxy = 0;
  for (let i = 0; i < n; i++) { const dx = x[i] - xm; sxx += dx * dx; sxy += dx * (y[i] - ym); }
  if (sxx === 0) {
    // rank 1 (every x the same): numpy's lstsq returns the minimum-norm solution of the scaled system
    const sc0 = Math.sqrt(x.reduce((a, b) => a + b * b, 0)), sc1 = Math.sqrt(n);
    if (sc0 === 0) return [0, ym];
    const u0 = x[0] / sc0, u1 = 1 / sc1;               // the two scaled columns are u0 * 1 and u1 * 1
    const t = npSum(y) / ((u0 * u0 + u1 * u1) * n);
    return [(t * u0) / sc0, (t * u1) / sc1];
  }
  const a = sxy / sxx;
  return [a, ym - a * xm];
}

/** np.corrcoef(x, y)[0, 1] */
export function corrcoef(x: number[], y: number[]): number {
  const n = x.length;
  const xm = npMean(x), ym = npMean(y);
  const dx = x.map(v => v - xm), dy = y.map(v => v - ym);
  let c00 = 0, c01 = 0, c11 = 0;
  for (let i = 0; i < n; i++) { c00 += dx[i] * dx[i]; c01 += dx[i] * dy[i]; c11 += dy[i] * dy[i]; }
  const f = 1 / (n - 1);
  c00 *= f; c01 *= f; c11 *= f;
  let r = c01 / Math.sqrt(c00) / Math.sqrt(c11);
  if (r > 1) r = 1;
  else if (r < -1) r = -1;
  return r;
}

/** pandas DataFrame.corr() (Pearson, pairwise complete rows; libalgos.nancorr). */
export function nancorr(cols: number[][]): number[][] {
  const K = cols.length, N = K ? cols[0].length : 0;
  const out: number[][] = Array.from({ length: K }, () => new Array<number>(K).fill(NaN));
  for (let xi = 0; xi < K; xi++) {
    for (let yi = 0; yi <= xi; yi++) {
      let nobs = 0, ssqdmx = 0, ssqdmy = 0, covxy = 0, meanx = 0, meany = 0;
      for (let i = 0; i < N; i++) {
        const vx = cols[xi][i], vy = cols[yi][i];
        if (Number.isNaN(vx) || Number.isNaN(vy)) continue;
        nobs += 1;
        const dx = vx - meanx, dy = vy - meany;
        meanx += (1 / nobs) * dx;
        meany += (1 / nobs) * dy;
        ssqdmx += (vx - meanx) * dx;
        ssqdmy += (vy - meany) * dy;
        covxy += (vx - meanx) * dy;
      }
      let val = NaN;
      if (nobs >= 1) {
        const divisor = Math.sqrt(ssqdmx * ssqdmy);
        if (divisor !== 0) val = Math.max(-1, Math.min(1, covxy / divisor));
      }
      out[xi][yi] = out[yi][xi] = val;
    }
  }
  return out;
}

// =================================================================== pd.cut
function roundFrac(x: number, precision: number): number {
  if (!Number.isFinite(x) || x === 0) return x;
  const whole = Math.trunc(x), frac = x - whole;
  const digits = whole === 0 ? -Math.floor(Math.log10(Math.abs(frac))) - 1 + precision : precision;
  return npAround(x, digits);
}

function inferPrecision(base: number, bins: number[]): number {
  for (let p = base; p < 20; p++) {
    const levels = bins.map(b => roundFrac(b, p));
    if (new Set(levels).size === bins.length) return p;
  }
  return base;
}

/** pd.cut(values, edges, right, include_lowest) -> for each value the interval [left, right] of its bin (as pandas
 *  labels it: edges rounded to the inferred precision), or null outside the bins / for NaN. */
export function cut(values: number[], edges: number[], right: boolean, includeLowest: boolean): ([number, number] | null)[] {
  for (let i = 1; i < edges.length; i++) {
    if (!(edges[i - 1] <= edges[i])) throw new PlotkitError("bins must increase monotonically.", "give the bin edges in increasing order");
  }
  if (new Set(edges).size < edges.length && edges.length !== 2) {
    throw new PlotkitError(`Bin edges must be unique: [${edges.map(pyRepr).join(", ")}].`, "give each bin edge once");
  }
  const precision = inferPrecision(3, edges);
  const breaks = edges.map(b => roundFrac(b, precision));
  if (right && includeLowest) breaks[0] = breaks[0] - pow10(-precision);
  const n = edges.length;
  return values.map(x => {
    if (Number.isNaN(x)) return null;
    let lo = 0, hi = n;
    while (lo < hi) {
      const m = (lo + hi) >> 1;
      if (right ? edges[m] < x : edges[m] <= x) lo = m + 1; else hi = m;
    }
    let id = lo;
    if (includeLowest && x === edges[0]) id = 1;
    if (id === n || id === 0) return null;
    return [breaks[id - 1], breaks[id]];
  });
}

// =================================================================== datetimes (epoch ms, naive as UTC)
const DAY_MS = 86400000;

function parts(ms: number): { date: string; h: number; m: number; s: number; us: number } {
  const totalUs = Math.round(ms * 1000);
  const days = Math.floor(totalUs / 86400e6);
  const tod = totalUs - days * 86400e6;
  const d = new Date(days * DAY_MS);
  const date = `${String(d.getUTCFullYear()).padStart(4, "0")}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-${String(d.getUTCDate()).padStart(2, "0")}`;
  const sec = Math.floor(tod / 1e6);
  return { date, h: Math.floor(sec / 3600), m: Math.floor(sec / 60) % 60, s: sec % 60, us: tod - sec * 1e6 };
}

const p2 = (n: number) => String(n).padStart(2, "0");

/** Timestamp.isoformat() */
export function isoFormat(ms: number): string {
  if (Number.isNaN(ms)) return "NaT";
  const p = parts(ms);
  return `${p.date}T${p2(p.h)}:${p2(p.m)}:${p2(p.s)}` + (p.us ? "." + String(p.us).padStart(6, "0") : "");
}

/** str(Timestamp) */
export function tsStr(ms: number): string {
  if (Number.isNaN(ms)) return "NaT";
  const p = parts(ms);
  return `${p.date} ${p2(p.h)}:${p2(p.m)}:${p2(p.s)}` + (p.us ? "." + String(p.us).padStart(6, "0") : "");
}

export function dateStr(ms: number): string {
  return parts(ms).date;
}

export function isMidnight(ms: number): boolean {
  return Math.round(ms * 1000) % 86400e6 === 0;
}

/** Series.astype(str) of a datetime column: dates alone when every value is midnight, seconds otherwise. */
export function datetimeStrs(v: number[]): (string | null)[] {
  const ok = v.filter(x => !Number.isNaN(x));
  const datesOnly = ok.every(isMidnight);
  const micro = ok.some(x => Math.round(x * 1000) % 1e6 !== 0);
  return v.map(x => {
    if (Number.isNaN(x)) return null;
    if (datesOnly) return dateStr(x);
    const p = parts(x);
    return `${p.date} ${p2(p.h)}:${p2(p.m)}:${p2(p.s)}` + (micro ? "." + String(p.us).padStart(6, "0") : "");
  });
}

/** pd.Timestamp(text) for the date forms a spec writes (2024-03-01, 2024/03/01 10:00, 20240301, 2024-03, 2024). */
export function parseTimestamp(text: string): number {
  const t = text.trim();
  let m = /^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?:(?:[T ]|\s+)(\d{1,2}):(\d{1,2})(?::(\d{1,2})(?:\.(\d{1,9}))?)?)?$/.exec(t);
  let y: number, mo: number, d: number, h = 0, mi = 0, s = 0, frac = "";
  if (m) {
    [y, mo, d] = [+m[1], +m[2], +m[3]];
    if (m[4] !== undefined) { h = +m[4]; mi = +m[5]; s = m[6] !== undefined ? +m[6] : 0; frac = m[7] ?? ""; }
  } else if ((m = /^(\d{4})(\d{2})(\d{2})$/.exec(t))) {
    [y, mo, d] = [+m[1], +m[2], +m[3]];
  } else if ((m = /^(\d{4})[-/.](\d{1,2})$/.exec(t))) {
    [y, mo, d] = [+m[1], +m[2], 1];
  } else if ((m = /^(\d{4})$/.exec(t))) {
    [y, mo, d] = [+m[1], 1, 1];
  } else {
    throw new PlotkitError(`cannot read "${text}" as a date`, "write dates as YYYY-MM-DD, with the time if needed: YYYY-MM-DD HH:MM");
  }
  const ms = Date.UTC(y, mo - 1, d, h, mi, s);
  const back = new Date(ms);
  if (mo < 1 || mo > 12 || back.getUTCDate() !== d || h > 23 || mi > 59 || s > 59) {
    throw new PlotkitError(`cannot read "${text}" as a date`, "write dates as YYYY-MM-DD, with the time if needed: YYYY-MM-DD HH:MM");
  }
  return ms + (frac ? Math.trunc(parseFloat("0." + frac) * 1e6) / 1000 : 0);
}

/** Days since 1970 of a datetime (pandas: microseconds / Timedelta(days=1)). */
export function msToDays(ms: number): number {
  return Math.round(ms * 1000) / 86400e6;
}

/** pd.to_datetime of an ISO string (as _plain wrote it, or as a spec gives a date). */
export function isoToMs(s: string): number {
  return parseTimestamp(s);
}

export function weekday(ms: number): number {
  return (((Math.floor(ms / DAY_MS) + 3) % 7) + 7) % 7;          // 1970-01-01 was a Thursday (3); Monday = 0
}

export function floorDay(ms: number): number {
  return Math.floor(ms / DAY_MS) * DAY_MS;
}

/** The start of the period (D, W-MON, MS, QS, YS) a datetime falls in; NaT stays NaT. */
export function periodStart(ms: number, p: string): number {
  if (Number.isNaN(ms)) return NaN;
  if (p === "W-MON") return floorDay(ms - weekday(ms) * DAY_MS);
  if (p === "D") return floorDay(ms);
  const d = new Date(floorDay(ms));
  const y = d.getUTCFullYear(), mo = d.getUTCMonth();
  if (p === "MS") return Date.UTC(y, mo, 1);
  if (p === "QS") return Date.UTC(y, mo - (mo % 3), 1);
  return Date.UTC(y, 0, 1);
}
