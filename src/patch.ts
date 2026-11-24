// The "echarts" key: a partial ECharts option merged over the drawn plot, checked against an allowlist (port of
// plotkit/echarts.py: _patch_error, _check_value, _check_mark_data, _check, validate_patch). The allowlist is
// tables.PATCH_ALLOWED; mark data ("data" of markArea/markLine/markPoint) is the "MARKDATA" sentinel.
import { PlotkitError } from "./errors.ts";
import { getCloseMatches } from "./difflib.ts";
import { pyRepr } from "./pyfmt.ts";
import { PATCH_ALLOWED, PATCH_ALIASES, PATCH_GRAPHIC_TYPES, PATCH_MARK_ITEM } from "./tables.ts";

export const PATCH_MAX_BYTES = 4096;

/** A node of the allowlist: null = a plain value, a dict of allowed keys, [item] = a list of such objects. */
type Allowed = null | "MARKDATA" | readonly Allowed[] | { readonly [k: string]: Allowed };
type Dict = Record<string, any>;

const ALLOWED = PATCH_ALLOWED as unknown as { readonly [k: string]: Allowed };
const MARK_ITEM = PATCH_MARK_ITEM as unknown as { readonly [k: string]: Allowed };
const ALIASES: Readonly<Record<string, string>> = PATCH_ALIASES;
const GRAPHIC_TYPES: readonly unknown[] = PATCH_GRAPHIC_TYPES;
const SAMPLE_HINT = 'e.g. "echarts": {"series": [{"lineStyle": {"type": "dotted"}}]}';

// Python's \s in a str pattern is str.isspace(); Python's re.I also lets "ı" and "İ" match "i" (JS's /iu does not).
const WS = "\\t-\\r\\x1c-\\x20\\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";
const I = "[iIıİ]";
const BAD_STRING = new RegExp(`^[${WS}]*(https?:|data:|f${I}le:|javascr${I}pt:|ftp:)|funct${I}on[${WS}]*\\(|=>`, "iu");

