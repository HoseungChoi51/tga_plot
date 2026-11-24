// plotkit-ts: a language model writes a small JSON spec; plotkit checks it against the data and draws it with
// ECharts. The public API; see README.md.
export { PlotkitError } from "./errors.ts";
export type { InputFile, RunCode, Frame } from "./types.ts";
export { systemPrompt, firstMessage, followupMessage, parseReply, replyJson, retryMessage, requestOptions, run, RETRIES }
  from "./agent.ts";
export type { ChatMessage, Llm, RunResult } from "./agent.ts";
export { validate, echartsOptions, renderSvg, route } from "./api.ts";
export type { Options, SvgFile, Kind } from "./api.ts";
export { previewText } from "./preview.ts";
export { normalizeSpec } from "./spec.ts";
export { isChartSpec, normalizeChart } from "./chartspec.ts";
export { validatePatch } from "./patch.ts";
export { revive, formatPy } from "./revive.ts";
export { quickjsRunCode } from "./quickjs.ts";
export type { QuickJSOptions } from "./quickjs.ts";
export { VERSION } from "./tables.ts";
