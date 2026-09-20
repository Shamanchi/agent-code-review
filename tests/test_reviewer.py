"""Unit-тесты правил и эволюции: без сети, детерминированы."""

from app.services.evolution import EvolutionStore
from app.services.reviewer import review_code
from app.services.rules import run_rules

SAMPLE = """from os import *

# TODO: handle retries
def greet(name):
    print("hi", name)
    try:
        return int(name)
    except:
        return -1
"""


def test_rules_find_all_expected() -> None:
    findings = run_rules(SAMPLE, max_function_lines=50)
    rules = {f.rule for f in findings}
    assert {"todo-comment", "print-call", "bare-except", "wildcard-import", "missing-docstring"} <= rules


def test_syntax_error_is_finding() -> None:
    findings = run_rules("def broken(:\n", max_function_lines=50)
    assert len(findings) == 1
    assert findings[0].rule == "syntax-error"
    assert findings[0].severity == 3


def test_evolution_reweights() -> None:
    store = EvolutionStore()
    assert store.weight("print-call") == 1.0
    assert store.feedback("print-call", accepted=False) == 0.8
    assert store.feedback("print-call", accepted=True) == 0.9
    # Границы: не ниже min и не выше max.
    for _ in range(20):
        store.feedback("print-call", accepted=False)
    assert store.weight("print-call") == 0.1


def test_review_sorts_by_weighted_score() -> None:
    store = EvolutionStore()
    store.feedback("todo-comment", accepted=False)  # 0.8
    result = review_code(SAMPLE, store, max_function_lines=50)
    assert result.summary["total"] == 5
    # bare-except (severity 3, weight 1.0) должен быть первым.
    assert result.findings[0].rule == "bare-except"
    assert result.findings[0].score == 3.0
