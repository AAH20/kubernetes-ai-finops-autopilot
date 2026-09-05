from __future__ import annotations

import json
from pathlib import Path


def _report_markdown(report: dict) -> str:
    lines = ["# AI FinOps Decision Evidence", "", f"**Status:** `{report['status']}`", ""]
    if report.get("recommendation"):
        rec = report["recommendation"]
        lines.extend([
            "## Recommendation", "",
            f"- Selected candidate: `{rec['selected_candidate']}`",
            f"- Baseline: `{rec['baseline_candidate']}`",
            f"- Projected monthly margin delta: `${rec['projected_monthly_margin_delta']:,.2f}`",
            f"- Forecast peak: `{rec['forecast_peak_rph']:,.2f}` requests/hour",
            f"- Capacity headroom: `{rec['capacity_headroom_percent']}%`",
            f"- Rollout: {rec['rollout']}", "",
        ])
    lines.extend(["## Candidate scorecard", "", "| Candidate | Admissible | Hourly cost | Cost/success | P95 | Quality | Margin/hour |", "|---|---:|---:|---:|---:|---:|---:|"])
    for row in report.get("candidates", []):
        c, e = row["candidate"], row["economics"]
        lines.append(f"| {c['name']} | {row['policy']['admissible']} | ${c['hourly_cost']:.2f} | ${e['cost_per_success']:.4f} | {c['p95_latency_ms']:.0f} ms | {c['quality_score']:.3f} | ${e['hourly_margin']:.2f} |")
    lines.extend(["", "## Evidence", "", f"SHA-256: `{report['evidence_sha256']}`", "", "> Projection, not promised savings. Validate through a controlled canary before production rollout.", ""])
    return "\n".join(lines)


def _values_yaml(report: dict) -> str:
    selected = report["recommendation"]["selected_candidate"] if report.get("recommendation") else "REVIEW_REQUIRED"
    return f"""# Generated proposal: human approval required
aiFinops:
  selectedCandidate: {selected}
  mode: shadow
  canaryPercent: 10
  rollbackOnSloViolation: true
  evidenceSha256: {report['evidence_sha256']}
"""


def _terraform(report: dict) -> str:
    selected = report["recommendation"]["selected_candidate"] if report.get("recommendation") else "REVIEW_REQUIRED"
    return f'''# Generated proposal: review before terraform plan/apply
variable "selected_inference_profile" {{
  type    = string
  default = "{selected}"
}}

variable "deployment_mode" {{
  type    = string
  default = "shadow"
  validation {{
    condition     = contains(["shadow", "canary", "active"], var.deployment_mode)
    error_message = "Mode must be shadow, canary, or active."
  }}
}}

output "decision_evidence_sha256" {{
  value = "{report['evidence_sha256']}"
}}
'''


def write_outputs(report: dict, output: str | Path) -> dict[str, Path]:
    root = Path(output)
    proposal = root / "gitops-proposal"
    proposal.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "decision.json",
        "markdown": root / "decision.md",
        "helm_values": proposal / "values.generated.yaml",
        "terraform": proposal / "main.tf",
    }
    paths["json"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    paths["markdown"].write_text(_report_markdown(report), encoding="utf-8")
    paths["helm_values"].write_text(_values_yaml(report), encoding="utf-8")
    paths["terraform"].write_text(_terraform(report), encoding="utf-8")
    return paths
