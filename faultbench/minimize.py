"""Bounded deletion minimization preserving one exact target/predicate identity."""
import json
from pathlib import Path
import time

from .evidence import make_record, replay_record, validate_record

ALGORITHM = "greedy-delete/1"
MAX_ATTEMPTS = 256


def minimize(record, predicate, max_attempts=MAX_ATTEMPTS):
    validate_record(record)
    if record["outcome"] != "ORACLE_MISMATCH":
        raise ValueError("only a replayable oracle mismatch can be minimized")
    selected = [i for i in record["failure_identities"] if i.endswith(":" + predicate)]
    if len(selected) != 1:
        raise ValueError("select one existing exact failure predicate")
    identity = selected[0]
    if type(max_attempts) is not int or not 1 <= max_attempts <= MAX_ATTEMPTS:
        raise ValueError("minimization attempt budget must be 1..256")
    if not replay_record(record)["replayable_failure"]:
        raise ValueError("parent failure did not reproduce")
    variant = record["target"]["variant"]
    trace, attempts, target_ns = record["trace"][:], 0, 0
    start = time.perf_counter_ns()
    state = "BUDGET_EXHAUSTED"
    while attempts < max_attempts:
        removed = False
        for index in range(len(trace)):
            # Empty input is outside the registered oracle domain.
            candidate = trace[:index] + trace[index + 1:]
            if not candidate:
                continue
            if attempts >= max_attempts:
                break
            attempts += 1
            trial = make_record(candidate, variant)
            target_ns += trial["runner_elapsed_ns"] or 0
            if trial["outcome"] == "ORACLE_MISMATCH" and identity in trial["failure_identities"]:
                trace, removed = candidate, True
                break
        else:
            if not removed:
                state = "ONE_MINIMAL_UNDER_SINGLE_RECORD_DELETION"
                break
        if not removed and attempts < max_attempts:
            state = "ONE_MINIMAL_UNDER_SINGLE_RECORD_DELETION"
            break
    metadata = {
        "lineage": {"parent_artifact_sha256": record["artifact_sha256"],
                    "parent_input_sha256": record["input_sha256"],
                    "selected_failure_identity": identity},
        "minimization": {"algorithm": ALGORITHM, "status": state, "attempt_budget": max_attempts,
                         "attempts": attempts, "before_records": len(record["trace"]),
                         "after_records": len(trace), "search_target_elapsed_ns": target_ns,
                         "search_wall_ns": time.perf_counter_ns() - start,
                         "equivalence": "Same target source digest and oracle predicate; not proof of same root cause or globally shortest input."},
    }
    child = make_record(trace, variant, metadata)
    if child["outcome"] != "ORACLE_MISMATCH" or identity not in child["failure_identities"]:
        raise ValueError("final minimized witness lost selected predicate")
    return child


def catalog(records):
    """Deduplicate by conservative property identity, never raw trace count."""
    groups = {}
    for record in records:
        validate_record(record)
        if record["outcome"] != "ORACLE_MISMATCH":
            continue
        for identity in record["failure_identities"]:
            groups.setdefault(identity, set()).add(record["artifact_sha256"])
    return {"schema": "fault-evidence/predicate-catalog/1",
            "identity_count": len(groups),
            "groups": {k: sorted(v) for k, v in sorted(groups.items())},
            "limit": "Property violations per seeded target, not deduplicated real-world bugs/root causes."}


def catalog_directory(directory):
    records = []
    for path in sorted(Path(directory).glob("*.json")):
        if path.name == "summary.json":
            continue
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return catalog(records)
