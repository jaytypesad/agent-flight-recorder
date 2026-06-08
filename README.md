# Agent Flight Recorder

> A tiny, framework-agnostic flight recorder for AI agent failures.

Most agent demos fail in obvious ways. Production agents fail in expensive,
ambiguous ways: a tool times out, the model acts as if it succeeded, context
drifts from the user's goal, and the team only sees the final bad answer.

Agent Flight Recorder is a small open-source pattern and reference
implementation for capturing agent traces, detecting risky spans with cheap
failure signatures, and sending only the suspicious parts to deeper evaluation.

The thesis is simple:

**Do not evaluate every agent step. Record every step, then evaluate the few
spans that look causally dangerous.**

## Why This Exists

The current agent stack has plenty of orchestration frameworks, tool routers,
memory abstractions, and evaluation dashboards. The missing layer is a practical
post-incident artifact:

- What did the agent believe the task was?
- Which observation first contradicted that belief?
- Did a tool fail and get ignored?
- Did the agent claim it verified something the tools never returned?
- Which five spans should a human or judge model inspect first?

Without that layer, teams end up doing forensic debugging from prompt logs,
screenshots, and vibes. Full-run evals help, but they are often too expensive,
too slow, and too coarse to explain why a single run failed.

## The Innovation

Agent Flight Recorder treats an agent run like an aircraft incident report:

1. **Append-only trace events** capture goals, tool calls, tool results,
   assistant messages, token counts, and recovery markers.
2. **Cheap failure signatures** flag likely causes: retry loops, unrecovered
   tool errors, unsupported claims, context drift, and cost spikes.
3. **Eval candidate selection** ranks suspicious spans so expensive human or
   model evaluation is focused where it matters.

This is intentionally not another agent framework. It is the thin reliability
layer that can sit beside any framework.

## Quick Start

```bash
cd agent-flight-recorder
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
afr examples/failing_research_agent.jsonl || true
```

Expected output:

```json
{"evidence": {"tool": "web_search", "window": ["web_search", "web_search", "web_search", "web_search"]}, "reason": "The same tool was called four times in a row.", "severity": "high", "signature": "retry_loop", "step_id": "s007"}
{"evidence": {"error": "429 rate limited", "tool": "web_search"}, "reason": "A tool returned an error and the next three events did not mark a recovery path.", "severity": "high", "signature": "unrecovered_tool_error", "step_id": "s003"}
{"evidence": {"message": "i verified the latest pricing changes and confirmed the api returned a current pricing page."}, "reason": "Assistant claimed tool-backed certainty without lexical support from tool outputs.", "severity": "high", "signature": "unsupported_tool_claim", "step_id": "s008"}
```

Run the tests with the Python standard library:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Trace Format

Traces are newline-delimited JSON. One event per line:

```json
{
  "run_id": "demo-run-001",
  "step_id": "s003",
  "kind": "tool_result",
  "timestamp_ms": 3000,
  "name": "web_search",
  "input": {},
  "output": { "error": "429 rate limited" },
  "metadata": { "tokens": 180 }
}
```

See [docs/trace-schema.md](docs/trace-schema.md) for the schema.

## Built-In Failure Signatures

| Signature | What it catches | Why it matters |
| --- | --- | --- |
| `retry_loop` | Same tool called four times in a row | Agents often keep retrying the wrong action instead of changing strategy. |
| `unrecovered_tool_error` | Tool error with no marked recovery | The final answer may be built on a missing observation. |
| `unsupported_tool_claim` | Verification claim without tool evidence | A cheap smoke test for tool-backed hallucination. |
| `context_drift` | Goal substitution after friction | The agent may complete a different task than the user asked for. |
| `cost_spike` | Step with abnormal token usage | Finds expensive spans worth prompt/context review. |

See [docs/failure-signatures.md](docs/failure-signatures.md) for details.

## Minimal Python Usage

```python
from agent_flight_recorder import read_jsonl, select_eval_candidates

events = read_jsonl("examples/failing_research_agent.jsonl")
for finding in select_eval_candidates(events, limit=3):
    print(finding.signature, finding.step_id, finding.reason)
```

## What To Build Next

This repository is deliberately small, but the pattern can grow in useful ways:

- Adapters for LangGraph, OpenAI Agents SDK, AutoGen, CrewAI, and custom tool
  loops.
- A redaction layer for secrets and personally identifiable information.
- A span packer that exports only the risky local context around each finding.
- CI mode that fails only on high-severity new signatures.
- A judge prompt library that evaluates selected spans, not whole transcripts.
- A tiny browser UI for replaying runs as an incident timeline.

## How To Use This In A Real Agent

Emit a `TraceEvent` whenever your agent:

- receives or rewrites a user goal,
- calls a tool,
- receives a tool result,
- sends a final or intermediate assistant message,
- retries, recovers, or changes strategy.

Then run Agent Flight Recorder before expensive evals:

```bash
afr traces/latest-run.jsonl --limit 5
```

The output becomes your eval queue, incident report seed, or CI reliability gate.

## Positioning

Agent Flight Recorder is complementary to observability and eval platforms.
Observability tells you what happened. Evals tell you whether output quality met
a bar. A flight recorder is the bridge: it identifies which moments in the run
are most likely to explain the failure.

## License

MIT
