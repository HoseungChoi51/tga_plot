// Python's number formatting and rounding, exactly: str.format / format specs (f, e, g, %, d, ",", widths),
// repr/str of floats, round(x, n) with half-even on the exact binary value. The labels plotkit writes
// ("Residue {y:.1f}%", "{x:.0f} °C", "{:.2f}") and the numbers it reports must match the Python implementation.

/** 10 ** k for an integer k, correctly rounded (V8's ** is not, e.g. 10 ** -4). */
export function pow10(k: number): number {
  return parseFloat(`1e${k}`);
}

/** The exact decimal value of a finite double: digits (no leading zeros except "0") and the position of the point
 *  (number of integer digits; may be <= 0). */
function exactDecimal(x: number): { neg: boolean; digits: string; point: number } {
  const neg = x < 0 || Object.is(x, -0);
  x = Math.abs(x);
  if (x === 0) return { neg, digits: "0", point: 1 };
  const buf = new DataView(new ArrayBuffer(8));
  buf.setFloat64(0, x);
  const hi = buf.getUint32(0), lo = buf.getUint32(4);
  const exp = (hi >>> 20) & 0x7ff;
  let mant = (BigInt(hi & 0xfffff) << 32n) | BigInt(lo);
  let e2: number;
  if (exp === 0) e2 = -1074;
  else { mant |= 1n << 52n; e2 = exp - 1075; }
  let digits: string, point: number;
  if (e2 >= 0) {
    digits = (mant << BigInt(e2)).toString();
    point = digits.length;
  } else {
    const k = -e2;                                   // mant / 2^k = mant * 5^k / 10^k
    digits = (mant * 5n ** BigInt(k)).toString();
    point = digits.length - k;
  }
  digits = digits.replace(/0+$/, "") || "0";
  return { neg, digits, point };
}

/** Round the exact decimal to keep `keep` digits after the point (half-even). Returns integer digit string and point. */
function roundAt(digits: string, point: number, keep: number): { digits: string; point: number } {
  const n = point + keep;                            // number of digits to keep from the start
  if (n < 0) return { digits: "0", point: 1 };
  if (digits.length <= n) return { digits, point };
  let head = digits.slice(0, n);
  const rest = digits.slice(n);
  const first = rest.charCodeAt(0) - 48;
  const tail = rest.slice(1).replace(/0+$/, "");
  const last = head.length ? head.charCodeAt(head.length - 1) - 48 : 0;
  const up = first > 5 || (first === 5 && (tail.length > 0 || last % 2 === 1));
  if (up) {
    const inc = (BigInt(head || "0") + 1n).toString();
    if (inc.length > (head.length || 1) || (head === "" && inc === "1")) {
      if (head === "") return { digits: "1", point: point + 1 };
      return { digits: inc, point: point + 1 };
    }
    head = inc.padStart(head.length, "0");
  }
  return { digits: head || "0", point };
}

function fixed(x: number, prec: number): string {
  const { neg, digits, point } = exactDecimal(x);
  const r = roundAt(digits, point, prec);
  let d = r.digits, p = r.point;
  if (p <= 0) { d = "0".repeat(1 - p) + d; p = 1; }
  if (d.length < p + prec) d = d + "0".repeat(p + prec - d.length);
  const int = d.slice(0, p).replace(/^0+(?=\d)/, "") || "0";
  const frac = d.slice(p, p + prec);
  return (neg ? "-" : "") + int + (prec > 0 ? "." + frac : "");
}

function expo(x: number, prec: number, upper = false): string {
  const { neg, digits, point } = exactDecimal(x);
  if (digits === "0") return (neg ? "-" : "") + "0" + (prec > 0 ? "." + "0".repeat(prec) : "") + (upper ? "E+00" : "e+00");
  // keep prec+1 significant digits
  const r = roundAt(digits, 0, prec + 1);             // digits as 0.ddd × 10^point
  let d = r.digits;
  const e = point - 1 + (r.point - 0);
  if (d.length < prec + 1) d = d + "0".repeat(prec + 1 - d.length);
  const mant = d[0] + (prec > 0 ? "." + d.slice(1, prec + 1) : "");
  const es = Math.abs(e) < 10 ? "0" + Math.abs(e) : String(Math.abs(e));
  return (neg ? "-" : "") + mant + (upper ? "E" : "e") + (e < 0 ? "-" : "+") + es;
}

function stripZeros(s: string): string {
  const m = /^(-?\d+)(\.\d*?)0*([eE].*)?$/.exec(s);
  if (!m) return s;
  const frac = m[2] === "." ? "" : m[2];
  return m[1] + frac + (m[3] ?? "");
}

/** The decimal exponent of x once rounded to prec significant digits. */
function decExp(x: number, prec: number): number {
  const { digits, point } = exactDecimal(x);
  const r = roundAt(digits, 0, prec);
  return point - 1 + r.point;
}

