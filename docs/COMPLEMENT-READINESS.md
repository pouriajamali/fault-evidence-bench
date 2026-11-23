# Complement consumer boundaries

These are shared inputs owned by their source projects, not extra services or
new implementations within this benchmark. They remain part of the full
roadmap; no one-to-one reassignment or automatic protocol coverage is implied.

## CMP-01 and CMP-03, owned by Settlement Trace Explorer

The public owner contract and synthetic cases were inspected at
[`6cba2ce35c2b496113684ff39603313923bb39aa`](https://github.com/pouriajamali/settlement-trace-explorer/tree/6cba2ce35c2b496113684ff39603313923bb39aa).
[Contract v1](https://github.com/pouriajamali/settlement-trace-explorer/blob/6cba2ce35c2b496113684ff39603313923bb39aa/docs/contract-v1.md)
uses `traceVersion=1.0`, `profile=lifi-status-observation-v1`.
The corpus blob is `0ed575335dc12606019733f4052543f98ad746b0` (49 cases).
Nine relevant fixture bodies were examined: six freshness declarations,
unknown route enum, not-found and timeout without observation.

Preserve native fields, observation time, asset/decimals and unknown values.
Freshness is a **declaration** in this profile; it does not verify reorgs,
native finality or a second endpoint. `onChainTruth=notVerified`,
`ledger=notIntegrated`, `resend=notAuthorized` remain explicit.
One LI.FI observation profile is not an implementation of
CCTP/CCIP/IBC/LayerZero/Wormhole/Hyperlane.

The currently qualified G4 target is a synthetic book recovery runner.
Network JSON observations are outside its oracle domain. They have not been
silently converted into book events, executed as code or called passing
network-target integration. A future network target needs an independent
predicate and adapter qualification using the exact owner version.

## CMP-04, owned by Point-in-Time Reference Lab

The inspected owner P0 record describes a draft evaluation recipe/manifest
extension and explicitly says no implemented/published manifest schema
version is present. An existing release-source inventory is not a dataset
evaluation recipe with cutoff/revision, input/code/config/output bindings.
The G4 `failure-artifact/1` envelope is not relabelled a CMP-04 implementation.

The P3 owner-consumption gate remains **BLOCKED** until an owner-published,
versioned evaluation manifest and valid/invalid fixtures can be pinned and
checked. The minimum is an explicit recipe, source/license statement, schema,
revision/cutoff and publication/observation distinction; input/code/config
digests; environment/seed/tolerance and mismatch/incomplete-artifact handling.
No live G1 service is required. Native source fields and unknowns must survive
consumer round-trip checks. This blocks phase completion, not the independently
verified book-runner replay or predicate-preserving minimizer.

## Full complement phase gates retained

| Phase | CMP-01 | CMP-03 | CMP-04 |
| --- | --- | --- | --- |
| P0 | Native profile, units, truth/observation and finality/expiry | Route/version/trust and native stages | Recipe/cutoff/revision and publication versus observation |
| P1 | Valid/missing/lagged/expired/unknown expected fixtures | Native/unknown state expected fixtures | Input/code/config changes with independent expected mismatch |
| P2 | Payload/time-preserving offline recorder/replay | First adapter, evidence-bound claims | Reproduce output or explicit mismatch reason |
| P3 | Endpoint observation-time/height comparison contract | Independent second profile; qualified G4/G6 consumption | G4/G5 validate owner version/digests without live service |
| P4 | Costed AI triage versus rule, false alarms/misses | Valid new scenarios versus fixed method at equal budget | Fixed temporal split/budget; no post-hoc test selection |
| P5 | Known reorg/stale/rate-limit/no-response cases | Delayed/duplicate/timeout/proof/finality/retry | Environment/seed/tolerance/incomplete-artifact boundaries |
| P6 | Demand-led versioned profiles and compatibility | SDK migration/regression preserving trust config | Licensed recipe/dataset executed by an independent user |

This table retains acceptance requirements; it is not an execution-status
claim for either owner. Paid/live/financial operations are unnecessary for
these offline contract gates.
