"""Run only a digest-pinned source file and exact approved mutation templates."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from .oracle import HarnessError, parse_trace

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "7909d6ddf46e5631a0a6c586c47ab994d7b57132"
BASELINE_SHA256 = "d2063b08f0f7e4108642acded4d90434095b7bc3d4e773ddc06e817f83226513"
TIMEOUT_SECONDS = 2
MAX_STDOUT_BYTES = 32768
MUTATIONS = {
    "gap-keeps-ready": ('return self.halt("GAP")', 'return self.status("GAP")'),
    "bypass-not-ready": ('if not self.ready:', 'if False:  # controlled seeded fault'),
    "accept-regressing-snapshot": ('if sequence < self.sequence:', 'if False:  # controlled seeded fault'),
}
VARIANTS = ("original", *MUTATIONS)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_bytes(variant="original"):
    raw = (ROOT / "vendor" / "book_replay.py").read_bytes()
    if digest(raw) != BASELINE_SHA256:
        raise HarnessError("pinned target digest mismatch")
    if variant == "original":
        return raw
    if variant not in MUTATIONS:
        raise HarnessError("unapproved target variant")
    old, new = MUTATIONS[variant]
    source = raw.decode("utf-8")
    if source.count(old) != 1:
        raise HarnessError("mutation anchor is not unique")
    return source.replace(old, new).encode("utf-8")


def execute(trace, variant="original", scratch=None):
    parse_trace(trace)
    source = source_bytes(variant)
    scratch = Path(scratch) if scratch else ROOT / ".build" / "workers"
    scratch.mkdir(parents=True, exist_ok=True)
    raw_input = ("\n".join(trace) + "\n").encode("ascii")
    with tempfile.TemporaryDirectory(prefix="replay-", dir=scratch) as directory:
        path = Path(directory) / "runner.py"
        path.write_bytes(source)
        start = time.perf_counter_ns()
        try:
            process = subprocess.run([sys.executable, "-I", "-B", str(path)],
                                     input=raw_input, capture_output=True, cwd=directory,
                                     timeout=TIMEOUT_SECONDS, check=False)
        except (subprocess.TimeoutExpired, OSError) as exc:
            raise HarnessError(type(exc).__name__) from exc
        elapsed = time.perf_counter_ns() - start
    if process.returncode != 0:
        raise HarnessError("target subprocess failed")
    if len(process.stdout) > MAX_STDOUT_BYTES or process.stderr:
        raise HarnessError("output cap exceeded or unexpected stderr")
    try:
        rows = process.stdout.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise HarnessError("non-ASCII target output") from exc
    return {"rows": rows, "target_sha256": digest(source), "input_sha256": digest(raw_input),
            "elapsed_ns": elapsed, "variant": variant, "timeout_seconds": TIMEOUT_SECONDS}
