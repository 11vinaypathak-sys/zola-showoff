#!/usr/bin/env python3
"""
ZOLA SIGNALING — the overtime rat-race, as a deterministic calculation.

Grounding: Akerlof 1976 ("The Economics of Caste and of Rat Races") and Landers,
Rebitzer & Taylor 1996 ("Rat Race Redux: Adverse Selection in the Determination of
Work Hours in Law Firms") model overwork as a Nash equilibrium, not a productivity
choice. Effort signals commitment when output can't be verified directly, so the
payoff to staying late depends on what OTHERS do, not on what's left to do. If
everyone leaving at contracted hours is the social optimum, but any one person
leaving first reads as defection, the group gets stuck at a Pareto-DOMINATED
equilibrium: everyone works longer, no one is better off *relative to peers* (the
whole point of staying), and the baseline for "looks committed" just moved up.
Stable (no one benefits by unilaterally deviating) but not efficient — a race to
the bottom that personal willpower alone cannot exit; it needs a changed rule
(a firm policy, a manager who leaves visibly, a coordinated norm), not more grit.

This turns "am I in the trap tonight" from a vibe into a number:
  deliverable_real    : a genuine external deadline/output is pending tonight
  told_by_principal   : a manager/client EXPLICITLY required this (not inferred)
  peer_anchored       : the real reason is "others are still here" / optics
  hours_over          : hours worked past contracted/baseline today

trap_score in [0,1] — 0 = fully rational overtime, 1 = pure signaling equilibrium.
Weights are authored (Vinay's standing read of the model), not derived — same
status as LAM_DECIDE in zola_decide.py. No LLM.

Every read appends to ~/.zola/signaling.jsonl (or $ZOLA_LEARN_DIR), so this
compounds into a trend the Black node can read, not a one-off number.

  python3 zola_signaling.py --deliverable-real 0 --told-by-principal 0 --peer-anchored 1 --hours-over 2
  python3 zola_signaling.py --trend                 # rolling read over logged history
"""
import sys, os, json, time, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zola_learn as L

LOG = os.path.join(L.ZDIR, "signaling.jsonl")

# A genuine reason (told_by_principal, else deliverable_real) sets the FLOOR; peer_anchored
# only adds optics riding on top of it. It never overrides a genuine reason into a trap —
# that would contradict the model (a real deadline doesn't stop being real because Rahul is
# also still at his desk). Pure TRAP requires BOTH no genuine reason AND peer anchoring.
FLOOR_TOLD    = 0.15   # explicit ask from whoever owns the deadline — strongest rational signal
FLOOR_DELIV   = 0.25   # a real deliverable, but no one explicitly asked you to stay for it
FLOOR_NEITHER = 0.55   # no genuine reason offered at all — ambiguous even before peer optics
PEER_ADD_TOLD    = 0.15
PEER_ADD_DELIV   = 0.20
PEER_ADD_NEITHER = 0.40

TRAP_T, RATIONAL_T = 0.6, 0.3


def score(deliverable_real, told_by_principal, peer_anchored, hours_over=0.0):
    if told_by_principal:
        s = FLOOR_TOLD + (PEER_ADD_TOLD if peer_anchored else 0)
    elif deliverable_real:
        s = FLOOR_DELIV + (PEER_ADD_DELIV if peer_anchored else 0)
    else:
        s = FLOOR_NEITHER + (PEER_ADD_NEITHER if peer_anchored else 0)
    s = min(1.0, round(s, 3))

    if s >= TRAP_T:
        verdict = "TRAP"
        read = ("SIGNALING EQUILIBRIUM — the deliverable isn't the reason you're still here; "
                "the baseline moved because leaving first reads as defection. Staying doesn't buy "
                "you anything relative to peers once they match you — it's a servicer hour, not an "
                "owner one: sold for status, not compounding into equity, output, or the exit.")
    elif s <= RATIONAL_T:
        verdict = "RATIONAL"
        read = ("GENUINE OVERTIME — a real deliverable or an explicit ask from whoever owns the "
                "deadline, not peer optics. Not the rat race; don't apply the trap framing here.")
    else:
        verdict = "MIXED"
        read = ("PARTIALLY ANCHORED — some real work, some status-matching. Isolate which hours are "
                "which; only the peer-anchored portion is the trap.")

    servicer_cost = round(hours_over * s, 2) if hours_over else 0.0
    return {
        "trap_score": s, "verdict": verdict, "read": read,
        "hours_over": hours_over, "servicer_hours": servicer_cost,
        "inputs": {"deliverable_real": bool(deliverable_real),
                   "told_by_principal": bool(told_by_principal),
                   "peer_anchored": bool(peer_anchored)},
    }


def log_entry(result):
    os.makedirs(L.ZDIR, exist_ok=True)
    row = dict(result); row["ts"] = time.time()
    with open(LOG, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def trend(n=14):
    rows = L._read_jsonl(LOG)[-n:]
    if not rows:
        return {"n": 0, "read": "no logged reads yet — every score() call with --log adds one"}
    avg = round(sum(r["trap_score"] for r in rows) / len(rows), 3)
    servicer_total = round(sum(r.get("servicer_hours", 0) for r in rows), 2)
    trap_nights = sum(1 for r in rows if r["verdict"] == "TRAP")
    return {
        "n": len(rows), "avg_trap_score": avg, "trap_nights": trap_nights,
        "servicer_hours_total": servicer_total,
        "read": (f"{trap_nights}/{len(rows)} reads were pure signaling equilibrium; "
                 f"{servicer_total}h sold for status matching, not output — "
                 "that's the number to bring to a firm-policy conversation, not willpower."),
    }


def _cli():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--deliverable-real", type=int, default=None)
    p.add_argument("--told-by-principal", type=int, default=None)
    p.add_argument("--peer-anchored", type=int, default=None)
    p.add_argument("--hours-over", type=float, default=0.0)
    p.add_argument("--log", action="store_true")
    p.add_argument("--trend", action="store_true")
    p.add_argument("--json", action="store_true")
    a, _ = p.parse_known_args()

    if a.trend:
        print(json.dumps(trend(), indent=1)); return

    if a.deliverable_real is None or a.told_by_principal is None or a.peer_anchored is None:
        print(__doc__); return

    r = score(a.deliverable_real, a.told_by_principal, a.peer_anchored, a.hours_over)
    if a.log:
        log_entry(r)
    print(json.dumps(r, indent=1) if a.json else
          f"  trap_score  : {r['trap_score']}  ({r['verdict']})\n"
          f"  servicer_hrs: {r['servicer_hours']}\n"
          f"  read        : {r['read']}")


if __name__ == "__main__":
    _cli()
