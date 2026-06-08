# Trace Schema

Agent Flight Recorder uses newline-delimited JSON so traces can be appended from
almost any runtime and streamed into ordinary log pipelines.

Each line is one event:

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

## Required Fields

- `run_id`: stable identifier for one agent run.
- `step_id`: stable identifier for one event within a run.
- `kind`: event category. The prototype understands `goal`, `tool_call`,
  `tool_result`, and `assistant_message`.
- `timestamp_ms`: event timestamp or monotonic sequence time in milliseconds.
- `name`: source of the event, such as the tool name or `assistant`.

## Flexible Fields

- `input`: structured inputs visible at that step.
- `output`: structured outputs visible at that step.
- `metadata`: operational details such as token counts, model name, retries,
  latency, recovery marker, or environment.

## Design Rule

The recorder should store enough evidence to replay the failure narrative without
storing unnecessary private data. Redact secrets before writing traces.
