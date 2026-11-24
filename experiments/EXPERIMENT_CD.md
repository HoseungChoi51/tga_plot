# Constrained decoding: does a schema-constrained reply make better plots?

The question: with thinking off, does constraining the model's reply to a per-request JSON Schema make the
plots better than today's free reply? The free reply is checked by plotkit, with `error` + `hint` sent back on
failure.

In a constrained run the model *cannot* write broken JSON, an unknown key, or a file, sheet or column name that
is not in the data preview. It can still choose the wrong column, the wrong aggregation or the wrong chart.
So the expected effect is fewer retries and fewer "no plot" turns. A higher pass rate would come only from those
turns. The grammar also forces canonical keys (`sheets`, never the alias `sheet`), and it could push a weak model
off its natural path. Either effect could go either way, which is why this is an experiment.

## What changed

| file | what |
|---|---|
| `spec_schema.py` | Builds the schema for one request from what the model is shown (files, sheets, columns → enums; only canonical keys). Two profiles: **full** (the spec as the prompts describe it; for llama.cpp, vLLM, SGLang) and **flat** (the same spec as a flat settings list, `flat_to_spec()` converts it back; fits the Anthropic API's schema limits). |
| `eval/cd.py` | Arm suffixes, `response_format` for OpenAI-compatible servers, an Anthropic Messages API backend (`output_config.format`, `output_config.effort`, thinking disabled), schema conformance. |
| `eval/cnt_runs.py` | CNT study: arms `P-mpl+cd`, `P-ec+cd`, `P-hyb+cd`, `…+cdflat`; `--backend`, `--effort`, `--cd-param`, `--asks`, `--cd-note`; new CSV columns `cd`, `model`, `schema_ok_first`, `schema_ok_all`, `schema_error`. |
| `eval/arms.py`, `eval/run_batch.py` | The same for the TGA study (Set A/B). |
| `run_agent.py` | `--constrain`: the app's minimal agent with constrained decoding. |
| `eval/cd_preflight.py` | Checks that a server really enforces the schema and compiles every schema the runs will send. |
| `eval/cd_compare.py` | Paired comparison of free vs constrained arms. |
| `eval/cd_selftest.py` | Offline checks (no model): replay of known-good specs, flat round trip, column resolution, API limits. |

Free arms are unchanged. Their prompts, retries and checks are as before; the only addition is the
`schema_ok_*` columns, which record whether each free reply would have fitted the schema.

## The arms

| arm | prompt | reply | decoding |
|---|---|---|---|
| `P-mpl`, `P-ec`, `P-hyb` | prompts/v2 (CNT) or AGENT.md (TGA), unchanged | JSON spec in a ```json fence | free |
| `…+cd` | the same prompt, unchanged | JSON spec, no fence (the grammar starts at `{`) | full schema |
| `…+cdflat` | the same prompt + a short "Reply format (settings list)" section | flat settings list → `flat_to_spec` → spec | flat schema |

- `+cd` vs free isolates the grammar. The prompt still asks for a fence, which the grammar does not allow, so
  the grammar simply makes the reply start at `{`. `--cd-note` adds one line saying so, if you want to test that too.
- `+cdflat` also changes the reply format and the prompt. That is a second variable, so on Qwen compare `+cdflat`
  with `+cd` to separate the format from the grammar.
- `--asks first` makes `asks` required, so the grammar writes it right after `file`/`chart`, before `x`, `y` and the
  rest. That is a small written plan without thinking. The default `last` matches the prompt examples.
  Treat it as a separate ablation run.
- Column names may be written in full, without the unit in brackets, or as the column letter. All three resolve
  to the same column, which the self-test checks. A `data_code` that adds columns opens a second branch where
  column names are free text.

## 0. Before any run

```
pip install jsonschema                       # used for the conformance columns and the checks
python eval/cd_selftest.py                   # offline; should match the numbers below
```

Then check that the server enforces schemas:

```
EVAL_API_KEY_FILE=~/.config/strixhalo_key python eval/cd_preflight.py --base-url http://strixhalo:8084/v1 --model qwen3.8-flash-next
ANTHROPIC_API_KEY=... python eval/cd_preflight.py --backend anthropic --model claude-haiku-5-5 --effort low
```

The probe must say `ENFORCED`. A server that silently ignores `response_format` would make the `+cd` arms
identical to the free ones. If llama.cpp shows `NOT ENFORCED`, retry with `--cd-param json_schema`
(llama.cpp's own field) and use the same flag in the runs. Every schema must come back `ok`. A compile failure
means a schema feature the server's converter lacks, so send me the message.

## 1. Main run: Qwen3.8 Flash Next on strixhalo, CNT dev split

Thinking is off, as in every CNT run (`enable_thinking: false`). Run all arms in the **same** run, so they share
the server, the time window and the requests:

```
EVAL_API_KEY_FILE=~/.config/strixhalo_key python eval/cnt_runs.py --split dev --name cd1 \
  --base-url http://strixhalo:8084/v1 --model qwen3.8-flash-next \
  --arms P-mpl,P-mpl+cd,P-mpl+cdflat,P-ec,P-ec+cd --repeat 3 --workers 2
python eval/cd_compare.py eval/results/cnt_cd1.csv --by kind --list
```

This is 44 turns × 5 arms × 3 repeats = 660 turns, plus retries. The P-ec arms need `npm install --prefix echartkit`.

Optional ablations, each in its own run:
- `--name cd1_asks --asks first --arms P-mpl,P-mpl+cd`
- `--name cd1_note --cd-note --arms P-mpl,P-mpl+cd`
- `--temperature 0.7` (the TGA study's setting) to see whether the grammar matters more when sampling is noisier

## 2. Proxy run: Claude Haiku 5.5 at low effort, thinking disabled

The Anthropic API accepts only the flat profile: every object must be closed, string lengths are not allowed,
and a schema may have at most 24 optional parameters and 16 anyOf. The full spec has hundreds of optional keys.

```
ANTHROPIC_API_KEY=... python eval/cnt_runs.py --split dev --name cdh --backend anthropic \
  --model claude-haiku-5-5 --effort low --temperature 0.2 \
  --arms P-mpl,P-mpl+cdflat,P-ec,P-ec+cdflat --repeat 3 --workers 4
python eval/cd_compare.py eval/results/cnt_cdh.csv --by kind --list
```

- Each call sends `thinking: {"type": "disabled"}` and `output_config: {"effort": "low"}`. The ~5k-token system
  prompt is marked for prompt caching.
- The API adds its own system prompt describing the format. Compiling a new schema the first time adds latency,
  so ignore `llm_s` for the first calls of each request.
- What this proxy can and can't tell you: whether a weaker model benefits from the grammar and the flat format.
  It cannot tell you the size of the effect on Qwen. Use it to decide whether the Qwen run is worth the server
  time, not in place of it.

## 3. TGA study (optional)

```
EVAL_API_KEY_FILE=~/.config/strixhalo_key python eval/run_batch.py --name cd_sx --base-url http://strixhalo:8084/v1 \
  --model qwen3.8-flash-next --no-think --temperature 0.7 --arms P-mpl,P-mpl+cd,P-ec,P-ec+cd --repeat 3 --workers 3
python eval/cd_compare.py eval/results/batch_cd_sx.csv --by group --list
```

## 4. Sealed split, once, at the end

The sealed split is held out. Run it only after the dev results have made you pick one design, with the free arm
and the chosen constrained arm on the same backend. The earlier sealed run went through opencode, which cannot
take a schema, so it is not a valid pair for the constrained arm.

```
... python eval/cnt_runs.py --split sealed --name cd_sealed --arms P-mpl,P-mpl+cd --repeat 3 ...
```

## Reading the result

`cd_compare.py` pairs each constrained arm with its free arm on (item, turn, repeat). For each pair it reports:
- the pass rate with a 95% CI from a bootstrap over items (repeats and session turns of one item are not independent)
- the paired Δ with its CI
- McNemar's exact test on the discordant pairs
- first-try pass, retry rate, "no plot" rate, median model time and output tokens
- `fits`: how often the arm's first reply fits the schema as written

For a free arm, `fits` is the share of replies the grammar would not have touched at all. In the offline replay
it was about 84%: most of the rest used the alias `sheet`.

| result | reading |
|---|---|
| Δ pass ≥ 0 with CI touching 0, but fewer retries and lower latency | The grammar removes repairs without changing the answers. Ship it: cheaper turns, no "no plot". |
| Δ pass clearly > 0 | It also fixes answers, probably wrong columns or files. Check the `--list` pairs. |
| Δ pass < 0 | The grammar pushes the model off its path. Read the losing pairs' replies (`run_dir`/record.json): forced canonical keys, a column it wanted to write differently, a cut-off reply. Try `--cd-note` and `--asks first` before giving up. |
| `+cdflat` < `+cd` on Qwen | The flat format costs more than the grammar gives. Use the full profile locally; on the API, flat is the only option. |

Before trusting a small Δ, look at the noise between repeats of the same free arm (pass rate by repeat in
`cnt_summary.py`). The two earlier free dev runs `cnt_dev_a` and `cnt_dev_b` differed by about 10 points on P-mpl,
which is why every arm here runs in the same run.

## Offline checks already done (`python eval/cd_selftest.py`)

- **Columns:** 316 enum values (full names, names without the unit, letters) over the CNT files. Each resolves to
  exactly the intended column with chartkit.
- **Replay:** 358 distinct specs that passed in the dev runs, plus 53 hand-written TGA answers.
  - After rewriting aliases to canonical keys, all fit the full schema except 2 P-mpl specs: one used an unknown
    key `smooth.col` that chartkit ignores, one used an `asks.how` of `"default"`.
  - As written, 84% of the dev specs fit. The grammar would have changed the other 16%, mostly `sheet` → `sheets`.
- **Flat:** the same 411 specs, written in the flat form and converted back, normalise to the same spec. 409 fit
  the flat schema; the other 2 are the same two specs.
- **Limits:** every flat schema stays within the Anthropic limits (0 optional parameters, at most 7 anyOf). The
  full schemas are 6–35 kB.
- **Plumbing:** tested against a fake server, end to end through `cnt_runs.py` (OpenAI and Anthropic backends,
  multi-turn), `run_batch.py` and `run_agent.py --constrain`. The fake server checked that every constrained
  request carried the schema, that the model's reply fitted it, that thinking was off, and that effort was sent.

Not checked here: grammar compilation and enforcement on a real llama.cpp or the Anthropic API.
`cd_preflight.py` does that on your side.

## Results (2026-11-23): OpenCode Go and Strix Halo

Qwen3.8 Flash, thinking off, temperature 0.2, CNT dev split, 3 repeats. Page: `python report/build_cd.py` → `report/cd/`.

| arm | OpenCode Go, 34 items | Strix Halo, 15-item subset |
|---|---|---|
| P-mpl (free) | 97.7% | 95.0% |
| P-mpl+cdflat | 81.8% (Δ −15.9, p < 0.001) | 90.0% (Δ −5.0, p = 0.51) |
| P-mpl+cdabc | 72.0% (Δ −25.8, p < 0.001) | not run |
| P-mpl+cd | 6.1% (Δ −91.7) | not run (see below) |
| P-ec (free) | 95.5% | 86.7% |
| P-ec+cdabc / P-ec+cdflat | 72.0% (Δ −23.5) | 83.3% (Δ −3.3, p = 0.75) |

**OpenCode Go** (`--backend anthropic --base-url https://opencode.ai/inference/go/anthropic --model qwen3.8-flash`,
key in `EVAL_API_KEY_FILE`):
- The gateway accepts object keys only in alphabetical order at every level.
  - Required keys are reordered.
  - An optional key that sorts before one already written is dropped silently.
  - A reply that starts with `"file"` therefore loses `asks`, `by`, `chart` and `data_code`. That explains `+cd`.
- `+cdabc` is the full schema plus a prompt note to write keys alphabetically. It brings `chart` back, but `by` then has to be written before `chart`, and with thinking off the model often puts the grouping column under `z` instead.
- `cd.py` sends a neutral `user-agent`: Cloudflare refuses Python's default with error code 1010. It also sends the per-conversation `x-opencode-session` header the gateway requires.

**Strix Halo** (gufo, `--cd-compat gufo`, see `eval/cd_gufo.py`):
- gufo rejects the schemas as written:
  - every enum and const needs a `type`;
  - every object must be closed;
  - the root must be one object;
  - `strict: true` needs every key required.
- gufo keeps the schema's key order, and optional keys may be skipped but not written earlier.
- The adapter does five things:
  - merges the root `anyOf`;
  - adds types;
  - closes the open maps (`annotate` gets a fixed name list; colour maps and the `echarts` patch are dropped);
  - orders keys by the model's own order, measured from the free dev replies;
  - sends `strict: false`.
- Flat schemas work: 0 retries and no "no plot" turns, against 2–7% retries free, but turns take about 60% longer and use about twice the output tokens.
- The adapted full schema hung the server: the request never returned and the box needed a restart. The full-schema arms were not run there.

`+cd2` (full schema plus a branch with `sheets` before `chart`, for engines that keep schema order with required keys
first) was added but not run: OpenCode Go sorts keys anyway, and gufo could not take the full schema.

The offline self-test validates replies with JSON Schema, which ignores key order. Both servers enforce an order,
so add a key-order probe to the preflight before trusting a schema on a new server.
