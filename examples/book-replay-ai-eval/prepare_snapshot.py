"""Recover the exact MIT evaluator bytes from this repository's history."""
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "vendor_snapshot"
REVISION = "7cb52e3c531b68174ddd09720b50a63764f0a685"
FILES = (
    "LICENSE", "THIRD_PARTY_NOTICES.md", "bench.py", "docs/EXPERIMENT.json",
    "faultbench/__init__.py", "faultbench/evidence.py", "faultbench/experiment.py",
    "faultbench/oracle.py", "faultbench/target.py", "corpus/controls.json",
    "vendor/LICENSE.book-replay-lab", "vendor/book_replay.py", "vendor/upstream-fixtures.json",
)

for name in FILES:
    data = subprocess.run(
        ["git", "cat-file", "blob", f"{REVISION}:{name}"], cwd=HERE,
        check=True, capture_output=True,
    ).stdout
    output = SNAPSHOT / name
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        if output.read_bytes() != data:
            raise SystemExit(f"Existing snapshot file differs: {name}")
    else:
        output.write_bytes(data)

print(f"Prepared {len(FILES)} original source and notice files at {REVISION}.")
