import unittest

from agent_flight_recorder import analyze_trace, read_jsonl, select_eval_candidates


class SignatureTests(unittest.TestCase):
    def test_failing_trace_flags_high_risk_signatures(self):
        events = read_jsonl("examples/failing_research_agent.jsonl")

        signatures = {finding.signature for finding in analyze_trace(events)}

        self.assertIn("retry_loop", signatures)
        self.assertIn("unrecovered_tool_error", signatures)
        self.assertIn("unsupported_tool_claim", signatures)
        self.assertIn("context_drift", signatures)
        self.assertIn("cost_spike", signatures)

    def test_healthy_trace_has_no_findings(self):
        events = read_jsonl("examples/healthy_trace.jsonl")

        self.assertEqual(analyze_trace(events), [])

    def test_eval_candidates_are_ranked_by_severity(self):
        events = read_jsonl("examples/failing_research_agent.jsonl")

        candidates = select_eval_candidates(events, limit=2)

        self.assertEqual(len(candidates), 2)
        self.assertTrue(all(candidate.severity == "high" for candidate in candidates))

    def test_retry_loop_points_to_fourth_consecutive_call(self):
        events = read_jsonl("examples/failing_research_agent.jsonl")

        retry_loop = next(finding for finding in analyze_trace(events) if finding.signature == "retry_loop")

        self.assertEqual(retry_loop.step_id, "s007")


if __name__ == "__main__":
    unittest.main()
