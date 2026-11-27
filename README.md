# Fault Evidence Bench

Measure replayable recovery failures on one pinned, synthetic stateful runner using an independent bounded oracle.

The public MIT Python runner from [book-replay-lab](https://github.com/pouriajamali/book-replay-lab/tree/7909d6ddf46e5631a0a6c586c47ab994d7b57132) is pinned by commit and SHA-256. Five handwritten control histories check a separate recovery-epoch oracle. Three controlled seeded faults have explicit witnesses; correct behaviours pass. No AI advantage, production security or new upstream bug is claimed.

The first failure family is recovery gating after gaps, disconnects and regressing snapshots. Fixed/random methods and any later AI arm must use the same oracle, seeds, execution opportunities and explicit generation costs. A negative AI result is valid. Unknown costs are not declared equal.

This repository contains public synthetic material only. It does not require an account, wallet, service, paid model or market data. Full phase gates and runnable documentation will accompany implementation.

## Reproduce the exploratory AI comparison

The [Book Replay AI experiment](examples/book-replay-ai-eval/) contains the .NET
11 coordinator, all 72 recorded AI inputs, the measured comparison and replayable
witnesses used in the [public Book Recovery demo](https://pouriajamali.site/playground/book-recovery/).
It is a bounded replay of a contextual Codex batch with matched target execution
budgets. The repository’s formal AI evaluation gates remain as documented below.

## Run the qualified checks

From a full source checkout with Python 3.12 or later installed:

```sh
python -B -m unittest discover -s tests -v
python -B bench.py demo
```

There are no Python package dependencies. The checks include all 32 original
upstream fixture scenarios / 74 literal output states, five correct controls,
three explicit seeded-fault witnesses, malformed-output/timeout handling and
digest/domain checks. The observed local run used Python 3.13.1 on Windows;
this is not an endorsement of that old patch for deployment.

Run a complete fixed/random baseline and replay its sealed results:

```sh
python -B bench.py compare --out local-results/first-run
python -B bench.py verify-run local-results/first-run
python -B bench.py replay local-results/first-run/fixed-17-00-gap-keeps-ready.json
```

Choose a new output directory. Each arm receives 24 candidate traces for each
of seeds 17, 43 and 101. Each candidate runs against the original and three
seeded variants: 288 target executions per arm, followed by separate replay
validation. The fixed corpus intentionally repeats five known controls.
Generation, target, oracle and artifact-write durations are recorded separately;
actual wall time varies by machine. This command has **no AI arm**. No model
cost, public-vulnerability count or statistical superiority is inferred.

Review [the frozen experiment contract](docs/EXPERIMENT.json),
[the oracle](faultbench/oracle.py), [controlled adapter](faultbench/target.py)
and [source attribution](THIRD_PARTY_NOTICES.md). [Artifact fields and boundaries](docs/ARTIFACTS.md)
explain source/config drift, replay and the difference between digests and trust.

The oracle covers at most 32 records of a deliberately narrow grammar:
`D`, `S <sequence> 100 5 200 5`, or positive bid updates
`U <sequence> B <price 90..110> <quantity 1..9>`, sequence 1..1000.
It checks recovery reason, readiness and accepted sequence, plus a relational
check that rejection retains visible levels. It does not implement a second
price book or establish correctness outside this grammar. Crashes, timeouts,
framing errors and invalid proposals are separate harness outcomes, not bugs.

## Development gates

P0 baseline/experiment definition, P1 bounded corpus/oracle and P2 replay
artifacts/fixed-random baseline are verified within their stated scope.
P2 source [`7cb52e3`](https://github.com/pouriajamali/fault-evidence-bench/commit/7cb52e3c531b68174ddd09720b50a63764f0a685)
passed [Windows/Linux CI](https://github.com/pouriajamali/fault-evidence-bench/actions/runs/45191646776).
[Recorded results](evidence/P2-results.json) include code digests and the checksum
of [all 576 raw artifacts and replay evidence](evidence/p2-baseline.zip).
Each arm had 72 original-target controls with zero oracle mismatches;
87 fixed-arm and 90 random-arm seeded failures all replayed. These counts are
artificial-fault observations, not distinct bugs or evidence of AI superiority.
P3 minimization and
owner-controlled CMP-01/03/04 integration, P4 cost-controlled AI evaluation,
P5 execution hardening and P6 independent reproduction remain subsequent
gates. A public source commit is not a tested release or independent use.

Temporary worker files stay under `.build/` in the checkout. The adapter runs
only the pinned source and three exact built-in mutations in fresh isolated
Python subprocesses. It does not execute proposal text. Process time/input/output
limits are not an OS security sandbox, memory quota or network firewall.

## Minimize the same failure

```sh
python -B bench.py minimize local-results/first-run/fixed-17-00-gap-keeps-ready.json --predicate readiness-mismatch --out local-results/minimized.json
python -B bench.py replay local-results/minimized.json
python -B bench.py catalog local-results/first-run
```

The minimizer retains the exact target digest and selected oracle predicate,
records the parent artifact/input digests and bounds deletion attempts at 256.
`ONE_MINIMAL_UNDER_SINGLE_RECORD_DELETION` means no one-record deletion preserves
that predicate within the qualified domain. It is not a globally shortest input
or proof of identical root cause. Budget exhaustion is reported explicitly.
[A recorded 3-to-2-record witness](evidence/P3-minimized.json) replays against
the same seeded variant; the parent is in the P2 raw evidence archive.

The minimizer/deduplication core is tested. **The full P3 phase is blocked on
owner-controlled complement consumption**, especially the unpublished CMP-04
evaluation-manifest version/fixtures. [Read the exact boundaries and retained
phase gates](docs/COMPLEMENT-READINESS.md). P4/P5/P6 remain subsequent work;
this source preview is not described as a completed AI benchmark or release.

[Full P0–P6 status and remaining qualification gates](docs/ROADMAP.md).
Developed with AI assistance; the separate oracle is not an external audit or
a measured experimental AI arm.
