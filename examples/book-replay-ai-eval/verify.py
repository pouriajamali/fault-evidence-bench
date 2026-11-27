"""Verify saved artifacts and rerun the first witness of each new AI scenario."""
import json
from pathlib import Path
import sys

from evaluate import ROOT
from faultbench.evidence import replay_record, validate_record
from faultbench.experiment import BUDGET, SEEDS, proposals
from faultbench.oracle import expected_states
from faultbench.target import VARIANTS, digest

output = Path(sys.argv[1])
comparison = json.loads((output / "comparison.json").read_text(encoding="utf-8"))
reference = json.loads((ROOT / "observed/comparison.json").read_text(encoding="utf-8"))
for field in ("extraFailureSignatures", "extraScenarioPairs"):
    assert comparison[field] == reference[field], field
metrics = (
    "submitted", "executions", "invalid", "outcomes", "unique_inputs", "event_records",
    "original_runs", "original_mismatches", "seeded_variants_detected",
    "failure_identities", "adjacent_pair_witnesses", "target_commit", "input_file_sha256",
)
assert comparison["arms"].keys() == reference["arms"].keys()
for name, arm in comparison["arms"].items():
    for metric in metrics:
        assert arm[metric] == reference["arms"][name][metric], (name, metric)
print("PASS deterministic metrics match the recorded comparison")
proposal_bytes = (ROOT / "ai-proposals.json").read_bytes()
ai = json.loads(proposal_bytes)
checked = 0
for arm, summary in comparison["arms"].items():
    assert summary["input_file_sha256"] == digest(proposal_bytes)
    expected = {}
    for seed in SEEDS:
        candidates = ai[str(seed)] if arm == "ai" else proposals(arm, seed, BUDGET)
        for i, trace in enumerate(candidates):
            for variant in VARIANTS:
                expected[f"{arm}-{seed}-{i:02}-{variant}.json"] = (seed, i, variant, trace)
    actual = {p.name for p in (output / arm).glob("*.json")} - {"arm.json"}
    assert actual == expected.keys()
    for file, (seed, index, variant, trace) in expected.items():
        result = validate_record(json.loads((output / arm / file).read_text(encoding="utf-8")))
        assert result["trace"] == trace and result["target"]["variant"] == variant
        assert result["metadata"] == {"arm": arm, "seed": seed, "candidate": index, "candidate_budget": BUDGET}
        checked += 1
print(f"PASS artifact inventory, source hashes and candidate binding: {checked}")

for pair in comparison["extraScenarioPairs"]:
    seed, index = comparison["arms"]["ai"]["adjacent_pair_witnesses"][pair]
    states = expected_states(ai[str(seed)][index])
    assert pair in {f"{a.reason} -> {b.reason}" for a, b in zip(states, states[1:])}
    statuses = {}
    for variant in VARIANTS:
        file = output / "ai" / f"ai-{seed}-{index:02}-{variant}.json"
        case = json.loads(file.read_text(encoding="utf-8"))
        assert replay_record(case)["status"] == "REPRODUCED"
        statuses[variant] = case["outcome"]
    print(f"PASS {pair}: {seed}/{index:02} replayed on all {len(VARIANTS)} targets; {statuses}")