function general(x: number, prec: number, upper = false, alt = false): string {
  if (prec === 0) prec = 1;
  if (x === 0) return (Object.is(x, -0) ? "-" : "") + (alt ? "0." + "0".repeat(prec - 1) : "0");
  const exp = decExp(x, prec);
  const s = exp >= -4 && exp < prec ? fixed(x, prec - 1 - exp) : expo(x, prec - 1, upper);
  return alt ? s : stripZeros(s);
}

/** format(x, ".N") (no type): like g, but scientific from exponent N-1 and at least one digit after the point. */
function noType(x: number, prec: number): string {
  if (prec === 0) prec = 1;
  if (x === 0) return (Object.is(x, -0) ? "-" : "") + "0.0";
  const exp = decExp(x, prec);
  if (exp >= -4 && exp < prec - 1) {
    const s = stripZeros(fixed(x, prec - 1 - exp));
    return s.includes(".") ? s : s + ".0";
  }
  return stripZeros(expo(x, prec - 1));
}

/** Python's repr(float) / str(float). */
export function pyRepr(x: number): string {
  if (Number.isNaN(x)) return "nan";
  if (x === Infinity) return "inf";
  if (x === -Infinity) return "-inf";
  if (x === 0) return Object.is(x, -0) ? "-0.0" : "0.0";
  const m = /^(-?)(\d)(?:\.(\d+))?e([+-]\d+)$/.exec(x.toExponential());
  if (!m) throw new Error(`cannot format ${x}`);
  const sign = m[1], digits = m[2] + (m[3] ?? ""), e = parseInt(m[4], 10);
  if (e >= -5 + 1 && e < 16) {                        // Python: fixed when -4 <= exp < 16
    if (e >= 0) {
      const int = digits.length > e + 1 ? digits.slice(0, e + 1) : digits + "0".repeat(e + 1 - digits.length);
      const frac = digits.length > e + 1 ? digits.slice(e + 1) : "0";
      return `${sign}${int}.${frac}`;
    }
    return `${sign}0.${"0".repeat(-e - 1)}${digits}`;
  }
  const mant = digits.length > 1 ? `${digits[0]}.${digits.slice(1)}` : digits;
  return `${sign}${mant}e${e < 0 ? "-" : "+"}${String(Math.abs(e)).padStart(2, "0")}`;
}

/** Python's round(x, n) for floats (n >= 0): the correctly rounded decimal, half-even, back to a float. */
export function pyRound(x: number, n = 0): number {
  if (!Number.isFinite(x)) return x;
  if (n < 0) {
    const f = pow10(-n);
    return pyRound(x / f, 0) * f;
  }
  return parseFloat(fixed(x, n));
}

/** A Python value for formatting: numbers carry whether Python had an int or a float. */
export type PyValue = number | string | boolean | null | undefined | PyInt | object;

/** Marks a number that is a Python int (so str() gives "5", not "5.0"). */
export class PyInt {
  readonly value: number;
  constructor(value: number) { this.value = value; }
}

export function int(v: number): PyInt {
  return new PyInt(v);
}

export class PyFormatError extends Error {
  readonly kind: "KeyError" | "IndexError" | "ValueError";
  constructor(kind: "KeyError" | "IndexError" | "ValueError", message: string) {
    super(message);
    this.kind = kind;
  }
}

/** Python's str() of a value (floats as repr, ints plain, None as "None", True/False). */
export function pyStr(v: PyValue): string {
  if (v instanceof PyInt) return String(v.value);
  if (typeof v === "number") return pyRepr(v);
  if (v === null || v === undefined) return "None";
  if (typeof v === "boolean") return v ? "True" : "False";
  return String(v);
}

function group(intPart: string, sep: string): string {
  const neg = intPart.startsWith("-");
  const d = neg ? intPart.slice(1) : intPart;
  const out = d.replace(/\B(?=(\d{3})+(?!\d))/g, sep);
  return (neg ? "-" : "") + out;
}

