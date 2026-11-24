// Loading the golden outputs (written from the Python plotkit by tools/ts_golden.py on branch lib/plotkit), and
// comparing TS results with them.
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const HERE = dirname(fileURLToPath(import.meta.url));
export const DATA = join(HERE, "data");
/** The data folders the goldens name files from (keys: the folders of the Python repo the goldens were made in). */
export const BASES: Record<string, string> = {
  "tests/inputs": join(DATA, "inputs"),
  "eval/inputs_b": join(DATA, "inputs_b"),
  "eval/cnt": join(DATA, "cnt"),
  "gallery": join(DATA, "gallery"),
};

/** A golden file's cases, with pooled arrays put back. NaN/inf stay as {"$f"} and dates as {"$date"} (see decode). */
export function golden<T = any>(name: string): T[] {
  const raw = JSON.parse(gunzipSync(readFileSync(join(HERE, "golden", `${name}.json.gz`))).toString("utf8"));
  const pool: Record<string, unknown> = raw.pool;
  const walk = (v: any): any => {
    if (Array.isArray(v)) return v.map(walk);
    if (v && typeof v === "object") {
      if (typeof v.$pool === "string" && Object.keys(v).length === 1) return walk(pool[v.$pool]);
      const out: any = {};
      for (const k of Object.keys(v)) out[k] = walk(v[k]);
      return out;
    }
    return v;
  };
  return raw.cases.map(walk);
}

/** {"$f": "nan"} -> NaN, {"$f": "inf"} -> Infinity; dates stay {"$date": iso}. */
export function decode(v: any): any {
  if (Array.isArray(v)) return v.map(decode);
  if (v && typeof v === "object") {
    if (typeof v.$f === "string" && Object.keys(v).length === 1) return v.$f === "nan" ? NaN : v.$f === "inf" ? Infinity : -Infinity;
    const out: any = {};
    for (const k of Object.keys(v)) out[k] = decode(v[k]);
    return out;
  }
  return v;
}

/** Differences between a TS result and the golden one: numbers equal within rel 1e-9 (abs 1e-12), NaN = NaN,
 *  {$date} = an ISO string or Date with the same instant, everything else exactly. Returns paths that differ. */
export function diff(actual: any, expected: any, path = "$", out: string[] = [], limit = 20): string[] {
  if (out.length >= limit) return out;
  expected = decode(expected);
  if (expected && typeof expected === "object" && typeof expected.$date === "string") {
    const a = actual instanceof Date ? actual.toISOString().replace(/\.000Z$/, "").replace(/Z$/, "") :
      actual && typeof actual === "object" && typeof actual.$date === "string" ? actual.$date : actual;
    if (String(a).replace(/T00:00:00$/, "") !== expected.$date.replace(/T00:00:00$/, "")) out.push(`${path}: ${a} != ${expected.$date}`);
    return out;
  }
  if (typeof expected === "number") {
    if (typeof actual !== "number") { out.push(`${path}: ${JSON.stringify(actual)} != ${expected}`); return out; }
    if (Number.isNaN(expected) && Number.isNaN(actual)) return out;
    if (expected === actual) return out;
    const tol = Math.max(1e-12, 1e-9 * Math.max(Math.abs(expected), Math.abs(actual)));
    if (!(Math.abs(expected - actual) <= tol)) out.push(`${path}: ${actual} != ${expected}`);
    return out;
  }
  if (Array.isArray(expected)) {
    if (!Array.isArray(actual)) { out.push(`${path}: not an array (${typeof actual})`); return out; }
    if (actual.length !== expected.length) out.push(`${path}: length ${actual.length} != ${expected.length}`);
    for (let i = 0; i < Math.min(actual.length, expected.length); i++) diff(actual[i], expected[i], `${path}[${i}]`, out, limit);
    return out;
  }
  if (expected && typeof expected === "object") {
    if (!actual || typeof actual !== "object" || Array.isArray(actual)) { out.push(`${path}: ${JSON.stringify(actual)?.slice(0, 80)} is not an object`); return out; }
    const ek = Object.keys(expected), ak = Object.keys(actual).filter(k => actual[k] !== undefined);
    for (const k of ek) if (!(k in actual) || actual[k] === undefined) out.push(`${path}.${k}: missing`);
    for (const k of ak) if (!(k in expected)) out.push(`${path}.${k}: extra (${JSON.stringify(actual[k])?.slice(0, 60)})`);
    for (const k of ek) if (k in actual) diff(actual[k], expected[k], `${path}.${k}`, out, limit);
    return out;
  }
  if (actual !== expected) out.push(`${path}: ${JSON.stringify(actual)?.slice(0, 120)} != ${JSON.stringify(expected)?.slice(0, 120)}`);
  return out;
}
