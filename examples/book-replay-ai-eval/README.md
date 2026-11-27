# Book Replay: fixed, random and AI-generated test sequences

This source example reproduces the comparison behind the
[Book Recovery demo](https://pouriajamali.site/playground/book-recovery/).
One test sequence is a short history of events. Each input method supplied
72 sequences. We ran each sequence on the same original Book Replay runner
and three controlled variants, for 288 executions per method.

| Input method | Executions | Runs with a detected mismatch | Distinct failure signatures | Distinct adjacent recovery outcomes |
| --- | ---: | ---: | ---: | ---: |
| Fixed cases | 288 | 87 | 11 | 10 |
| Seeded random | 288 | 90 | 12 | 32 |
| AI-generated | 288 | 108 | 12 | 34 |

Random and AI input found the same 12 variant-and-rule combinations. The AI
input exercised two additional adjacent outcomes: a gap followed by an older
snapshot, and an older snapshot rejected immediately before a valid one.
All three groups hit all three controlled variants, and none disagreed with
the reference on the original runner within this corpus.

View the [exact comparison](observed/comparison.json),
[verified witness replays](observed/verification.txt), and
[recorded original and deliberately faulty outputs](observed/witnesses).

## Reproduce the recorded batch

Use Git, Python 3.12 and .NET SDK 11.0.100. Windows was tested with Python
3.12.10 and .NET runtime 11.0.0. Use a full Git clone so the pinned evaluator
commit is available for byte-exact extraction. The run requires no package
feeds or AI account. The recorded AI inputs are checked in.

```powershell
git clone https://github.com/pouriajamali/fault-evidence-bench.git
cd fault-evidence-bench/examples/book-replay-ai-eval
python -B prepare_snapshot.py
dotnet restore --configfile NuGet.Config
dotnet build --no-restore -c Release
dotnet bin/Release/net11.0/ReplayEval.dll (Get-Command python).Source local-results
python -B verify.py local-results
```

On a POSIX shell substitute `python3` for `python` and pass
`"$(command -v python3)"` as the coordinator’s interpreter argument. Use a new
results directory for each run. The coordinator writes each of the 864 replay
records and a comparison JSON. Verification checks their input and source
bindings, matches deterministic metrics against the recorded comparison and
reruns both additional scenarios on all four target versions. Timing is
machine-specific.

For a quicker replay of the article’s example, run these after preparing the
snapshot:

```sh
python -B vendor_snapshot/bench.py replay observed/witnesses/ai-17-16-original.json
python -B vendor_snapshot/bench.py replay observed/witnesses/ai-17-16-accept-regressing-snapshot.json
```

## Scope

[Program.cs](Program.cs) uses .NET 11’s process helper and a C# 15 closed
hierarchy to represent completed reports, infrastructure failures and timeouts.
[evaluate.py](evaluate.py) calls the unchanged reference and runner from
[the pinned evaluator commit](https://github.com/pouriajamali/fault-evidence-bench/tree/7cb52e3c531b68174ddd09720b50a63764f0a685).
The model generated data in a bounded grammar. The same evaluator scores all
three methods. See the [frozen protocol](PROTOCOL.md) and
[recorded input](ai-proposals.json).

This is an exploratory, contextual Codex batch. Target-execution budgets and
per-input caps were equal. Generation cost and independently identified model
version were unavailable. The results describe these deliberate variants and
this reference, without making a claim about unseen faults or the repository’s
separate formal AI evaluation gate. Upstream MIT notices are recovered with the
original source.
