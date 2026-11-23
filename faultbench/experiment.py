"""Matched-opportunity fixed/random baseline, with descriptive seeded outcomes."""
import json
from pathlib import Path
import random
import time

from .evidence import canonical, make_record, replay_record, write_record
from .target import ROOT, VARIANTS, digest

SEEDS = (17, 43, 101)
BUDGET = 24


def controls():
    return json.loads((ROOT / "corpus/controls.json").read_text(encoding="utf-8"))


def proposals(arm, seed, budget=BUDGET):
    if arm == "fixed":
        corpus = controls()
        return [corpus[i % len(corpus)]["trace"][:] for i in range(budget)]
    if arm != "random":
        raise ValueError("only fixed and random arms are implemented; no simulated AI arm")
    rng = random.Random(seed)
    result = []
    for _ in range(budget):
        sequence = rng.randint(2, 20)
        trace = [f"S {sequence} 100 5 200 5"]
        for _ in range(rng.randint(2, 11)):
            operation = rng.choice(("U", "U", "U", "S", "D"))
            sequence = max(1, min(1000, sequence + rng.choice((-2, -1, 0, 1, 2))))
            trace.append("D" if operation == "D" else
                         f"S {sequence} 100 5 200 5" if operation == "S" else
                         f"U {sequence} B {rng.randint(90, 110)} {rng.randint(1, 9)}")
        result.append(trace)
    return result


def compare(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    arms = {}
    start = time.perf_counter_ns()
    for arm in ("fixed", "random"):
        seen, counts = set(), {}
        logging_ns = oracle_ns = target_ns = generation_ns = 0
        original_mismatches = original_runs = runs = 0
        for seed in SEEDS:
            generation_start = time.perf_counter_ns()
            candidates = proposals(arm, seed, BUDGET)
            generation_ns += time.perf_counter_ns() - generation_start
            for index, trace in enumerate(candidates):
                for variant in VARIANTS:
                    record = make_record(trace, variant, {"arm": arm, "seed": seed, "candidate": index,
                                                         "candidate_budget": BUDGET})
                    logging_start = time.perf_counter_ns()
                    write_record(output / f"{arm}-{seed}-{index:02}-{variant}.json", record)
                    logging_ns += time.perf_counter_ns() - logging_start
                    counts[record["outcome"]] = counts.get(record["outcome"], 0) + 1
                    seen.update(record["failure_identities"])
                    target_ns += record["runner_elapsed_ns"] or 0
                    oracle_ns += record["oracle_elapsed_ns"] or 0
                    original_runs += variant == "original"
                    original_mismatches += variant == "original" and bool(record["violations"])
                    runs += 1
        arms[arm] = {"submitted_candidates": len(SEEDS) * BUDGET,
                     "target_executions": runs, "outcomes": counts,
                     "unique_target_predicate_identities": sorted(seen),
                     "original_target_mismatches": original_mismatches,
                     "original_target_runs": original_runs, "target_elapsed_ns": target_ns,
                     "oracle_elapsed_ns": oracle_ns, "generation_elapsed_ns": generation_ns,
                     "artifact_write_elapsed_ns": logging_ns}
    summary = {"schema": "fault-evidence/baseline-summary/1", "seeds": list(SEEDS),
               "candidate_budget_per_seed": BUDGET, "variants": list(VARIANTS), "arms": arms,
               "corpus_sha256": digest((ROOT / "corpus/controls.json").read_bytes()),
               "generator_source_sha256": digest(Path(__file__).read_bytes()),
               "total_wall_ns": time.perf_counter_ns() - start,
               "ai_arm": "NOT_RUN", "ai_tokens": None, "ai_cost": None,
               "claim_scope": "Descriptive artificial-fault sensitivity only; opportunities/caps matched, actual times reported. Duplicate predicates are deduplicated per target variant, not counted as distinct upstream bugs. No statistical or AI-advantage claim. Fixed arm intentionally repeats five known controls; samples are not independent.",
               "replay_validation": "Separate verify-run command; verification is outside search opportunity budget."}
    with (output / "summary.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(summary, stream, indent=2)
        stream.write("\n")
    return summary


def verify_run(directory):
    directory = Path(directory)
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    files = sorted(p for p in directory.glob("*.json") if p.name != "summary.json")
    required = {f"{arm}-{seed}-{i:02}-{v}.json": (arm, seed, i, v)
                for arm in ("fixed", "random") for seed in SEEDS for i in range(BUDGET) for v in VARIANTS}
    if {p.name for p in files} != set(required):
        raise ValueError("run artifact inventory is incomplete or has unexpected files")
    if (summary["schema"] != "fault-evidence/baseline-summary/1" or summary["seeds"] != list(SEEDS)
            or summary["candidate_budget_per_seed"] != BUDGET or summary["variants"] != list(VARIANTS)
            or summary["corpus_sha256"] != digest((ROOT / "corpus/controls.json").read_bytes())
            or summary["generator_source_sha256"] != digest(Path(__file__).read_bytes())):
        raise ValueError("comparison source/config drift")
    counts = {arm: {"checked": 0, "failures": 0, "reproduced_failures": 0, "consistent": 0}
              for arm in ("fixed", "random")}
    identities = {arm: set() for arm in counts}
    outcomes = {arm: {} for arm in counts}
    for path in files:
        record = json.loads(path.read_text(encoding="utf-8"))
        arm, seed, index, variant = required[path.name]
        if (record["metadata"] != {"arm": arm, "seed": seed, "candidate": index, "candidate_budget": BUDGET}
                or record["target"]["variant"] != variant
                or record["trace"] != proposals(arm, seed, BUDGET)[index]):
            raise ValueError("artifact seed/candidate/variant binding mismatch")
        result = replay_record(record)
        counts[arm]["checked"] += 1
        counts[arm]["failures"] += record["outcome"] == "ORACLE_MISMATCH"
        counts[arm]["consistent"] += result["status"] == "REPRODUCED"
        counts[arm]["reproduced_failures"] += result["replayable_failure"]
        identities[arm].update(record["failure_identities"])
        outcome = record["outcome"]
        outcomes[arm][outcome] = outcomes[arm].get(outcome, 0) + 1
    for arm in counts:
        if (summary["arms"][arm]["outcomes"] != outcomes[arm]
                or summary["arms"][arm]["unique_target_predicate_identities"] != sorted(identities[arm])):
            raise ValueError("summary does not match sealed artifacts")
    passed = all(c["consistent"] == c["checked"] and c["failures"] == c["reproduced_failures"]
                 for c in counts.values())
    return {"passed": passed, "arms": counts,
            "limit": "Fresh local replay by the same operator; not independent external reproduction or review."}
