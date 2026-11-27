"""Score one arm with the unchanged public runner and reference rules."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "vendor_snapshot"))
from faultbench.evidence import make_record, write_record
from faultbench.experiment import BUDGET, SEEDS, proposals
from faultbench.oracle import DomainError, expected_states
from faultbench.target import BASELINE_COMMIT, VARIANTS, digest

PINNED = {
    "bench.py": "4364b7f3c04bce281e7f9b6e4f059bccceac7270d2e37d5b8531c691bb4f72b1",
    "faultbench/__init__.py": "202ac0f9259834d13a783f97e434b797b93d1c2c64b6ed47600ccc8d7f9c1c34",
    "faultbench/oracle.py": "c98fafc51ac483f9881313a395c6ef0b88bbf622649e59a9ac9e47093a3fbb70",
    "faultbench/target.py": "f99d9340fd66d4d6e9f4a8d5c5ee999d74d505897e4dd4dd9fd46fb87c80f985",
    "faultbench/evidence.py": "04186bb12a150b2f6e6b8c1b232272d0b61cf5c899a191ae3cc6e5ce4e97bdaa",
    "faultbench/experiment.py": "98a5bab231301103b7c933e0781d346d12937ec9ce02545417e8e59b499fa5af",
    "corpus/controls.json": "702f0a120c6080a2d014a5f3d1d7b34e0d8388279d52f1536fa4df187d6a785f",
    "vendor/book_replay.py": "d2063b08f0f7e4108642acded4d90434095b7bc3d4e773ddc06e817f83226513",
}


def evaluate(arm, output):
    for name, expected in PINNED.items():
        observed = digest((ROOT / "vendor_snapshot" / name).read_bytes())
        if observed != expected:
            raise ValueError(f"source digest mismatch: {name} ({observed})")

    source = (ROOT / "ai-proposals.json").read_bytes()
    if len(source) > 16_384:
        raise ValueError("AI candidate file exceeds 16 KiB")
    ai = json.loads(source)
    if set(ai) != set(map(str, SEEDS)) or any(len(group) != BUDGET for group in ai.values()):
        raise ValueError("AI slots do not match the frozen budget")

    output.mkdir(parents=True, exist_ok=False)
    counts = Counter()
    signatures = set()
    exercised_pairs = {}
    bad_variants = set()
    unique_inputs = set()
    original_mismatches = invalid = original_runs = runs = event_records = target_ns = 0
    started = perf_counter_ns()
    for seed in SEEDS:
        candidates = ai[str(seed)] if arm == "ai" else proposals(arm, seed, BUDGET)
        for index, trace in enumerate(candidates):
            try:
                states = expected_states(trace)
            except DomainError:
                invalid += 1
                continue
            event_records += len(trace)
            unique_inputs.add(tuple(trace))
            for left, right in zip(states, states[1:]):
                exercised_pairs.setdefault(f"{left.reason} -> {right.reason}", [seed, index])
            for variant in VARIANTS:
                case = make_record(trace, variant, {"arm": arm, "seed": seed, "candidate": index, "candidate_budget": BUDGET})
                write_record(output / f"{arm}-{seed}-{index:02}-{variant}.json", case)
                counts[case["outcome"]] += 1
                signatures.update(case["failure_identities"])
                runs += 1
                target_ns += case["runner_elapsed_ns"] or 0
                if variant == "original":
                    original_runs += 1
                    original_mismatches += bool(case["violations"])
                elif case["violations"]:
                    bad_variants.add(variant)
    summary = {
        "schema": "local-book-replay-arm/1",
        "arm": arm,
        "submitted": BUDGET * len(SEEDS),
        "executions": runs,
        "invalid": invalid,
        "outcomes": dict(counts),
        "unique_inputs": len(unique_inputs),
        "event_records": event_records,
        "original_runs": original_runs,
        "original_mismatches": original_mismatches,
        "seeded_variants_detected": sorted(bad_variants),
        "failure_identities": sorted(signatures),
        "adjacent_pair_witnesses": dict(sorted(exercised_pairs.items())),
        "target_commit": BASELINE_COMMIT,
        "input_file_sha256": digest(source),
        "target_ns": target_ns,
        "wall_ns": perf_counter_ns() - started,
        "python": sys.version,
    }
    with (output / "arm.json").open("x", encoding="utf-8") as output_file:
        json.dump(summary, output_file, indent=2, ensure_ascii=True)
    print(json.dumps(summary, ensure_ascii=True, separators=(",", ":")))


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("arm", choices=("fixed", "random", "ai"))
    args.add_argument("output", type=Path)
    settings = args.parse_args()
    evaluate(settings.arm, settings.output)
