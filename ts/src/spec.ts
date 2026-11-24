// The curve spec check (port of plotkit/core.py: normalize_spec and what it calls, expand_files, output_formats,
// not_done). A JSON spec arrives as plain JS values; the helpers at the top give them Python's semantics where the
// Python code relies on them: str() / repr(), truthiness, ==, float() / int() of text, str.strip().
// JSON numbers carry no int/float mark here: an integral number is taken as a Python int (repr 800, not 800.0).
import { PlotkitError } from "./errors.ts";
import { pyRepr } from "./pyfmt.ts";
import { getCloseMatches } from "./difflib.ts";
import { isColorLike } from "./colors.ts";
import {
  DEFAULTS, TGA_PRESET, TOP_ALIASES, AXIS_ALIASES, ANNOT_ALIASES, ANNOT_KEYS, ANNOT_TYPES, KOREAN_COLORS,
  LINESTYLES, LINESTYLE_NAMES, LEGEND_PLACES, KOREAN_PLACES, FORMATS,
} from "./tables.ts";
import { validatePatch } from "./patch.ts";

/** A Python dict as plotkit uses it (a JSON object). */
export type Dict = Record<string, any>;

// =================================================================== Python semantics of JSON values
export function isDict(v: unknown): v is Dict {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

/** d.get(k, dflt) on a JSON object or a table (own keys only: "constructor" etc. are not keys). */
export function get<T, D>(d: Readonly<Record<string, T>>, k: string, dflt: D): T | D {
  return Object.hasOwn(d, k) ? d[k] : dflt;
}

/** d[k] = v, also for a key named "__proto__". */
export function put(d: Dict, k: string, v: unknown): void {
  if (k === "__proto__") Object.defineProperty(d, k, { value: v, writable: true, enumerable: true, configurable: true });
  else d[k] = v;
}

/** Python's bool(v). */
export function truthy(v: unknown): boolean {
  if (v === null || v === undefined || v === false) return false;
  if (typeof v === "number") return v !== 0;                    // NaN is true in Python
  if (typeof v === "string" || Array.isArray(v)) return v.length > 0;
  if (isDict(v)) return Object.keys(v).length > 0;
  return true;
}

/** An integral JSON number, taken as a Python int. */
export function isPyInt(v: unknown): v is number {
  return typeof v === "number" && Number.isSafeInteger(v);
}

function asNumber(v: unknown): number | undefined {
  return typeof v === "number" ? v : typeof v === "boolean" ? Number(v) : undefined;
}

/** Python's a == b for JSON values (True == 1 == 1.0, False == 0). */
export function pyEq(a: unknown, b: unknown): boolean {
  const na = asNumber(a), nb = asNumber(b);
  if (na !== undefined || nb !== undefined) return na !== undefined && nb !== undefined && na === nb;
  if (a === null || a === undefined || b === null || b === undefined) return (a ?? null) === (b ?? null);
  if (typeof a === "string" || typeof b === "string") return a === b;
  if (Array.isArray(a) || Array.isArray(b)) {
    return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((x, i) => pyEq(x, b[i]));
  }
  if (isDict(a) && isDict(b)) {
    const ka = Object.keys(a), kb = Object.keys(b);
    return ka.length === kb.length && ka.every(k => Object.hasOwn(b, k) && pyEq(a[k], b[k]));
  }
  return false;
}

/** Python's `v in (a, b, ...)`. */
export function pyIn(v: unknown, options: readonly unknown[]): boolean {
  return options.some(o => pyEq(v, o));
}

const NONPRINTABLE = /[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}\p{Zl}\p{Zp}\p{Zs}]/u;

function reprString(s: string): string {
  const q = s.includes("'") && !s.includes('"') ? '"' : "'";
  let out = q;
  for (const ch of s) {
    const cp = ch.codePointAt(0)!;
    if (ch === q || ch === "\\") out += "\\" + ch;
    else if (ch === "\t") out += "\\t";
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (cp < 0x20 || cp === 0x7f) out += "\\x" + cp.toString(16).padStart(2, "0");
    else if (cp < 0x7f || !NONPRINTABLE.test(ch)) out += ch;
    else if (cp <= 0xff) out += "\\x" + cp.toString(16).padStart(2, "0");
    else if (cp <= 0xffff) out += "\\u" + cp.toString(16).padStart(4, "0");
    else out += "\\U" + cp.toString(16).padStart(8, "0");
  }
  return out + q;
}

/** Python's repr() of a JSON value. */
export function pyReprValue(v: unknown): string {
  if (v === null || v === undefined) return "None";
  if (v === true) return "True";
  if (v === false) return "False";
  if (typeof v === "number") return isPyInt(v) ? String(v === 0 ? 0 : v) : pyRepr(v);
  if (typeof v === "string") return reprString(v);
  if (Array.isArray(v)) return "[" + v.map(pyReprValue).join(", ") + "]";
  if (isDict(v)) return "{" + Object.entries(v).map(([k, x]) => reprString(k) + ": " + pyReprValue(x)).join(", ") + "}";
  return String(v);
}

/** Python's str() of a JSON value (also what an f-string writes). */
export function pyStrValue(v: unknown): string {
  return typeof v === "string" ? v : pyReprValue(v);
}

