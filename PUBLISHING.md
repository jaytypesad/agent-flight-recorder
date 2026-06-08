# Publishing Checklist

Use this checklist when turning the folder into a GitHub repository.

## Repository

Recommended repository name:

```text
agent-flight-recorder
```

Recommended description:

```text
A tiny flight recorder for AI agent traces: capture workflow events, flag risky spans, and select cheap eval candidates.
```

Suggested topics:

```text
ai-agents, llm, evals, observability, tool-calling, agent-framework
```

## First Commit

```bash
git init
git add .
git commit -m "feat: publish agent flight recorder prototype"
```

## Smoke Test

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
afr examples/failing_research_agent.jsonl || true
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Launch Post

Short version:

```text
I built Agent Flight Recorder, a tiny reliability layer for AI agents.

Instead of evaluating every step, it records every step and flags the spans most
likely to explain a failure: retry loops, ignored tool errors, unsupported
verification claims, context drift, and cost spikes.

The goal is to make agent failures replayable and cheap to triage.
```

Long version:

```text
Production agent failures are hard to debug because the final answer hides the
causal chain. Agent Flight Recorder adds an append-only trace format plus cheap
failure signatures so teams can pick the few spans worth human or model review.

It is framework-agnostic, standard-library Python, and meant to sit beside
LangGraph, OpenAI Agents SDK, AutoGen, CrewAI, or a custom loop.
```
