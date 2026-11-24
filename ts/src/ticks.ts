// The tick values matplotlib's MaxNLocator picks (a port of plotkit/ticks.py, itself a port of matplotlib 3.11 for
// plotkit's settings: no integer/symmetric/prune, autolimit "data", nbins "auto" = 9).
import { pow10, pyDivmod, pyFloorDiv } from "./pyfmt.ts";

export const STEPS = [1, 2, 2.5, 5, 10];
const TINY = 2.2250738585072014e-308;              // np.finfo(float).tiny

function nonsingular(vmin: number, vmax: number, expander: number, tiny: number): [number, number] {
  if (!Number.isFinite(vmin) || !Number.isFinite(vmax)) return [-expander, expander];
  if (vmax < vmin) [vmin, vmax] = [vmax, vmin];
  const maxabs = Math.max(Math.abs(vmin), Math.abs(vmax));
  if (maxabs < (1e6 / tiny) * TINY) return [-expander, expander];
  if (vmax - vmin <= maxabs * tiny) {
    if (vmax === 0 && vmin === 0) return [-expander, expander];
    vmin -= expander * Math.abs(vmin);
    vmax += expander * Math.abs(vmax);
  }
  return [vmin, vmax];
}

function scaleRange(vmin: number, vmax: number, n: number, threshold = 100): [number, number] {
  const dv = Math.abs(vmax - vmin);
  const meanv = (vmax + vmin) / 2;
  let offset = 0;
  if (!(Math.abs(meanv) / dv < threshold)) {
    offset = Math.sign(meanv) * pow10(pyFloorDiv(Math.log10(Math.abs(meanv)), 1));
  }
  const scale = pow10(pyFloorDiv(Math.log10(dv / n), 1));
  return [scale, offset];
}

class EdgeInteger {
  readonly step: number;
  readonly offset: number;
  constructor(step: number, offset: number) { this.step = step; this.offset = Math.abs(offset); }
  closeto(ms: number, edge: number): boolean {
    let tol: number;
    if (this.offset > 0) {
      const digits = Math.log10(this.offset / this.step);
      tol = Math.min(0.4999, Math.max(1e-10, 10 ** (digits - 12)));
    } else tol = 1e-10;
    return Math.abs(ms - edge) < tol;
  }
  le(x: number): number {
    const [d, m] = pyDivmod(x, this.step);
    return this.closeto(m / this.step, 1) ? d + 1 : d;
  }
  ge(x: number): number {
    const [d, m] = pyDivmod(x, this.step);
    return this.closeto(m / this.step, 0) ? d : d + 1;
  }
}

function extendedSteps(steps: number[]): number[] {
  let s = [...steps];
  if (s[0] !== 1) s = [1, ...s];
  if (s[s.length - 1] !== 10) s = [...s, 10];
  return [...s.slice(0, -1).map(v => 0.1 * v), ...s, 10 * s[1]];
}

/** = matplotlib.ticker.MaxNLocator(nbins, steps).tick_values(vmin, vmax) */
export function tickValues(vmin: number, vmax: number, nbins: number | "auto" = 10, steps = STEPS, minNTicks = 2): number[] {
  [vmin, vmax] = nonsingular(vmin, vmax, 1e-13, 1e-14);
  const nb = nbins === "auto" ? 9 : Math.trunc(nbins);
  const [scale, offset] = scaleRange(vmin, vmax, nb);
  const lo = vmin - offset, hi = vmax - offset;
  const st = extendedSteps(steps).map(v => v * scale);
  const raw = (hi - lo) / nb;
  let istep = st.findIndex(v => v >= raw);
  if (istep < 0) istep = st.length - 1;
  let ticks: number[] = [];
  for (let k = istep; k >= 0; k--) {
    const step = st[k];
    const best = pyFloorDiv(lo, step) * step;
    const edge = new EdgeInteger(step, offset);
    const low = edge.le(lo - best), high = edge.ge(hi - best);
    ticks = [];
    for (let i = low; i <= high; i++) ticks.push(i * step + best);
    if (ticks.filter(t => t <= hi && t >= lo).length >= minNTicks) break;
  }
  return ticks.map(t => t + offset);
}
