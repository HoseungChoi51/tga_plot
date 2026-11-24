// Port of the reader in plotkit/core.py: data files (the host's InputFile bytes) -> raw tables -> the numeric table
// of a sheet, column matching, the TGA column guess, and sheet selection. Python helpers whose behaviour shows in the
// results (str(), repr(), strip(), splitlines(), set order, Path names) are reproduced here.
import type { Cell, InputFile, Tables } from "./types.ts";
import { PlotkitError } from "./errors.ts";
import { pyDivmod, pyRepr, pyRound } from "./pyfmt.ts";
import { getCloseMatches } from "./difflib.ts";

/** spec["read"]: how to read text files and where the table starts. */
export interface ReadOptions {
  header_row?: unknown;
  data_start_row?: unknown;
  sep?: unknown;
  decimal?: unknown;
  encoding?: unknown;
}

/** One numeric column of a sheet (analyze_table). values: one number per body row, NaN where it has none. */
export interface Column {
  letter: string;
  index: number;
  name: string;
  values: number[];
}

/** analyze_table's result. */
export interface Table {
  columns: Column[];
  header_rows: number[];
  data_start_row: number;
  n_rows: number;
}

// =================================================================== Python string behaviour
/** Python's whitespace (str.isspace, and \s in re for str patterns), as a regex character-class body. */
export const PY_WS = "\\t\\n\\x0b\\x0c\\r\\x1c-\\x1f \\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";
/** Python's \w for str patterns (alphanumerics and _), as a regex atom for lookarounds (u flag): \b is emulated
 *  with (?<!W) / (?!W). */
export const PY_W = "[\\p{L}\\p{N}_]";
const WS_RUN = new RegExp(`[${PY_WS}]+`, "u");

function isPyWs(c: number): boolean {
  return (c >= 9 && c <= 13) || (c >= 0x1c && c <= 0x20) || c === 0x85 || c === 0xa0 || c === 0x1680
    || (c >= 0x2000 && c <= 0x200a) || c === 0x2028 || c === 0x2029 || c === 0x202f || c === 0x205f || c === 0x3000;
}

/** str.strip() / str.strip(chars) (chars: BMP characters). */
export function pyStrip(s: string, chars?: string): string {
  const drop = chars === undefined ? isPyWs : (c: number) => chars.includes(String.fromCharCode(c));
  let a = 0, b = s.length;
  while (a < b && drop(s.charCodeAt(a))) a++;
  while (b > a && drop(s.charCodeAt(b - 1))) b--;
  return a === 0 && b === s.length ? s : s.slice(a, b);
}

/** str.split() with no arguments. */
export function pySplitWs(s: string): string[] {
  return pyStrip(s).split(WS_RUN).filter(p => p !== "");
}

/** str.splitlines(). */
export function splitLines(s: string): string[] {
  const out = s.split(/\r\n|[\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029]/);
  if (out.length && out[out.length - 1] === "") out.pop();
  return out;
}

/** len() of a str: code points. */
export function pyLen(s: string): number {
  let n = 0;
  for (const _ of s) n++;
  return n;
}

/** Compare strings by code point, as Python does. */
export function cmpCodePoints(a: string, b: string): number {
  const x = Array.from(a), y = Array.from(b);
  for (let i = 0; i < Math.min(x.length, y.length); i++) {
    const d = x[i].codePointAt(0)! - y[i].codePointAt(0)!;
    if (d) return d < 0 ? -1 : 1;
  }
  return x.length - y.length < 0 ? -1 : x.length > y.length ? 1 : 0;
}

/** Unicode decimal digits to ASCII (Python's \d and float() accept them). Nd digits come in runs of ten from 0. */
export function asciiDigits(s: string): string {
  if (/^[\x00-\x7f]*$/.test(s)) return s;
  return s.replace(/\p{Nd}/gu, ch => {
    let cp = ch.codePointAt(0)!, k = 0;
    while (/\p{Nd}/u.test(String.fromCodePoint(cp - 1))) { cp--; k++; }
    return String(k % 10);
  });
}

/** str() of an int held as a number. */
export function intStr(v: number): string {
  if (Object.is(v, -0)) return "0";
  return Math.abs(v) < 1e21 ? String(v) : BigInt(v).toString();
}

/** Whether a number from a file or a spec was a Python int. Python keeps the distinction (openpyxl gives an int
 *  when the cell text has no "." or exponent; JSON gives an int for "5"); JS does not, so: integral and short. */
export function isIntLike(v: number): boolean {
  return Number.isInteger(v) && Math.abs(v) < 1e16;
}

/** str() of a number as Python would show it (see isIntLike). */
export function numStr(v: number): string {
  return isIntLike(v) ? intStr(v) : pyRepr(v);
}

/** str() of a raw cell: datetime as "YYYY-MM-DD HH:MM:SS", numbers as int or float. */
export function cellStr(c: Cell | undefined): string {
  if (c === null || c === undefined) return "None";
  if (typeof c === "string") return c;
  if (typeof c === "boolean") return c ? "True" : "False";
  if (typeof c === "number") return numStr(c);
  return c.date.replace("T", " ");
}

/** str() of a spec value (str, number, bool, None, list, dict). */
export function pyStrOf(v: unknown): string {
  if (typeof v === "string") return v;
  if (typeof v === "number") return numStr(v);
  if (v === null || v === undefined || typeof v === "boolean") return cellStr(v as Cell);
  return pyReprOf(v);
}

const NONPRINT = /[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}\p{Zl}\p{Zp}\p{Zs}]/u;

/** repr() of a str. */
export function reprStr(s: string): string {
  const q = s.includes("'") && !s.includes('"') ? '"' : "'";
  let out = q;
  for (const ch of s) {
    const cp = ch.codePointAt(0)!;
    if (ch === "\\" || ch === q) out += "\\" + ch;
    else if (ch === "\t") out += "\\t";
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch !== " " && NONPRINT.test(ch)) {
      out += cp <= 0xff ? "\\x" + cp.toString(16).padStart(2, "0") : cp <= 0xffff ? "\\u" + cp.toString(16).padStart(4, "0")
        : "\\U" + cp.toString(16).padStart(8, "0");
    } else out += ch;
  }
  return out + q;
}

/** repr() of a JSON-like value (lists of names, numbers, ...). */
export function pyReprOf(v: unknown): string {
  if (typeof v === "string") return reprStr(v);
  if (typeof v === "number" || typeof v === "boolean" || v === null || v === undefined) return pyStrOf(v);
  if (Array.isArray(v)) return "[" + v.map(pyReprOf).join(", ") + "]";
  if (typeof v === "object") {
    return "{" + Object.entries(v as Record<string, unknown>).map(([k, x]) => `${reprStr(k)}: ${pyReprOf(x)}`).join(", ") + "}";
  }
  return String(v);
}

/** Python truthiness of a cell or a spec value. */
export function pyTruthy(v: unknown): boolean {
  if (v === null || v === undefined || v === false || v === 0 || v === "") return false;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === "object" && !("date" in (v as object))) return Object.keys(v as object).length > 0;
  return true;
}

/** _row_number: read.header_row / read.data_start_row as a 1-based row number, as Python's int() reads it (nRows:
 *  the row must be in the sheet). */
export function rowNumber(v: unknown, key: string, nRows: number | null = null): number {
  let n: number | null = null;
  if (typeof v === "number") n = Number.isFinite(v) ? Math.trunc(v) : null;
  else if (typeof v === "string") {
    const t = asciiDigits(pyStrip(v));
    if (/^[+-]?\d+(_\d+)*$/.test(t)) n = parseInt(t.replace(/_/g, ""), 10);
  }
  if (n === null || n < 1) {
    throw new PlotkitError(`read.${key} must be a row number from 1, not ${pyReprOf(v)}`, "rows count from 1 at the top of the sheet, e.g. 3");
  }
  if (nRows !== null && n > nRows) throw new PlotkitError(`read.${key} ${n} is after the end of the sheet (it has ${nRows} rows)`, `check read.${key}`);
  return n;
}

