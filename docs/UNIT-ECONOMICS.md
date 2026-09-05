# Unit economics and KPIs

## Core equations

```text
served requests       = min(demand, candidate capacity)
successful outcomes   = served requests × success rate
cost per success      = hourly cost ÷ successful outcomes
hourly revenue        = successful outcomes × revenue per success
contribution margin   = hourly revenue − hourly infrastructure/model cost
monthly margin delta  = (candidate margin − baseline margin) × 730
```

The example's `$0.035` revenue per success and candidate prices are synthetic. A customer pilot must replace them with invoices, amortized infrastructure cost, support cost, discounts, measured success criteria and actual business value.

## Operational KPIs

- P50, P95 and P99 inference latency
- Availability and successful outcome rate
- Requests and tokens per second
- GPU compute/memory utilization and idle hours
- KV-cache hit rate and batching efficiency
- Queue depth and time-to-first-token
- Capacity headroom and forecast error
- Carbon and energy per successful outcome

## Financial KPIs

- Cost per successful inference
- Cost per completed agent workflow
- Contribution margin per workload, tenant and product
- Tokens and successful outcomes per dollar
- Avoided idle capacity and egress cost
- Reserved/spot/on-demand coverage
- Cloud/API/on-premises break-even utilization
- Predicted-versus-realized margin delta

## Automation KPIs

- Recommendation acceptance rate
- Change failure and rollback rates
- SLO regressions caught during canary
- Evidence completeness and freshness
- Mean time from regression to proposal
- Percentage of proposals with measured post-change outcomes

Never market projected savings as realized savings. Publish both the baseline period and post-change measurement window, including volume and quality changes.
