from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_finops.engine import analyze
from ai_finops.forecast import linear_forecast
from ai_finops.render import write_outputs


ROOT = Path(__file__).parents[1]


def fixture(name: str) -> dict:
    return json.loads((ROOT / "examples" / name).read_text())


class EngineTests(unittest.TestCase):
    def test_selects_admissible_higher_margin_candidate(self) -> None:
        report = analyze(fixture("retail-inference.json"))
        self.assertEqual("RECOMMENDATION_READY", report["status"])
        self.assertEqual("aks-nim-l40s-batched", report["recommendation"]["selected_candidate"])
        self.assertGreater(report["recommendation"]["projected_monthly_margin_delta"], 0)

    def test_policy_rejects_cheaper_but_noncompliant_candidate(self) -> None:
        report = analyze(fixture("retail-inference.json"))
        candidate = next(row for row in report["candidates"] if row["candidate"]["name"] == "cheap-public-api")
        self.assertFalse(candidate["policy"]["admissible"])
        self.assertEqual({"p95_latency", "quality", "availability", "data_residency"}, set(candidate["policy"]["failures"]))

    def test_no_admissible_candidate(self) -> None:
        report = analyze(fixture("no-admissible-candidate.json"))
        self.assertEqual("NO_ADMISSIBLE_CANDIDATE", report["status"])
        self.assertIsNone(report["recommendation"])

    def test_missing_evidence_fails_closed(self) -> None:
        report = analyze({})
        self.assertEqual("INCOMPLETE", report["status"])
        self.assertTrue(report["validation_errors"])

    def test_capacity_caps_successful_requests(self) -> None:
        bundle = fixture("retail-inference.json")
        bundle["workload"]["requests_per_hour"] = 10000
        report = analyze(bundle)
        candidate = next(row for row in report["candidates"] if row["candidate"]["name"] == "aks-nim-l40s-batched")
        self.assertEqual(3300 * 0.982, candidate["economics"]["successful_requests_per_hour"])

    def test_forecast_reports_backtest_error(self) -> None:
        result = linear_forecast([100, 110, 120, 130])
        self.assertEqual([140, 150, 160], result["predicted_requests_per_hour"])
        self.assertEqual(0, result["backtest_mae"])

    def test_receipt_stable_across_timestamp(self) -> None:
        first = fixture("retail-inference.json")
        second = fixture("retail-inference.json")
        first["collected_at"] = "2026-01-01T00:00:00Z"
        second["collected_at"] = "2026-02-01T00:00:00Z"
        self.assertEqual(analyze(first)["evidence_sha256"], analyze(second)["evidence_sha256"])

    def test_outputs_are_review_gated(self) -> None:
        report = analyze(fixture("retail-inference.json"))
        with tempfile.TemporaryDirectory() as temp:
            paths = write_outputs(report, temp)
            values = paths["helm_values"].read_text()
            self.assertIn("mode: shadow", values)
            self.assertIn("requires_human_approval", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