// The order CPython iterates a set of small non-negative ints (hash(n) == n): max(set(xs), key=xs.count) keeps the
// first maximum in this order, so ties resolve as in Python.
export function pySetOrder(xs: number[]): number[] {
  const LINEAR_PROBES = 9, PERTURB_SHIFT = 5;
  let mask = 7, table: (number | undefined)[] = new Array(8), fill = 0;
  const insert = (tab: (number | undefined)[], m: number, key: number, check: boolean): boolean => {
    let perturb = key, i = key & m;
    for (;;) {
      const probes = i + LINEAR_PROBES <= m ? LINEAR_PROBES : 0;
      for (let j = 0; j <= probes; j++) {
        const e = tab[i + j];
        if (e === undefined) { tab[i + j] = key; return true; }
        if (check && e === key) return false;
      }
      perturb = Math.floor(perturb / 2 ** PERTURB_SHIFT);
      i = (i * 5 + 1 + perturb) & m;
    }
  };
  for (const x of xs) {
    if (!Number.isInteger(x) || x < 0 || x > 0x3fffffff) throw new Error("pySetOrder: small non-negative ints only");
    if (!insert(table, mask, x, true)) continue;
    fill++;
    if (fill * 5 >= mask * 3) {
      let size = 8;
      while (size <= fill * 4) size *= 2;
      const old = table;
      table = new Array(size);
      mask = size - 1;
      for (const e of old) if (e !== undefined) insert(table, mask, e, false);
    }
  }
  return table.filter((e): e is number => e !== undefined);
}

/** max(set(xs), key=xs.count). */
export function pyMode(xs: number[]): number {
  const count = new Map<number, number>();
  for (const x of xs) count.set(x, (count.get(x) ?? 0) + 1);
  let best = NaN, bestN = -1;
  for (const x of pySetOrder(xs)) if (count.get(x)! > bestN) { best = x; bestN = count.get(x)!; }
  return best;
}

// =================================================================== paths
/** PurePosixPath(p) as a string: "." parts and repeated slashes dropped. */
export function normPath(p: string): string {
  if (p === "") return ".";
  const lead = p.startsWith("//") && !p.startsWith("///") ? "//" : p.startsWith("/") ? "/" : "";
  const parts = p.split("/").filter(x => x !== "" && x !== ".");
  const s = lead + parts.join("/");
  return s === "" ? "." : s;
}

/** Path(p).name */
export function pathName(p: string): string {
  const s = normPath(p);
  if (s === "." || s === "/" || s === "//") return "";
  return s.slice(s.lastIndexOf("/") + 1);
}

/** Path(p).parent, as a string */
export function pathParent(p: string): string {
  const s = normPath(p);
  const i = s.lastIndexOf("/");
  if (i < 0) return ".";
  if (i === 0) return "/";
  if (i === 1 && s.startsWith("//")) return "//";
  return s.slice(0, i);
}

/** Path(p).suffix */
export function pathSuffix(p: string): string {
  const name = pathName(p);
  const i = name.lastIndexOf(".");
  return i > 0 && i < name.length - 1 ? name.slice(i) : "";
}

/** Path(p).stem */
export function pathStem(p: string): string {
  const name = pathName(p);
  const i = name.lastIndexOf(".");
  return i > 0 && i < name.length - 1 ? name.slice(0, i) : name;
}

/** The file a spec names, among the files the host gave (Python: the path must exist). */
export function findFile(files: InputFile[], name: string): InputFile {
  const want = normPath(String(name));
  const hit = files.find(f => f.name === name) ?? files.find(f => normPath(f.name) === want);
  if (hit) return hit;
  const parent = pathParent(want);
  const near = files.filter(f => pathParent(f.name) === parent).map(f => pathName(f.name)).slice(0, 20);
  const all = files.map(f => f.name).slice(0, 20);
  throw new PlotkitError(`file not found: ${name}`,
    near.length ? `files in ${parent}: ${near.join(", ")}` : all.length ? `files given: ${all.join(", ")}` : "check the path");
}

// =================================================================== reading
const NUM_RE = /^[+-]?(\p{Nd}+(\.\p{Nd}*)?|\.\p{Nd}+)([eE][+-]?\p{Nd}+)?$/u;

/** _to_num: a cell as a float, or null (text that is not a number, dates, booleans, empty). */
export function toNum(v: Cell | undefined, decimal = "."): number | null {
  if (v === null || v === undefined || typeof v === "boolean") return null;
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  if (typeof v !== "string") return null;                      // dates, times, ...
  let s = pyStrip(v).replaceAll("−", "-").replaceAll(" ", "");
  if (!s) return null;
  if (decimal === ",") s = s.replaceAll(".", "").replaceAll(",", ".");
  if (!NUM_RE.test(s)) return null;
  return Number(asciiDigits(s));
}

export function colLetter(i: number): string {
  let s = "";
  i += 1;
  while (i) {
    const r = (i - 1) % 26;
    i = Math.floor((i - 1) / 26);
    s = String.fromCharCode(65 + r) + s;
  }
  return s;
}

export function colIndex(letter: string): number {
  let n = 0;
  for (const ch of letter.toUpperCase()) n = n * 26 + (ch.codePointAt(0)! - 64);
  return n - 1;
}

function textDecode(label: string, bytes: Uint8Array): string {
  return new TextDecoder(label, { fatal: true, ignoreBOM: true }).decode(bytes);
}

// cp949 (Python's codec, strict). The platform's "euc-kr" decoder is not cp949 everywhere (Node's ICU one lacks the
// 8822 UHC Hangul and passes some invalid bytes), so only its KS X 1001 table is used: the UHC extension holds the
// Hangul syllables KS X 1001 lacks, in Unicode order.
let ksTable: Uint16Array | null = null;
let uhcHangul: Uint16Array | null = null;

function cp949Tables(): [Uint16Array, Uint16Array] {
  if (ksTable && uhcHangul) return [ksTable, uhcHangul];
  const ks = new Uint16Array(94 * 94);
  const dec = new TextDecoder("euc-kr");
  const inKs = new Uint8Array(11172);
  for (let b = 0xa1; b <= 0xfe; b++) {
    if (b === 0xc9 || b === 0xfe) continue;                     // user-defined rows: not in cp949
    for (let t = 0xa1; t <= 0xfe; t++) {
      const s = dec.decode(new Uint8Array([b, t]));
      if (s.length !== 1 || s === "\ufffd") continue;
      const cp = s.charCodeAt(0);
      ks[(b - 0xa1) * 94 + (t - 0xa1)] = cp;
      if (cp >= 0xac00 && cp <= 0xd7a3) inKs[cp - 0xac00] = 1;
    }
  }
  ks[(0xa2 - 0xa1) * 94 + (0xe6 - 0xa1)] = 0x20ac;              // €, ® (added to KS X 1001 in 1998)
  ks[(0xa2 - 0xa1) * 94 + (0xe7 - 0xa1)] = 0xae;
  const ext: number[] = [];
  for (let k = 0; k < 11172; k++) if (!inKs[k]) ext.push(0xac00 + k);
  ksTable = ks;
  uhcHangul = Uint16Array.from(ext);
  return [ksTable, uhcHangul];
}

/** Position of a UHC extension code (lead 0x81-0xC6) among the extension codes, or -1. */
function uhcIndex(b: number, t: number): number {
  const k = t >= 0x41 && t <= 0x5a ? t - 0x41 : t >= 0x61 && t <= 0x7a ? t - 0x61 + 26 : t >= 0x81 && t <= 0xfe ? t - 0x81 + 52 : -1;
  if (k < 0 || b < 0x81 || b > 0xc6) return -1;
  if (b <= 0xa0) return (b - 0x81) * 178 + k;
  if (k >= 52 + 32) return -1;                                  // leads A1-C6: trail up to 0xA0
  return 32 * 178 + (b - 0xa1) * 84 + k;
}

/** bytes.decode("cp949"), or with ksOnly bytes.decode("euc_kr") (KS X 1001 only; its 8-byte A4D4 make-up
 *  sequences are not decoded); throws on bytes Python's codec rejects. */
export function decodeCp949(raw: Uint8Array, ksOnly = false): string {
  const [ks, ext] = cp949Tables();
  const out: number[] = [];
  let s = "";
  for (let i = 0; i < raw.length;) {
    const b = raw[i];
    if (b < 0x80) { out.push(b); i++; }
    else {
      const t = raw[i + 1];
      if (t === undefined) throw new TypeError("truncated cp949 data");
      let cp = 0;
      if (b >= 0xa1 && b <= 0xfe && t >= 0xa1 && t <= 0xfe) cp = ksOnly && b === 0xa4 && t === 0xd4 ? 0 : ks[(b - 0xa1) * 94 + (t - 0xa1)];
      else if (!ksOnly) {
        const k = uhcIndex(b, t);
        if (k >= 0 && k < ext.length) cp = ext[k];
      }
      if (!cp) throw new TypeError("invalid cp949 data");
      out.push(cp);
      i += 2;
    }
    if (out.length >= 8192) { s += String.fromCharCode(...out); out.length = 0; }
  }
  return s + String.fromCharCode(...out);
}

