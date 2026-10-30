#!/usr/bin/env python3
"""
ZOLA LADDER (showoff build) — the Career Verdict feed from a ladder file. INFORMS.

A rung lights only when every one of its conditions carries a done date. No partial credit, no score.
    ACT      conditions left on the next rung, with the one that has a due date as the move
    DATA     a condition the system cannot verify from inside (measurable: false) becomes a request
    SETTLED  the current rung, with the date it lit
Reads engine/demo-ladder.json (synthetic).     python3 engine/zola_ladder.py --json > assets/demo-ladder.json
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    with open(os.path.join(HERE, "demo-ladder.json")) as fh:
        return json.load(fh)


def verdicts(d=None):
    d = d or load()
    rungs = d["rungs"]
    idx = next(i for i, r in enumerate(rungs) if r["level"] == d["current"])
    cur, nxt = rungs[idx], rungs[idx + 1] if idx + 1 < len(rungs) else None
    basis = {"source": "engine/demo-ladder.json", "n": sum(len(r["conditions"]) for r in rungs), "asof": d["asof"], "level": "B"}
    out, rows, checklist = [], [], []
    for i, r in enumerate(rungs):
        done = all(c.get("done") for c in r["conditions"])
        lit_on = max((c["done"] for c in r["conditions"] if c.get("done")), default=None) if done else None
        left = sum(1 for c in r["conditions"] if not c.get("done"))
        status = "done" if (done and i < idx) else ("current" if i == idx else ("next · %d to go" % left if i == idx + 1 else "locked"))
        rows.append(dict(level=r["level"], name=r["name"], status=status, lit_on=lit_on, left=left))
    if nxt:
        left = [c for c in nxt["conditions"] if not c.get("done")]
        checklist = [dict(text=c["text"], done=bool(c.get("done")), measurable=c.get("measurable", True)) for c in nxt["conditions"]]
        dated = [c for c in left if c.get("due")]
        out.append(dict(node="career", id="car.next." + nxt["level"], metric="conditions left on " + nxt["level"], value=len(left), unit="count",
                        threshold=0, rule="the rung lights when every listed condition is ticked · no partial credit", basis=basis, confidence=0.9,
                        move=dict(what=dated[0]["text"].lower() if dated else "tick the next condition", amount=None, unit=None, by=dated[0]["due"] if dated else None),
                        changes_if="a condition is ticked or the ladder is edited", verdict="ACT" if left else "SETTLED"))
        for c in left:
            if c.get("measurable", True) is False:
                out.append(dict(node="career", id="car.data." + "".join(ch for ch in c["text"].lower() if ch.isalnum() or ch == " ").replace(" ", "_"),
                                metric=c["text"].lower(), value=None, unit=None, threshold=None,
                                rule="cannot be measured from inside; needs one named outside reference", basis=dict(basis, level="D"),
                                move=dict(what="name one person outside the team who has seen the work", amount=None, unit=None, by=None),
                                confidence=1.0, changes_if="the reference is entered", verdict="DATA"))
    out.append(dict(node="career", id="car.current", metric="current rung · " + cur["level"], value=rows[idx]["lit_on"], unit="date", threshold=None,
                    rule="lit on the date its last condition was ticked", basis=basis, move=None, confidence=1.0,
                    changes_if="never; a lit rung stays lit", verdict="SETTLED"))
    return dict(asof=d["asof"], node="career", current=d["current"], rows=rows, checklist=checklist,
                left=out[0]["value"] if nxt else 0, verdicts=out)


if __name__ == "__main__":
    f = verdicts()
    if "--json" in sys.argv:
        print(json.dumps(f, indent=1)); sys.exit()
    print(f"\n  ZOLA LADDER · {f['asof']} · current {f['current']} · {f['left']} left on the next rung")
    for v in f["verdicts"]:
        m = v.get("move") or {}
        print(f"  {v['verdict']:<8} {v['metric']:<40} {str(v['value']):>10} → {m.get('what','')} {m.get('by') or ''}")
