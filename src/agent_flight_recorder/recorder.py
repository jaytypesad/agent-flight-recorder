"""Trace event primitives for agent workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class TraceEvent:
    """One append-only event emitted by an agent workflow."""

    run_id: str
    step_id: str
    kind: str
    timestamp_ms: int
    name: str
    input: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TraceEvent":
        return cls(
            run_id=str(payload["run_id"]),
            step_id=str(payload["step_id"]),
            kind=str(payload["kind"]),
            timestamp_ms=int(payload["timestamp_ms"]),
            name=str(payload["name"]),
            input=dict(payload.get("input", {})),
            output=dict(payload.get("output", {})),
            metadata=dict(payload.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def read_jsonl(path: str | Path) -> list[TraceEvent]:
    events: list[TraceEvent] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                events.append(TraceEvent.from_dict(json.loads(stripped)))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid trace event at line {line_number}: {exc}") from exc
    return events


def write_jsonl(path: str | Path, events: Iterable[TraceEvent]) -> None:
    with Path(path).open("w", encoding="utf-8") as file:
        for event in events:
            file.write(json.dumps(event.to_dict(), ensure_ascii=True, sort_keys=True))
            file.write("\n")