function latin1(bytes: Uint8Array): string {
  let s = "";
  for (let i = 0; i < bytes.length; i += 8192) s += String.fromCharCode(...bytes.subarray(i, i + 8192));
  return s;
}

// Python's codec names (encodings.aliases, after normalize_encoding) for the encodings decoded here.
const CODECS: Record<string, string[]> = {
  "utf-8": ["utf_8", "u8", "utf", "utf8", "utf8_ucs2", "utf8_ucs4", "cp65001"],
  "utf-8-sig": ["utf_8_sig"],
  "utf-16": ["utf_16", "u16", "utf16"],
  "utf-16le": ["utf_16_le", "utf_16le", "unicodelittleunmarked"],
  "utf-16be": ["utf_16_be", "utf_16be", "unicodebigunmarked"],
  "cp949": ["cp949", "949", "ms949", "uhc"],
  "euc-kr": ["euc_kr", "euckr", "korean", "ksc5601", "ks_c_5601", "ks_c_5601_1987", "ksx1001", "ks_x_1001"],
  "latin-1": ["latin_1", "iso8859_1", "8859", "cp819", "csisolatin1", "ibm819", "iso8859", "iso_8859_1", "iso_8859_1_1987",
    "iso_ir_100", "l1", "latin", "latin1"],
  "ascii": ["ascii", "646", "ansi_x3.4_1968", "ansi_x3_4_1968", "ansi_x3.4_1986", "cp367", "csascii", "ibm367", "iso646_us",
    "iso_646.irv_1991", "iso_ir_6", "us", "us_ascii"],
  "cp1252": ["cp1252", "windows_1252"],
};

/** Python's normalize_encoding (after lower()): runs of other characters than ASCII letters, digits and "." become
 *  one "_", none at the ends. */
function codecKey(name: string): string {
  return name.toLowerCase().split(/[^a-z0-9.]+/).filter(Boolean).join("_");
}

/** bytes.decode(encoding) for read.encoding: Python's codecs for the encodings above, else the platform's decoder
 *  for that label. Errors as plotkit.core._decode raises them. */
function decodeAs(raw: Uint8Array, encoding: string, name: string): string {
  const key = codecKey(encoding);
  const codec = Object.keys(CODECS).find(c => CODECS[c].includes(key));
  const notText = () => new PlotkitError(`${name} is not ${encoding} text`,
    'check read.encoding (e.g. "utf-8" or "cp949"), or leave it out to detect the encoding');
  let dec: InstanceType<typeof TextDecoder> | null = null;
  if (!codec) {
    for (const label of [encoding.trim().toLowerCase(), key.replace(/_/g, "-")]) {
      try {
        dec = new TextDecoder(label, { fatal: true, ignoreBOM: true });
        break;
      } catch { /* next */ }
    }
    if (!dec) throw new PlotkitError(`unknown encoding "${encoding}"`, 'use "utf-8", "cp949", "utf-16" or "latin-1", or leave read.encoding out');
  }
  try {
    switch (codec) {
      case "utf-8": return textDecode("utf-8", raw);
      case "utf-8-sig": return textDecode("utf-8", raw[0] === 0xef && raw[1] === 0xbb && raw[2] === 0xbf ? raw.subarray(3) : raw);
      case "utf-16":
        if (raw[0] === 0xfe && raw[1] === 0xff) return textDecode("utf-16be", raw.subarray(2));
        return textDecode("utf-16le", raw[0] === 0xff && raw[1] === 0xfe ? raw.subarray(2) : raw);
      case "utf-16le": return textDecode("utf-16le", raw);
      case "utf-16be": return textDecode("utf-16be", raw);
      case "cp949": return decodeCp949(raw);
      case "euc-kr": return decodeCp949(raw, true);
      case "latin-1": return latin1(raw);
      case "ascii":
        if (raw.some(b => b > 0x7f)) throw new TypeError("not ascii");
        return latin1(raw);
      case "cp1252":
        if (raw.some(b => b === 0x81 || b === 0x8d || b === 0x8f || b === 0x90 || b === 0x9d)) throw new TypeError("undefined byte");
        return textDecode("windows-1252", raw);
      default: return dec!.decode(raw);
    }
  } catch {
    throw notText();
  }
}

/** _decode: read.encoding if set; else UTF-16 (BOM or many zero bytes), UTF-8 with BOM, UTF-8, cp949, latin-1.
 *  name: the file, for the errors. */
export function decodeText(raw: Uint8Array, encoding?: unknown, name = "the file"): string {
  if (pyTruthy(encoding)) return decodeAs(raw, String(encoding), name);
  const head = raw.subarray(0, 2000);
  let zeros = 0;
  for (const b of head) if (b === 0) zeros++;
  let detected: [string, () => string] | null = null;
  if ((raw[0] === 0xff && raw[1] === 0xfe) || (raw[0] === 0xfe && raw[1] === 0xff)) {
    detected = ["UTF-16", () => textDecode(raw[0] === 0xff ? "utf-16le" : "utf-16be", raw.subarray(2))];
  } else if (raw[0] === 0xef && raw[1] === 0xbb && raw[2] === 0xbf) {
    detected = ["UTF-8", () => textDecode("utf-8", raw.subarray(3))];
  } else if (zeros > Math.floor(head.length / 4)) {                 // UTF-16 without BOM
    detected = ["UTF-16", () => textDecode(head[1] === 0 ? "utf-16le" : "utf-16be", raw)];
  }
  if (detected) {
    try {
      return detected[1]();
    } catch {
      throw new PlotkitError(`${name} looks like ${detected[0]} text but could not be decoded`, "set read.encoding, or save the file again as UTF-8");
    }
  }
  try {
    return textDecode("utf-8", raw);
  } catch { /* next */ }
  try {
    return decodeCp949(raw);
  } catch { /* next */ }
  return latin1(raw);
}

const SEP_NAMES: Record<string, string> = { "tab": "\t", "\\t": "\t", "space": "space", "whitespace": "space", " ": "space" };
const DATE_TIME_SUB = new RegExp(`(?<!${PY_W})\\p{Nd}{4}[./-]\\p{Nd}{1,2}[./-]\\p{Nd}{1,2}(?!${PY_W})|`
  + `(?<!${PY_W})\\p{Nd}{1,2}:\\p{Nd}{2}(:\\p{Nd}{2})?(?!${PY_W})`, "gu");
const DECIMAL_COMMA = /(?<![\p{Nd}.])-?\p{Nd}+,\p{Nd}+(?![\p{Nd}.])/u;
const DECIMAL_POINT = /\p{Nd}\.\p{Nd}/u;
const HEADER_SPLIT = new RegExp(`[${PY_WS}]{2,}|\\t`, "u");

