from pathlib import Path
import unittest

from agent_flight_recorder import TraceEvent, read_jsonl, write_jsonl


class RecorderTests(unittest.TestCase):
    def test_jsonl_round_trip(self):
        path = Path(self._testMethodName).with_suffix(".jsonl")
        events = [
            TraceEvent(
                run_id="run-1",
                step_id="s001",
                kind="tool_call",
                timestamp_ms=123,
                name="search",
                input={"query": "agent evals"},
                output={},
                metadata={"tokens": 24},
            )
        ]

        try:
            write_jsonl(path, events)

            self.assertEqual(read_jsonl(path), events)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