const PY_SPACE = "\\t-\\r\\x1c-\\x20\\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";
const STRIP = new RegExp(`^[${PY_SPACE}]+|[${PY_SPACE}]+$`, "g");

/** Python's str.strip() (Python's whitespace is not JS's: \x1c-\x1f and \x85 are, U+FEFF is not). */
export function pyStrip(s: string): string {
  return s.replace(STRIP, "");
}

const DIGIT = /\p{Nd}/u;

/** Unicode decimal digits as ASCII, as float() and int() read them ("１２３" -> "123"). */
function asciiDigits(s: string): string {
  return s.replace(/\p{Nd}/gu, ch => {
    const cp = ch.codePointAt(0)!;
    if (cp < 0x80) return ch;
    let start = cp;                                  // digits come in runs of ten from 0 to 9
    while (start > 0 && DIGIT.test(String.fromCodePoint(start - 1))) start--;
    return String((cp - start) % 10);
  });
}

const FLOAT_RE = /^[+-]?(?:(?:\d(?:_?\d)*)?\.\d(?:_?\d)*|\d(?:_?\d)*\.?)(?:[eE][+-]?\d(?:_?\d)*)?$/;
const FLOAT_SPECIAL = /^([+-]?)(inf|infinity|nan)$/i;
const INT_RE = /^[+-]?\d(?:_?\d)*$/;

/** Python's float(s) of a str; undefined where Python raises ValueError. */
export function pyFloatOfStr(s: string): number | undefined {
  const t = asciiDigits(pyStrip(s));
  const sp = FLOAT_SPECIAL.exec(t);
  if (sp) return sp[2].toLowerCase() === "nan" ? NaN : sp[1] === "-" ? -Infinity : Infinity;
  return FLOAT_RE.test(t) ? parseFloat(t.replaceAll("_", "")) : undefined;
}

/** Python's float(v); undefined where Python raises (ValueError or TypeError). */
export function pyFloat(v: unknown): number | undefined {
  if (typeof v === "number") return v;
  if (typeof v === "boolean") return Number(v);
  if (typeof v === "string") return pyFloatOfStr(v);
  return undefined;
}

/** Python's int(v); undefined where Python raises (int(None), int("1.5"), int(inf), ...). */
export function pyInt(v: unknown): number | undefined {
  if (typeof v === "boolean") return Number(v);
  if (typeof v === "number") return Number.isFinite(v) ? Math.trunc(v) || 0 : undefined;
  if (typeof v === "string") {
    const t = asciiDigits(pyStrip(v));
    return INT_RE.test(t) ? Number(BigInt(t.replaceAll("_", ""))) : undefined;
  }
  return undefined;
}

/** Python's list(v): a list's items, a dict's keys, a str's characters; undefined where Python raises. */
export function pyList(v: unknown): unknown[] | undefined {
  if (Array.isArray(v)) return [...v];
  if (isDict(v)) return Object.keys(v);
  if (typeof v === "string") return Array.from(v);
  return undefined;
}

/** Python's sorted() order of str: by code point (JS's < compares UTF-16 units). */
export function pyCompare(a: string, b: string): number {
  let i = 0, j = 0;
  while (i < a.length && j < b.length) {
    const ca = a.codePointAt(i)!, cb = b.codePointAt(j)!;
    if (ca !== cb) return ca - cb;
    i += ca > 0xffff ? 2 : 1;
    j += cb > 0xffff ? 2 : 1;
  }
  return (a.length - i) - (b.length - j);
}

/** "\n".join(lines): Python raises TypeError on a line that is not text. */
function joinLines(lines: unknown[], key: string): string {
  const bad = lines.find(x => typeof x !== "string");
  if (bad !== undefined) {
    throw new PlotkitError(`"${key}" must be text or a list of text lines, got ${pyReprValue(bad)} in the list`,
      "write each line as a string");
  }
  return lines.join("\n");
}

// =================================================================== spec
const AXES = ["x", "y1", "y2"] as const;
type Axis = typeof AXES[number];
const ANNOT_KEY_LIST: readonly string[] = ANNOT_KEYS;
const ANNOT_TYPE_LIST: readonly string[] = ANNOT_TYPES;
const LEGEND_PLACE_LIST: readonly string[] = LEGEND_PLACES;
const FORMAT_LIST: readonly string[] = FORMATS;
const DEFAULT_KEYS = Object.keys(DEFAULTS);

export function suggest(key: string, allowed: Iterable<string>): string {
  const m = getCloseMatches(key, allowed, 1, 0.5);
  return m.length ? ` Did you mean "${m[0]}"?` : "";
}

/** _deep_merge: base with over merged into it, dicts recursively (copies; plotkit itself no longer calls it). */
export function deepMerge(base: Dict, over: Dict): Dict {
  const out: Dict = structuredClone(base);
  for (const [k, v] of Object.entries(over)) {
    put(out, k, isDict(v) && isDict(get(out, k, null)) ? deepMerge(out[k], v) : structuredClone(v));
  }
  return out;
}

