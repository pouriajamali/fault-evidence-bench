# Replay artifact contract, version 1

`fault-evidence/failure-artifact/1` binds a proposed trace to the exact public
runner commit and original/mutated source digest, oracle source digest/version,
adapter version, execution configuration and seed/candidate metadata. It stores
every runner output row, oracle violation, measured target/oracle duration and
the actual interpreter/platform. The input byte digest and canonical proposal
digest are separate: invalid proposals have no executed input bytes.

`artifact_sha256` hashes the canonical JSON object with that field omitted.
This detects accidental change. Anyone can recompute it; it is not a signature,
proof of execution, source authenticity, human review or a CMP-04 implementation.
Replay refuses unknown schema, target, oracle, adapter or configuration drift.
It executes the pinned variant again and compares actual rows and predicates,
excluding timing because timing is not deterministic.

Outcomes:

| Outcome | Meaning |
| --- | --- |
| NO_ORACLE_MISMATCH | No violation in this bounded oracle; not complete correctness |
| ORACLE_MISMATCH | Explicit expected/actual violation; seeded variants are artificial |
| INVALID_PROPOSAL | Outside the fixed grammar or byte/record limit; not a bug |
| HARNESS_ERROR | Crash, timeout, framing error or adapter failure; not a bug |

A failure identity is the target variant source digest, oracle predicate
version and violated clause. Multiple seeds, trace variants and repeated events
do not create additional identities. Several clauses can expose one seeded
mechanism, so predicate identity counts must not be described as distinct bugs.

The comparison report keeps search execution opportunity counts equal. Actual
generation, runner, oracle and logging durations are reported rather than
declared equal. Every submitted candidate consumes its opportunity even if
invalid or the harness fails. Reproduction runs are a separate validation
cost, not additional search opportunities. The verifier checks the exact file
inventory, seed/candidate/variant binding, regenerated candidate trace, outcome
counts and identity set against the sealed artifacts; missing/extra records fail.

The fixed corpus is five handwritten known controls, repeated to fill the
registered budget. Random generation is a deterministic bounded grammar and
does not adapt to target results. These are descriptive sensitivity checks on
three artificial mutations, with original-target controls as the explicit
false-positive denominator. They are not independent statistical samples or
competitor benchmarks. AI proposal metadata, generation cost and holdout
provenance are separate later gates; the baseline is never renamed an AI arm.

The worker executes a fixed argv with `shell=False` in a fresh directory under
the checkout's `.build/`, isolated Python mode and a two-second timeout. Only
the digest-pinned original or three built-in source substitutions can execute;
proposal strings pass a closed grammar. Input size and record count are checked
before execution. Output size is checked after capture: this is a correctness
boundary for trusted bounded targets, **not** a hard streaming-memory limit.
There is no OS-enforced filesystem/network sandbox or general untrusted-code
execution. Expanding that trust boundary requires new isolation qualification.
