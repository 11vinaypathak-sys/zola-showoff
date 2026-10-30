#!/usr/bin/env python3
"""
ZOLA SESSIONS (showoff build) — the Creative Verdict feed from a studio log. INFORMS.

The grid is the log: one cell per day, planned or not, made or not. The verdict is the six-week rate
against the owner's floor, and the move is next month's plan set from what was made, not what was hoped.
Reads engine/demo-sessions.json (synthetic).   python3 engine/zola_sessions.py --json > assets/demo-sessions.json
"""
import json, os, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    with open(os.path.join(HERE, "demo-sessions.json")) as fh:
        return json.load(fh)


def parse_days(s):
    s = s.replace(" ", "")
    return [dict(planned=s[i] == "P", made=s[i + 1] == "1") for i in range(0, len(s), 2)]


def verdicts(d=None):
    d = d or load()
    days = parse_days(d["days"])
    start = dt.date.fromisoformat(d["start"])
    asof = (start + dt.timedelta(days=len(days) - 1)).isoformat()
    planned = sum(1 for x in days if x["planned"]); made = sum(1 for x in days if x["made"])
    rate = made / planned if planned else 0.0
    floor = d["rule"]["floor"]
    basis = {"source": "engine/demo-sessions.json", "n": len(days), "asof": asof, "level": "A"}
    next_plan = max(1, made)                      # next window's plan = what was actually made in this one
    first_next = (dt.date.fromisoformat(asof).replace(day=1) + dt.timedelta(days=32)).replace(day=1).isoformat()
    out = [dict(node="creative", id="cre.rate", metric="sessions made against planned", value=round(rate, 4), unit="share", threshold=floor,
                rule="under %d%% for six weeks and next month’s plan shrinks to what was actually made" % round(floor * 100), basis=basis, confidence=0.95,
                move=dict(what="plan %d sessions next month, not %d" % (next_plan, planned), amount=None, unit=None, by=first_next) if rate < floor else None,
                changes_if="the six-week rate crosses %d%%" % round(floor * 100), verdict="ACT" if rate < floor else "SETTLED")]
    streak = 0
    for x in reversed(days):
        if x["made"]: streak += 1
        else: break
    out.append(dict(node="creative", id="cre.streak", metric="current streak", value=streak, unit="count", threshold=None,
                    rule="counted, not celebrated", basis=basis, move=None, confidence=1.0, changes_if="tomorrow", verdict="SETTLED"))
    return dict(asof=asof, node="creative", planned=planned, made=made, rate=round(rate, 4), floor=floor, days=days, verdicts=out)


if __name__ == "__main__":
    f = verdicts()
    if "--json" in sys.argv:
        print(json.dumps(f, indent=1)); sys.exit()
    print(f"\n  ZOLA SESSIONS · {f['asof']} · {f['made']}/{f['planned']} made · rate {f['rate']:.0%} vs floor {f['floor']:.0%}")
    for v in f["verdicts"]:
        m = v.get("move") or {}
        print(f"  {v['verdict']:<8} {v['metric']:<36} {str(v['value']):>8} → {m.get('what','')} {m.get('by') or ''}")