/** A line style in any spelling plotkit accepts ("--", "점선", "dotted", ...) as solid, dashed, dotted or dashdot.
 *  Both engines read only these four names, so a spelling draws the same everywhere. */
export function linestyleName(v: unknown, where: string): string {
  const ls = pyStrip(pyStrValue(v)).toLowerCase();
  if (!Object.hasOwn(LINESTYLES, ls)) throw new PlotkitError(`${where} ${pyReprValue(v)} unknown`, "use solid, dashed, dotted or dashdot");
  return get(LINESTYLE_NAMES, get(LINESTYLES, ls, "-"), "solid");
}

/** _num: a number from a number or text ("1,5" -> 1.5); None and booleans stay as they are. */
export function num(v: unknown, where: string): any {
  if (v === null || v === undefined || typeof v === "boolean") return v;
  if (typeof v === "number") return v;
  const f = pyFloatOfStr(pyStrip(pyStrValue(v)).replaceAll(",", "."));
  if (f === undefined) throw new PlotkitError(`${where} must be a number, got ${pyReprValue(v)}`, "write a plain number, e.g. 200");
  return f;
}

/** _color: a colour name (also Korean), hex code (with or without #) or anything matplotlib reads. */
export function color(c: unknown, where: string): string {
  const s = pyStrip(pyStrValue(c));
  let c2: string = get(KOREAN_COLORS, s, s);
  if (/^[0-9a-fA-F]{6}$/.test(c2)) c2 = "#" + c2;
  if (!isColorLike(c2)) {
    throw new PlotkitError(`${where}: ${pyReprValue(c)} is not a color`,
      'use a name like "red", "navy", "black" or a hex code like "#c0392b"');
  }
  return c2;
}

function normalizeAxis(name: Axis, d: unknown): Dict {
  if (d === false || d === null || d === undefined) {
    if (name === "y2") return { show: false };
    throw new PlotkitError(`${name} cannot be switched off`, "only y2 can be false");
  }
  if (typeof d === "string") d = { col: d };      // "x": "B"  -> {"col": "B"}
  if (!isDict(d)) throw new PlotkitError(`"${name}" must be an object like {"col": "B"}, got ${pyReprValue(d)}`);
  const allowed = Object.keys(DEFAULTS[name]);
  const out: Dict = {};
  for (const [k, v0] of Object.entries(d)) {
    let v: unknown = v0;
    let k2: string = get(AXIS_ALIASES, k.toLowerCase(), k.toLowerCase());
    if (["range", "lim", "limits", "ylim", "xlim"].includes(k2)) {
      if (!(Array.isArray(v) && v.length === 2)) throw new PlotkitError(`${name}.${k} must be [min, max]`);
      out.min = v[0];
      out.max = v[1];
      continue;
    }
    if (name === "x" && k2 === "flip") {          // x has no data sign: flip means a reversed axis
      k2 = "invert";
      v = !pyIn(v, [false, null, "none", "no"]);
    }
    if (!allowed.includes(k2)) {
      throw new PlotkitError(`unknown key "${name}.${k}".${suggest(k2, allowed)}`,
        `allowed keys for ${name}: ${[...allowed].sort(pyCompare).join(", ")}`);
    }
    out[k2] = v;
  }
  for (const k of ["minor", "invert"]) {
    if (Object.hasOwn(out, k)) out[k] = !pyIn(out[k], [false, null, "none", "no", 0]);
  }
  for (const k of ["min", "max", "step", "width", "label_size", "tick_size"]) {
    if (Object.hasOwn(out, k)) out[k] = num(out[k], `${name}.${k}`);
  }
  for (const k of ["label_color", "tick_color"]) {
    if (out[k] !== undefined && out[k] !== null) out[k] = color(out[k], `${name}.${k}`);
  }
  if (out.step !== undefined && out.step !== null && out.step <= 0) throw new PlotkitError(`${name}.step must be > 0`);
  if (Object.hasOwn(out, "color") && out.color !== null) out.color = color(out.color, `${name}.color`);
  if (Object.hasOwn(out, "linestyle")) out.linestyle = linestyleName(out.linestyle, `${name}.linestyle`);
  if (Object.hasOwn(out, "style") && !pyIn(out.style, ["line", "scatter", "line+marker"])) {
    throw new PlotkitError(`${name}.style ${pyReprValue(out.style)} unknown`, "use line, scatter or line+marker");
  }
  if (Object.hasOwn(out, "flip")) {
    const f0: unknown = out.flip;
    const bad = () => new PlotkitError(`${name}.flip ${pyReprValue(f0)} unknown`, "use none, flip, peaks_up or peaks_down");
    if (Array.isArray(f0) || isDict(f0)) throw bad();         // Python: TypeError (unhashable) in the dict lookup
    const f = pyEq(f0, true) ? "flip" : pyEq(f0, false) || f0 === null ? "none" :
      f0 === "up" ? "peaks_up" : f0 === "down" ? "peaks_down" : f0;
    if (!pyIn(f, ["none", "flip", "peaks_up", "peaks_down"])) throw bad();
    out.flip = f;
  }
  return out;
}