/** format(value, spec) as Python does it, for the specs plotkit uses. */
export function formatValue(v: PyValue, spec: string): string {
  const m = /^(?:(.)?([<>=^]))?([+\- ])?(#)?(0)?(\d+)?([,_])?(?:\.(\d+))?([bcdeEfFgGnosxX%])?$/.exec(spec);
  if (!m) throw new PyFormatError("ValueError", `Invalid format specifier '${spec}'`);
  let [, fill, align, sign, alt, zero, width, grouping, precS, type] = m;
  const prec = precS === undefined ? undefined : parseInt(precS, 10);
  const isInt = v instanceof PyInt || typeof v === "boolean";
  let num: number | undefined = v instanceof PyInt ? v.value : typeof v === "number" ? v : typeof v === "boolean" ? (v ? 1 : 0) : undefined;
  let body: string;
  if (num === undefined) {
    if (type && type !== "s") throw new PyFormatError("ValueError", `Unknown format code '${type}' for object of type 'str'`);
    body = pyStr(v);
    if (prec !== undefined) body = Array.from(body).slice(0, prec).join("");
    align = align ?? "<";
  } else {
    if (isInt && (type === "d" || type === undefined || type === "n") && prec === undefined) {
      body = String(Math.trunc(num));
    } else {
      if (type === "d") throw new PyFormatError("ValueError", `Unknown format code 'd' for object of type 'float'`);
      const x = num;
      const t = type ?? (isInt ? "d" : "");
      if (!Number.isFinite(x)) body = Number.isNaN(x) ? "nan" : x > 0 ? "inf" : "-inf";
      else if (t === "f" || t === "F") body = fixed(x, prec ?? 6);
      else if (t === "e" || t === "E") body = expo(x, prec ?? 6, t === "E");
      else if (t === "g" || t === "G") body = general(x, prec ?? 6, t === "G", !!alt);
      else if (t === "%") body = fixed(x * 100, prec ?? 6) + "%";
      else if (t === "n") body = general(x, prec ?? 6);
      else if (t === "") {
        if (prec === undefined) body = pyRepr(x);
        else body = noType(x, prec);
      } else throw new PyFormatError("ValueError", `Unknown format code '${t}' for object of type 'float'`);
    }
    if (sign === "+" && !body.startsWith("-")) body = "+" + body;
    else if (sign === " " && !body.startsWith("-")) body = " " + body;
    if (grouping) {
      const mm = /^([+\- ]?)(\d+)(.*)$/.exec(body);
      if (mm) body = mm[1] + group(mm[2], grouping) + mm[3];
    }
    align = align ?? (zero ? "=" : ">");
    if (zero && !fill) fill = "0";
  }
  const w = width ? parseInt(width, 10) : 0;
  const len = Array.from(body).length;
  if (len >= w) return body;
  const f = fill ?? " ";
  const pad = w - len;
  if (align === "<") return body + f.repeat(pad);
  if (align === "^") return f.repeat(Math.floor(pad / 2)) + body + f.repeat(pad - Math.floor(pad / 2));
  if (align === "=") {
    const mm = /^([+\- ]?)(.*)$/.exec(body)!;
    return mm[1] + f.repeat(pad) + mm[2];
  }
  return f.repeat(pad) + body;
}

/** Python's str.format(*args, **kwargs) for the templates plotkit uses ({} {0} {x} {x:.1f} {{ }}). */
export function pyFormat(template: string, args: PyValue[] = [], kwargs: Record<string, PyValue> = {}): string {
  let out = "";
  let auto = 0;
  let i = 0;
  while (i < template.length) {
    const ch = template[i];
    if (ch === "{") {
      if (template[i + 1] === "{") { out += "{"; i += 2; continue; }
      const end = template.indexOf("}", i);
      if (end < 0) throw new PyFormatError("ValueError", "Single '{' encountered in format string");
      const field = template.slice(i + 1, end);
      const colon = field.indexOf(":");
      let name = colon >= 0 ? field.slice(0, colon) : field;
      const spec = colon >= 0 ? field.slice(colon + 1) : "";
      let conv = "";
      const bang = name.indexOf("!");
      if (bang >= 0) { conv = name.slice(bang + 1); name = name.slice(0, bang); }
      let v: PyValue;
      if (name === "") {
        if (auto >= args.length) throw new PyFormatError("IndexError", "Replacement index " + auto + " out of range for positional args tuple");
        v = args[auto++];
      } else if (/^\d+$/.test(name)) {
        const k = parseInt(name, 10);
        if (k >= args.length) throw new PyFormatError("IndexError", "Replacement index " + k + " out of range for positional args tuple");
        v = args[k];
      } else {
        if (!(name in kwargs)) throw new PyFormatError("KeyError", `'${name}'`);
        v = kwargs[name];
      }
      if (conv === "r" || conv === "s") v = conv === "r" && typeof v === "string" ? `'${v}'` : pyStr(v);
      out += formatValue(v, spec);
      i = end + 1;
      continue;
    }
    if (ch === "}") {
      if (template[i + 1] === "}") { out += "}"; i += 2; continue; }
      throw new PyFormatError("ValueError", "Single '}' encountered in format string");
    }
    out += ch;
    i++;
  }
  return out;
}

/** Python's round-half-even to an integer, as round(x) does. */
export function roundHalfEven(x: number): number {
  return pyRound(x, 0);
}

/** Python's float floor division and modulo (divmod for floats; numpy's floor_divide agrees). */
export function pyDivmod(x: number, y: number): [number, number] {
  let mod = x % y;                                   // fmod
  let div = (x - mod) / y;
  if (mod) {
    if ((y < 0) !== (mod < 0)) { mod += y; div -= 1.0; }
  } else {
    mod = Math.sign(y) < 0 || Object.is(y, -0) ? -0 : 0;
  }
  let floordiv: number;
  if (div) {
    floordiv = Math.floor(div);
    if (div - floordiv > 0.5) floordiv += 1.0;
  } else {
    floordiv = (x / y) < 0 || Object.is(x / y, -0) ? -0 : 0;
  }
  return [floordiv, mod];
}

export function pyFloorDiv(x: number, y: number): number {
  return pyDivmod(x, y)[0];
}
