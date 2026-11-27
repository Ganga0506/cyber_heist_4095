"""Defensive regression coverage for the restricted console."""

from asyncio import CancelledError
from contextlib import ExitStack
from time import monotonic

import pytest
from fastapi import HTTPException

import console_guard
import gameplay
from console_expression import ConsoleRejected, ConsoleTimeout, evaluate, parse_expression
from console_guard import ConsoleGate
from tests.test_gameplay import new_agent

PATH = "/api/puzzles/1/code"
SOLUTION = "decode64(encoded)"


def start_lesson(client, name="fixture.agent"):
    headers = new_agent(client, name)
    assert client.post("/api/missions/1/start", headers=headers).status_code == 200
    return headers


def send_code(client, headers, action, code):
    return client.post(PATH, headers=headers, json={"action": action, "code": code})


@pytest.mark.parametrize("code", [
    "encoded.upper()", "unknown(encoded)", "lower(encoded)", "decode64(\u212fncoded)",
    "import os\nprint('fixture')", "print('fixture')",
    "[encoded]", "encoded + encoded", "decode64(" * 13 + "encoded" + ")" * 13,
    r'"\ud800"',
])
def test_restricted_grammar_blocks_unsupported_constructs(client, code):
    headers = start_lesson(client)
    response = send_code(client, headers, "submit", code)
    assert response.status_code == 200
    result = response.json()
    assert result["error"] and result["status"] == "blocked"
    assert result["cases"] and all(case["status"] == "skipped" and "output" not in case for case in result["cases"])
    assert result["attempt"]["points_awarded"] == 0
    assert result["attempt"]["unlocked_mission_ids"] == []


def test_bounded_source_and_runtime_values(client):
    headers = start_lesson(client)
    for code in ("x" * 513, "\u00e9" * 512 + "x", "\U0001f600" * 300):
        assert send_code(client, headers, "save", code).status_code == 422
    result = send_code(client, headers, "run", "decode64(True)").json()
    assert all(case["error"] == "decode64 needs a text input" for case in result["cases"])
    result = send_code(client, headers, "run", SOLUTION).json()
    assert result["passed"]
    assert result["cases"][-1]["output"] == "<note>"


def test_kill_switch_and_deadline_preserve_drafts_and_scores(client, monkeypatch, caplog):
    headers = start_lesson(client)
    other = start_lesson(client, "other.agent")
    monkeypatch.setenv("CYBERHEIST_CONSOLE_MODE", "disabled")
    assert send_code(client, headers, "save", "initial draft").json() == {"saved": True}
    assert send_code(client, headers, "submit", SOLUTION).status_code == 503

    monkeypatch.setenv("CYBERHEIST_CONSOLE_MODE", "unexpected")
    assert send_code(client, headers, "run", SOLUTION).status_code == 503
    monkeypatch.setenv("CYBERHEIST_CONSOLE_MODE", "simulation")
    real_runner = gameplay.run_cases

    def timeout(*args, **kwargs):
        raise ConsoleTimeout

    monkeypatch.setattr(gameplay, "run_cases", timeout)
    assert send_code(client, headers, "submit", SOLUTION).status_code == 503
    assert "console_evaluation_stopped reason=deadline" in caplog.text
    assert SOLUTION not in caplog.text
    progress = client.get("/api/me/progress", headers=headers).json()
    assert progress["score"] == 0
    assert progress["missions"][0]["puzzles"][0]["draft"] == "initial draft"
    assert client.get("/api/me/progress", headers=other).json()["missions"][0]["puzzles"][0]["draft"] is None

    monkeypatch.setattr(gameplay, "run_cases", real_runner)
    assert send_code(client, headers, "run", SOLUTION).json()["passed"]


def test_account_quota_concurrency_and_interrupted_cleanup(monkeypatch):
    monkeypatch.setattr(console_guard, "REQUESTS_PER_USER", 2)
    gate = ConsoleGate()
    with pytest.raises(CancelledError):
        with gate.admit(1, execute=True):
            with pytest.raises(HTTPException) as busy:
                with gate.admit(1, execute=True):
                    pytest.fail("Same-account request was admitted twice")
            assert busy.value.status_code == 429
            raise CancelledError
    with gate.admit(1, execute=True):
        pass
    with pytest.raises(HTTPException) as exhausted:
        with gate.admit(1, execute=False):
            pytest.fail("Account quota was bypassed")
    assert exhausted.value.status_code == 429
    with ExitStack() as stack:
        for user_id in range(2, 2 + console_guard.MAX_ACTIVE):
            stack.enter_context(gate.admit(user_id, execute=True))
        with pytest.raises(HTTPException) as full:
            with gate.admit(20, execute=True):
                pytest.fail("Console admitted work beyond global capacity")
        assert full.value.status_code == 429
    with gate.admit(20, execute=True):
        pass


def test_evaluator_checks_deadline_tree_size_and_expanding_output():
    params = ({"sender_domain"}, {"lower"})
    with pytest.raises(ConsoleTimeout):
        parse_expression("sender_domain", *params, monotonic() - 1)
    tree = "True"
    for _ in range(5):
        tree = f"({tree} == {tree})"
    with pytest.raises(ConsoleRejected, match="Simplify"):
        parse_expression(tree, *params, monotonic() + 1)
    expression = parse_expression('lower("' + "\u0130" * 200 + '")', *params, monotonic() + 1)
    with pytest.raises(ConsoleRejected, match="512-byte"):
        evaluate(expression, {}, monotonic() + 1)


def test_policy_threshold_logs_a_single_aggregate_event(caplog):
    gate = ConsoleGate()
    for _ in range(20):
        gate.policy_rejection()
    assert caplog.messages == ["console_policy_rejections threshold=10 window_seconds=60"]