/** _read_text: {stem: rows of str}, decimal mark. Separator and decimal mark are detected unless read sets them. */
export function readText(name: string, bytes: Uint8Array, ro: ReadOptions = {}): [Map<string, Cell[][]>, string] {
  let sep: unknown = ro.sep ?? null;
  if (sep !== null && (typeof sep !== "string" || sep === "")) {
    throw new PlotkitError(`read.sep must be a separator like "," or "tab", not ${pyReprOf(sep)}`, 'use ",", ";", "tab" or "space", or leave it out');
  }
  const text = decodeText(bytes, ro.encoding, pathName(name));
  const lines = splitLines(text);
  const nonblank = lines.filter(ln => pyStrip(ln));
  const tail = nonblank.length > 60 ? nonblank.slice(-60) : nonblank;
  if (typeof sep === "string" && Object.hasOwn(SEP_NAMES, sep)) sep = SEP_NAMES[sep];
  if (sep === null) {                // the most lines with the same count wins (preamble/footer lines may differ)
    for (const cand of ["\t", ";", ",", "|"]) {
      const counts = tail.map(ln => ln.split(cand).length - 1);
      if (counts.length) {
        const mode = pyMode(counts);
        if (mode >= 1 && counts.filter(c => c === mode).length >= 0.7 * counts.length) {
          sep = cand;
          break;
        }
      }
    }
    sep = sep || "space";
  }
  let decimal: unknown = ro.decimal ?? null;
  if (decimal === null) {
    const sample = tail.join(" ").replace(DATE_TIME_SUB, " ");
    decimal = sep !== "," && DECIMAL_COMMA.test(sample) && !DECIMAL_POINT.test(sample) ? "," : ".";
  }
  const dec = String(decimal);
  const rows: Cell[][] = [];
  for (const ln of lines) {
    if (!pyStrip(ln)) {
      rows.push([]);
      continue;
    }
    let parts: string[];
    if (sep === "space") {
      parts = pySplitWs(ln);
      const nums = parts.filter(p => toNum(p, dec) !== null).length;
      if (nums < parts.length) parts = pyStrip(ln).split(HEADER_SPLIT);   // header line: split on 2+ spaces
    } else {
      parts = ln.split(sep as string).map(p => pyStrip(pyStrip(p), '"'));
    }
    rows.push(parts);
  }
  return [new Map([[pathStem(name), rows]]), dec];
}

// ------------------------------------------------------------------- .xlsx (openpyxl read_only, data_only)
// openpyxl's builtin number formats; a style's format decides whether its numbers are dates.
const BUILTIN_FORMATS: Record<number, string> = {
  0: "General", 1: "0", 2: "0.00", 3: "#,##0", 4: "#,##0.00", 5: '"$"#,##0_);("$"#,##0)', 6: '"$"#,##0_);[Red]("$"#,##0)',
  7: '"$"#,##0.00_);("$"#,##0.00)', 8: '"$"#,##0.00_);[Red]("$"#,##0.00)', 9: "0%", 10: "0.00%", 11: "0.00E+00",
  12: "# ?/?", 13: "# ??/??", 14: "mm-dd-yy", 15: "d-mmm-yy", 16: "d-mmm", 17: "mmm-yy", 18: "h:mm AM/PM",
  19: "h:mm:ss AM/PM", 20: "h:mm", 21: "h:mm:ss", 22: "m/d/yy h:mm", 37: "#,##0_);(#,##0)", 38: "#,##0_);[Red](#,##0)",
  39: "#,##0.00_);(#,##0.00)", 40: "#,##0.00_);[Red](#,##0.00)", 41: '_(* #,##0_);_(* \\(#,##0\\);_(* "-"_);_(@_)',
  42: '_("$"* #,##0_);_("$"* \\(#,##0\\);_("$"* "-"_);_(@_)', 43: '_(* #,##0.00_);_(* \\(#,##0.00\\);_(* "-"??_);_(@_)',
  44: '_("$"* #,##0.00_)_("$"* \\(#,##0.00\\)_("$"* "-"??_)_(@_)', 45: "mm:ss", 46: "[h]:mm:ss", 47: "mmss.0",
  48: "##0.0E+0", 49: "@",
};
const DATE_STRIP = /"[^\n]*?"|\[(?!hh?\]|mm?\]|ss?\])[^\]]*\]/g;
const TIMEDELTA_RE = /\[hh?\](:mm(:ss(\.0*)?)?)?|\[mm?\](:ss(\.0*)?)?|\[ss?\](\.0*)?/i;

function isDateFormat(fmt: string | undefined): boolean {
  if (fmt === undefined) return false;
  return /(?<![_\\])[dmhysDMHYS]/.test(fmt.split(";")[0].replace(DATE_STRIP, ""));
}

function isTimedeltaFormat(fmt: string | undefined): boolean {
  if (fmt === undefined) return false;
  return TIMEDELTA_RE.test(fmt.split(";")[0]);
}

