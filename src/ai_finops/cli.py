from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import analyze
from .render import write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate AI inference economics and produce a controlled GitOps proposal")
    parser.add_argument("bundle", help="Workload economics evidence JSON")
    parser.add_argument("--output", default="generated/ai-finops")
    parser.add_argument("--fail-on-policy", action="store_true")
    args = parser.parse_args()
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    report = analyze(bundle)
    paths = write_outputs(report, args.output)
    print(json.dumps({"status": report["status"], "recommendation": report.get("recommendation"), "outputs": {key: str(value) for key, value in paths.items()}}, indent=2))
    if report["status"] == "INCOMPLETE" or (args.fail_on_policy and report["status"] == "NO_ADMISSIBLE_CANDIDATE"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