function guessAnnotType(name: string): string | null {
  const n = name.toLowerCase();
  const starts = (ps: string[]) => ps.some(p => n.startsWith(p));
  if (starts(["residue", "value", "res", "잔류", "잔량"])) return "value_at_x";
  if (starts(["peak", "max", "dtg", "피크", "최대"])) return "peak";
  if (starts(["band", "span", "shade", "region", "구간", "음영"])) return "band";
  for (const t of ["vline", "hline", "text"]) if (n.startsWith(t)) return t;
  return null;
}

function normalizeAnnotations(a: unknown): [Record<string, Dict | null>, boolean] {
  if (a === null || a === undefined || a === false) return [{}, true];
  let replace = false;
  if (Array.isArray(a)) {                          // a list replaces the preset labels completely
    replace = true;
    const named: Dict = {};
    a.forEach((i, n) => put(named, `${pyStrValue(isDict(i) && truthy(get(i, "type", null)) ? i.type : "label")}_${n + 1}`, i));
    a = named;
  }
  if (!isDict(a)) throw new PlotkitError('"annotate" must be an object like {"residue": {"x": 800}}');
  const out: Record<string, Dict | null> = {};
  for (const [name, d] of Object.entries(a)) {
    if (d === false || d === null || d === undefined) {
      put(out, name, null);
      continue;
    }
    if (d === true) {                              // "residue": true = asked for, with the preset settings
      put(out, name, {});
      continue;
    }
    if (!isDict(d)) throw new PlotkitError(`annotate.${name} must be an object, true or false, got ${pyReprValue(d)}`);
    const dd: Dict = {};
    for (const [k, v] of Object.entries(d)) {
      const k2: string = get(ANNOT_ALIASES, k.toLowerCase(), k.toLowerCase());
      if (!ANNOT_KEY_LIST.includes(k2)) {
        throw new PlotkitError(`unknown key "annotate.${name}.${k}".${suggest(k2, ANNOT_KEY_LIST)}`,
          `allowed: ${ANNOT_KEY_LIST.join(", ")}`);
      }
      dd[k2] = v;
    }
    for (const k of ["x", "y", "x_min", "x_max", "min_rel", "size", "alpha"]) {
      if (Object.hasOwn(dd, k)) dd[k] = num(dd[k], `annotate.${name}.${k}`);
    }
    if (Object.hasOwn(dd, "count")) {
      const c = pyInt(num(dd.count, `annotate.${name}.count`));
      if (c === undefined) {                       // Python: int(None) / int(inf) raise
        throw new PlotkitError(`annotate.${name}.count must be a number, got ${pyReprValue(dd.count)}`, "write a plain number, e.g. 2");
      }
      dd.count = c;
    }
    if (Object.hasOwn(dd, "linestyle")) dd.linestyle = linestyleName(dd.linestyle, `annotate.${name}.linestyle`);
    if (Object.hasOwn(dd, "on")) {
      let on = pyStrValue(dd.on).toLowerCase();
      on = get({ left: "y1", right: "y2", y: "y1", "1": "y1", "2": "y2" }, on, on);
      if (on !== "y1" && on !== "y2") throw new PlotkitError(`annotate.${name}.on must be y1 or y2, got ${pyReprValue(dd.on)}`);
      dd.on = on;
    }
    if (Object.hasOwn(dd, "color") && dd.color !== null) dd.color = color(dd.color, `annotate.${name}.color`);
    if (Object.hasOwn(dd, "type") && !ANNOT_TYPE_LIST.includes(dd.type)) {   // (Python: TypeError for a list or dict)
      throw new PlotkitError(`annotate.${name}.type ${pyReprValue(dd.type)} unknown.${suggest(pyStrValue(dd.type), ANNOT_TYPE_LIST)}`,
        `types: ${ANNOT_TYPE_LIST.join(", ")}`);
    }
    put(out, name, dd);
  }
  return [out, replace];
}

/** Validate a user spec and merge it over defaults (and the preset). names: the files the host gave, for patterns
 *  in "file". The result keeps plotkit's internal keys (_preset_label, _preset_text, _requested, _text_color_set). */
