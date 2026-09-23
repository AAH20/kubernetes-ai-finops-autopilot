import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ai_finops.live_compare import CompareError, compare, write_outputs


ROOT = Path(__file__).resolve().parents[1] / "examples" / "live-compare"
PLAN = json.loads((ROOT / "plan.synthetic.json").read_text())
BASELINE = json.loads((ROOT / "baseline.synthetic.json").read_text())
CANDIDATE = json.loads((ROOT / "candidate.synthetic.json").read_text())


class LiveCompareTests(unittest.TestCase):
    def test_synthetic_example_cannot_issue_canary(self):
        result = compare(PLAN, BASELINE, CANDIDATE)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["gates"]["operator_supplied_measurements"])
        with TemporaryDirectory() as directory:
            (Path(directory) / "canary-90-10.yaml").write_text("stale")
            write_outputs(PLAN, result, Path(directory))
            self.assertFalse((Path(directory) / "canary-90-10.yaml").exists())

    def test_passing_measured_inputs_prepare_canary_and_rollback(self):
        baseline = {**BASELINE, "provenance": "operator_supplied_measurement"}
        candidate = {**CANDIDATE, "provenance": "operator_supplied_measurement"}
        result = compare(PLAN, baseline, candidate)
        self.assertEqual(result["status"], "CANARY_REVIEW_REQUIRED")
        self.assertGreater(result["projected_cost_reduction_pct"], 30)
        with TemporaryDirectory() as directory:
            write_outputs(PLAN, result, Path(directory))
            canary = (Path(directory) / "canary-90-10.yaml").read_text()
            rollback = (Path(directory) / "rollback-baseline.yaml").read_text()
            self.assertIn("weight: 90", canary)
            self.assertIn("weight: 10", canary)
            self.assertIn("weight: 100", rollback)
            self.assertNotIn("model-candidate", rollback)

    def test_regressed_quality_or_latency_holds(self):
        baseline = {**BASELINE, "provenance": "operator_supplied_measurement"}
        candidate = {**CANDIDATE, "provenance": "operator_supplied_measurement",
                     "latency_p95_s": 3.0}
        result = compare(PLAN, baseline, candidate)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["gates"]["candidate_latency"])
        low_quality = {**PLAN, "quality": {**PLAN["quality"], "candidate_score": 0.8}}
        self.assertFalse(compare(low_quality, baseline, CANDIDATE)["gates"]["quality_nonregression"])

    def test_incomparable_workloads_rejected(self):
        changed = {**CANDIDATE, "workload_digest_sha256": "f" * 64}
        with self.assertRaisesRegex(CompareError, "same model and workload"):
            compare(PLAN, BASELINE, changed)

    def test_inconsistent_throughput_rejected(self):
        changed = {**CANDIDATE, "successful_requests_per_s": 50.0}
        with self.assertRaisesRegex(CompareError, "throughput disagrees"):
            compare(PLAN, BASELINE, changed)


if __name__ == "__main__":
    unittest.main()
