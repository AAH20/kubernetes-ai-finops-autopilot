from __future__ import annotations


REQUIRED_ROOT = {"metadata", "workload", "constraints", "candidates", "history"}
REQUIRED_WORKLOAD = {"requests_per_hour", "tokens_per_request", "revenue_per_success"}
REQUIRED_CONSTRAINTS = {"max_p95_latency_ms", "min_quality_score", "min_availability", "allowed_residencies"}
REQUIRED_CANDIDATE = {
    "name", "provider", "hourly_cost", "requests_per_hour", "success_rate",
    "p95_latency_ms", "quality_score", "gpu_utilization", "carbon_g_per_hour",
    "residency", "availability",
}


def validate(bundle: dict) -> list[str]:
    errors = [f"missing root field: {key}" for key in sorted(REQUIRED_ROOT - bundle.keys())]
    workload = bundle.get("workload", {})
    constraints = bundle.get("constraints", {})
    errors.extend(f"missing workload field: {key}" for key in sorted(REQUIRED_WORKLOAD - workload.keys()))
    errors.extend(f"missing constraint field: {key}" for key in sorted(REQUIRED_CONSTRAINTS - constraints.keys()))
    candidates = bundle.get("candidates", [])
    if not candidates:
        errors.append("at least one candidate is required")
    for index, candidate in enumerate(candidates):
        errors.extend(
            f"candidate[{index}] missing field: {key}"
            for key in sorted(REQUIRED_CANDIDATE - candidate.keys())
        )
    history = bundle.get("history", [])
    if len(history) < 3:
        errors.append("history requires at least three demand observations")
    return errors
