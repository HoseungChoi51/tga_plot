// The model side and the reference loop with a fake model (nothing is sent anywhere), and data_code through the
// public API with the QuickJS sandbox.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { BASES } from "./golden.ts";
import { echartsOptions, firstMessage, followupMessage, parseReply, PlotkitError, quickjsRunCode, renderSvg,
  requestOptions, retryMessage, run, systemPrompt } from "../src/index.ts";
import type { ChatMessage, InputFile } from "../src/index.ts";

const file = (name: string): InputFile => ({ name, bytes: readFileSync(join(BASES["tests/inputs"], name)) });
const FILES = [file("run_log.csv"), file("TGA.xlsx")];
const GOOD = { file: "run_log.csv", chart: "bar", x: "반응기", y: { col: "수율", agg: "mean" },
  asks: [{ ask: "반응기별 평균 수율", how: "key" }, { ask: "박스 플롯으로", how: "unsupported" }] };
const fenced = (spec: unknown) => "알겠습니다.\n```json\n" + JSON.stringify(spec) + "\n```";

function fake(...replies: string[]) {
  const calls: { messages: ChatMessage[]; options: Record<string, unknown> }[] = [];
  const llm = async (messages: ChatMessage[], options: Record<string, unknown>) => {
    calls.push({ messages: messages.map(m => ({ ...m })), options });
    return replies.shift()!;
  };
  return { llm, calls };
}

test("a good reply gives options", async () => {
  const { llm, calls } = fake(fenced(GOOD));
  const r = await run("반응기별 평균 수율, 박스 플롯으로", ["run_log.csv"], FILES, llm);
  assert.ok(r.ok && r.attempts === 1 && r.options.length === 1);
  assert.deepEqual(r.spec, GOOD);
  assert.deepEqual(r.not_done, ["박스 플롯으로"]);
  const [sys, user] = calls[0].messages;
  assert.equal(sys.content, systemPrompt());
  assert.ok(user.content.startsWith("데이터 미리보기:\n파일 run_log.csv"));
  assert.ok(user.content.endsWith("사용자 요청:\n반응기별 평균 수율, 박스 플롯으로"));
});

test("a bad key gets the error and hint, then a retry", async () => {
  const bad = { ...GOOD, colour_by: "등급" };
  const { llm, calls } = fake(fenced(bad), fenced(GOOD));
  const r = await run("반응기별 평균 수율", ["run_log.csv"], FILES, llm);
  assert.ok(r.ok && r.attempts === 2);
  const retry = calls[1].messages.at(-1)!;
  assert.equal(retry.role, "user");
  assert.ok(retry.content.startsWith('plotkit error: unknown key "colour_by"') && retry.content.includes("\nhint: "));
  assert.ok(retry.content.endsWith("고쳐서 다시 보내 주세요."));
});

test("unreadable replies use up the retries", async () => {
  const { llm, calls } = fake("no json here", "still none", "{broken");
  const r = await run("반응기별 평균 수율", ["run_log.csv"], FILES, llm);
  assert.ok(!r.ok && r.attempts === 3 && calls.length === 3);
  assert.ok(r.error!.startsWith("your reply could not be read") && r.hint === "reply with one ```json block");
});

test("reasoning changes only the request options; follow-ups keep the history", async () => {
  const a = fake(fenced(GOOD)), b = fake(fenced(GOOD));
  await run("x", ["run_log.csv"], FILES, a.llm);
  await run("x", ["run_log.csv"], FILES, b.llm, { reasoning: true });
  assert.deepEqual(a.calls[0].messages, b.calls[0].messages);
  assert.deepEqual(a.calls[0].options, requestOptions(false));
  assert.deepEqual(b.calls[0].options, { chat_template_kwargs: { enable_thinking: true } });
  const c = fake(fenced(GOOD), fenced({ ...GOOD, chart: "hbar" }));
  const r1 = await run("반응기별 평균 수율", ["run_log.csv"], FILES, c.llm);
  const r2 = await run("가로 막대로", ["run_log.csv"], FILES, c.llm, { history: r1.transcript });
  assert.ok(r2.ok && (r2.spec as any).chart === "hbar");
  assert.deepEqual(c.calls[1].messages.slice(0, -1), r1.transcript);
  assert.deepEqual(c.calls[1].messages.at(-1), { role: "user", content: "사용자 요청 (이어서):\n가로 막대로" });
  assert.ok(followupMessage("x", GOOD).includes("지금 그림의 spec"));
});

test("message helpers", async () => {
  assert.deepEqual(parseReply('<think>{"a":1}</think>```json\n{"file": "a.csv"}\n```'), { file: "a.csv" });
  assert.throws(() => parseReply("```json\n[1, 2]\n```"), PlotkitError);
  assert.equal(retryMessage(new PlotkitError("sheet 3 not found", "sheets: A, B")),
    "plotkit error: sheet 3 not found\nhint: sheets: A, B\n\n고쳐서 다시 보내 주세요.");
  assert.ok((await firstMessage("요청", ["TGA.xlsx"], FILES)).includes("파일 TGA.xlsx (시트 3개)"));
});

test("data_code runs in the host's sandbox, and is refused without one", async () => {
  const runCode = quickjsRunCode();
  const chart = { file: "run_log.csv", chart: "bar", x: "반응기", y: { col: "수율_x10", agg: "mean" },
    data_code: "for (const r of rows) r['수율_x10'] = r['수율'] * 10" };
  const c = await echartsOptions(chart, FILES, { runCode });
  assert.ok(c.ok && Math.max(...c.values.series["수율_x10"]) > 40);
  const curve = { file: "TGA.xlsx", sheets: 1, data_code: "x = x.map(v => v + 273.15)", x: { label: "Temperature (K)" } };
  const k = await renderSvg(curve, FILES, { runCode });
  assert.ok(k.ok && k.files.length === 1 && k.files[0].svg.includes("Temperature (K)"));
  await assert.rejects(echartsOptions(chart, FILES), (e: any) => e instanceof PlotkitError && /no data_code/.test(e.hint));
});
