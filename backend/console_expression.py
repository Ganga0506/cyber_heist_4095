"""Small, side-effect-free expression evaluator for fictional lesson data."""

import ast
import base64
import binascii
import time
from types import MappingProxyType

MAX_SOURCE_CHARS = 512
MAX_SOURCE_BYTES = 1024
MAX_NODES = 48
MAX_DEPTH = 12
MAX_TEXT_BYTES = 512
EVALUATION_SECONDS = 0.05


class ConsoleRejected(ValueError):
    pass


class ConsoleSyntaxError(ConsoleRejected):
    pass


class ConsoleTimeout(RuntimeError):
    pass


def check_deadline(deadline):
    if time.monotonic() >= deadline:
        raise ConsoleTimeout


def check_text(value, limit):
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        raise ConsoleRejected("Use valid Unicode text") from None
    if size > limit:
        raise ConsoleRejected(f"Text exceeds the {limit}-byte limit")
    return value


def check_source(code):
    if len(code) > MAX_SOURCE_CHARS:
        raise ConsoleRejected(f"Use at most {MAX_SOURCE_CHARS} characters")
    return check_text(code, MAX_SOURCE_BYTES)


def decode64(value):
    try:
        return base64.b64decode(value, validate=True).decode("utf-8")
    except (ValueError, binascii.Error):
        raise ValueError("decode64 needs valid Base64 that decodes to UTF-8 text") from None


FUNCTIONS = MappingProxyType({"decode64": decode64, "lower": str.lower})
UNSUPPORTED = "Use lesson inputs, text, True or False, the listed functions, or =="


def parse_expression(code, names, functions, deadline):
    check_deadline(deadline)
    source = check_source(code).strip()
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as error:
        raise ConsoleSyntaxError(f"Python syntax error on line {error.lineno or 1}. Check brackets, quotes, and punctuation.") from None
    except RecursionError:
        raise ConsoleRejected("Simplify your expression to fit the lesson") from None
    for statement in tree.body:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            raise ConsoleRejected(f"Imports are blocked in this lesson (line {statement.lineno}).")
    if not tree.body:
        raise ConsoleSyntaxError("Python syntax error. Enter an expression to test.")
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Expr):
        raise ConsoleRejected("This lesson allows one expression. Python statements are blocked.")
    expression = tree.body[0].value
    pending = [(expression, 1)]
    count = 0
    while pending:
        check_deadline(deadline)
        node, depth = pending.pop()
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            raise ConsoleRejected("Simplify your expression to fit the lesson")
        match node:
            case ast.Constant(value=value) if type(value) is str:
                check_text(value, MAX_TEXT_BYTES)
            case ast.Constant(value=value) if type(value) is bool:
                pass
            case ast.Name(id=name) if name in names and ast.get_source_segment(source, node) == name:
                pass
            case ast.Call(func=ast.Name(id=name) as function, args=[argument], keywords=[]) if (
                name in functions and ast.get_source_segment(source, function) == name
            ):
                pending.append((argument, depth + 1))
            case ast.Call(func=ast.Name(id="print")):
                raise ConsoleRejected("print() is blocked. Enter the expression directly to see its value in the test results.")
            case ast.Compare(left=left, ops=[ast.Eq()], comparators=[right]):
                pending.extend(((left, depth + 1), (right, depth + 1)))
            case _:
                raise ConsoleRejected(UNSUPPORTED)
    return expression


def evaluate(node, inputs, deadline):
    check_deadline(deadline)
    match node:
        case ast.Constant(value=value):
            result = value
        case ast.Name(id=name):
            result = inputs[name]
        case ast.Call(func=ast.Name(id=name), args=[argument]):
            value = evaluate(argument, inputs, deadline)
            if type(value) is not str:
                raise ValueError(f"{name} needs a text input")
            result = FUNCTIONS[name](value)
        case ast.Compare(left=left, ops=[ast.Eq()], comparators=[right]):
            result = evaluate(left, inputs, deadline) == evaluate(right, inputs, deadline)
        case _:
            raise ConsoleRejected(UNSUPPORTED)
    check_deadline(deadline)
    if type(result) is str:
        check_text(result, MAX_TEXT_BYTES)
    elif type(result) is not bool:
        raise ConsoleRejected("Lesson values must be text or Boolean")
    return result
