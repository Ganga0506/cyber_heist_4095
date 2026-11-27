"""Mission 1 curriculum and a bounded interpreter for Python expressions."""

import ast
import base64
import binascii

from pydantic import BaseModel


class Lesson(BaseModel):
    title: str
    concept: str
    objective: str
    explanation: str
    starter: str
    hints: list[str]
    recap: str


LESSONS = {
    1: Lesson(
        title="Decode the intercepted clue",
        concept="Function calls and text encoding",
        objective="Write a Python expression that decodes the Base64 text in encoded.",
        explanation="A function takes an input and returns a result. In this editor, decode64(text) converts Base64 into readable text. The starter decodes a fixed example.",
        starter='decode64("SEVMTE8=")',
        hints=["Run the starter and compare both outputs.", "Replace the quoted example with the variable encoded. Leave the variable unquoted."],
        recap="You called a function with a variable so the same expression could decode different clues.",
    ),
    2: Lesson(
        title="Verify the sender domain",
        concept="String normalization and equality",
        objective="Return True when sender_domain matches trusted_domain, ignoring letter case.",
        explanation="lower(text) makes a lowercase copy of text. Python's == compares two values and returns True or False. The evidence contains fictional domain names extracted from message headers.",
        starter="sender_domain",
        hints=["Compare the two domains using ==.", "Call lower on each variable before comparing them. Both sides can contain uppercase letters."],
        recap="You normalized both inputs before testing exact equality. A similar-looking domain can still fail the comparison.",
    ),
}

PUBLIC_CASES = {
    1: [({"encoded": "SEVMTE8="}, "HELLO"), ({"encoded": "Tk9URQ=="}, "NOTE")],
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


def decode64(value):
    try:
        return base64.b64decode(value, validate=True).decode("utf-8")
    except (ValueError, binascii.Error):
        raise ValueError("decode64 needs valid Base64 that decodes to UTF-8 text") from None


FUNCTIONS = {"decode64": decode64, "lower": str.lower}


def interpret(node, inputs):
    match node:
        case ast.Constant(value=value) if type(value) in (str, bool):
            return value
        case ast.Name(id=name) if name in inputs:
            return inputs[name]
        case ast.Call(func=ast.Name(id=name), args=[argument], keywords=[]) if name in FUNCTIONS:
            value = interpret(argument, inputs)
            if not isinstance(value, str):
                raise ValueError(f"{name} needs a text input")
            return FUNCTIONS[name](value)
        case ast.Compare(left=left, ops=[ast.Eq()], comparators=[right]):
            return interpret(left, inputs) == interpret(right, inputs)
        case ast.Name(id=name):
            raise ValueError(f"Unknown input {name!r}")
        case _:
            raise ValueError("Use input names, text, True or False, decode64(), lower(), or ==")


def run_cases(order, code, *, final=False):
    try:
        if len(code) > 512:
            raise ValueError("Use at most 512 characters")
        tree = ast.parse(code.strip(), mode="eval")
        if sum(1 for _ in ast.walk(tree)) > 48:
            raise ValueError("Simplify your expression to fit the lesson")
    except SyntaxError as error:
        return {"error": f"Python syntax error. {error.msg}", "cases": [], "passed": False}
    except ValueError as error:
        return {"error": str(error), "cases": [], "passed": False}

    cases = []
    for inputs, expected in PUBLIC_CASES[order]:
        try:
            output = interpret(tree.body, inputs)
            passed = type(output) is type(expected) and output == expected
            cases.append(dict(inputs=inputs, expected=expected, output=output, passed=passed))
        except ValueError as error:
            cases.append(dict(inputs=inputs, expected=expected, error=str(error), passed=False))
    passed = all(case["passed"] for case in cases)
    if final and passed:
        try:
            passed = all(
                type(output := interpret(tree.body, inputs)) is type(expected) and output == expected
                for inputs, expected in EXTRA_CASES[order]
            )
        except ValueError:
            passed = False
    error = None
    if final and not passed and all(case["passed"] for case in cases):
        error = "An additional test failed. Check that your expression works with any provided input."
    return {"error": error, "cases": cases, "passed": passed}
