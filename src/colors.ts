// Colours as matplotlib reads them (names, hex, grey levels, the colour cycle) and the built-in colormaps, from
// data/colors.json (generated from matplotlib by plotkit/colors.py). Same results as the Python plotkit.
import DATA from "./data/colors.json" with { type: "json" };

type Rgba = [number, number, number, number];
const NAMES = DATA.names as unknown as Record<string, string | number[]>;
const CYCLE = DATA.cycle as unknown as string[];
const CMAPS = DATA.cmaps as unknown as Record<string, [string, string]>;
const NTH = /^C[0-9]+$/;

export function toRgba(c: unknown): Rgba {
  if (typeof c === "string" && NTH.test(c)) c = CYCLE[parseInt(c.slice(1), 10) % CYCLE.length];
  const orig = c;
  if (typeof c === "string") {
    if (c.toLowerCase() === "none") return [0, 0, 0, 0];
    if (Object.hasOwn(NAMES, c)) c = NAMES[c];
    else if ([...c].length !== 1 && Object.hasOwn(NAMES, c.toLowerCase())) c = NAMES[c.toLowerCase()];
  }
  if (typeof c === "string") {
    if (/^#[a-fA-F0-9]+$/.test(c)) {
      const h = c.slice(1);
      const byte = (i: number) => parseInt(h.slice(i, i + 2), 16) / 0xff;
      const nib = (i: number) => parseInt(h[i], 16) / 0xf;
      if (h.length === 6) return [byte(0), byte(2), byte(4), 1];
      if (h.length === 3) return [nib(0), nib(1), nib(2), 1];
      if (h.length === 8) return [byte(0), byte(2), byte(4), byte(6)];
      if (h.length === 4) return [nib(0), nib(1), nib(2), nib(3)];
      throw new Error(`Invalid hex color specifier: ${JSON.stringify(orig)}`);
    }
    const s = c.trim();
    const g = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(s) || /^[+-]?(inf|infinity|nan)$/i.test(s) ? parseFloat(s) : NaN;
    if (Number.isNaN(g) && !/^[+-]?nan$/i.test(s)) throw new Error(`Invalid RGBA argument: ${JSON.stringify(orig)}`);
    if (!(g >= 0 && g <= 1)) throw new Error(`Invalid string grayscale value ${JSON.stringify(orig)}`);
    return [g, g, g, 1];
  }
  if (Array.isArray(c) && (c.length === 3 || c.length === 4) && c.every(x => typeof x === "number")) {
    const v = [...c, ...(c.length === 3 ? [1] : [])] as Rgba;
    if (v.some(x => x < 0 || x > 1)) throw new Error("RGBA values should be within 0-1 range");
    return v;
  }
  throw new Error(`Invalid RGBA argument: ${JSON.stringify(orig)}`);
}

export function isColorLike(c: unknown): boolean {
  try { toRgba(c); return true; } catch { return false; }
}

export function toRgb(c: unknown): [number, number, number] {
  const [r, g, b] = toRgba(c);
  return [r, g, b];
}

/** #rrggbb, rounded as Python's round() does (half-even). */
export function toHex(c: unknown): string {
  return "#" + toRgb(c).map(v => halfEven(v * 255).toString(16).padStart(2, "0")).join("");
}

function halfEven(x: number): number {
  const f = Math.floor(x), d = x - f;
  if (d > 0.5) return f + 1;
  if (d < 0.5) return f;
  return f % 2 === 0 ? f : f + 1;
}

/** A colormap as 256 levels, picked for t in 0..1 the way matplotlib does. */
export class Colormap {
  readonly name: string;
  readonly lut: string[];
  private readonly darkMask: string;
  readonly N: number;
  constructor(name: string, lut: string[], dark: string) {
    this.name = name; this.lut = lut; this.darkMask = dark; this.N = lut.length;
  }
  private level(t: number): number {
    let x = t * this.N;
    if (x === this.N) x = this.N - 1;
    if (x < 0) return 0;
    return Math.min(Math.trunc(x), this.N - 1);
  }
  hex(t: number): string { return this.lut[this.level(t)]; }
  /** True when a label on the colour at t should be white (luminance below one half). */
  dark(t: number): boolean { return this.darkMask[this.level(t)] === "1"; }
}

/** The built-in colormap called name; undefined when there is none. */
export function colormap(name: string): Colormap | undefined {
  if (!Object.hasOwn(CMAPS, name)) return undefined;
  const [lut, dark] = CMAPS[name];
  const levels: string[] = [];
  for (let i = 0; i < lut.length; i += 6) levels.push("#" + lut.slice(i, i + 6));
  return new Colormap(name, levels, dark);
}

export function colormapNames(): string[] {
  return Object.keys(CMAPS).sort();
}
