"""Cheap failure signatures for agent traces.

The signatures are intentionally simple. They are meant to find trace spans worth
reviewing or sending to an expensive evaluator, not to replace human judgment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .recorder import TraceEvent


@dataclass(frozen=True)
class Finding:
    step_id: str
    signature: str
    severity: str
    reason: str
    evidence: dict[str, object]


def analyze_trace(events: Iterable[TraceEvent]) -> list[Finding]:
    ordered = sorted(events, key=lambda event: event.timestamp_ms)
    findings: list[Finding] = []
    findings.extend(_detect_retry_loop(ordered))
    findings.extend(_detect_context_drift(ordered))
    findings.extend(_detect_tool_error_without_recovery(ordered))
    findings.extend(_detect_unsupported_tool_claim(ordered))
    findings.extend(_detect_cost_spike(ordered))
    return sorted(findings, key=_finding_rank)


def select_eval_candidates(events: Iterable[TraceEvent], limit: int = 5) -> list[Finding]:
    """Return the riskiest findings to evaluate instead of brute-forcing all steps."""

    return analyze_trace(events)[:limit]


def _detect_retry_loop(events: list[TraceEvent]) -> list[Finding]:
    findings: list[Finding] = []
    recent_names: list[str] = []
    for event in events:
        if event.kind != "tool_call":
            recent_names = []
            continue
        recent_names.append(event.name)
        recent_names = recent_names[-4:]
        if len(recent_names) == 4 and len(set(recent_names)) == 1:
            findings.append(
                Finding(
                    step_id=event.step_id,
                    signature="retry_loop",
                    severity="high",
                    reason="The same tool was called four times in a row.",
                    evidence={"tool": event.name, "window": recent_names},
                )
            )
            break
    return findings


def _detect_context_drift(events: list[TraceEvent]) -> list[Finding]:
    declared_goal = ""
    findings: list[Finding] = []
    for event in events:
        if event.kind == "goal":
            declared_goal = str(event.output.get("summary", "")).lower()
            continue
        if event.kind != "assistant_message" or not declared_goal:
            continue
        message = str(event.output.get("text", "")).lower()
        if "instead" in message and not _shares_keywords(declared_goal, message):
            findings.append(
                Finding(
                    step_id=event.step_id,
                    signature="context_drift",
                    severity="medium",
                    reason="Assistant pivoted with 'instead' while sharing few keywords with the declared goal.",
                    evidence={"goal": declared_goal, "message": message[:180]},
                )
            )
    return findings


def _detect_tool_error_without_recovery(events: list[TraceEvent]) -> list[Finding]:
    findings: list[Finding] = []
    for index, event in enumerate(events):
        if event.kind != "tool_result" or not event.output.get("error"):
            continue
        next_events = events[index + 1 : index + 4]
        recovered = any(
            next_event.kind in {"assistant_message", "tool_call"}
            and str(next_event.metadata.get("recovery", "")).lower() in {"true", "yes", "1"}
            for next_event in next_events
        )
        if not recovered:
            findings.append(
                Finding(
                    step_id=event.step_id,
                    signature="unrecovered_tool_error",
                    severity="high",
                    reason="A tool returned an error and the next three events did not mark a recovery path.",
                    evidence={"tool": event.name, "error": event.output.get("error")},
                )
            )
    return findings


def _detect_unsupported_tool_claim(events: list[TraceEvent]) -> list[Finding]:
    tool_outputs = " ".join(
        str(event.output.get("text", event.output)) for event in events if event.kind == "tool_result"
    ).lower()
    findings: list[Finding] = []
    claim_markers = ["confirmed", "verified", "successfully completed", "the api returned"]
    for event in events:
        if event.kind != "assistant_message":
            continue
        message = str(event.output.get("text", "")).lower()
        if any(marker in message for marker in claim_markers) and not _shares_keywords(tool_outputs, message):
            findings.append(
                Finding(
                    step_id=event.step_id,
                    signature="unsupported_tool_claim",
                    severity="high",
                    reason="Assistant claimed tool-backed certainty without lexical support from tool outputs.",
                    evidence={"message": message[:180]},
                )
            )
    return findings


def _detect_cost_spike(events: list[TraceEvent]) -> list[Finding]:
    token_counts = [
        int(event.metadata.get("tokens", 0))
        for event in events
        if str(event.metadata.get("tokens", "0")).isdigit()
    ]
    if len(token_counts) < 3:
        return []
    median = sorted(token_counts)[len(token_counts) // 2]
    threshold = max(4000, median * 4)
    findings: list[Finding] = []
    for event in events:
        tokens = int(event.metadata.get("tokens", 0)) if str(event.metadata.get("tokens", "0")).isdigit() else 0
        if tokens >= threshold:
            findings.append(
                Finding(
                    step_id=event.step_id,
                    signature="cost_spike",
                    severity="medium",
                    reason="A step used far more tokens than the run's typical step.",
                    evidence={"tokens": tokens, "threshold": threshold},
                )
            )
    return findings


def _shares_keywords(left: str, right: str) -> bool:
    stopwords = {"the", "and", "for", "with", "that", "this", "from", "into", "instead", "then"}
    left_words = {word for word in _words(left) if word not in stopwords and len(word) > 3}
    right_words = {word for word in _words(right) if word not in stopwords and len(word) > 3}
    return bool(left_words & right_words)


def _words(text: str) -> list[str]:
    return ["".join(char for char in word if char.isalnum()) for word in text.lower().split()]


def _finding_rank(finding: Finding) -> tuple[int, str]:
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    return severity_rank.get(finding.severity, 3), finding.signature
