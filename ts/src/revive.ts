// Turn the markers in plotkit's chart options back into functions, before chart.setOption(option).
// Port of plotkit/js/revive.mjs (same code, typed loosely). No imports and no Node APIs: runs anywhere.
/* eslint-disable @typescript-eslint/no-explicit-any */

/** Python-style "{:.1f}", "{:,.0f}", "{:.3g}", "{:.1%}" (with any text around it) applied to v. */
export function formatPy(fmt: string, v: any): string {
  if (v == null || (typeof v === "number" && !Number.isFinite(v))) return "";
  return fmt.replace(/\{[A-Za-z0-9_]*:?(,?)(?:\.(\d+))?([fgde%])?\}/g, (_, comma, prec, type) => {
    if (typeof v !== "number") return String(v);
    const p = prec === undefined ? null : Number(prec);
    let s;
    if (type === "f") s = v.toFixed(p ?? 6);
    else if (type === "%") s = (v * 100).toFixed(p ?? 6) + "%";
    else if (type === "e") s = v.toExponential(p ?? 6);
    else if (type === "d") s = Math.round(v).toString();
    else s = gfmt(v, p ?? 6);
    if (comma) {
      const [i, d] = s.split(".");
      s = i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (d !== undefined ? "." + d : "");
    }
    return s;
  });
}

function gfmt(v: number, p: number): string {
  if (v === 0) return "0";
  const e = Math.floor(Math.log10(Math.abs(v)));
  if (e < -4 || e >= Math.max(p, 1)) return Number(v.toExponential(Math.max(p - 1, 0))).toExponential().replace("e+", "e+0").replace(/e\+0(\d\d)/, "e+$1");
  return String(Number(v.toPrecision(Math.max(p, 1))));
}

function valueOf(p: any): any {
  if (p == null) return p;
  if (typeof p !== "object") return p;                  // axis label formatters get the value itself
  let v = p.value;
  if (Array.isArray(v)) v = v[v.length - 1];
  else if (v && typeof v === "object") v = v.value;
  return v;
}

function histBar(opacity: number): any {
  return (params: any, api: any) => {
    const x0 = api.value(0), x1 = api.value(1), y = api.value(2), base = api.value(3) || 0;
    const a = api.coord([x0, base + y]), b = api.coord([x1, base]);
    return { type: "rect", shape: { x: a[0], y: a[1], width: Math.max(0, b[0] - a[0] - 0.5), height: b[1] - a[1] },
             style: { fill: api.visual("color"), opacity, stroke: "#ffffff", lineWidth: 0.5 } };
  };
}

function errorBar(horizontal: boolean): any {
  return (params: any, api: any) => {
    const k = api.value(0), lo = api.value(1), hi = api.value(2);
    const a = horizontal ? api.coord([lo, k]) : api.coord([k, lo]);
    const b = horizontal ? api.coord([hi, k]) : api.coord([k, hi]);
    const w = 4;
    const cap = (p: any) => horizontal ? { x1: p[0], y1: p[1] - w, x2: p[0], y2: p[1] + w } : { x1: p[0] - w, y1: p[1], x2: p[0] + w, y2: p[1] };
    const style = { stroke: "#222222", lineWidth: 1.2 };
    return { type: "group", children: [
      { type: "line", shape: { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, style },
      { type: "line", shape: cap(a), style }, { type: "line", shape: cap(b), style }] };
  };
}

/** Replace the marker strings with functions, in place. */
export function revive(option: any): any {
  const walk = (o: any) => {
    if (Array.isArray(o)) { o.forEach(walk); return; }
    if (!o || typeof o !== "object") return;
    for (const [k, v] of Object.entries(o)) {
      if (typeof v === "string" && v.startsWith("__fmt__")) {
        const f = v.slice(7);
        o[k] = (p: any) => formatPy(f, valueOf(p));
      } else if (typeof v === "string" && v.startsWith("__pie__:")) {
        const mode = v.slice(8);
        o[k] = (p: any) => mode === "value" ? `${p.name}\n${formatPy("{:.4g}", p.value)}`
          : mode === "both" ? `${p.name}\n${formatPy("{:.4g}", p.value)} (${p.percent.toFixed(1)}%)`
          : mode === "none" ? p.name : `${p.name}\n${p.percent.toFixed(1)}%`;
      } else if (k === "renderItem" && v === "__histbar__") {
        o[k] = histBar(o.itemStyle?.opacity ?? 0.9);
      } else if (k === "renderItem" && typeof v === "string" && v.startsWith("__errorbar__")) {
        o[k] = errorBar(v.endsWith(":h"));
      } else walk(v);
    }
  };
  walk(option);
  return option;
}
