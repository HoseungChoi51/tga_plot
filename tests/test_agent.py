"""The model side and the reference loop, with a fake model (offline; nothing is sent anywhere)."""
import json
from pathlib import Path

import pytest

import plotkit
from plotkit import agent

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
GOOD = {"file": "run_log.csv", "chart": "bar", "x": "반응기", "y": {"col": "수율", "agg": "mean"},
        "asks": [{"ask": "반응기별 평균 수율", "how": "key"}, {"ask": "박스 플롯으로", "how": "unsupported"}]}


class FakeLLM:
    """Replies from a list, and records what it was sent."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, messages, **options):
        self.calls.append({"messages": [dict(m) for m in messages], "options": options})
        return self.replies.pop(0)


def fenced(spec):
    return "알겠습니다.\n```json\n" + json.dumps(spec, ensure_ascii=False) + "\n```"


def test_a_good_reply_gives_options():
    llm = FakeLLM(fenced(GOOD))
    r = agent.run("반응기별 평균 수율, 박스 플롯으로", ["run_log.csv"], llm, base=INPUTS)
    assert r["ok"] and r["attempts"] == 1
    assert r["spec"] == GOOD                                 # as the model wrote it (file names relative to base)
    assert len(r["options"]) == 1 and r["options"][0]["series"]
    assert r["not_done"] == ["박스 플롯으로"]
    first = llm.calls[0]["messages"]
    assert first[0]["role"] == "system" and first[0]["content"] == agent.system_prompt("echarts")
    assert first[1]["content"].startswith("데이터 미리보기:\n파일 run_log.csv") and first[1]["content"].endswith(
        "사용자 요청:\n반응기별 평균 수율, 박스 플롯으로")


def test_a_bad_key_gets_the_error_and_hint_then_a_retry():
    bad = {**GOOD, "colour_by": "등급"}
    llm = FakeLLM(fenced(bad), fenced(GOOD))
    r = agent.run("반응기별 평균 수율", ["run_log.csv"], llm, base=INPUTS)
    assert r["ok"] and r["attempts"] == 2
    retry = llm.calls[1]["messages"][-1]
    assert retry["role"] == "user" and retry["content"].startswith('plotkit error: unknown key "colour_by"')
    assert "\nhint: " in retry["content"] and retry["content"].endswith("고쳐서 다시 보내 주세요.")
    assert llm.calls[1]["messages"][-2] == {"role": "assistant", "content": fenced(bad)}


def test_unreadable_replies_use_up_the_retries():
    llm = FakeLLM("no json here", "still none", "{broken")
    r = agent.run("반응기별 평균 수율", ["run_log.csv"], llm, base=INPUTS)
    assert not r["ok"] and r["attempts"] == 3 and len(llm.calls) == 3
    assert r["error"].startswith("your reply could not be read") and r["hint"] == "reply with one ```json block"
    assert r["options"] == []


def test_reasoning_changes_only_the_request_options():
    a, b = FakeLLM(fenced(GOOD)), FakeLLM(fenced(GOOD))
    agent.run("반응기별 평균 수율", ["run_log.csv"], a, base=INPUTS)
    agent.run("반응기별 평균 수율", ["run_log.csv"], b, base=INPUTS, reasoning=True)
    assert a.calls[0]["messages"] == b.calls[0]["messages"]
    assert a.calls[0]["options"] == {"chat_template_kwargs": {"enable_thinking": False}}
    assert b.calls[0]["options"] == {"chat_template_kwargs": {"enable_thinking": True}}


def test_the_follow_up_turn_carries_the_last_spec():
    llm = FakeLLM(fenced(GOOD), fenced({**GOOD, "chart": "hbar"}))
    r1 = agent.run("반응기별 평균 수율", ["run_log.csv"], llm, base=INPUTS)
    r2 = agent.run("가로 막대로", ["run_log.csv"], llm, base=INPUTS, history=r1["transcript"])
    assert r2["ok"] and r2["spec"]["chart"] == "hbar"
    sent = llm.calls[1]["messages"]
    assert sent[:-1] == r1["transcript"]                     # the history, with the last spec in the assistant turn
    assert fenced(GOOD) in [m["content"] for m in sent if m["role"] == "assistant"]
    assert sent[-1] == {"role": "user", "content": "사용자 요청 (이어서):\n가로 막대로"}
    assert "지금 그림의 spec" in agent.followup_message("x", last_spec=GOOD)     # for apps that do not keep history


def test_request_options():
    assert agent.request_options() == {"chat_template_kwargs": {"enable_thinking": False}}
    assert agent.request_options(True) == {"chat_template_kwargs": {"enable_thinking": True}}


def test_parse_reply():
    assert agent.parse_reply("<think>{\"no\": 1}</think>\n```json\n{\"file\": \"a.csv\"}\n```") == {"file": "a.csv"}
    assert agent.parse_reply('그럼 {"file": "a.csv", "x": {"col": "B"}} 로 할게요') == {"file": "a.csv", "x": {"col": "B"}}
    with pytest.raises(plotkit.PlotkitError):
        agent.parse_reply("```json\n[1, 2]\n```")


def test_retry_message_from_an_error_or_a_result():
    e = plotkit.PlotkitError("sheet 3 not found", "sheets: A, B")
    assert agent.retry_message(e) == "plotkit error: sheet 3 not found\nhint: sheets: A, B\n\n고쳐서 다시 보내 주세요."
    assert agent.retry_message({"ok": False, "error": "x", "hint": ""}) == "plotkit error: x\n\n고쳐서 다시 보내 주세요."


def test_system_prompts():
    ec, mpl = agent.system_prompt("echarts"), agent.system_prompt("matplotlib")
    core_md = (Path(agent.PROMPTS) / "core.md").read_text(encoding="utf-8")
    assert ec.startswith(core_md) and mpl.startswith(core_md) and ec != mpl


def test_preview_names_files_relative_to_base():
    rel = agent.preview(["run_log.csv"], base=INPUTS)
    absolute = agent.preview([str(INPUTS / "run_log.csv")], base=HERE)         # outside base: shown as given
    assert rel.splitlines()[1] == "파일 run_log.csv"
    assert absolute.splitlines()[1] == "파일 inputs/run_log.csv"
    assert agent.preview([str(INPUTS / "run_log.csv")], base="/nowhere").splitlines()[1] == f"파일 {(INPUTS / 'run_log.csv').as_posix()}"
