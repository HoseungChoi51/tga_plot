import { test } from "node:test";
import assert from "node:assert/strict";
import { golden, decode } from "./golden.ts";
import { formatValue, pyRepr, pyRound, int } from "../src/pyfmt.ts";
import { getCloseMatches, ratio } from "../src/difflib.ts";
import { isColorLike, toHex } from "../src/colors.ts";
import { tickValues } from "../src/ticks.ts";

const B = decode(golden("basics")[0]);

function bad<T>(cases: T[], check: (c: T) => string | null): string[] {
  const out: string[] = [];
  for (const c of cases) { const m = check(c); if (m) out.push(m); if (out.length > 10) break; }
  return out;
}

test("format specs equal Python's format() for floats", () => {
  assert.deepEqual(bad(B.format, ([v, sp, want]: [number, string, string]) => {
    const got = formatValue(v, sp);
    return got === want ? null : `format(${v}, '${sp}') = ${got}, want ${want}`;
  }), []);
});

test("format specs equal Python's format() for ints", () => {
  assert.deepEqual(bad(B.format_int, ([v, sp, want]: [number, string, string]) => {
    const got = formatValue(int(v), sp);
    return got === want ? null : `format(${v}, '${sp}') = ${got}, want ${want}`;
  }), []);
});

test("repr and round equal Python's", () => {
  assert.deepEqual(bad(B.repr, ([v, want]: [number, string]) => pyRepr(v) === want ? null : `repr(${v}) = ${pyRepr(v)}, want ${want}`), []);
  assert.deepEqual(bad(B.round, ([v, k, want]: [number, number, number]) =>
    Object.is(pyRound(v, k), want) || pyRound(v, k) === want ? null : `round(${v}, ${k}) = ${pyRound(v, k)}, want ${want}`), []);
});

test("difflib ratio and get_close_matches equal Python's", () => {
  assert.deepEqual(bad(B.ratio, ([a, b, want]: [string, string, number]) => ratio(a, b) === want ? null : `ratio(${a}, ${b}) = ${ratio(a, b)}, want ${want}`), []);
  assert.deepEqual(bad(B.close, ([w, poss, n, c, want]: [string, string[], number, number, string[]]) => {
    const got = getCloseMatches(w, poss, n, c);
    return JSON.stringify(got) === JSON.stringify(want) ? null : `close(${w}) = ${got}, want ${want}`;
  }), []);
});

test("colours equal matplotlib's", () => {
  assert.deepEqual(bad(B.colors, ([c, like, hex]: [string, boolean, string | null]) => {
    if (isColorLike(c) !== like) return `${c}: like ${isColorLike(c)}`;
    return like && toHex(c) !== hex ? `${c}: ${toHex(c)} != ${hex}` : null;
  }), []);
});

test("ticks equal matplotlib's MaxNLocator", () => {
  assert.deepEqual(bad(B.ticks, ([a, b, nb, want]: [number, number, number | "auto", number[]]) => {
    const got = tickValues(a, b, nb);
    return got.length === want.length && got.every((v, i) => v === want[i]) ? null : `ticks(${a}, ${b}, ${nb}) = ${got}, want ${want}`;
  }), []);
});
