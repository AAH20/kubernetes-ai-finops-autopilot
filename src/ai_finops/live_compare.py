"""Compare two measured inference configurations and prepare reversible canary artifacts."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import math
from pathlib import Path
import re


K8S_NAME = re.compile(r"^[a-z][a-z0-9-]{0,61}[a-z0-9]$")
HOSTNAME = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")


class CompareError(ValueError):
    pass


def _number(value: object, label: str, *, positive: bool = False) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise CompareError(f"{label} must be a finite number")
    if value < 0 or (positive and value == 0):
        raise CompareError(f"{label} must be {'positive' if positive else 'nonnegative'}")
    return float(value)


def _cost(value: object, label: str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise CompareError(f"{label} must be a decimal amount") from None
    if not amount.is_finite() or amount <= 0:
        raise CompareError(f"{label} must be positive")
    return amount


def _name(value: object, label: str) -> str:
    if not isinstance(value, str) or not K8S_NAME.fullmatch(value):
        raise CompareError(f"{label} must be a Kubernetes name")
    return value


def _benchmark(value: dict, label: str) -> dict:
    required = {"schema_version", "model", "requested", "succeeded", "failed", "concurrency",
                "duration_s", "successful_requests_per_s", "latency_p95_s", "ttft_p95_s", "provenance",
                "workload_digest_sha256"}
    if not isinstance(value, dict) or required - value.keys():
        raise CompareError(f"{label} benchmark is incomplete")
    if value["schema_version"] != "1.0":
        raise CompareError(f"{label} has unsupported benchmark schema")
    if not all(type(value[key]) is int for key in ("requested", "succeeded", "failed", "concurrency")):
        raise CompareError(f"{label} request counts must be integers")
    if (value["requested"] < 1 or value["succeeded"] < 0 or value["failed"] < 0
            or value["succeeded"] + value["failed"] != value["requested"]
            or not 1 <= value["concurrency"] <= value["requested"]):
        raise CompareError(f"{label} request counts are inconsistent")
    for key in ("duration_s", "successful_requests_per_s", "latency_p95_s", "ttft_p95_s"):
        _number(value[key], f"{label} {key}")
    if value["duration_s"] <= 0:
        raise CompareError(f"{label} duration must be positive")
    measured_rps = value["succeeded"] / value["duration_s"]
    if abs(measured_rps - value["successful_requests_per_s"]) > max(0.01, measured_rps * 0.02):
        raise CompareError(f"{label} throughput disagrees with count and duration")
    digest = value["workload_digest_sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise CompareError(f"{label} workload digest must be lowercase SHA-256 hex")
    return value


def compare(plan: dict, baseline: dict, candidate: dict) -> dict:
    if not isinstance(plan, dict):
        raise CompareError("plan must be an object")
    for key in ("service_id", "namespace", "route_name", "gateway_name",
                "baseline_service", "candidate_service"):
        _name(plan.get(key), key)
    hostname = plan.get("hostname")
    if not isinstance(hostname, str) or not HOSTNAME.fullmatch(hostname):
        raise CompareError("hostname is invalid")
    if plan["baseline_service"] == plan["candidate_service"]:
        raise CompareError("baseline and candidate must be different services")
    port = plan.get("service_port")
    if type(port) is not int or not 1 <= port <= 65535:
        raise CompareError("service_port is invalid")
    baseline = _benchmark(baseline, "baseline")
    candidate = _benchmark(candidate, "candidate")
    if baseline["model"] != candidate["model"] or baseline["workload_digest_sha256"] != candidate["workload_digest_sha256"]:
        raise CompareError("benchmarks must use the same model and workload digest")
    if baseline["requested"] != candidate["requested"] or baseline["concurrency"] != candidate["concurrency"]:
        raise CompareError("benchmarks must use equal request count and concurrency")
    targets = plan.get("targets")
    if not isinstance(targets, dict):
        raise CompareError("targets are required")
    min_requests = targets.get("minimum_requests")
    if type(min_requests) is not int or min_requests < 1:
        raise CompareError("minimum_requests must be a positive integer")
    max_latency = _number(targets.get("maximum_p95_latency_s"), "maximum_p95_latency_s", positive=True)
    max_ttft = _number(targets.get("maximum_p95_ttft_s"), "maximum_p95_ttft_s", positive=True)
    min_quality = _number(targets.get("minimum_quality_score"), "minimum_quality_score")
    min_savings = _number(targets.get("minimum_cost_reduction_pct"), "minimum_cost_reduction_pct")
    if min_quality > 1 or min_savings >= 100:
        raise CompareError("quality or cost reduction target is out of range")
    quality = plan.get("quality")
    if not isinstance(quality, dict):
        raise CompareError("quality scores are required")
    baseline_quality = _number(quality.get("baseline_score"), "baseline quality")
    candidate_quality = _number(quality.get("candidate_score"), "candidate quality")
    if max(baseline_quality, candidate_quality) > 1:
        raise CompareError("quality scores must be between zero and one")
    suite_digest = quality.get("suite_digest_sha256")
    if not isinstance(suite_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", suite_digest):
        raise CompareError("quality suite digest must be lowercase SHA-256 hex")
    prices = plan.get("costs")
    if not isinstance(prices, dict):
        raise CompareError("costs are required")
    baseline_hourly = _cost(prices.get("baseline_hourly_usd"), "baseline hourly cost")
    candidate_hourly = _cost(prices.get("candidate_hourly_usd"), "candidate hourly cost")
    if baseline["successful_requests_per_s"] == 0 or candidate["successful_requests_per_s"] == 0:
        raise CompareError("both benchmarks require positive successful throughput")
    baseline_unit = baseline_hourly / Decimal(str(baseline["successful_requests_per_s"] * 3600))
    candidate_unit = candidate_hourly / Decimal(str(candidate["successful_requests_per_s"] * 3600))
    reduction = (baseline_unit - candidate_unit) / baseline_unit * 100
    gates = {
        "operator_supplied_measurements": all(
            item["provenance"] == "operator_supplied_measurement" for item in (baseline, candidate)),
        "minimum_sample": baseline["requested"] >= min_requests,
        "baseline_healthy": baseline["failed"] == 0,
        "candidate_healthy": candidate["failed"] == 0,
        "candidate_latency": candidate["latency_p95_s"] <= max_latency,
        "candidate_ttft": candidate["ttft_p95_s"] <= max_ttft,
        "quality_floor": candidate_quality >= min_quality,
        "quality_nonregression": candidate_quality >= baseline_quality,
        "cost_reduction": reduction >= Decimal(str(min_savings)),
    }
    result = {
        "schema_version": "1.0", "service_id": plan["service_id"],
        "status": "CANARY_REVIEW_REQUIRED" if all(gates.values()) else "HOLD",
        "gates": gates,
        "baseline_cost_per_1000_successes_usd": round(float(baseline_unit * 1000), 4),
        "candidate_cost_per_1000_successes_usd": round(float(candidate_unit * 1000), 4),
        "projected_cost_reduction_pct": round(float(reduction), 2),
        "scope": "Short-run throughput projection from operator-supplied benchmark and hourly cost; not a realized billing saving.",
        "quality_scope": "Operator-supplied scores; this tool cannot authenticate evaluators or test-answer quality.",
        "route_scope": "A proposed HTTPRoute only; no traffic change is executed.",
    }
    canonical = json.dumps({"plan": plan, "baseline": baseline, "candidate": candidate},
                           sort_keys=True, separators=(",", ":")).encode()
    result["input_sha256"] = sha256(canonical).hexdigest()
    return result


def route_yaml(plan: dict, *, canary: bool) -> str:
    base = plan["baseline_service"]
    candidate = plan["candidate_service"]
    port = plan["service_port"]
    second = (f"\n        - name: {candidate}\n          port: {port}\n          weight: 10" if canary else "")
    return f"""# Review the existing route and save its exact state before applying this proposal.
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: {plan['route_name']}
  namespace: {plan['namespace']}
spec:
  parentRefs:
    - name: {plan['gateway_name']}
  hostnames:
    - {plan['hostname']}
  rules:
    - backendRefs:
        - name: {base}
          port: {port}
          weight: {90 if canary else 100}{second}
"""


def write_outputs(plan: dict, report: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    if report["status"] == "CANARY_REVIEW_REQUIRED":
        (output / "canary-90-10.yaml").write_text(route_yaml(plan, canary=True))
        (output / "rollback-baseline.yaml").write_text(route_yaml(plan, canary=False))
    else:
        for name in ("canary-90-10.yaml", "rollback-baseline.yaml"):
            (output / name).unlink(missing_ok=True)
