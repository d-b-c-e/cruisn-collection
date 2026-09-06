"""Score force candidates only inside manually reviewed time intervals."""
import math


def evaluate(candidates, labels):
    if labels.get("schema") != 1 or labels.get("clock") != "emulated_ms":
        raise ValueError("labels require schema 1 and emulated_ms clock")
    coverage = labels["coverage"]
    def interval(pair):
        return len(pair) == 2 and all(isinstance(x, (float, int)) and math.isfinite(x) for x in pair) and 0 <= pair[0] <= pair[1]
    if not coverage or any(not interval(p) for p in coverage):
        raise ValueError("invalid reviewed coverage")
    if any(a[1] >= b[0] for a, b in zip(coverage, coverage[1:])):
        raise ValueError("reviewed coverage must be ordered and disjoint")
    events = labels["events"]
    for e in events:
        pair = [e["start_ms"], e["end_ms"]]
        if not e.get("kind") or not interval(pair) or not any(a <= pair[0] <= pair[1] <= b for a, b in coverage):
            raise ValueError("contact label must lie within reviewed coverage")
    if any(a["end_ms"] >= b["start_ms"] for a, b in zip(events, events[1:])):
        raise ValueError("contact labels must be ordered and disjoint")
    if any(not isinstance(t, (int, float)) or not math.isfinite(t) or t < 0 for t in candidates):
        raise ValueError("invalid candidate time")
    covered = sorted(t for t in candidates if any(a <= t <= b for a, b in coverage))
    used = set()
    matches = []
    for event in events:
        hits = [i for i, t in enumerate(covered) if i not in used and event["start_ms"] <= t <= event["end_ms"]]
        if hits:
            used.add(hits[0])
        matches.append(dict(event, candidate_ms=covered[hits[0]] if hits else None))
    tp = len(used)
    return {"matched_contacts": tp, "missed_contacts": len(events) - tp,
            "unmatched_candidates": len(covered) - tp,
            "unreviewed_candidates": len(candidates) - len(covered),
            "precision": tp / len(covered) if covered else None,
            "recall": tp / len(events) if events else None, "events": matches}
