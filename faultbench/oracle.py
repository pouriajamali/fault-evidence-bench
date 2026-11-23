"""Independent recovery-epoch relation; deliberately has no price-book model.

Domain restrictions make lexical errors, crosses and deletions impossible.
The relation comes from the written contract, not from importing the target.
"""
from dataclasses import dataclass
import re

ORACLE_VERSION = "recovery-fold/1"
MAX_RECORDS = 32
MAX_INPUT_BYTES = 4096


class DomainError(ValueError):
    """A proposal outside the qualified grammar; never a target bug."""


class HarnessError(RuntimeError):
    """Execution, framing or adapter failure; never a target bug."""


@dataclass(frozen=True)
class Event:
    kind: str
    sequence: int = 0


@dataclass(frozen=True)
class Expected:
    reason: str
    ready: bool
    sequence: int
    preserve: bool


def parse_trace(trace):
    if not isinstance(trace, list) or not 1 <= len(trace) <= MAX_RECORDS:
        raise DomainError("trace must contain 1..32 records")
    if any(not isinstance(row, str) for row in trace):
        raise DomainError("record must be a string")
    try:
        raw = ("\n".join(trace) + "\n").encode("ascii")
    except UnicodeEncodeError as exc:
        raise DomainError("qualified grammar is ASCII") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise DomainError("trace byte limit")
    events = []
    for row in trace:
        if row == "D":
            events.append(Event("disconnect"))
            continue
        snapshot = re.fullmatch(r"S ([1-9][0-9]{0,3}) 100 5 200 5", row)
        update = re.fullmatch(r"U ([1-9][0-9]{0,3}) B (9[0-9]|10[0-9]|110) ([1-9])", row)
        match = snapshot or update
        if match is None or int(match[1]) > 1000:
            raise DomainError("record outside qualified recovery grammar")
        events.append(Event("snapshot" if snapshot else "update", int(match[1])))
    return events


def expected_states(trace):
    """Fold a small relation over (accepted sequence, readiness).

    No target reason/state is consulted. The price tuple is excluded except
    for the separate relational rejection-atomicity check in judge().
    """
    accepted, ready = 0, False
    result = []
    for event in parse_trace(trace):
        s = event.sequence
        if event.kind == "disconnect":
            reason, ready, preserve = "DISCONNECTED", False, True
        elif event.kind == "snapshot":
            preserve = s < accepted
            reason = "STALE_SNAPSHOT" if preserve else "SNAPSHOT"
            ready = not preserve
            accepted = accepted if preserve else s
        else:
            relation = "old" if s <= accepted else "next" if s == accepted + 1 else "gap"
            # Declarative control relation; no price-level update logic.
            reason, next_ready, advance = {
                (False, "old"): ("NOT_READY", False, False),
                (False, "next"): ("NOT_READY", False, False),
                (False, "gap"): ("NOT_READY", False, False),
                (True, "old"): ("STALE", True, False),
                (True, "next"): ("UPDATE", True, True),
                (True, "gap"): ("GAP", False, False),
            }[(ready, relation)]
            accepted, ready, preserve = (s if advance else accepted), next_ready, not advance
        result.append(Expected(reason, ready, accepted, preserve))
    return result


def judge(trace, rows):
    expected = expected_states(trace)
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise HarnessError("output row count differs from input record count")
    failures = []
    previous_prices = ("-", "-", "-", "-")
    reasons = {"SNAPSHOT", "STALE_SNAPSHOT", "UPDATE", "STALE", "GAP", "NOT_READY", "DISCONNECTED"}
    for i, (state, row) in enumerate(zip(expected, rows)):
        fields = row.split("|") if isinstance(row, str) else []
        if (len(fields) != 7 or fields[0] not in reasons or fields[1] not in ("0", "1")
                or not re.fullmatch(r"[0-9]{1,10}", fields[2])
                or any(not re.fullmatch(r"-|[0-9]{1,10}", f) for f in fields[3:])):
            raise HarnessError("malformed target output")
        actual = (fields[0], fields[1] == "1", int(fields[2]))
        wanted = (state.reason, state.ready, state.sequence)
        predicates = ("reason-mismatch", "readiness-mismatch", "accepted-sequence-mismatch")
        for predicate, a, e in zip(predicates, actual, wanted):
            if a != e:
                failures.append({"event": i, "predicate": predicate, "expected": e, "actual": a})
        prices = tuple(fields[3:])
        if state.preserve and prices != previous_prices:
            failures.append({"event": i, "predicate": "rejection-state-mutation",
                             "expected": list(previous_prices), "actual": list(prices)})
        previous_prices = prices
    return failures