export function normalizeSpec(user: unknown, names: readonly string[] = []): Dict {
  if (typeof user === "string") user = { file: user };
  if (!isDict(user)) throw new PlotkitError("the spec must be a JSON object");
  user = structuredClone(user);                    // (Python shares, and may change, the caller's objects)
  // map aliases / dotted keys at the top level
  const u: Dict = {};
  for (const [k, v] of Object.entries(user as Dict)) {
    const kl = k.toLowerCase();
    const k2: string = get(TOP_ALIASES, kl, kl);
    if (k2.includes(".")) {
      const i = k2.indexOf(".");
      const a = k2.slice(0, i), b = k2.slice(i + 1);
      if (!Object.hasOwn(u, a)) put(u, a, {});
      if (!isDict(u[a])) {                         // Python: TypeError (u[a][b] = v on a non-dict)
        throw new PlotkitError(`"${a}" is given both as ${pyReprValue(u[a])} and through "${k}"`,
          `write it once, e.g. "${a}": {"${b}": ...}`);
      }
      put(u[a], b, v);
    } else if (Object.hasOwn(u, k2) && isDict(u[k2]) && isDict(v)) {
      for (const [kk, vv] of Object.entries(v)) put(u[k2], kk, vv);
    } else {
      put(u, k2, v);
    }
  }
  const unknown = Object.keys(u).filter(k => !Object.hasOwn(DEFAULTS, k));
  if (unknown.length) {
    const k = unknown[0];
    const kAx: string = get(AXIS_ALIASES, k, k);
    if (Object.hasOwn(DEFAULTS.y1, kAx) || kAx === "range" || kAx === "lim") {
      throw new PlotkitError(`"${k}" belongs to an axis, not the top level`,
        `put it inside "x", "y1" or "y2", e.g. "x": {"${kAx}": ...}`);
    }
    const kAn: string = get(ANNOT_ALIASES, k, k);
    if (ANNOT_KEY_LIST.includes(kAn) || /^(residue|peak|vline|hline|note)/.test(k)) {
      throw new PlotkitError(`"${k}" belongs inside "annotate"`,
        'e.g. "annotate": {"residue": {"x": 700}} or "annotate": {"vline1": {"type": "vline", "x": 450}}');
    }
    throw new PlotkitError(`unknown key "${k}".${suggest(k, DEFAULT_KEYS)}`, "top-level keys: " + DEFAULT_KEYS.join(", "));
  }
  if (!truthy(get(u, "file", null))) throw new PlotkitError('"file" is missing', 'add "file": "your_data.xlsx"');

  const p0 = Object.hasOwn(u, "preset") ? u.preset : DEFAULTS.preset;
  const preset = pyStrValue(truthy(p0) ? p0 : "none").toLowerCase();
  if (preset !== "tga" && preset !== "none") throw new PlotkitError(`preset ${pyReprValue(preset)} unknown`, 'use "tga" or "none"');

  const spec: Dict = structuredClone(DEFAULTS) as Dict;
  if (preset === "tga") {
    const p: Dict = structuredClone(TGA_PRESET) as Dict;
    for (const ax of AXES) Object.assign(spec[ax], p[ax], { _preset_label: true });
    spec.annotate = p.annotate;
    for (const d of Object.values(spec.annotate) as Dict[]) d._preset_text = true;
  }
  spec.preset = preset;

  for (const ax of AXES) {
    if (Object.hasOwn(u, ax)) {
      const n = normalizeAxis(ax, u[ax]);
      Object.assign(spec[ax], n);
      if (Object.hasOwn(n, "label")) delete spec[ax]._preset_label;
    }
  }
  if (Object.hasOwn(u, "annotate")) {
    const [ann, replace] = normalizeAnnotations(u.annotate);
    const base: Dict = replace ? {} : spec.annotate;
    for (const [name, d] of Object.entries(ann)) {
      if (d === null) {
        delete base[name];
      } else {                                     // named in the user's spec: say "no data" instead of hiding it
        put(base, name, { ...(Object.hasOwn(base, name) ? base[name] : {}), ...d, _requested: true });
        if (Object.hasOwn(d, "text")) delete base[name]._preset_text;
      }
    }
    spec.annotate = base;
  }
  for (const [name, d] of Object.entries(spec.annotate) as [string, Dict][]) {
    if (!Object.hasOwn(d, "type")) d.type = guessAnnotType(name);
    if (d.type === null) throw new PlotkitError(`annotate.${name} needs a "type"`, `types: ${ANNOT_TYPE_LIST.join(", ")}`);
    const need = get({ value_at_x: "x", vline: "x", hline: "y" }, d.type, null);
    if (need && (d[need] === undefined || d[need] === null)) {
      throw new PlotkitError(`annotate.${name} needs "${need}"`, `e.g. "annotate": {"${name}": {"${need}": 800}}`);
    }
    if (d.type === "band") {
      if (d.x_min === undefined || d.x_min === null || d.x_max === undefined || d.x_max === null) {
        throw new PlotkitError(`annotate.${name} (band) needs "x_min" and "x_max"`,
          `e.g. "annotate": {"${name}": {"type": "band", "x_min": 300, "x_max": 450}}`);
      }
      if (d.x_max <= d.x_min) throw new PlotkitError(`annotate.${name}: x_max must be larger than x_min`);
      if (d.alpha !== undefined && d.alpha !== null && !(0 <= d.alpha && d.alpha <= 1)) {
        throw new PlotkitError(`annotate.${name}.alpha must be between 0 and 1`, "e.g. 0.15");
      }
    }
  }
  for (const k of ["read", "output"] as const) {
    if (Object.hasOwn(u, k)) {
      if (!isDict(u[k])) throw new PlotkitError(`"${k}" must be an object`);
      const allowed = Object.keys(DEFAULTS[k]);
      for (const kk of Object.keys(u[k])) {
        if (!allowed.includes(kk)) {
          throw new PlotkitError(`unknown key "${k}.${kk}".${suggest(kk, allowed)}`, `allowed: ${allowed.join(", ")}`);
        }
      }
      Object.assign(spec[k], u[k]);
    }
  }
  for (const k of ["file", "sheets", "grid", "size", "dpi", "font", "font_size", "combine", "text_color", "tick_direction",
    "code", "data_code", "asks", "names", "offset", "panels"]) {
    if (Object.hasOwn(u, k)) spec[k] = u[k];
  }
  if (Object.hasOwn(u, "colors") && u.colors !== null && u.colors !== undefined) {
    let c: unknown = u.colors;
    if (typeof c === "string" && ["mono", "흑백", "bw", "black and white", "grayscale"].includes(c.toLowerCase())) {
      c = ["black", "#666666", "#999999", "#333333", "#bbbbbb", "#555555"];
    }
    if (isDict(c)) c = Object.values(c);
    const list: unknown[] = Array.isArray(c) ? c : [c];
    spec.colors = list.map((x, i) => color(x, `colors[${i}]`));
  }
  if (spec.names !== null && !Array.isArray(spec.names)) spec.names = [spec.names];
  if (spec.offset !== null) spec.offset = num(spec.offset, "offset");
  if (!pyIn(spec.panels, [null, false])) {
    const pv = pyStrValue(spec.panels).toLowerCase();
    if (["true", "split", "stacked", "2", "two", "위아래", "separate", "subplots", "vertical"].includes(pv)) {
      spec.panels = "split";
    } else {
      throw new PlotkitError(`panels ${pyReprValue(spec.panels)} unknown`, 'use "split" (y1 above, y2 below)');
    }
  } else {
    spec.panels = null;
  }
  if (Array.isArray(spec.data_code)) spec.data_code = joinLines(spec.data_code, "data_code");
  if (!Array.isArray(spec.asks)) spec.asks = [spec.asks];
  if (!pyIn(Object.hasOwn(u, "echarts") ? u.echarts : null, [null, {}, false])) {
    spec.echarts = validatePatch(u.echarts);       // the allowlist lives with the engine
  }
  if (Object.hasOwn(u, "title")) {
    let t: unknown = u.title;
    if (t === null || t === undefined || t === false) t = { text: "" };
    if (typeof t === "string") t = { text: t };
    if (!isDict(t)) throw new PlotkitError('"title" must be text or {"text": ..., "size": ..., "color": ...}');
    const t2: Dict = {};
    for (const [k, v] of Object.entries(t)) {
      put(t2, get({ label: "text", fontsize: "size", font_size: "size", colour: "color" }, k, k), v);
    }
    for (const k of Object.keys(t2)) {
      if (!["text", "size", "color"].includes(k)) throw new PlotkitError(`unknown key "title.${k}"`, "title keys: text, size, color");
    }
    Object.assign(spec.title, t2);
  }
  if (Object.hasOwn(u, "legend")) {
    let lg: unknown = u.legend;
    if (lg === false || lg === null || lg === undefined || lg === "none") lg = { show: false };
    else if (lg === true) lg = { show: true };
    else if (typeof lg === "string") lg = { where: lg };
    if (!isDict(lg)) throw new PlotkitError('"legend" must be a position text, false, or {"where": ..., "show": ..., "size": ...}');
    const lg2: Dict = {};
    for (const [k, v] of Object.entries(lg)) {
      put(lg2, get({ position: "where", loc: "where", location: "where", fontsize: "size", font_size: "size", visible: "show" }, k, k), v);
    }
    for (const k of Object.keys(lg2)) {
      if (!["where", "show", "size"].includes(k)) throw new PlotkitError(`unknown key "legend.${k}"`, "legend keys: where, show, size");
    }
    Object.assign(spec.legend, lg2);
  }
  const where0: unknown = spec.legend.where;
  const badPlace = () => new PlotkitError(`legend position ${pyReprValue(spec.legend.where)} unknown`,
    "use one of: " + LEGEND_PLACE_LIST.join(", "));
  if (Array.isArray(where0) || isDict(where0)) throw badPlace();      // Python: TypeError (unhashable) in the lookup
  spec.legend.where = typeof where0 === "string" ? get(KOREAN_PLACES, where0, where0) : where0;
  if (spec.legend.where === "none") spec.legend.show = false;
  if (!LEGEND_PLACE_LIST.includes(spec.legend.where)) throw badPlace();
  if (truthy(spec.title.color)) spec.title.color = color(spec.title.color, "title.color");
  spec.text_color = color(truthy(spec.text_color) ? spec.text_color : "black", "text_color");
  spec._text_color_set = truthy(get(u, "text_color", null));   // then it also beats the line colours
  const tds = pyStrValue(spec.tick_direction);
  const td = get({ "안쪽": "in", "바깥쪽": "out", "밖": "out", "안": "in", "양쪽": "inout" }, tds, tds.toLowerCase());
  if (!["in", "out", "inout"].includes(td)) {
    throw new PlotkitError(`tick_direction ${pyReprValue(spec.tick_direction)} unknown`, "use in, out or inout");
  }
  spec.tick_direction = td;
  if (Array.isArray(spec.code)) spec.code = joinLines(spec.code, "code");
  spec.file = expandFiles(Array.isArray(spec.file) ? spec.file : [spec.file], names);
  spec.output.format = outputFormats(spec.output.format);
  return spec;
}

