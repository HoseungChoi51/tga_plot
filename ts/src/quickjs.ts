// A RunCode for the data hatch on QuickJS (quickjs-emscripten), the same isolation as KetchupE's
// electron/excel/sandbox.ts: no host callbacks, modules, files or network inside; a fixed Date and a seeded
// Math.random; an interrupt after timeoutMs; JSON in and out, non-finite numbers refused. KetchupE can pass its own
// runner instead; this one is for tests and for hosts without one. quickjs-emscripten is an optional peer dependency.
import type { RunCode } from "./types.ts";

export interface QuickJSOptions {
  timeoutMs?: number;      // default 15 s, as KetchupE
  maxCodeChars?: number;   // default 30,000
  executionTime?: number;  // what Date.now() returns inside
}

export function quickjsRunCode(opts: QuickJSOptions = {}): RunCode {
  const timeoutMs = opts.timeoutMs ?? 15_000, maxChars = opts.maxCodeChars ?? 30_000, now = opts.executionTime ?? 0;
  return async (body: string, input: unknown, signal?: AbortSignal) => {
    if (body.length > maxChars) throw new Error(`the code is longer than ${maxChars} characters`);
    const { getQuickJS } = await import("quickjs-emscripten");
    const engine = await getQuickJS();
    const runtime = engine.newRuntime();
    const deadline = Date.now() + timeoutMs;
    runtime.setInterruptHandler(() => Date.now() > deadline || !!signal?.aborted);
    const context = runtime.newContext();
    try {
      const init = context.evalCode(`(() => {
        const OriginalDate = Date, now = ${JSON.stringify(now)};
        const FixedDate = new Proxy(OriginalDate, {
          apply: () => new OriginalDate(now).toString(),
          construct: (target, args, receiver) => Reflect.construct(target, args.length ? args : [now], receiver)
        });
        Object.defineProperty(FixedDate, "now", { value: () => now });
        OriginalDate.prototype.constructor = FixedDate;
        globalThis.Date = FixedDate;
        let seed = 123456789;
        Math.random = () => { seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5; return (seed >>> 0) / 4294967296; };
      })()`);
      if (init.error) { init.error.dispose(); throw new Error("could not set up the sandbox"); }
      init.value.dispose();
      const json = JSON.stringify(JSON.stringify(input));
      const result = context.evalCode(`(() => { const encode = JSON.stringify, finite = Number.isFinite;
        const output = (function(input) { "use strict";\n${body}\n})(JSON.parse(${json}));
        if (output === undefined) throw new Error("the code returned nothing");
        return encode(output, (_k, v) => { if (typeof v === "number" && !finite(v)) throw new Error("Non-finite number in result"); return v; }); })()`,
        "data_code.js");
      if (result.error) {
        let detail = "error or time limit";
        try {
          const message = context.getProp(result.error, "message");
          try { if (context.typeof(message) === "string") detail = context.getString(message).slice(0, 500); } finally { message.dispose(); }
        } finally { result.error.dispose(); }
        throw new Error(detail);
      }
      try {
        if (context.typeof(result.value) !== "string") throw new Error("the code must return JSON");
        return JSON.parse(context.getString(result.value));
      } finally { result.value.dispose(); }
    } finally { context.dispose(); runtime.dispose(); }
  };
}
