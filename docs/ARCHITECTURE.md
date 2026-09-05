# Architecture

## Components

1. **Collectors** normalize cost, Kubernetes, GPU, inference, quality and business telemetry into one evidence contract.
2. **Forecasting** predicts near-term request demand and publishes backtest error.
3. **Economics** measures cost per successful outcome, throughput per dollar, revenue and contribution margin.
4. **Policy gates** reject candidates violating latency, quality, availability or residency constraints.
5. **Optimizer** ranks admissible candidates by projected hourly margin.
6. **Proposal writer** emits reviewable GitOps/Infrastructure-as-Code artifacts in shadow mode.
7. **Canary evaluator** is planned to compare projected and realized economics before promotion or rollback.

## Trust boundaries

The evaluator needs evidence, not cloud credentials. Live collection should use separate read-only identities. A future executor must be isolated behind approval, policy and rollback controls. Business revenue inputs are commercially sensitive and should remain inside the customer's telemetry boundary.

## Decision semantics

Demand is capped by each candidate's declared capacity. Successful throughput is served demand multiplied by observed success rate. Revenue is successful throughput multiplied by value per successful outcome. Contribution margin is modeled revenue minus infrastructure/model cost; it is not accounting gross profit unless all relevant costs are included.

Policy failures apply a hard exclusion rather than a soft financial penalty. This prevents an inexpensive but unqualified provider from winning the optimization.

## Data sources planned for production

- Kubernetes Metrics API and kube-state-metrics
- Prometheus and NVIDIA DCGM Exporter
- OpenCost allocation API
- OpenTelemetry GenAI traces and application outcome events
- Azure Cost Management exports and Retail Prices API
- AKS node-pool, KEDA/HPA and Azure Monitor signals
- NVIDIA NIM, Triton and vLLM serving metrics
- Git, Terraform/OpenTofu and Helm deployment state