/** A format or list of formats, checked: ["png", "pdf", ...] (jpeg -> jpg, tiff -> tif). */
export function outputFormats(fmts: unknown, key = "output.format"): string[] {
  const list = typeof fmts === "string" ? [fmts] : pyList(fmts);
  if (list === undefined) throw new PlotkitError(`${key} ${pyReprValue(fmts)} not supported`, "use png, pdf, svg, jpg or tif");   // Python: TypeError
  const out = list.map(f => pyStrValue(f).toLowerCase().replace(/^\.+/, "").replaceAll("jpeg", "jpg").replaceAll("tiff", "tif"));
  for (const f of out) {
    if (!FORMAT_LIST.includes(f)) throw new PlotkitError(`${key} ${pyReprValue(f)} not supported`, "use png, pdf, svg, jpg or tif");
  }
  return out;
}

/** The asks the model marked unsupported, to tell the user (curves and charts alike). */
export function notDone(spec: Dict): string[] {
  const asks: unknown = Object.hasOwn(spec, "asks") && truthy(spec.asks) ? spec.asks : [];
  const items = pyList(asks);
  if (items === undefined) {                       // Python: TypeError (not iterable)
    throw new PlotkitError(`"asks" must be a list, got ${pyReprValue(asks)}`, 'e.g. "asks": [{"ask": "...", "how": "key"}]');
  }
  return items.filter((a): a is Dict => isDict(a) &&
    ["unsupported", "no", "none", "not_done"].includes(pyStrValue(get(a, "how", "")).toLowerCase()))
    .map(a => pyStrValue(get(a, "ask", "")));
}

