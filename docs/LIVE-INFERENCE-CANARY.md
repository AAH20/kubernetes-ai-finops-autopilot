# Measured inference comparison and canary handoff

The first live-data path compares two operator-supplied `gifp-bench` reports for the **same model and workload**. It combines successful throughput, p95 latency and time to first token with declared hourly delivery cost and a separately reviewed quality score. It prepares a 90/10 Gateway API `HTTPRoute` proposal and a baseline-only rollback manifest only when every gate passes. It never applies either manifest or changes traffic automatically.

## Reproduce the fictional case

```bash
PYTHONPATH=src python3 -m ai_finops.live_compare_cli \
  examples/live-compare/plan.synthetic.json \
  examples/live-compare/baseline.synthetic.json \
  examples/live-compare/candidate.synthetic.json \
  --output /tmp/ai-finops-live-comparison
```

The output is `HOLD` and contains only `comparison.json`, because both reports identify themselves as `synthetic_fixture`. No canary manifest is generated from this example. All prices, metrics, services and domains in it are fictional.

## Use real, approved test windows

1. Choose one production-representative, customer-approved prompt distribution and quality evaluation suite. Record their SHA-256 digests, model revision, cluster and GPU type, vLLM/Dynamo image digest, time window and traffic source. The included `gifp-bench` command measures a single prompt; use a broader approved harness before a customer rollout.
2. Run the [GPU Inference Platform benchmark](https://github.com/AAH20/gpu-inference-platform/blob/main/docs/PRODUCTION_PILOT.md) against baseline and candidate with the same prompt, request count, concurrency and model. Retain raw reports privately. Add `provenance: operator_supplied_measurement` and the **same** `workload_digest_sha256` to both reports after checking their conditions. This is a declaration, not independent authentication.
3. Supply full hourly costs for each allocation, including idle capacity, network, storage and monitoring where applicable. Score quality on the same reviewed suite for both configurations. The score and suite digest in the plan are operator-supplied and must be supported by retained evaluation results.
4. Run `ai-finops-live-compare PLAN BASELINE CANDIDATE --output PRIVATE_DIR`. A `CANARY_REVIEW_REQUIRED` result creates `canary-90-10.yaml` and `rollback-baseline.yaml`. Any hold removes old route artifacts from that output directory. The comparison cannot prove billing savings or approve a change.
5. A named operator inspects the existing route and saves its exact YAML, confirms the Gateway API controller and namespace, then reviews the proposed full `HTTPRoute` before any apply. The generated rollback manifest directs 100% of traffic to baseline, but restoring the *saved original route* may be necessary if it had other rules or filters. Run a post-canary quality and SLO check on actual customer traffic before considering promotion. These operational actions are outside this release.

The comparator rejects different models, workload digests, request counts or concurrency. It holds on failures, insufficient samples, latency/TTFT regression against targets, quality regression or insufficient projected cost reduction. Its unit cost estimate is `hourly allocation cost / (successful requests per second × 3600)`. The percentage is a **short-run throughput projection**: it is not a billed saving, and it ignores demand variation unless the input hourly cost and utilization reflect that variation. Measure a full billing period before making a savings claim.

Gateway API defines weighted backends for traffic splitting; the weights in `HTTPRoute` are relative proportions, so 90 and 10 yield a 90/10 split. See the [official traffic-splitting guide](https://gateway-api.sigs.k8s.io/guides/user-guides/traffic-splitting/).
