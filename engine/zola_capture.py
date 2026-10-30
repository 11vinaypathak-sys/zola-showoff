#!/usr/bin/env python3
"""
ZOLA CAPTURE — auto-feed the self-improving loop (kills the manual rate() step).

Turns a relay conclusion's honest wins/losses into loop input automatically:
  wins  -> rate +1, losses -> rate -1, then learn() + skills.extract() in one call.
The signal comes from REAL assessment (a relay conclusion of what actually happened —
a reply came / didn't, content shipped + landed / didn't). NEVER fabricated. The rule:
only pass a win/loss that had a real observable outcome, not a feeling.

  python3 zola_capture.py --win warm_intro_referral --loss cold_dm_blast --note "Aug-8 relay"

Called by the relay flow ("process the relay queue") so concluding a chat feeds the loop.
Isolate tests with ZOLA_LEARN_DIR.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zola_learn as L
import zola_skills as S

def ingest(wins=None, losses=None, note=""):
    wins, losses = wins or [], losses or []
    for w in wins:   L.rate(w, 1.0, note or "relay: worked")
    for l in losses: L.rate(l, -1.0, note or "relay: failed")
    learned = L.learn()
    skills = S.extract()
    return {"rated_wins": wins, "rated_losses": losses,
            "signals_now": list(learned.get("signals", {}).keys()),
            "skills": skills}

if __name__ == "__main__":
    a = sys.argv[1:]
    wins, losses, note, i = [], [], "", 0
    while i < len(a):
        if a[i] == "--win"  and i + 1 < len(a): wins.append(a[i + 1]); i += 2
        elif a[i] == "--loss" and i + 1 < len(a): losses.append(a[i + 1]); i += 2
        elif a[i] == "--note" and i + 1 < len(a): note = a[i + 1]; i += 2
        else: i += 1
    if not wins and not losses: print(__doc__); sys.exit(0)
    print(json.dumps(ingest(wins, losses, note), indent=2))
