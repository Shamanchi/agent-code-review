"""Детерминированные AST-правила ревью Python-кода."""

from __future__ import annotations

import ast
import io
import tokenize

from pydantic import BaseModel


class RawFinding(BaseModel):
    rule: str
    severity: int
    line: int
    message: str
    suggestion: str


def _check_todo(source: str) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        upper = line.upper()
        if "TODO" in upper or "FIXME" in upper:
            findings.append(
                RawFinding(
                    rule="todo-comment",
                    severity=1,
                    line=lineno,
                    message="TODO/FIXME marker left in code",
                    suggestion="Create a tracking issue and remove the marker, or resolve it now",
                )
            )
    return findings


def _check_print(tree: ast.AST) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            findings.append(
                RawFinding(
                    rule="print-call",
                    severity=1,
                    line=node.lineno,
                    message="print() call in code",
                    suggestion="Use logging instead of print for non-CLI code",
                )
            )
    return findings


def _check_bare_except(tree: ast.AST) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append(
                RawFinding(
                    rule="bare-except",
                    severity=3,
                    line=node.lineno,
                    message="Bare except: catches everything including KeyboardInterrupt",
                    suggestion="Catch specific exceptions, e.g. except (ValueError, KeyError)",
                )
            )
    return findings


def _check_wildcard_import(tree: ast.AST) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    findings.append(
                        RawFinding(
                            rule="wildcard-import",
                            severity=2,
                            line=node.lineno,
                            message=f"Wildcard import from {node.module or '?'}",
                            suggestion="Import explicit names to keep namespace clear",
                        )
                    )
    return findings


def _check_functions(tree: ast.AST, max_lines: int) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > max_lines:
                findings.append(
                    RawFinding(
                        rule="long-function",
                        severity=2,
                        line=node.lineno,
                        message=f"Function {node.name!r} is {length} lines (limit {max_lines})",
                        suggestion="Split the function into smaller helpers",
                    )
                )
            if ast.get_docstring(node) is None:
                findings.append(
                    RawFinding(
                        rule="missing-docstring",
                        severity=1,
                        line=node.lineno,
                        message=f"Function {node.name!r} has no docstring",
                        suggestion="Add a one-line docstring describing the contract",
                    )
                )
    return findings


def run_rules(source: str, max_function_lines: int = 50) -> list[RawFinding]:
    """Прогнать все правила. Возвращает находки в порядке обхода (стабильно)."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [
            RawFinding(
                rule="syntax-error",
                severity=3,
                line=exc.lineno or 0,
                message=f"Syntax error: {exc.msg}",
                suggestion="Fix the syntax so the module parses",
            )
        ]
    findings: list[RawFinding] = []
    findings.extend(_check_todo(source))
    findings.extend(_check_print(tree))
    findings.extend(_check_bare_except(tree))
    findings.extend(_check_wildcard_import(tree))
    findings.extend(_check_functions(tree, max_function_lines))
    # Стабильный порядок для тестов: по (severity desc, line, rule).
    findings.sort(key=lambda f: (-f.severity, f.line, f.rule))
    return findings


def token_count(source: str) -> int:
    """Грубая оценка размера для summary (без внешних зависимостей)."""
    try:
        return sum(1 for _ in tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return 0
