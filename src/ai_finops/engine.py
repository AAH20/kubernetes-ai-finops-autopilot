from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from .forecast import linear_forecast
from .models import Candidate, Economics
from .schema import validate


def economics(candidate: Candidate, workload: dict) -> Economics:
    demand = float(workload["requests_per_hour"])
    served = min(demand, candidate.requests_per_hour)
    successful = served * candidate.success_rate
    revenue = successful * float(workload["revenue_per_success"])
    margin = revenue - candidate.hourly_cost
    tokens = successful * float(workload["tokens_per_request"])
    return Economics(
        successful_requests_per_hour=round(successful, 4),
        hourly_revenue=round(revenue, 4),
        hourly_margin=round(margin, 4),
        margin_percent=round((margin / revenue * 100) if revenue else -100.0, 2),
        cost_per_success=round(candidate.hourly_cost / successful, 6) if successful else float("inf"),
        revenue_per_success=float(workload["revenue_per_success"]),
        tokens_per_dollar=round(tokens / candidate.hourly_cost, 2) if candidate.hourly_cost else float("inf"),
    )


def policy(candidate: Candidate, constraints: dict) -> list[str]:
    failures = []
    if candidate.p95_latency_ms > constraints["max_p95_latency_ms"]:
        failures.append("p95_latency")
    if candidate.quality_score < constraints["min_quality_score"]:
        failures.append("quality")
    if candidate.availability < constraints["min_availability"]:
        failures.append("availability")
    if candidate.residency not in constraints["allowed_residencies"]:
        failures.append("data_residency")
    return failures


def analyze(bundle: dict) -> dict:
    errors = validate(bundle)
    receipt_input = {key: value for key, value in bundle.items() if key != "collected_at"}
    receipt = hashlib.sha256(json.dumps(receipt_input, sort_keys=True).encode()).hexdigest()
    if errors:
        return {"status": "INCOMPLETE", "validation_errors": errors, "evidence_sha256": receipt}

    rows = []
    for raw in bundle["candidates"]:
        candidate = Candidate.from_dict(raw)
        values = economics(candidate, bundle["workload"])
        failures = policy(candidate, bundle["constraints"])
        score = values.hourly_margin - (len(failures) * 1_000_000)
        rows.append({
            "candidate": raw,
            "economics": values.to_dict(),
            "policy": {"admissible": not failures, "failures": failures},
            "optimization_score": round(score, 4),
        })
    rows.sort(key=lambda row: (-row["optimization_score"], row["candidate"]["name"]))
    winner = next((row for row in rows if row["policy"]["admissible"]), None)
    baseline_name = bundle["metadata"].get("baseline", bundle["candidates"][0]["name"])
    baseline = next(row for row in rows if row["candidate"]["name"] == baseline_name)
    forecast = linear_forecast([float(value) for value in bundle["history"]])
    peak = max(forecast["predicted_requests_per_hour"])
    recommendation = None
    if winner:
        delta = winner["economics"]["hourly_margin"] - baseline["economics"]["hourly_margin"]
        recommendation = {
            "action": "propose_gitops_change" if winner["candidate"]["name"] != baseline_name else "retain_baseline",
            "selected_candidate": winner["candidate"]["name"],
            "baseline_candidate": baseline_name,
            "projected_hourly_margin_delta": round(delta, 4),
            "projected_monthly_margin_delta": round(delta * 730, 2),
            "forecast_peak_rph": peak,
            "capacity_headroom_percent": round((winner["candidate"]["requests_per_hour"] - peak) / peak * 100, 2) if peak else 0,
            "requires_human_approval": True,
            "rollout": "10% canary, evaluate SLO and economics, then promote or roll back",
        }
    return {
        "status": "RECOMMENDATION_READY" if winner else "NO_ADMISSIBLE_CANDIDATE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_sha256": receipt,
        "forecast": forecast,
        "recommendation": recommendation,
        "candidates": rows,
    }
