#!/usr/bin/env python3
"""
ZOLA SWEEPS (showoff build) — the Intel Verdict feed from a sweep log. INFORMS.

Sixty-two sweeps over a month. Each has a spread against a control group. A crossing below the threshold with a
named source is a SIGNAL (ACT); a crossing without one is a WATCH (WAIT); everything else is a silence and is
logged as a result (SETTLED). Silence is the feature, so it is counted.
Reads engine/demo-sweeps.json (synthetic).     python3 engine/zola_sweeps.py --json > assets/demo-sweeps.json
"""
import json, os, sys, random, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
DAYS = 31


def load():
    with open(os.path.join(HERE, "demo-sweeps.json")) as fh:
        return json.load(fh)


def verdicts(d=None):
    d = d or load()
    rnd = random.Random(d.get("seed", 1))
    thr = d["rule"]["threshold"]
    start = dt.date.fromisoformat(d["start"])
    events = {round(e["day"] * 2): dict(e, kind="signal") for e in d["signals"]}
    events.update({round(w["day"] * 2): dict(w, kind="watch") for w in d["watches"]})
    sweeps = []
    for k in range(DAYS * 2):
        day = k / 2
        if k in events:
            e = events[k]; sweeps.append(dict(day=day, spread=e["spread"], source=e.get("source"), kind=e["kind"], note=e.get("note")))
        else:
            sweeps.append(dict(day=day, spread=round(rnd.gauss(-0.05, 0.14), 3), source=None, kind="silent"))
    signals = [s for s in sweeps if s["kind"] == "signal"]; watches = [s for s in sweeps if s["kind"] == "watch"]
    silent = [s for s in sweeps if s["kind"] == "silent"]
    asof = (start + dt.timedelta(days=DAYS - 1)).isoformat()
    basis = {"source": "engine/demo-sweeps.json", "n": len(sweeps), "asof": asof, "level": "A"}
    out = []
    for s in signals:
        date = (start + dt.timedelta(days=s["day"])).isoformat()
        out.append(dict(node="intel", id="int.signal.%g" % s["day"], metric="spread vs control · " + s["source"].lower(), value=s["spread"], unit="pts",
                        threshold=thr, rule="a crossing below %g with a named source is a signal" % thr, basis=basis, confidence=0.85,
                        move=dict(what="move the lead to the front of the week", amount=None, unit=None, by=(start + dt.timedelta(days=s["day"] + 1)).isoformat()),
                        changes_if="the spread recovers above %g or the source is withdrawn" % thr, verdict="ACT", date=date))
    for w in watches:
        out.append(dict(node="intel", id="int.watch.%g" % w["day"], metric="spread vs control · no named source", value=w["spread"], unit="pts", threshold=thr,
                        rule="a crossing without a named source is a watch, not a signal", basis=basis, confidence=0.6, move=None,
                        changes_if="a source is named or the spread recovers", verdict="WAIT"))
    out.append(dict(node="intel", id="int.silence", metric="sweeps run · silent", value=len(silent), unit="count", threshold=None,
                    rule="silence after a sweep is a result and is logged as one", basis=basis, move=None, confidence=1.0,
                    changes_if="a sweep returns a crossing", verdict="SETTLED"))
    gaps = []
    marks = sorted(s["day"] for s in signals)
    for a, b in zip(marks, marks[1:]):
        gaps.append(dict(from_day=a, to_day=b, days=b - a))
    return dict(asof=asof, node="intel", start=d["start"], days=DAYS, threshold=thr, sweeps=len(sweeps), signals=signals, watches=watches,
                silent=len(silent), gaps=gaps, verdicts=out)


if __name__ == "__main__":
    f = verdicts()
    if "--json" in sys.argv:
        print(json.dumps(f, indent=1)); sys.exit()
    print(f"\n  ZOLA SWEEPS · {f['asof']} · {f['sweeps']} sweeps · {len(f['signals'])} signals · {len(f['watches'])} watches · {f['silent']} silent")
    for v in f["verdicts"]:
        m = v.get("move") or {}
        print(f"  {v['verdict']:<8} {v['metric']:<44} {str(v['value']):>7} → {m.get('what','')} {m.get('by') or ''}")
