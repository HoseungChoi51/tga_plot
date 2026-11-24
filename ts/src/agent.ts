// The model side: the system prompt, the messages, reading the reply, the retry turn, and a reference loop.
// A port of plotkit/agent.py; the strings are the same (the CNT study's protocol), except that data_code is
// JavaScript here (prompts/core.md).
import { PlotkitError } from "./errors.ts";
import { PROMPT_CORE, PROMPT_HATCH_ECHARTS } from "./prompts.ts";
import { previewText } from "./preview.ts";
import type { InputFile, RunCode } from "./types.ts";

export const RETRIES = 2;

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

/** The system prompt: the spec, the asks, the examples, and the ECharts hatch. */
export function systemPrompt(): string {
  return PROMPT_CORE + PROMPT_HATCH_ECHARTS;
}

/** The first user turn: the data preview, then the request. names: the files as the user named them (patterns
 *  allowed); files: their bytes. */
export async function firstMessage(request: string, names: string[], files: InputFile[]): Promise<string> {
  return `${await previewText(names, files)}\n\n사용자 요청:\n${request}`;
}

/** A later turn on the same plot. Pass lastSpec only when the app does not send the chat history. */
export function followupMessage(request: string, lastSpec?: unknown): string {
  const head = lastSpec === undefined ? "" : "지금 그림의 spec:\n```json\n" + JSON.stringify(lastSpec, null, 1) + "\n```\n\n";
  return `${head}사용자 요청 (이어서):\n${request}`;
}

/** The JSON text in a reply: <think> blocks dropped, the first ```json block, else the outermost {...}. */
export function replyJson(text: string): string {
  text = (text ?? "").replace(/<think>[\s\S]*?<\/think>/g, "");
  const m = /```(?:json)?\s*\n([\s\S]*?)```/.exec(text);
  return m ? m[1] : text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1);
}

/** The spec in a model reply. Raises PlotkitError, to send back with retryMessage, when there is no JSON object. */
export function parseReply(text: string): Record<string, unknown> {
  let spec: unknown;
  try {
    spec = JSON.parse(replyJson(text));
  } catch (e) {
    throw new PlotkitError(`your reply could not be read: ${(e as Error).message}`, "reply with one ```json block");
  }
  if (!spec || typeof spec !== "object" || Array.isArray(spec)) {
    throw new PlotkitError("your reply could not be read: the JSON is not an object", "reply with one ```json block");
  }
  return spec as Record<string, unknown>;
}

/** The turn that sends an error back: plotkit's message and hint, and a request to fix it. */
export function retryMessage(err: PlotkitError | { error?: string; hint?: string }): string {
  const [msg, hint] = err instanceof PlotkitError ? [err.message, err.hint] : [err.error ?? "", err.hint ?? ""];
  return `plotkit error: ${msg}` + (hint ? `\nhint: ${hint}` : "") + "\n\n고쳐서 다시 보내 주세요.";
}

/** Extra request-body fields for a locally served model (llama.cpp, vLLM, SGLang; Qwen-style templates): thinking
 *  off unless the user asks for it. */
export function requestOptions(reasoning = false): Record<string, unknown> {
  return { chat_template_kwargs: { enable_thinking: !!reasoning } };
}

export type Llm = (messages: ChatMessage[], options: Record<string, unknown>, signal?: AbortSignal) => Promise<string>;

export interface RunResult {
  ok: boolean;
  spec: Record<string, unknown> | null;
  options: unknown[];
  warnings: string[];
  not_done: string[];
  values: unknown;
  error: string | null;
  hint: string | null;
  attempts: number;
  transcript: ChatMessage[];
}

/** One request -> the spec and its live ECharts options (nothing is drawn to files). The reference loop: preview ->
 *  model -> parse -> options, at most `retries` retries with plotkit's error and hint. history: the transcript of an
 *  earlier run on the same plot (the request is then a follow-up). */
export async function run(request: string, names: string[], files: InputFile[], llm: Llm,
  opts: { reasoning?: boolean; history?: ChatMessage[]; retries?: number; runCode?: RunCode; signal?: AbortSignal } = {}):
  Promise<RunResult> {
  const { echartsOptions } = await import("./api.ts");
  const retries = opts.retries ?? RETRIES;
  const options = requestOptions(opts.reasoning);
  const messages: ChatMessage[] = opts.history?.length
    ? [...opts.history, { role: "user", content: followupMessage(request) }]
    : [{ role: "system", content: systemPrompt() }, { role: "user", content: await firstMessage(request, names, files) }];
  let spec: Record<string, unknown> | null = null;
  let err: PlotkitError | null = null;
  for (let attempt = 1; attempt <= retries + 1; attempt++) {
    const reply = await llm(messages, options, opts.signal);
    messages.push({ role: "assistant", content: reply });
    try {
      spec = parseReply(reply);
      const res = await echartsOptions(spec, files, { runCode: opts.runCode, signal: opts.signal });
      return { ok: true, spec, options: res.options, warnings: res.warnings, not_done: res.not_done, values: res.values,
        error: null, hint: null, attempts: attempt, transcript: messages };
    } catch (e) {
      if (!(e instanceof PlotkitError)) throw e;
      err = e;
      if (attempt <= retries) messages.push({ role: "user", content: retryMessage(e) });
    }
  }
  return { ok: false, spec, options: [], warnings: [], not_done: [], values: {}, error: err!.message, hint: err!.hint,
    attempts: retries + 1, transcript: messages };
}
