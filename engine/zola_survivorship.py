#!/usr/bin/env python3
"""
ZOLA SURVIVORSHIP — the survivorship-bias lens, as a deterministic calculation.

The loop learns from outcomes you RECORDED. Survivorship bias is the distortion in that:
  1. DENOMINATOR — "3 replies" is meaningless without "out of how many sent". A move that
     looks like it works may just be UNDER-SAMPLED. The honest floor is the Wilson lower
     bound: given n tries, the lowest the true success rate plausibly is. 1/1 -> ~21%, NOT 100%.
  2. INVISIBLE GRAVEYARD — a move you never TRIED is absent, not "avoid". Absence != evidence.
  3. SURVIVOR-OF-ONE — a single win reads as proof; it isn't until the sample grows.

This turns "don't trust survivors" from a slogan into a number the loop + Black node apply.
No LLM. Reads the same ~/.zola/ratings.jsonl the loop already writes.

  python3 zola_survivorship.py            # full readout over the real store
  python3 zola_survivorship.py <move>     # one move's corrected picture

Isolate tests with ZOLA_LEARN_DIR.
"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zola_learn as L
import zola_verify as V                        # the shared kernel
try:
    import zola_skills as S
    UNIVERSE = list(S.ALIASES.keys())          # the known candidate moves = the "did I even try it" set
except Exception:
    UNIVERSE = ["warm_intro", "cold_apply", "cold_dm", "referral", "content_inbound"]

TRUST_N = 8   # below this, a positive move is still survivorship-risky (thin denominator)
# Below this many TOTAL attempts there is no usable base rate, so no move can be
# compared to anything and every lift figure would be noise wearing a decimal.
POOL_N = 20


def wilson_lower(w, n, z=1.96):
    """Honest floor on a success rate at ~95% — the survivorship correction. 1/1 -> 0.21."""
    if n <= 0:
        return 0.0
    p = w / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return max(0.0, round((centre - margin) / denom, 3))


def wilson_upper(w, n, z=1.96):
    """The other end of the same interval. Needed to ask whether a move's rate is
    DISTINGUISHABLE from the base rate, which the floor alone cannot answer."""
    if n <= 0:
        return 1.0
    p = w / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return min(1.0, round((centre + margin) / denom, 3))

def _tallies():
    by = {}
    for r in L._read_jsonl(L.RATINGS):
        t = r.get("target")
        if not t:
            continue
        try:
            sc = float(r.get("score", 0))
        except (TypeError, ValueError):
            continue
        d = by.setdefault(t, {"attempts": 0, "wins": 0})
        d["attempts"] += 1
        if sc > 0:
            d["wins"] += 1
    return by

def base_rate(by=None):
    """The POOLED rate across every recorded move — the reference a move is judged against.

    THE GAP THIS CLOSES. A floor of 40% is not an edge until you know what the
    alternative was. If everything you try replies at 35%, a 40% move is noise
    wearing a decimal point, and switching strategy on it is the same mistake as
    reading 22%-vs-16.7% as a Mars effect: an observed rate above a base rate is
    not a finding until you compute what it does to your prior.

    Routed through the kernel's rate(), which refuses to exist without its
    denominator and will not call a thin sample a rate at all.
    """
    by = _tallies() if by is None else by
    wins = sum(d["wins"] for d in by.values())
    att = sum(d["attempts"] for d in by.values())
    r = V.rate(wins, att)
    r["usable"] = att >= POOL_N
    if not r["usable"] and att > 0:
        r["why"] = "n=%d across all moves is too thin for a base rate" % att
    return r


def move_view(target, by=None, base=None):
    by = _tallies() if by is None else by
    d = by.get(target, {"attempts": 0, "wins": 0})
    a, w = d["attempts"], d["wins"]
    base = base_rate(by) if base is None else base

    if a == 0:
        # An untested move's best estimate is the BASE RATE, not zero. Treating
        # absence as a low score is how the graveyard stays invisible.
        prior = base["rate"] if base["usable"] else None
        return {"move": target, "attempts": 0, "wins": 0, "raw_rate": None,
                "honest_floor": 0.0, "ceiling": None, "lift": None,
                "distinguishable": False, "level": "X",
                "best_estimate": prior,
                "read": ("UNTESTED — absence isn't evidence; your best estimate for it is "
                         "the base rate %d%%, not zero" % round(prior * 100)) if prior is not None
                        else "UNTESTED — absence isn't evidence, and there is no base rate to fall back on"}

    raw = round(w / a, 3)
    floor = wilson_lower(w, a)
    ceil = wilson_upper(w, a)
    lift = distinguishable = None
    if base["usable"] and base["rate"]:
        lift = round(V.likelihood(raw, base["rate"]), 3)
        # The real test is not the lift, it is whether this move's interval
        # EXCLUDES the base rate. Overlapping intervals means indistinguishable,
        # however large the lift looks.
        distinguishable = (floor > base["rate"]) or (ceil < base["rate"])

    if a < TRUST_N:
        read = (f"SURVIVOR-RISK — {w}/{a} looks like {int(raw*100)}% but honest floor is "
                f"{int(floor*100)}% (thin sample)")
        level = "D"
    elif distinguishable:
        read = (f"DISTINGUISHABLE — {w}/{a}, interval {int(floor*100)}-{int(ceil*100)}% "
                f"excludes the {int(base['rate']*100)}% base rate")
        level = "A"
    elif base["usable"]:
        read = (f"INDISTINGUISHABLE — {w}/{a}, interval {int(floor*100)}-{int(ceil*100)}% "
                f"straddles the {int(base['rate']*100)}% base rate; the lift is noise")
        level = "D"
    else:
        read = (f"SAMPLED — {w}/{a}, floor {int(floor*100)}% (denominator big enough to "
                f"trust, but no base rate to compare against yet)")
        level = "B"

    return {"move": target, "attempts": a, "wins": w, "raw_rate": raw,
            "honest_floor": floor, "ceiling": ceil, "lift": lift,
            "distinguishable": bool(distinguishable), "level": level,
            "best_estimate": floor, "read": read}

def survivorship():
    by = _tallies()
    base = base_rate(by)
    tried = [move_view(t, by, base) for t in by]
    tried.sort(key=lambda m: -(m["honest_floor"]))
    untested = [m for m in UNIVERSE if m not in by]

    # What a decision should actually rest on: only moves whose interval clears
    # the base rate. Everything else is a candidate, not a conclusion.
    actionable = [m["move"] for m in tried if m["distinguishable"]]
    out = {
        "base_rate": base,
        "tried": tried,
        "untested": untested,
        "actionable": actionable,
        "graveyard_note": ("moves you've NEVER tried — you have zero evidence either way; "
                           "don't treat their absence as a verdict") if untested else "every known move has been tested",
        "rule": "trust the honest_floor, not the raw_rate; a positive move under "
                f"{TRUST_N} attempts is a survivor, not a proof.",
        "base_rule": ("a rate is only an edge if its interval EXCLUDES the pooled base "
                      "rate; a lift with overlapping intervals is noise"),
    }
    if not base["usable"]:
        out["verdict"] = ("NO BASE RATE YET — %s. Until then no move can be compared to "
                          "any other, and the ranking below orders floors, not findings."
                          % (base["why"] or "insufficient data"))
    elif not actionable:
        out["verdict"] = ("NOTHING IS DISTINGUISHABLE — every move's interval straddles the "
                          "%d%% base rate. Keep sampling; do not switch strategy on this."
                          % round(base["rate"] * 100))
    else:
        out["verdict"] = ("DISTINGUISHABLE: %s — interval clears the %d%% base rate"
                          % (", ".join(actionable), round(base["rate"] * 100)))
    return out


def decision_table(target):
    """What this move's evidence does to a prior. The honest counterpart to a lift.

    Same arithmetic as the Gauquelin table in zola_astronomy: an edge that moves
    a 50/50 belief to 57% is not a strategy, whether the input is a planet or a
    reply rate.
    """
    m = move_view(target)
    if not m.get("lift"):
        return {"move": target, "lift": None,
                "note": "no base rate or no attempts — nothing to convert"}
    return {"move": target, "lift": m["lift"],
            "rows": V.diagnostic_table(m["lift"]),
            "distinguishable": m["distinguishable"]}

def corrected_confidence(target):
    """Confidence the loop should actually trust = the survivorship floor. Feeds advise()."""
    return move_view(target)["honest_floor"]

if __name__ == "__main__":
    a = sys.argv[1:]
    if a:
        print(json.dumps(move_view(a[0]), indent=1))
    else:
        print(json.dumps(survivorship(), indent=1))
