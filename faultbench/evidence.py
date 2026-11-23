"""Versioned replay records. Digests detect drift, not authenticity or authorship."""
import json
from pathlib import Path
import platform
import sys
import time

from . import VERSION
from .oracle import DomainError, HarnessError, ORACLE_VERSION, judge
from .target import BASELINE_COMMIT, ROOT, digest, execute, source_bytes

SCHEMA = "fault-evidence/failure-artifact/1"
CONFIG = {"max_records": 32, "max_input_bytes": 4096, "timeout_seconds": 2,
          "max_stdout_bytes": 32768, "execution": "pinned-source-and-approved-templates-only"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def oracle_digest():
    return digest((ROOT / "faultbench/oracle.py").read_bytes())


def identities(record):
    return sorted({record["target"]["source_sha256"] + ":" + ORACLE_VERSION + ":" + f["predicate"]
                   for f in record["violations"]})


def make_record(trace, variant="original", metadata=None):
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")
    record = {
        "schema": SCHEMA, "adapter_version": VERSION,
        "target": {"repository": "https://github.com/pouriajamali/book-replay-lab",
                   "commit": BASELINE_COMMIT, "variant": variant,
                   "source_sha256": digest(source_bytes(variant)), "license": "MIT",
                   "seeded_fault": variant != "original"},
        "oracle": {"version": ORACLE_VERSION, "source_sha256": oracle_digest()},
        "config": CONFIG.copy(), "config_sha256": digest(canonical(CONFIG)),
        "trace": trace, "proposal_sha256": digest(canonical(trace)),
        "metadata": metadata or {},
        "environment": {"python": sys.version, "platform": platform.platform()},
        "violations": [], "rows": [], "runner_elapsed_ns": None,
        "oracle_elapsed_ns": None,
    }
    try:
        execution = execute(trace, variant)
        record["rows"] = execution["rows"]
        record["runner_elapsed_ns"] = execution["elapsed_ns"]
        record["input_sha256"] = execution["input_sha256"]
        start = time.perf_counter_ns()
        record["violations"] = judge(trace, execution["rows"])
        record["oracle_elapsed_ns"] = time.perf_counter_ns() - start
        record["outcome"] = "ORACLE_MISMATCH" if record["violations"] else "NO_ORACLE_MISMATCH"
    except DomainError as exc:
        record["outcome"], record["error"] = "INVALID_PROPOSAL", str(exc)
    except HarnessError as exc:
        record["outcome"], record["error"] = "HARNESS_ERROR", str(exc)
    record["failure_identities"] = identities(record)
    record["artifact_sha256"] = digest(canonical(record))
    return record


def write_record(path, record):
    path = Path(path)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, indent=2, ensure_ascii=True)
        stream.write("\n")


def validate_record(record):
    try:
        if record["schema"] != SCHEMA or record["adapter_version"] != VERSION:
            raise ValueError("unsupported artifact schema")
        body = {k: v for k, v in record.items() if k != "artifact_sha256"}
        if digest(canonical(body)) != record["artifact_sha256"]:
            raise ValueError("artifact content digest mismatch")
        if record["oracle"] != {"version": ORACLE_VERSION, "source_sha256": oracle_digest()}:
            raise ValueError("oracle version/source drift")
        target = record["target"]
        if target["commit"] != BASELINE_COMMIT or target["source_sha256"] != digest(source_bytes(target["variant"])):
            raise ValueError("target version/source drift")
        if record["config"] != CONFIG or record["config_sha256"] != digest(canonical(CONFIG)):
            raise ValueError("execution config drift")
        if digest(canonical(record["trace"])) != record["proposal_sha256"]:
            raise ValueError("proposal digest mismatch")
        if record["failure_identities"] != identities(record):
            raise ValueError("failure identity mismatch")
    except (KeyError, TypeError, HarnessError) as exc:
        raise ValueError("malformed or unsupported artifact") from exc
    return record


def replay_record(record):
    validate_record(record)
    if record["outcome"] not in ("ORACLE_MISMATCH", "NO_ORACLE_MISMATCH"):
        return {"status": "NOT_A_REPLAYABLE_RESULT", "replayable_failure": False,
                "artifact_sha256": record["artifact_sha256"]}
    current = make_record(record["trace"], record["target"]["variant"], record["metadata"])
    same = all(current.get(key) == record.get(key)
               for key in ("rows", "violations", "failure_identities", "input_sha256", "outcome"))
    return {"status": "REPRODUCED" if same else "MISMATCH",
            "replayable_failure": same and record["outcome"] == "ORACLE_MISMATCH",
            "artifact_sha256": record["artifact_sha256"],
            "runner_elapsed_ns": current["runner_elapsed_ns"]}
