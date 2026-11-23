# Fault Evidence Bench

Measure replayable recovery failures on one pinned, synthetic stateful runner using an independent bounded oracle.

The public MIT Python runner from [book-replay-lab](https://github.com/pouriajamali/book-replay-lab/tree/7909d6ddf46e5631a0a6c586c47ab994d7b57132) is pinned by commit and SHA-256. Five handwritten control histories check a separate recovery-epoch oracle. Three controlled seeded faults have explicit witnesses; correct behaviours pass. No AI advantage, production security or new upstream bug is claimed.

The first failure family is recovery gating after gaps, disconnects and regressing snapshots. Fixed/random methods and any later AI arm must use the same oracle, seeds, execution opportunities and explicit generation costs. A negative AI result is valid. Unknown costs are not declared equal.

This repository contains public synthetic material only. It does not require an account, wallet, service, paid model or market data. Full phase gates and runnable documentation will accompany implementation.

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

P0 baseline/experiment definition and P1 bounded corpus/oracle are locally
verified. P2 replay artifacts and fixed/random comparison, P3 minimization and
owner-controlled CMP-01/03/04 integration, P4 cost-controlled AI evaluation,
P5 execution hardening and P6 independent reproduction remain subsequent
gates. A public source commit is not a tested release or independent use.

Temporary worker files stay under `.build/` in the checkout. The adapter runs
only the pinned source and three exact built-in mutations in fresh isolated
Python subprocesses. It does not execute proposal text. Process time/input/output
limits are not an OS security sandbox, memory quota or network firewall.
