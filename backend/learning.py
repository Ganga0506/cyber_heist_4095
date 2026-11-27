"""Mission 1 curriculum and a bounded interpreter for Python expressions."""

import time

from pydantic import BaseModel

from console_expression import EVALUATION_SECONDS, evaluate, parse_expression


class Lesson(BaseModel):
    title: str
    concept: str
    objective: str
    explanation: str
    starter: str
    hint_count: int = 3
    recap: str


LESSONS = {
    1: Lesson(
        title="Decode the intercepted clue",
        concept="Function calls and text encoding",
        objective="Write a Python expression that decodes the Base64 text in encoded.",
        explanation="A function takes an input and returns a result. In this editor, decode64(text) converts Base64 into readable text. The starter decodes a fixed example.",
        starter='decode64("SEVMTE8=")',
        recap="You called a function with a variable to decode different clues. Decoded content remains untrusted text, even when it looks like markup.",
    ),
    2: Lesson(
        title="Verify the sender domain",
        concept="String normalization and equality",
        objective="Return True when sender_domain matches trusted_domain, ignoring letter case.",
        explanation="lower(text) makes a lowercase copy of text. Python's == compares two values and returns True or False. The evidence contains fictional domain names extracted from message headers.",
        starter="sender_domain",
        recap="You normalized both inputs before testing exact equality. A similar-looking domain can still fail the comparison.",
    ),
}

PUBLIC_CASES = {
    1: [({"encoded": "SEVMTE8="}, "HELLO"), ({"encoded": "Tk9URQ=="}, "NOTE"),
        ({"encoded": "PG5vdGU+"}, "<note>")],
    2: [
        ({"sender_domain": "VAULT.test", "trusted_domain": "vault.test"}, True),
        ({"sender_domain": "vault.test.example", "trusted_domain": "vault.test"}, False),
    ],
}
EXTRA_CASES = {
    1: [({"encoded": "QUNDRVNTLVBPSU5ULUEx"}, "ACCESS-POINT-A1"), ({"encoded": ""}, "")],
    2: [
        ({"sender_domain": "office.test", "trusted_domain": "OFFICE.TEST"}, True),
        ({"sender_domain": "fake-office.test", "trusted_domain": "office.test"}, False),
    ],
}


def lesson_for(puzzle):
    return LESSONS.get(puzzle.puzzle_order) if puzzle.mission_id == 1 else None


LESSON_FUNCTIONS = {1: frozenset({"decode64"}), 2: frozenset({"lower"})}


def skipped_cases(order, error, status):
    return {"error": error, "status": status, "passed": False, "cases": [
        {"inputs": inputs, "expected": expected, "passed": False, "status": "skipped"}
        for inputs, expected in PUBLIC_CASES[order]
    ]}

def run_cases(order, code, *, final=False):
    deadline = time.monotonic() + EVALUATION_SECONDS
    names = PUBLIC_CASES[order][0][0].keys()
    expression = parse_expression(code, names, LESSON_FUNCTIONS[order], deadline)
    cases = []
    for inputs, expected in PUBLIC_CASES[order]:
        try:
            output = evaluate(expression, inputs, deadline)
            passed = type(output) is type(expected) and output == expected
            cases.append(dict(inputs=inputs, expected=expected, output=output, passed=passed,
                              status="passed" if passed else "failed"))
        except ValueError as error:
            cases.append(dict(inputs=inputs, expected=expected, error=str(error), passed=False, status="error"))
    passed = all(case["passed"] for case in cases)
    if final and passed:
        try:
            passed = all(
                type(output := evaluate(expression, inputs, deadline)) is type(expected) and output == expected
                for inputs, expected in EXTRA_CASES[order]
            )
        except ValueError:
            passed = False
    error = None
    if final and not passed and all(case["passed"] for case in cases):
        error = "An additional test failed. Check that your expression works with any provided input."
    return {"error": error, "cases": cases, "passed": passed, "status": "passed" if passed else "failed"}