function isDict(v: unknown): v is Dict {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

function patchError(path: string, key: string, allowed: { readonly [k: string]: Allowed }): never {
  const keys = Object.keys(allowed);
  const a = key.toLowerCase().replaceAll(" ", "");
  const alias = Object.hasOwn(ALIASES, a) ? ALIASES[a] : undefined;
  const guess = alias !== undefined && keys.includes(alias) ? alias : (getCloseMatches(key, keys, 1, 0.5)[0] ?? null);
  const where = path ? `${path}.${key}` : key;
  const hint = guess ? `did you mean ${path ? path + "." : ""}${guess}?` : "";
  throw new PlotkitError(`unknown path "echarts.${where}"`, (hint ? hint + " " : "") + `allowed here: ${keys.join(", ")}`);
}

function checkValue(v: unknown, path: string): void {
  if (typeof v === "string") {
    if (BAD_STRING.test(v)) {
      throw new PlotkitError(`echarts.${path}: links, data URLs and code are not allowed`,
        "write plain text, numbers or colours only");
    }
  } else if (Array.isArray(v)) {
    v.forEach((x, i) => checkValue(x, `${path}[${i}]`));
  } else if (isDict(v)) {
    throw new PlotkitError(`echarts.${path} must be a plain value, not an object`);
  } else if (!(v === null || v === undefined || typeof v === "boolean" || typeof v === "number")) {
    throw new PlotkitError(`echarts.${path}: unsupported value ${String(v)}`);
  }
}

/** markArea/markLine/markPoint data: a list of items, or of [start, end] pairs of items. */
function checkMarkData(v: unknown, path: string): void {
  if (!Array.isArray(v)) throw new PlotkitError(`echarts.${path} must be a list`, 'e.g. "data": [[{"xAxis": 300}, {"xAxis": 450}]]');
  if (v.length > 50) throw new PlotkitError(`echarts.${path} has more than 50 items`, "annotations only; the data comes from the file");
  v.forEach((item, i) => {
    const pair: unknown[] = Array.isArray(item) ? item : [item];
    if (pair.length > 2) throw new PlotkitError(`echarts.${path}[${i}] must be one item or a [start, end] pair`);
    pair.forEach((it, j) => {
      const p = `${path}[${i}]` + (Array.isArray(item) ? `[${j}]` : "");
      if (!isDict(it)) throw new PlotkitError(`echarts.${p} must be an object like {"xAxis": 300}`);
      check(it, MARK_ITEM, p);
    });
  });
}

function check(v: unknown, allowed: Allowed, path: string): void {
  if (allowed === "MARKDATA") return checkMarkData(v, path);
  if (Array.isArray(allowed)) {                     // a list of objects (yAxis, series, graphic)
    const items: unknown[] = Array.isArray(v) ? v : [v];
    if (path === "yAxis" && items.length > 2) throw new PlotkitError("echarts.yAxis has more than 2 entries", "0 = y1 (left), 1 = y2 (right)");
    items.forEach((it, i) => {
      if (it === null || it === undefined || (isDict(it) && Object.keys(it).length === 0)) return;   // a placeholder
      if (!isDict(it)) throw new PlotkitError(`echarts.${path}[${i}] must be an object (or {} to skip it)`);
      check(it, allowed[0], `${path}[${i}]`);
      if (path === "graphic" && !GRAPHIC_TYPES.includes(Object.hasOwn(it, "type") ? it.type : null)) {
        throw new PlotkitError(`echarts.graphic[${i}].type must be one of ${GRAPHIC_TYPES.join(", ")}`);
      }
    });
    return;
  }
  if (allowed !== null && typeof allowed === "object") {
    const a = allowed as { readonly [k: string]: Allowed };
    if (!isDict(v)) throw new PlotkitError(`echarts.${path} must be an object`);
    for (const [k, x] of Object.entries(v)) {
      if (!Object.hasOwn(a, k)) patchError(path, k, a);
      check(x, a[k], path ? `${path}.${k}` : k);
    }
    return;
  }
  checkValue(v, path);
}

/** Python's json.dumps(v, ensure_ascii=False) with the default separators, for the size limit. */
function jsonDumps(v: unknown): string {
  if (v === null || v === undefined) return "null";
  if (v === true) return "true";
  if (v === false) return "false";
  if (typeof v === "number") {
    if (Number.isNaN(v)) return "NaN";
    if (!Number.isFinite(v)) return v > 0 ? "Infinity" : "-Infinity";
    return Number.isSafeInteger(v) ? String(v === 0 ? 0 : v) : pyRepr(v);   // JSON integers are Python ints
  }
  if (typeof v === "string") return jsonString(v);
  if (Array.isArray(v)) return "[" + v.map(jsonDumps).join(", ") + "]";
  if (isDict(v)) return "{" + Object.entries(v).map(([k, x]) => jsonString(k) + ": " + jsonDumps(x)).join(", ") + "}";
  return jsonString(String(v));
}

const JSON_ESC: Record<string, string> = { '"': '\\"', "\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t", "\b": "\\b", "\f": "\\f" };

function jsonString(s: string): string {
  return '"' + s.replace(/[\x00-\x1f\\"]/g, c => JSON_ESC[c] ?? "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0")) + '"';
}

/** Check an "echarts" value against the allowlist. Returns a clean copy or raises PlotkitError. */
export function validatePatch(patch: unknown): Dict {
  if (typeof patch === "string") {
    try {
      patch = JSON.parse(patch);                   // (Python's json.loads also reads NaN and Infinity)
    } catch {
      throw new PlotkitError('"echarts" must be an object (a partial ECharts option)', SAMPLE_HINT);
    }
  }
  if (!isDict(patch)) throw new PlotkitError('"echarts" must be an object (a partial ECharts option)', SAMPLE_HINT);
  if (new TextEncoder().encode(jsonDumps(patch)).length > PATCH_MAX_BYTES) {
    throw new PlotkitError(`"echarts" is larger than ${PATCH_MAX_BYTES} bytes`, "keep it to the few settings no key covers");
  }
  const fixed: Dict = {};
  for (const [k, v] of Object.entries(patch)) {        // "xaxis" -> "xAxis" etc. at the top level only
    const kl = k.toLowerCase();
    const k2 = Object.hasOwn(ALLOWED, k) ? k : Object.hasOwn(ALIASES, kl) ? ALIASES[kl] : k;
    setKey(fixed, k2, v);
  }
  check(fixed, ALLOWED, "");
  for (const k of ["yAxis", "series", "graphic"]) {
    if (Object.hasOwn(fixed, k) && !Array.isArray(fixed[k])) fixed[k] = [fixed[k]];
  }
  return structuredClone(fixed);
}

function setKey(o: Dict, k: string, v: unknown): void {
  if (k === "__proto__") Object.defineProperty(o, k, { value: v, writable: true, enumerable: true, configurable: true });
  else o[k] = v;
}