// =================================================================== file patterns
/** File names with * or ? become the matching files, sorted; others stay as they are. names: the files the host
 *  gave (relative, "/" separators); a pattern matches them as Python's glob does in their folder. */
export function expandFiles(files: readonly unknown[], names: readonly string[]): string[] {
  const out: string[] = [];
  let fs: NameTree | undefined;
  for (const f0 of files) {
    const f = pyStrValue(f0);
    if (/[*?[]/.test(f)) {
      fs ??= new NameTree(names);
      const hits = iglob(f, fs, false).sort(pyCompare);
      if (!hits.length) throw new PlotkitError(`no file matches ${f}`, "check the folder and the pattern");
      out.push(...hits);
    } else {
      out.push(f);
    }
  }
  return out;
}

/** The folder the host's files make: the files and the folders their names imply. */
class NameTree {
  readonly kinds = new Map<string, "file" | "dir">([["", "dir"]]);
  readonly children = new Map<string, string[]>([["", []]]);
  constructor(names: readonly string[]) {
    for (const name of names) {
      const parts = name.split("/").filter(p => p !== "" && p !== ".");
      let cur = "";
      parts.forEach((p, i) => {
        const path = cur ? `${cur}/${p}` : p;
        const kind = i === parts.length - 1 ? "file" : "dir";
        if (!this.kinds.has(path)) {
          this.kinds.set(path, kind);
          this.children.get(cur)!.push(p);
          if (kind === "dir") this.children.set(path, []);
        }
        cur = path;
      });
    }
  }
  /** What a path names, resolved as the OS does ("a/./b", "a/../b", "dir/"); "" names nothing. */
  lookup(path: string): { kind: "file" | "dir"; key: string } | null {
    if (path === "" || path.startsWith("/")) return null;
    const stack: string[] = [];
    let kind: "file" | "dir" = "dir";
    for (const c of path.split("/")) {
      if (kind !== "dir") return null;
      if (c === "" || c === ".") continue;
      if (c === "..") {
        if (!stack.length) return null;           // outside the folder: unknown here
        stack.pop();
        continue;
      }
      stack.push(c);
      const k = this.kinds.get(stack.join("/"));
      if (!k) return null;
      kind = k;
    }
    return { kind, key: stack.join("/") };
  }
  lexists(path: string): boolean {
    return this.lookup(path) !== null;
  }
  isdir(path: string): boolean {
    return this.lookup(path)?.kind === "dir";
  }
  listdir(path: string, dironly: boolean): string[] {
    const hit = path === "" ? { kind: "dir", key: "" } : this.lookup(path);
    if (!hit || hit.kind !== "dir") return [];
    const names = this.children.get(hit.key) ?? [];
    return dironly ? names.filter(n => this.kinds.get(hit.key ? `${hit.key}/${n}` : n) === "dir") : names;
  }
}

const hasMagic = (s: string) => /[*?[]/.test(s);

function splitPath(p: string): [string, string] {          // os.path.split (posix)
  const i = p.lastIndexOf("/") + 1;
  let head = p.slice(0, i);
  const tail = p.slice(i);
  if (head && head !== "/".repeat(head.length)) head = head.replace(/\/+$/, "");
  return [head, tail];
}

function joinPath(a: string, b: string): string {          // os.path.join (posix), two parts
  if (b.startsWith("/")) return b;
  if (!a || a.endsWith("/")) return a + b;
  return a + "/" + b;
}

/** glob._iglob without recursive "**" (plotkit calls glob.glob(pattern) plainly). */
function iglob(pathname: string, fs: NameTree, dironly: boolean): string[] {
  const [dirname, basename] = splitPath(pathname);
  if (!hasMagic(pathname)) {
    if (basename) return fs.lexists(pathname) ? [pathname] : [];
    return fs.isdir(dirname) ? [pathname] : [];
  }
  if (!dirname) return glob1("", basename, fs, dironly);
  const dirs = dirname !== pathname && hasMagic(dirname) ? iglob(dirname, fs, true) : [dirname];
  const out: string[] = [];
  for (const d of dirs) {
    const names = hasMagic(basename) ? glob1(d, basename, fs, dironly) : glob0(d, basename, fs);
    for (const name of names) out.push(joinPath(d, name));
  }
  return out;
}

function glob1(dirname: string, pattern: string, fs: NameTree, dironly: boolean): string[] {
  let names = fs.listdir(dirname, dironly);
  if (!pattern.startsWith(".")) names = names.filter(x => !x.startsWith("."));
  const re = fnmatchRegExp(pattern);
  return re ? names.filter(n => re.test(n)) : [];
}

function glob0(dirname: string, basename: string, fs: NameTree): string[] {
  if (basename) return fs.lexists(dirname ? joinPath(dirname, basename) : basename) ? [basename] : [];
  return fs.isdir(dirname) ? [basename] : [];
}

const STAR = Symbol("*");
const REGEX_SYNTAX = new Set("^$\\.*+?()[]{}|/");
const escapeChar = (c: string) => (REGEX_SYNTAX.has(c) ? "\\" + c : c);
const escapeClassChar = (c: string) => ("\\]^-[".includes(c) ? "\\" + c : c);

/** fnmatch.translate as a JS RegExp (null when Python's re would reject the pattern). Python's atomic
 *  "(?>.*?fixed)" groups match the same names as plain ".*" here: each fixed piece has a fixed length. */
function fnmatchRegExp(pattern: string): RegExp | null {
  const pat = Array.from(pattern);                // code points, as Python indexes str
  const res: (string | typeof STAR)[] = [];
  let i = 0;
  const n = pat.length;
  while (i < n) {
    const c = pat[i];
    i++;
    if (c === "*") {
      if (!res.length || res[res.length - 1] !== STAR) res.push(STAR);
    } else if (c === "?") {
      res.push(".");
    } else if (c === "[") {
      let j = i;
      if (j < n && pat[j] === "!") j++;
      if (j < n && pat[j] === "]") j++;
      while (j < n && pat[j] !== "]") j++;
      if (j >= n) {
        res.push("\\[");
        continue;
      }
      const stuff = pat.slice(i, j);
      // Python builds the class body as regex text: unescaped "-" = a range, "\x" = the literal x
      let body: string[];
      if (!stuff.includes("-")) {
        body = stuff.flatMap(ch => (ch === "\\" ? ["\\", "\\"] : [ch]));
      } else {
        const chunks: string[][] = [];
        let k = pat[i] === "!" ? i + 2 : i + 1;
        for (;;) {
          k = k < j ? pat.indexOf("-", k) : -1;
          if (k < 0 || k >= j) break;
          chunks.push(pat.slice(i, k));
          i = k + 1;
          k = k + 3;
        }
        const chunk = pat.slice(i, j);
        if (chunk.length) chunks.push(chunk);
        else chunks[chunks.length - 1].push("-");
        for (let m = chunks.length - 1; m > 0; m--) {   // remove empty ranges
          const prev = chunks[m - 1], next = chunks[m];
          if (prev.length && next.length && prev[prev.length - 1].codePointAt(0)! > next[0].codePointAt(0)!) {
            chunks[m - 1] = [...prev.slice(0, -1), ...next.slice(1)];
            chunks.splice(m, 1);
          }
        }
        body = [];
        chunks.forEach((ch, m) => {
          if (m) body.push("-");
          for (const x of ch) body.push(...(x === "\\" ? ["\\", "\\"] : x === "-" ? ["\\", "-"] : [x]));
        });
      }
      i = j + 1;
      if (!body.length) res.push("(?!)");
      else if (body.length === 1 && body[0] === "!") res.push(".");
      else res.push(classToJs(body));
    } else {
      res.push(escapeChar(c));
    }
  }
  const src = res.map(p => (p === STAR ? ".*" : p)).join("");
  try {
    return new RegExp(`^(?:${src})$`, "su");
  } catch {
    return null;
  }
}

/** Python's class body (as regex text, before the leading "!" -> "^") as a JS class. */
function classToJs(body: string[]): string {
  let k = 0, neg = false;
  if (body[0] === "!") {
    neg = true;
    k = 1;
  }
  // a leading "^" or "[" is literal (Python escapes it); "\x" is the literal x; "a-b" is a range
  const atoms: { ch: string; range?: boolean }[] = [];
  while (k < body.length) {
    if (body[k] === "\\" && k + 1 < body.length) {
      atoms.push({ ch: body[k + 1] });
      k += 2;
    } else if (body[k] === "-" && atoms.length && k + 1 < body.length) {
      atoms.push({ ch: "-", range: true });
      k++;
    } else {
      atoms.push({ ch: body[k] });
      k++;
    }
  }
  let out = "";
  atoms.forEach(a => { out += a.range ? "-" : escapeClassChar(a.ch); });
  return `[${neg ? "^" : ""}${out}]`;
}
