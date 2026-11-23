# Public source reuse

`vendor/book_replay.py` and `vendor/upstream-fixtures.json` are exact bytes
from Pouria Jamali's public MIT `book-replay-lab` at commit
`7909d6ddf46e5631a0a6c586c47ab994d7b57132` (`book_replay.py` and `fixtures.json`).
The original notice is retained as `vendor/LICENSE.book-replay-lab`.

Runner SHA-256: `d2063b08f0f7e4108642acded4d90434095b7bc3d4e773ddc06e817f83226513`.
Seeded fault variants are exact, approved textual mutations of that public
runner in temporary worker directories. They are synthetic sensitivity tests,
not claims of existing upstream bugs. No private handoff or employer source is included.

The independent bounded oracle, controls and experiment harness are new work.
No upstream repository or historical benchmark output is modified.