function xmlUnescape(s: string): string {
  return s.replace(/&(#x[0-9a-fA-F]+|#\d+|amp|lt|gt|quot|apos);/g, (m, e: string) =>
    e[0] === "#" ? String.fromCodePoint(parseInt(e[1] === "x" ? e.slice(2) : e.slice(1), e[1] === "x" ? 16 : 10))
      : ({ amp: "&", lt: "<", gt: ">", quot: '"', apos: "'" } as Record<string, string>)[e] ?? m);
}

function xmlAttrs(tag: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const m of tag.matchAll(/([\w:.-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g)) out[m[1].replace(/^[\w.-]+:/, "")] = xmlUnescape(m[2] ?? m[3]);
  return out;
}

async function inflateRaw(data: Uint8Array): Promise<Uint8Array> {
  const ds = new DecompressionStream("deflate-raw");
  const writer = ds.writable.getWriter();
  writer.write(data as Uint8Array<ArrayBuffer>).catch(() => undefined);
  writer.close().catch(() => undefined);
  const chunks: Uint8Array[] = [];
  const reader = ds.readable.getReader();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }
  const out = new Uint8Array(chunks.reduce((n, c) => n + c.length, 0));
  let k = 0;
  for (const c of chunks) { out.set(c, k); k += c.length; }
  return out;
}

/** One file of a zip archive (stored or deflated), or null. */
async function zipEntry(zip: Uint8Array, name: string): Promise<Uint8Array | null> {
  const dv = new DataView(zip.buffer, zip.byteOffset, zip.byteLength);
  let eocd = -1;
  for (let i = zip.length - 22; i >= Math.max(0, zip.length - 22 - 65535); i--) {
    if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) return null;
  const count = dv.getUint16(eocd + 10, true);
  let p = dv.getUint32(eocd + 16, true);
  const td = new TextDecoder();
  for (let k = 0; k < count && p + 46 <= zip.length; k++) {
    if (dv.getUint32(p, true) !== 0x02014b50) return null;
    const method = dv.getUint16(p + 10, true), size = dv.getUint32(p + 20, true);
    const nlen = dv.getUint16(p + 28, true), elen = dv.getUint16(p + 30, true), clen = dv.getUint16(p + 32, true);
    const local = dv.getUint32(p + 42, true);
    const entry = td.decode(zip.subarray(p + 46, p + 46 + nlen)).replace(/^\//, "");
    if (entry === name) {
      const start = local + 30 + dv.getUint16(local + 26, true) + dv.getUint16(local + 28, true);
      const data = zip.subarray(start, start + size);
      if (method === 0) return data;
      if (method === 8) return inflateRaw(data);
      return null;
    }
    p += 46 + nlen + elen + clen;
  }
  return null;
}

/** openpyxl's date_formats / timedelta_formats: per cell style index (cellXfs order), from the raw styles.xml
 *  (ExcelJS drops the backslash escapes of format codes, which decide what openpyxl takes for a date). */
async function styleKinds(zip: Uint8Array): Promise<Map<number, "date" | "timedelta">> {
  const out = new Map<number, "date" | "timedelta">();
  let raw: Uint8Array | null = null;
  try {
    raw = await zipEntry(zip, "xl/styles.xml");
  } catch { /* unreadable styles: no dates, as openpyxl without a stylesheet */ }
  if (!raw) return out;
  const xml = new TextDecoder().decode(raw);
  const custom = new Map<number, string>();
  for (const m of xml.matchAll(/<(?:[\w.-]+:)?numFmt\b([^>]*)>/g)) {
    const a = xmlAttrs(m[1]);
    if (a.numFmtId !== undefined && a.formatCode !== undefined) custom.set(parseInt(a.numFmtId, 10), a.formatCode);
  }
  const block = /<(?:[\w.-]+:)?cellXfs\b[^>]*?(?:\/>|>([\s\S]*?)<\/(?:[\w.-]+:)?cellXfs>)/.exec(xml);
  let idx = 0;
  for (const m of (block?.[1] ?? "").matchAll(/<(?:[\w.-]+:)?xf\b([^>]*)>/g)) {
    const id = parseInt(xmlAttrs(m[1]).numFmtId ?? "0", 10);
    const fmt = custom.has(id) ? custom.get(id) : BUILTIN_FORMATS[id];
    if (isDateFormat(fmt)) out.set(idx, isTimedeltaFormat(fmt) ? "timedelta" : "date");
    idx++;
  }
  return out;
}

/** The shared strings as openpyxl reads them (read_string_table: the text of each <si>, plain text then runs,
 *  phonetic runs left out, "x005F_" removed; other _xHHHH_ escapes stay as they are), from the raw part. */
async function sharedStrings(zip: Uint8Array): Promise<string[] | null> {
  let path = "xl/sharedStrings.xml";
  try {
    const ct = await zipEntry(zip, "[Content_Types].xml");
    for (const o of ct ? new TextDecoder().decode(ct).matchAll(/<(?:[\w.-]+:)?Override\b[^>]*>/g) : []) {
      const a = xmlAttrs(o[0]);
      if (a.ContentType === "application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml" && a.PartName) path = a.PartName.replace(/^\//, "");
    }
    const raw = await zipEntry(zip, path);
    if (!raw) return null;
    const xml = new TextDecoder().decode(raw).replace(/\r\n?/g, "\n");          // XML end-of-line handling
    const out: string[] = [];
    for (const si of xml.matchAll(/<(?:[\w.-]+:)?si\b[^>]*?(?:\/>|>([\s\S]*?)<\/(?:[\w.-]+:)?si>)/g)) {
      const body = (si[1] ?? "").replace(/<(?:[\w.-]+:)?rPh\b[\s\S]*?<\/(?:[\w.-]+:)?rPh>/g, "");
      let text = "";
      for (const t of body.matchAll(/<(?:[\w.-]+:)?t\b[^>]*?(?:\/>|>([\s\S]*?)<\/(?:[\w.-]+:)?t>)/g)) {
        text += (t[1] ?? "").split(/(<!\[CDATA\[[\s\S]*?\]\]>)/).map(x => x.startsWith("<![CDATA[") ? x.slice(9, -3) : xmlUnescape(x)).join("");
      }
      out.push(text.replaceAll("x005F_", ""));
    }
    return out;
  } catch {
    return null;
  }
}

const DAY_MS = 86400000;

/** Days from 1970-01-01 to a proleptic Gregorian date (any year). */
export function daysFromCivil(y: number, m: number, d: number): number {
  y -= m <= 2 ? 1 : 0;
  const era = Math.floor(y / 400);
  const yoe = y - era * 400;
  const doy = Math.floor((153 * (m + (m > 2 ? -3 : 9)) + 2) / 5) + d - 1;
  const doe = yoe * 365 + Math.floor(yoe / 4) - Math.floor(yoe / 100) + doy;
  return era * 146097 + doe - 719468;
}

/** The date of a day number (days since 1970-01-01). */
export function civilFromDays(z: number): [number, number, number] {
  z += 719468;
  const era = Math.floor(z / 146097);
  const doe = z - era * 146097;
  const yoe = Math.floor((doe - Math.floor(doe / 1460) + Math.floor(doe / 36524) - Math.floor(doe / 146096)) / 365);
  const doy = doe - (365 * yoe + Math.floor(yoe / 4) - Math.floor(yoe / 100));
  const mp = Math.floor((5 * doy + 2) / 153);
  const d = doy - Math.floor((153 * mp + 2) / 5) + 1;
  const m = mp + (mp < 10 ? 3 : -9);
  return [era * 400 + yoe + (m <= 2 ? 1 : 0), m, d];
}

const p2 = (n: number) => String(n).padStart(2, "0");

/** datetime.isoformat() of epoch milliseconds (naive, read as UTC); microseconds kept from a fractional part. */
export function isoFromMs(ms: number): string {
  const days = Math.floor(ms / DAY_MS);
  const [y, m, d] = civilFromDays(days);
  const us = Math.round((ms - days * DAY_MS) * 1000);
  const secs = Math.floor(us / 1e6), frac = us - secs * 1e6;
  return `${String(y).padStart(4, "0")}-${p2(m)}-${p2(d)}T${p2(Math.floor(secs / 3600))}:${p2(Math.floor(secs / 60) % 60)}:${p2(secs % 60)}`
    + (frac ? "." + String(frac).padStart(6, "0") : "");
}

/** Epoch milliseconds of a naive ISO date-time, read as UTC. */
export function msFromIso(iso: string): number {
  const m = /^(\d{4,})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?)?$/.exec(iso);
  if (!m) return NaN;
  return daysFromCivil(+m[1], +m[2], +m[3]) * DAY_MS + ((+(m[4] ?? 0)) * 3600 + (+(m[5] ?? 0)) * 60 + (+(m[6] ?? 0))) * 1000
    + (m[7] ? +m[7].padEnd(6, "0") / 1000 : 0);
}

/** str(datetime.timedelta) from days, seconds, microseconds (normalized). */
function timedeltaStr(totalUs: number): string {
  const days = Math.floor(totalUs / 86400e6);
  const rest = totalUs - days * 86400e6;
  const secs = Math.floor(rest / 1e6), us = rest - secs * 1e6;
  let s = `${Math.floor(secs / 3600)}:${p2(Math.floor(secs / 60) % 60)}:${p2(secs % 60)}`;
  if (days) s = `${days} day${Math.abs(days) !== 1 ? "s" : ""}, ` + s;
  return us ? s + "." + String(us).padStart(6, "0") : s;
}

/** openpyxl's from_excel: a date cell's serial number as a datetime ({date}), a time or a timedelta (their str(),
 *  which is what plotkit makes of them), or "#VALUE!" outside the datetime range. */
export function fromExcel(value: number, date1904: boolean, timedelta: boolean): Cell {
  if (timedelta) {
    const d = Math.trunc(value), secsF = (value - d) * 86400, s = Math.trunc(secsF);
    let us = d * 86400e6 + s * 1e6 + pyRound((secsF - s) * 1e6);
    if (us % 1e6) {
      const sec = Math.floor(us / 1e6);
      us = sec * 1e6 + pyRound((us - sec * 1e6) / 1000) * 1000;
    }
    return timedeltaStr(us);
  }
  const [dayF, fraction] = pyDivmod(value, 1);
  let day = dayF;
  const ms = pyRound(fraction * 86400 * 1000);
  if (value >= 0 && value < 1 && ms < DAY_MS) {                 // a time of day: str(time)
    const secs = Math.floor(ms / 1000), frac = ms % 1000;
    return `${p2(Math.floor(secs / 3600))}:${p2(Math.floor(secs / 60) % 60)}:${p2(secs % 60)}` + (frac ? "." + String(frac * 1000).padStart(6, "0") : "");
  }
  if (value > 0 && value < 60 && !date1904) day += 1;
  const epoch = date1904 ? daysFromCivil(1904, 1, 1) : daysFromCivil(1899, 12, 30);
  const t = (epoch + day) * DAY_MS + ms;
  const y = civilFromDays(Math.floor(t / DAY_MS))[0];
  if (!Number.isFinite(t) || y < 1 || y > 9999) return "#VALUE!";
  return { date: isoFromMs(t) };
}

// ExcelJS value types (Enums.ValueType)
const T_MERGE = 1, T_NUMBER = 2, T_STRING = 3, T_HYPERLINK = 5, T_FORMULA = 6, T_BOOLEAN = 9, T_ERROR = 10;

interface RawCell {
  type: number;
  value: unknown;
  result: unknown;
  styleId: number | undefined;
}

function richText(v: unknown): string {
  if (v && typeof v === "object" && Array.isArray((v as { richText?: unknown }).richText)) {
    return (v as { richText: { text?: string }[] }).richText.map(r => r.text ?? "").join("");
  }
  return v === undefined || v === null ? "" : String(v);
}

/** ExcelJS decodes the _xHHHH_ escapes of rich text runs, openpyxl keeps them. Control characters can only come
 *  from such escapes (XML can not hold them), so they are written back. */
function reescape(s: string): string {
  return s.replace(/[\x00-\x08\x0b-\x1f]/g, ch => `_x${ch.charCodeAt(0).toString(16).toUpperCase().padStart(4, "0")}_`);
}

let excelJS: Promise<any> | null = null;
function loadExcelJS(): Promise<any> {
  excelJS ??= import("exceljs").then((m: any) => m.default ?? m);
  return excelJS;
}

/** _read_xlsx: openpyxl's load_workbook(read_only=True, data_only=True) and iter_rows(values_only=True), with
 *  ExcelJS. The sheets' rows are taken from ExcelJS's parsed model before it builds its worksheets (where merged
 *  cells repeat their value and the <dimension> of the sheet, which sets openpyxl's row width and row count, is
 *  lost); numbers are converted to dates by openpyxl's rule on the raw styles. */
export async function readXlsx(name: string, bytes: Uint8Array): Promise<Map<string, Cell[][]>> {
  const ExcelJS = await loadExcelJS();
  const kinds = await styleKinds(bytes);
  const strings = await sharedStrings(bytes);
  const wb = new ExcelJS.Workbook();
  const xlsx = wb.xlsx;
  const raw = new WeakMap<object, RawCell>();
  let sheets: any[] = [];
  let date1904 = false;
  const reconcile = xlsx.reconcile;
  xlsx.reconcile = function (this: unknown, model: any, options: unknown) {
    for (const ws of model.worksheets ?? []) {
      for (const row of ws.rows ?? []) {
        for (const c of row.cells ?? []) raw.set(c, { type: c.type, value: c.value, result: c.result, styleId: c.styleId });
      }
    }
    reconcile.call(this, model, options);
    // in the workbook's order (ExcelJS keeps its parsed sheets in archive order)
    const all: any[] = model.worksheets ?? [];
    sheets = (model.sheets ?? []).map((sh: any) => all.find(ws => ws.id === sh.id && ws.name === sh.name)).filter(Boolean);
    date1904 = !!(model.properties && model.properties.date1904);
  };
  try {
    await xlsx.load(bytes);
  } catch {
    throw new PlotkitError(`${pathName(name)} could not be read as an .xlsx file`,
      "check that it is an Excel workbook; open it in Excel and save it again as .xlsx");
  }
  const number = (v: number, styleId: number | undefined): Cell => {
    const k = styleId === undefined ? undefined : kinds.get(styleId);
    return k ? fromExcel(v, date1904, k === "timedelta") : v;
  };
  const value = (c: any): Cell => {
    const r = raw.get(c);
    if (!r) return null;
    switch (r.type) {
      case T_NUMBER:
        return typeof r.value === "number" ? number(r.value, r.styleId) : null;
      case T_FORMULA: {
        const v = r.result;
        if (v === undefined || v === null) return null;
        if (typeof v === "number") return number(v, r.styleId);
        if (typeof v === "boolean") return v;
        if (typeof v === "object" && "error" in (v as object)) return String((v as { error: unknown }).error);
        return String(v);
      }
      case T_BOOLEAN:
        return r.value as boolean;
      case T_ERROR:
        return String((r.value as { error: unknown })?.error ?? "");
      case T_STRING: {
        const v = c.type === T_HYPERLINK ? c.text : c.value;
        if (typeof r.value === "number") return strings?.[r.value] ?? reescape(richText(v)).replaceAll("x005F_", "");
        return typeof v === "string" ? v : reescape(richText(v));                     // inline string
      }
      case T_MERGE:
      default:
        return null;
    }
  };
  const out = new Map<string, Cell[][]>();
  for (const ws of sheets) {
    const dim = parseDimension(ws.dimensions);
    out.set(String(ws.name), sheetRows(ws.rows ?? [], dim, value));
  }
  return out;
}

/** openpyxl's worksheet size from <dimension ref>: [max_col, max_row] (null when missing). */
function parseDimension(ref: unknown): [number | null, number | null] {
  if (typeof ref !== "string") return [null, null];
  const m = /^\$?([A-Za-z]{1,3})?\$?(\d+)?(?::\$?([A-Za-z]{1,3})?\$?(\d+)?)?$/.exec(ref);
  if (!m) return [null, null];
  const col = m[3] ?? m[1], row = m[4] ?? m[2];
  return [col ? colIndex(col) + 1 : null, row ? parseInt(row, 10) : null];
}

/** ReadOnlyWorksheet._cells_by_row from A1 to the dimension's end: missing rows filled, every row max_col wide
 *  (without a dimension: as long as its last cell), rows past max_row dropped. */
function sheetRows(rows: any[], [maxCol, maxRow]: [number | null, number | null], value: (c: any) => Cell): Cell[][] {
  const empty = (): Cell[] => (maxCol === null ? [] : new Array<Cell>(maxCol).fill(null));
  const out: Cell[][] = [];
  let counter = 1, idx = 1, rowCounter = 0;
  for (const row of rows) {
    idx = Number.isFinite(row.number) ? row.number : rowCounter + 1;
    rowCounter = idx;
    if (maxRow !== null && idx > maxRow) break;
    for (; counter < idx; counter++) out.push(empty());
    if (counter <= idx) {
      const cells: { col: number; v: Cell }[] = [];
      let colCounter = 0;
      for (const c of row.cells ?? []) {
        const m = typeof c.address === "string" ? /^\$?([A-Za-z]+)\$?\d+$/.exec(c.address) : null;
        colCounter = m ? colIndex(m[1]) + 1 : colCounter + 1;
        cells.push({ col: colCounter, v: value(c) });
      }
      if (!cells.length && maxCol === null) out.push([]);
      else {
        const width = maxCol ?? cells[cells.length - 1].col;
        const r = new Array<Cell>(width).fill(null);
        for (const { col, v } of cells) if (col >= 1 && col <= width) r[col - 1] = v;
        out.push(r);
      }
      counter++;
    }
  }
  if (maxRow !== null && maxRow < idx) for (; counter <= maxRow; counter++) out.push(empty());
  return out;
}

const OLE2 = [0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1];

/** read_tables: {sheet name: raw rows} and the decimal mark of one file. */
export async function readTables(file: InputFile, ro: ReadOptions | null = null): Promise<Tables> {
  const r = ro ?? {};
  const ext = pathSuffix(file.name).toLowerCase();
  if (ext === ".xlsx" || ext === ".xlsm") return { sheets: await readXlsx(file.name, file.bytes), decimal: "." };
  if (ext === ".xls") {
    // Python reads old binary .xls with xlrd; ExcelJS can not. Some ".xls" are really text (or html): those are
    // read as text, as Python does when xlrd fails on them.
    if (OLE2.every((b, i) => file.bytes[i] === b)) {
      throw new PlotkitError(`${pathName(file.name)} is an old Excel .xls file, which can not be read here`, "save it as .xlsx (Excel: File > Save As > Excel Workbook) and use that file");
    }
  }
  const [sheets, decimal] = readText(file.name, file.bytes, r);
  return { sheets, decimal };
}

/** read_tables for a file name among the host's files. */
export async function readTablesNamed(files: InputFile[], name: string, ro: ReadOptions | null = null): Promise<Tables> {
  return readTables(findFile(files, name), ro);
}

// =================================================================== the numeric table of a sheet
/** analyze_table: find the header and the numeric block. */
export function analyzeTable(rowsIn: Cell[][], decimal = ".", headerRow: unknown = null, dataStartRow: unknown = null): Table {
  let width = 0;
  for (const r of rowsIn) width = Math.max(width, r.length);
  const rows: Cell[][] = rowsIn.map(r => r.length < width ? [...r, ...new Array<Cell>(width - r.length).fill(null)] : [...r]);
  const nums = rows.map(r => r.map(c => toNum(c, decimal)));
  const ncount = nums.map(r => r.filter(n => n !== null).length);
  if (!rows.length || !ncount.some(n => n > 0)) throw new PlotkitError("no numbers found in this sheet");
  const hr = pyTruthy(headerRow) ? rowNumber(headerRow, "header_row", rows.length) : null;
  const dsr = pyTruthy(dataStartRow) ? rowNumber(dataStartRow, "data_start_row") : null;

  let ds: number;
  if (dsr !== null) {
    ds = dsr - 1;
  } else if (hr !== null) {
    ds = hr;
    while (ds < rows.length && ncount[ds] < 2) ds++;
  } else {
    let wide = ncount.filter(c => c >= 2);
    if (!wide.length) wide = ncount.filter(c => c >= 1);
    const w = pyMode(wide);
    let found: number | null = null;
    for (let i = 0; i < ncount.length; i++) {
      if (ncount[i] >= w) {
        const nxt: number[] = [];
        for (let j = i + 1; j < Math.min(rows.length, i + 40); j++) if (ncount[j] || rows[j].some(pyTruthy)) nxt.push(ncount[j]);
        if (nxt.slice(0, 5).every(n => n >= Math.max(1, w - 1))) {
          found = i;
          break;
        }
      }
    }
    ds = found ?? ncount.findIndex(c => c === w);
  }
  if (ds >= rows.length) throw new PlotkitError("data start row is after the end of the sheet");

  const body = nums.slice(ds);
  const bodyRows = body.filter(r => r.some(v => v !== null));
  const dataCols: number[] = [];
  for (let j = 0; j < width; j++) {
    if (bodyRows.filter(r => r[j] !== null).length >= 0.5 * Math.max(1, bodyRows.length)) dataCols.push(j);
  }
  if (!dataCols.length) throw new PlotkitError("no numeric columns found");

  const isTextual = (r: number): boolean => {
    const row = rows.at(r)!;
    const txt = dataCols.filter(j => {
      const c = row[j];
      return c !== null && pyStrip(cellStr(c)) !== "" && toNum(c, decimal) === null;
    }).length;
    return txt >= Math.max(1, Math.ceil(dataCols.length / 2));
  };

  let hdrRows: number[] = [];
  if (hr !== null) {
    hdrRows = [hr - 1];
  } else {
    let i = ds - 1;
    while (i >= 0 && hdrRows.length < 2) {
      if (!rows[i].some(c => c !== null && pyStrip(cellStr(c)))) {
        if (hdrRows.length) break;
        i--;
        continue;
      }
      if (isTextual(i)) {
        hdrRows.unshift(i);
        i--;
      } else break;
    }
    if (hdrRows.length === 2 && !looksLikeUnits(rows[hdrRows[1]], dataCols)) hdrRows = hdrRows.slice(1);   // upper row is a title
  }

  const columns: Column[] = [];
  for (const j of dataCols) {
    const parts: string[] = [];
    for (const r of hdrRows) {
      const c = rows[r][j];
      if (c !== null && pyStrip(cellStr(c))) parts.push(pyStrip(cellStr(c)));
    }
    columns.push({ letter: colLetter(j), index: j, name: parts.join(" "), values: body.map(r => r[j] ?? NaN) });
  }
  return { columns, header_rows: hdrRows.map(r => r + 1), data_start_row: ds + 1, n_rows: bodyRows.length };
}

const UNIT_RE = new RegExp(`^[\\(\\[]?[${PY_WS}]*(%|°c|℃|c|k|min|s|sec|h|mg|g|µg|ug|mw|w/g|mw/mg|%/°c|%/c|%/min|mg/min|°c/min|%/℃|deg\\.?c|1/°c)[${PY_WS}]*[\\)\\]]?$`, "iu");

export function looksLikeUnits(row: Cell[], cols: number[]): boolean {
  const cells = cols.filter(j => row[j] !== null && pyStrip(cellStr(row[j]))).map(j => pyStrip(cellStr(row[j])));
  if (!cells.length) return false;
  return cells.filter(c => UNIT_RE.test(c)).length >= 0.5 * cells.length;
}

// ---------------------------------------------------------- column matching
const NORM_RE = new RegExp(`[${PY_WS}._\\-:·,]+`, "gu");

export function norm(s: unknown): string {
  return pyStrOf(s).toLowerCase().replace(NORM_RE, "");
}

export function base(s: unknown): string {
  return norm(pyStrOf(s).replace(/[\(\[\{][^\n]*?[\)\]\}]/g, ""));
}

const COL_WORDS = new RegExp(`^(col(umn)?[${PY_WS}]*)|([${PY_WS}]*(열|행|column|col|컬럼|칸))$`, "giu");

/** find_column: a column by letter or (part of) its name. */
export function findColumn(table: Table, query: unknown, where: string): Column {
  const cols = table.columns;
  let q = pyStrip(pyStrOf(query));
  q = pyStrip(q.replace(COL_WORDS, ""));
  if (/^[A-Za-z]{1,2}$/.test(q)) {
    const idx = colIndex(q);
    const maxIdx = Math.max(...cols.map(c => c.index));
    if (idx <= maxIdx) {
      for (const c of cols) if (c.index === idx) return c;
      throw new PlotkitError(`${where}: column ${q.toUpperCase()} has no numbers`, "columns with numbers: " + colList(cols));
    }
  }
  const qn = norm(q), qb = base(q);
  if (!qn) throw new PlotkitError(`${where}: empty column name`);
  const scored: [number, Column][] = [];
  for (const c of cols) {
    const n = norm(c.name), b = base(c.name);
    if (!n) continue;
    let s = 0;
    if (b === qb || n === qn) s = 3;
    else if (n.startsWith(qn) || (qb && b.startsWith(qb))) s = 2;
    else if (n.includes(qn) || (qb && n.includes(qb))) s = 1;
    if (s) scored.push([s, c]);
  }
  if (!scored.length) {
    throw new PlotkitError(`${where}: no column matches "${pyStrOf(query)}"`, "use a letter or part of one of these names: " + colList(cols));
  }
  const top = Math.max(...scored.map(([s]) => s));
  const best = scored.filter(([s]) => s === top).map(([, c]) => c);
  if (best.length > 1) throw new PlotkitError(`${where}: "${pyStrOf(query)}" matches several columns: ` + colList(best), "use the column letter instead");
  return best[0];
}

export function colList(cols: Column[]): string {
  return cols.map(c => `${c.letter} "${c.name || "(no name)"}"`).join(", ");
}

const W = PY_W;
export const ROLE_PATTERNS: [string, RegExp[]][] = [
  ["y2", [/deriv/u, /dtg/u, new RegExp(`(?<!${W})d\\.?[${PY_WS}]*w(?!${W})`, "u"), /dw\/?dt/u, /미분/u,
    new RegExp(`%[${PY_WS}]*/[${PY_WS}]*(°|℃|c(?!${W})|min|deg)`, "u"), new RegExp(`/[${PY_WS}]*(°c|℃)`, "u")]],
  ["time", [/time/u, /시간/u, new RegExp(`^[${PY_WS}]*t[${PY_WS}]*\\([${PY_WS}]*(min|s)[${PY_WS}]*\\)`, "u"),
    new RegExp(`\\([${PY_WS}]*(min|s|sec)[${PY_WS}]*\\)[${PY_WS}]*$`, "u")]],
  ["x", [/temp/u, /온도/u, new RegExp(`^[${PY_WS}]*t[${PY_WS}]*(\\(|$)`, "u"), /(°c|℃)/u]],
  ["y1", [/weight/u, new RegExp(`(?<!${W})wt`, "u"), /mass/u, /무게/u, /중량/u, /질량/u, new RegExp(`^[${PY_WS}]*tg(?!${W})`, "u"),
    new RegExp(`\\([${PY_WS}]*%[${PY_WS}]*\\)`, "u"), new RegExp(`^[${PY_WS}]*%[${PY_WS}]*$`, "u")]],
];
const Y2_UNIT = new RegExp(`°c|℃|/c(?!${W})`, "u");

// ---------------------------------------------------------- numpy, as guess_tga_columns uses it
/** numpy's pairwise summation (np.add.reduce on a contiguous float64 array). */
function pairwiseSum(a: number[], lo: number, n: number): number {
  if (n < 8) {
    let res = 0;
    for (let i = 0; i < n; i++) res += a[lo + i];
    return res;
  }
  if (n <= 128) {
    const r = [0, 1, 2, 3, 4, 5, 6, 7].map(k => a[lo + k]);
    let i = 8;
    for (; i < n - (n % 8); i += 8) for (let k = 0; k < 8; k++) r[k] += a[lo + i + k];
    let res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
    for (; i < n; i++) res += a[lo + i];
    return res;
  }
  let n2 = Math.floor(n / 2);
  n2 -= n2 % 8;
  return pairwiseSum(a, lo, n2) + pairwiseSum(a, lo + n2, n - n2);
}

export function npSum(a: number[]): number {
  return pairwiseSum(a, 0, a.length);
}

export function npMean(a: number[]): number {
  return npSum(a) / a.length;
}

export function npStd(a: number[]): number {
  const m = npMean(a);
  return Math.sqrt(npMean(a.map(x => Math.abs(x - m) ** 2)));
}

/** np.gradient(f, x) (edge_order 1). */
export function npGradient(f: number[], x: number[]): number[] {
  const n = f.length, out = new Array<number>(n);
  const dx = x.slice(1).map((v, i) => v - x[i]);
  if (dx.every(d => d === dx[0])) {
    const h = dx[0];
    for (let i = 1; i < n - 1; i++) out[i] = (f[i + 1] - f[i - 1]) / (2 * h);
    out[0] = (f[1] - f[0]) / h;
    out[n - 1] = (f[n - 1] - f[n - 2]) / h;
    return out;
  }
  for (let i = 1; i < n - 1; i++) {
    const dx1 = dx[i - 1], dx2 = dx[i];
    const a = -dx2 / (dx1 * (dx1 + dx2)), b = (dx2 - dx1) / (dx1 * dx2), c = dx1 / (dx2 * (dx1 + dx2));
    out[i] = a * f[i - 1] + b * f[i] + c * f[i + 1];
  }
  out[0] = (f[1] - f[0]) / dx[0];
  out[n - 1] = (f[n - 1] - f[n - 2]) / dx[n - 2];
  return out;
}

/** np.corrcoef(x, y)[0, 1] */
export function npCorrcoef(x: number[], y: number[]): number {
  const mx = npMean(x), my = npMean(y);
  const xs = x.map(v => v - mx), ys = y.map(v => v - my);
  let sxx = 0, syy = 0, sxy = 0;
  for (let i = 0; i < xs.length; i++) { sxx += xs[i] * xs[i]; syy += ys[i] * ys[i]; sxy += xs[i] * ys[i]; }
  const f = 1 / (x.length - 1);
  const cxy = sxy * f;
  const r = cxy / Math.sqrt(sxx * f) / Math.sqrt(syy * f);
  return Number.isNaN(r) ? r : Math.min(1, Math.max(-1, r));
}

/** guess_tga_columns: x (temperature), y1 (weight), y2 (DTG) by names, then by values. */
export function guessTgaColumns(table: Table): [Partial<Record<"x" | "y1" | "y2", Column>>, string] {
  const cols = table.columns;
  const roles: Record<string, Column[]> = { x: [], y1: [], y2: [], time: [] };
  for (const c of cols) {
    const name = c.name.toLowerCase();
    if (!name) continue;
    for (const [role, pats] of ROLE_PATTERNS) {
      if (pats.some(p => p.test(name))) {
        roles[role].push(c);
        break;
      }
    }
  }
  const pick: Partial<Record<"x" | "y1" | "y2", Column>> = {};
  if (roles.x.length) pick.x = roles.x.find(c => c.name.toLowerCase().includes("sample")) ?? roles.x[0];
  if (roles.y1.length) pick.y1 = roles.y1.find(c => c.name.includes("%")) ?? roles.y1[0];
  if (roles.y2.length) pick.y2 = roles.y2.find(c => Y2_UNIT.test(c.name.toLowerCase())) ?? roles.y2[0];
  let how = "by name";
  if (Object.keys(pick).length < 3) {                // fill gaps from the values
    how = Object.keys(pick).length ? "by name and values" : "by values";
    const used = new Set(Object.values(pick));
    let free = cols.filter(c => !used.has(c));
    if (!pick.x) {
      const cand: [number, Column][] = [];
      for (const c of free) {
        const v = c.values.filter(Number.isFinite);
        if (v.length > 10) {
          let up = 0;
          for (let i = 1; i < v.length; i++) if (v[i] - v[i - 1] > 0) up++;
          const inc = up / (v.length - 1);
          let max = -Infinity, min = Infinity;
          for (const x of v) { if (x > max) max = x; if (x < min) min = x; }
          if (inc > 0.7 && max >= 150 && max <= 2000 && min < 200) cand.push([inc, c]);
        }
      }
      if (cand.length) pick.x = cand.reduce((a, b) => (b[0] > a[0] ? b : a))[1];
    }
    free = free.filter(c => c !== pick.x);
    if (!pick.y1) {
      const cand: Column[] = [];
      for (const c of free) {
        const v = c.values.filter(Number.isFinite);
        if (v.length > 10) {
          const head = npMean(v.slice(0, 5)), tail = npMean(v.slice(-5));
          if (head >= 50 && head <= 110 && tail < head) cand.push(c);
        }
      }
      if (cand.length) pick.y1 = cand[0];
    }
    free = free.filter(c => c !== pick.y1);
    if (!pick.y2 && pick.x && pick.y1) {
      let best: Column | null = null, bestr = 0.6;
      const T = pick.x.values, Wt = pick.y1.values;
      const ok = T.map((t, i) => Number.isFinite(t) && Number.isFinite(Wt[i]));
      if (ok.filter(Boolean).length > 10) {
        const g = npGradient(Wt.filter((_, i) => ok[i]), T.filter((_, i) => ok[i]));
        for (const c of free) {
          const v = c.values.filter((_, i) => ok[i]);
          const m = v.map((x, i) => Number.isFinite(x) && Number.isFinite(g[i]));
          const vm = v.filter((_, i) => m[i]), gm = g.filter((_, i) => m[i]);
          if (vm.length > 10 && npStd(vm) > 0) {
            const r = Math.abs(npCorrcoef(vm, gm));
            if (r > bestr) { best = c; bestr = r; }
          }
        }
      }
      if (best !== null) pick.y2 = best;
    }
  }
  return [pick, how];
}

// =================================================================== loading
/** What load_sheets and build_jobs read of a spec. */
export interface SheetSpec {
  file: unknown[];
  sheets?: unknown;
  read?: ReadOptions | null;
  [key: string]: unknown;
}

/** load_sheets: (file, sheet name, table) for every selected sheet; a sheet that has no table is a PlotkitError
 *  in the list when all of several sheets were asked for. */
export async function loadSheets(specOrFile: SheetSpec | string, files: InputFile[], roIn: ReadOptions | null = null):
  Promise<[string, string, Table | PlotkitError][]> {
  const isSpec = typeof specOrFile !== "string";
  const fileList = isSpec ? specOrFile.file.map(f => pyStrOf(f)) : [specOrFile];
  const ro: ReadOptions = (isSpec ? specOrFile.read : roIn) ?? {};
  const sel = isSpec ? ("sheets" in specOrFile ? specOrFile.sheets : "all") : "all";
  const out: [string, string, Table | PlotkitError][] = [];
  for (const f of fileList) {
    const { sheets: tables, decimal } = await readTablesNamed(files, f, ro);
    const names = [...tables.keys()];
    const chosen = selectSheets(names, sel, f);
    for (const n of chosen) {
      let t: Table;
      try {
        t = analyzeTable(tables.get(n)!, decimal, ro.header_row, ro.data_start_row);
      } catch (e) {
        if (!(e instanceof PlotkitError)) throw e;
        if ((sel === "all" || sel === null || sel === undefined) && chosen.length > 1) {
          out.push([f, n, new PlotkitError(e.message, e.hint)]);
          continue;
        }
        throw new PlotkitError(`${pathName(f)} / sheet "${n}": ${e.message}`, e.hint);
      }
      out.push([f, n, t]);
    }
  }
  return out;
}

/** _select_sheets: the sheets a spec's "sheets" names (all, numbers from 1, names or parts of names). */
export function selectSheets(names: string[], sel: unknown, f: string): string[] {
  if (sel === "all" || sel === null || sel === undefined || sel === "" || sel === "*") return names;
  const list = Array.isArray(sel) ? sel : [sel];
  const chosen: string[] = [];
  for (let s of list as unknown[]) {
    if (typeof s === "string" && /^[0-9]+$/.test(pyStrip(s)) && !names.includes(s)) s = parseInt(pyStrip(s), 10);   // ASCII digits only
    if (typeof s === "number") {
      const i = Number.isFinite(s) ? Math.trunc(s) : s;
      if (!(i >= 1 && i <= names.length)) {
        throw new PlotkitError(`sheet number ${pyStrOf(i)} does not exist in ${pathName(f)}`, `it has ${names.length} sheet(s): ${pyReprOf(names)}`);
      }
      chosen.push(names[i - 1]);
      continue;
    }
    let hit = names.filter(n => n === s);
    if (!hit.length) hit = names.filter(n => norm(n) === norm(s));
    if (!hit.length) hit = names.filter(n => norm(n).includes(norm(s)));
    if (hit.length !== 1) {
      const m = getCloseMatches(pyStrOf(s), names, 3, 0.3);
      throw new PlotkitError(`sheet "${pyStrOf(s)}" ${hit.length ? "is ambiguous" : "not found"} in ${pathName(f)}`,
        `sheet names: ${pyReprOf(names)}` + (m.length ? `; closest: ${pyReprOf(m)}` : ""));
    }
    chosen.push(hit[0]);
  }
  return chosen;
}
