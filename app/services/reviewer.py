"""Оркестрация ревью: правила + веса эволюции + summary."""

from __future__ import annotations

from pydantic import BaseModel

from app.services.evolution import EvolutionStore
from app.services.rules import RawFinding, run_rules, token_count


class Finding(BaseModel):
    rule: str
    severity: int
    line: int
    message: str
    suggestion: str
    weight: float
    score: float


class ReviewResult(BaseModel):
    findings: list[Finding]
    summary: dict


def review_code(source: str, store: EvolutionStore, max_function_lines: int = 50) -> ReviewResult:
    raw: list[RawFinding] = run_rules(source, max_function_lines)
    findings = [
        Finding(
            rule=f.rule,
            severity=f.severity,
            line=f.line,
            message=f.message,
            suggestion=f.suggestion,
            weight=store.weight(f.rule),
            score=round(store.weight(f.rule) * f.severity, 2),
        )
        for f in raw
    ]
    findings.sort(key=lambda f: (-f.score, -f.severity, f.line, f.rule))
    by_severity: dict[str, int] = {}
    for f in findings:
        key = str(f.severity)
        by_severity[key] = by_severity.get(key, 0) + 1
    return ReviewResult(
        findings=findings,
        summary={"total": len(findings), "by_severity": by_severity, "tokens": token_count(source)},
    )
