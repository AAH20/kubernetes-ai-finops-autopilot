from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Candidate:
    name: str
    provider: str
    hourly_cost: float
    requests_per_hour: float
    success_rate: float
    p95_latency_ms: float
    quality_score: float
    gpu_utilization: float
    carbon_g_per_hour: float
    residency: str
    availability: float

    @classmethod
    def from_dict(cls, value: dict) -> "Candidate":
        return cls(**value)


@dataclass(frozen=True)
class Economics:
    successful_requests_per_hour: float
    hourly_revenue: float
    hourly_margin: float
    margin_percent: float
    cost_per_success: float
    revenue_per_success: float
    tokens_per_dollar: float

    def to_dict(self) -> dict:
        return asdict(self)
