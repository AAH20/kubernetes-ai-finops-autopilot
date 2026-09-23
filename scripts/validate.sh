#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m ai_finops.cli examples/retail-inference.json --output "${TMPDIR:-/tmp}/ai-finops-validation"
PYTHONPATH=src python3 -m ai_finops.cli examples/no-admissible-candidate.json --output "${TMPDIR:-/tmp}/ai-finops-no-candidate" --fail-on-policy && exit 1 || test $? -eq 2
PYTHONPATH=src python3 -m ai_finops.live_compare_cli examples/live-compare/plan.synthetic.json examples/live-compare/baseline.synthetic.json examples/live-compare/candidate.synthetic.json --output "${TMPDIR:-/tmp}/ai-finops-live-comparison"

python3 -m json.tool "${TMPDIR:-/tmp}/ai-finops-validation/decision.json" >/dev/null
grep -q "mode: shadow" "${TMPDIR:-/tmp}/ai-finops-validation/gitops-proposal/values.generated.yaml"
grep -q "review before terraform plan/apply" "${TMPDIR:-/tmp}/ai-finops-validation/gitops-proposal/main.tf"
grep -q '"status": "HOLD"' "${TMPDIR:-/tmp}/ai-finops-live-comparison/comparison.json"
test ! -e "${TMPDIR:-/tmp}/ai-finops-live-comparison/canary-90-10.yaml"
