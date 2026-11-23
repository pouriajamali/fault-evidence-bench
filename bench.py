"""Offline entry point; proposal text is data, never executable code."""
import argparse
import json
from pathlib import Path
import sys

from faultbench.evidence import make_record, replay_record, write_record
from faultbench.experiment import compare, controls, verify_run
from faultbench.minimize import catalog_directory, minimize
from faultbench.target import VARIANTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="five fixed histories against original and approved seeded variants")
    c = sub.add_parser("compare", help="full preregistered fixed/random baseline; no AI arm")
    c.add_argument("--out", type=Path, required=True, help="new directory; existing path is refused")
    r = sub.add_parser("replay", help="validate and replay one sealed artifact")
    r.add_argument("artifact", type=Path)
    v = sub.add_parser("verify-run", help="freshly replay every original and seeded result in a comparison")
    v.add_argument("directory", type=Path)
    m = sub.add_parser("minimize", help="preserve one exact failure predicate while deleting records")
    m.add_argument("artifact", type=Path)
    m.add_argument("--predicate", required=True)
    m.add_argument("--out", type=Path, required=True, help="new artifact file; parent directory must exist")
    d = sub.add_parser("catalog", help="deduplicate sealed failure records by target/predicate identity")
    d.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "demo":
        result = []
        for case in controls():
            for variant in VARIANTS:
                record = make_record(case["trace"], variant, {"control": case["id"]})
                result.append({"control": case["id"], "variant": variant, "outcome": record["outcome"],
                               "predicates": sorted({v["predicate"] for v in record["violations"]})})
        print(json.dumps({"scope": "seeded faults, not new upstream bugs or AI", "results": result}, indent=2))
        return 0 if all(r["outcome"] == "NO_ORACLE_MISMATCH" for r in result if r["variant"] == "original") else 1
    if args.command == "compare":
        result = compare(args.out)
    elif args.command == "replay":
        result = replay_record(json.loads(args.artifact.read_text(encoding="utf-8")))
    elif args.command == "minimize":
        child = minimize(json.loads(args.artifact.read_text(encoding="utf-8")), args.predicate)
        write_record(args.out, child)
        result = {"artifact_sha256": child["artifact_sha256"], "metadata": child["metadata"],
                  "replay": replay_record(child)}
    elif args.command == "catalog":
        result = catalog_directory(args.directory)
    else:
        result = verify_run(args.directory)
    print(json.dumps(result, indent=2))
    return 1 if result.get("passed") is False or result.get("status") in ("MISMATCH", "NOT_A_REPLAYABLE_RESULT") else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
