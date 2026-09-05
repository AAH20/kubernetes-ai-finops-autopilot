# AI FinOps Decision Evidence

**Status:** `RECOMMENDATION_READY`

## Recommendation

- Selected candidate: `aks-nim-l40s-batched`
- Baseline: `azure-openai-standard`
- Projected monthly margin delta: `$11,277.04`
- Forecast peak: `2,814.29` requests/hour
- Capacity headroom: `17.26%`
- Rollout: 10% canary, evaluate SLO and economics, then promote or roll back

## Candidate scorecard

| Candidate | Admissible | Hourly cost | Cost/success | P95 | Quality | Margin/hour |
|---|---:|---:|---:|---:|---:|---:|
| aks-nim-l40s-batched | True | $15.80 | $0.0067 | 1290 ms | 0.880 | $66.69 |
| azure-openai-standard | True | $31.50 | $0.0133 | 1450 ms | 0.910 | $51.24 |
| cheap-public-api | False | $7.20 | $0.0031 | 2300 ms | 0.820 | $74.28 |

## Evidence

SHA-256: `55b79e8551c8fcdbc2e5f21271caaac2399d38b20d16435659901102b4fb3de5`

> Projection, not promised savings. Validate through a controlled canary before production rollout.
