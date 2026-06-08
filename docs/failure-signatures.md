# Failure Signatures

The prototype ships with five deliberately cheap signatures. They are not final
truth. They are a triage layer for deciding which spans deserve human review or
expensive model-based evaluation.

## `retry_loop`

The same tool is called four times in a row. This often means the agent is stuck
behind a rate limit, malformed query, missing permission, or stale assumption.

## `unrecovered_tool_error`

A tool result contains an error, and the next three events do not mark a recovery
path. This catches the common failure mode where an agent silently moves past a
broken observation.

## `unsupported_tool_claim`

The assistant claims verification or tool-backed certainty, but tool outputs do
not contain overlapping evidence. This is a cheap hallucination smoke test for
tool-using agents.

## `context_drift`

The assistant pivots with "instead" while sharing few keywords with the declared
goal. This catches work substitution, which is common when agents hit friction.

## `cost_spike`

One event uses at least 4x the run's median token count and at least 4000 tokens.
This helps identify spans where context assembly or runaway reasoning made the
run expensive.
