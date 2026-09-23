import argparse
import json
from pathlib import Path

from .live_compare import CompareError, compare, write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare measured inference configurations")
    parser.add_argument("plan", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text())
        report = compare(plan, json.loads(args.baseline.read_text()),
                         json.loads(args.candidate.read_text()))
        write_outputs(plan, report, args.output)
    except (OSError, json.JSONDecodeError, CompareError) as exc:
        parser.error(str(exc))
    print(json.dumps({"status": report["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
