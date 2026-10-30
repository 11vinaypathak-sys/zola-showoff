#!/usr/bin/env python3
"""
ZOLA LEARN — the self-improving loop (deterministic core).

Closes the loop Hermes calls "self-improving": outcomes get RATED, the loop
LEARNS a per-target signal from those ratings + the event log, writes it to
~/.zola/learned.json, and any decision READS that signal to bias itself.
NO LLM at runtime — plain, auditable aggregation (ZOLA's deterministic core).
The "agentic shell" (turning a signal into a prose lesson) is the relay loop / Claude.

  python3 zola_learn.py rate <target> <score -1..1> ["note"]   # capture an outcome
  python3 zola_learn.py learn                                   # aggregate -> learned.json
  python3 zola_learn.py show [target]                           # inspect learned signal
  python3 zola_learn.py recall <target>                         # the bias a decision applies
  python3 zola_learn.py demo                                    # PROVE the loop changes an output

Isolate for tests with env ZOLA_LEARN_DIR (defaults to ~/.zola).
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import zola_verify as V
except Exception:                      # the loop must still run without the kernel
    V = None

ZDIR    = os.environ.get("ZOLA_LEARN_DIR", os.path.expanduser("~/.zola"))
RATINGS = os.path.join(ZDIR, "ratings.jsonl")
EVENTS  = os.path.join(ZDIR, "events.jsonl")
LEARNED = os.path.join(ZDIR, "learned.json")

def _append(path, obj):
    os.makedirs(ZDIR, exist_ok=True)
    with open(path, "a") as f: f.write(json.dumps(obj) + "\n")

def _read_jsonl(path):
    out = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try: out.append(json.loads(line))
                    except Exception: pass
    except FileNotFoundError: pass
    return out

def rate(target, score, note=""):
    score = max(-1.0, min(1.0, float(score)))
    _append(RATINGS, {"ts": time.time(), "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
                      "target": target, "score": score, "note": note})
    return {"rated": target, "score": score}

def _verdict(wavg):
    """The verdict rule, factored out so leave-one-out can reuse it verbatim."""
    return "reinforce" if wavg > 0.25 else ("avoid" if wavg < -0.25 else "neutral")


def learn():
    ratings, events = _read_jsonl(RATINGS), _read_jsonl(EVENTS)
    by = {}
    for r in ratings:
        t = r.get("target")
        if not t:
            continue
        try:
            sc = float(r.get("score", 0))
        except (TypeError, ValueError):
            continue  # skip a corrupt/hand-edited rating line rather than crash the whole loop
        by.setdefault(t, []).append(max(-1.0, min(1.0, sc)))  # clamp defensively too
    # Pooled mean across EVERY target — the reference a single target is judged
    # against. A target at +0.40 is not a signal if everything averages +0.40;
    # then the number says something about the rater, not the target.
    all_scores = [s for v in by.values() for s in v]
    pooled = round(sum(all_scores) / len(all_scores), 3) if all_scores else 0.0

    signals = {}
    for t, scores in by.items():
        n = len(scores)
        wts = [1.6 ** i for i in range(n)]             # newest ratings weigh most -> a move can DECAY
        wavg = round(sum(w * s for w, s in zip(wts, scores)) / sum(wts), 3)
        life = round(sum(scores) / n, 3)               # lifetime avg, for reference
        bias = round(wavg * min(1.0, n / 3.0), 3)      # recency-weighted + confidence-damped
        verdict = _verdict(wavg)

        # ── 1. HOW MUCH IS THIS VERDICT JUST THE LAST RATING? ────────────────
        # The 1.6^i weighting never gives the newest rating less than ~38% of
        # the total, and at n=3 it is ~50%. So drop the newest and recompute:
        # if the verdict moves, it was carried by one outcome. Leave-one-out is
        # deterministic — no distributional assumption needed.
        newest_share = round(wts[-1] / sum(wts), 3)
        if n >= 2:
            w2 = wts[:-1]
            wavg_wo = round(sum(w * s for w, s in zip(w2, scores[:-1])) / sum(w2), 3)
            stable = (_verdict(wavg_wo) == verdict)
        else:
            wavg_wo, stable = None, False      # a single rating is never stable

        # ── 2. IS IT DISTINGUISHABLE FROM THE POOLED MEAN? ──────────────────
        lift = round(wavg - pooled, 3)

        # ── 3. IS IT SITTING ON THE VERDICT THRESHOLD? ──────────────────────
        # Within 0.10 of +/-0.25 the verdict is a coin-flip on rounding.
        near_thresh = min(abs(abs(wavg) - 0.25), abs(wavg)) if V is None else \
            V.undetermined(wavg, 0.10, boundaries=[-0.25, 0.25])["distance"]
        on_edge = near_thresh <= 0.10

        # ── EVIDENCE LEVEL, so a consumer can refuse to act on a weak signal ─
        # The lift test only means anything with two or more targets: with one,
        # the target IS the pool and lift is 0 by construction. Applying it then
        # would silently downgrade every signal for a reason that is arithmetic,
        # not evidential.
        comparable = len(by) > 1
        if n < 3 or not stable:
            level = "D"
        elif on_edge or (comparable and abs(lift) < 0.15):
            level = "C"
        else:
            level = "B"

        warn = []
        if n < 3:
            warn.append("n=%d — below the damping floor, this is a survivor not a signal" % n)
        if not stable and n >= 2:
            warn.append("verdict FLIPS to '%s' if the newest rating is removed"
                        % _verdict(wavg_wo))
        if on_edge:
            warn.append("sits %.2f from the %+.2f verdict threshold" % (near_thresh, 0.25))
        if comparable and abs(lift) < 0.15:
            warn.append("only %+.2f from the %+.2f pooled mean — says little about THIS target"
                        % (lift, pooled))
        elif not comparable:
            warn.append("only one target rated — nothing to compare against, so the "
                        "pooled mean cannot tell you whether this is specific to it")

        signals[t] = {"avg": wavg, "life_avg": life, "n": n, "bias": bias, "verdict": verdict,
                      "level": level, "stable": bool(stable), "newest_share": newest_share,
                      "avg_without_newest": wavg_wo, "lift_vs_pooled": lift,
                      "on_threshold": bool(on_edge), "warnings": warn,
                      "lesson": f"{t}: recent {wavg:+.2f} (life {life:+.2f}) over {n} -> {verdict}"
                                + (f" [{level}] " + "; ".join(warn) if warn else f" [{level}]")}
    trusted = [t for t, s in signals.items() if s["level"] in ("A", "B")]
    meta = {"_updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "_events_seen": len(events), "_ratings_seen": len(ratings),
            "_pooled_mean": pooled,
            "_trusted": trusted,
            "_note": ("no signal here is trustworthy yet: every one is thin, unstable, "
                      "on a threshold, or indistinguishable from the pooled mean"
                      if not trusted else
                      "trustworthy signals (level A/B): " + ", ".join(trusted)),
            "signals": signals}
    os.makedirs(ZDIR, exist_ok=True)
    with open(LEARNED, "w") as f: json.dump(meta, f, indent=1)
    return meta

def recall(target):
    try: d = json.load(open(LEARNED))
    except Exception: return {"bias": 0.0, "verdict": "neutral", "lesson": "no learning yet"}
    return d.get("signals", {}).get(target, {"bias": 0.0, "verdict": "neutral",
                                              "lesson": "no signal for " + target})

def score_move(target, base=0.5, trust_only=False):
    """A decision score the loop demonstrably shifts (the integration point for the engine).

    trust_only=True applies the bias ONLY from a level A/B signal. A D-level
    signal is one rating, or a verdict that flips when you remove the newest
    rating — letting that move a decision score is the loop laundering a single
    outcome as learning. The default stays False so existing callers are
    unchanged, but anything making a real decision should pass True.
    """
    r = recall(target)
    bias = r.get("bias", 0.0)
    if trust_only and r.get("level") not in ("A", "B"):
        bias = 0.0
    return round(base + bias * 0.5, 3), r

def demo():
    t = "ship_the_film"
    s0, _ = score_move(t)
    print(f"  BEFORE rating   -> decision score for '{t}': {s0}")
    for _ in range(3): rate(t, 1.0, "demo: it worked")
    learn()
    s1, r = score_move(t)
    print(f"  learned signal  -> {r['lesson']}")
    print(f"  AFTER rating x3 -> decision score for '{t}': {s1}")
    print(f"  CHANGED = {s1 != s0}  → the loop read real ratings and shifted the output. Not a hoax.")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    c = a[0]
    if c == "rate" and len(a) >= 3: print(json.dumps(rate(a[1], a[2], a[3] if len(a) > 3 else "")))
    elif c == "learn": m = learn(); print(json.dumps({"updated": m["_updated"], "signals_learned": list(m["signals"].keys()), "ratings_seen": m["_ratings_seen"]}, indent=1))
    elif c == "show": d = json.load(open(LEARNED)) if os.path.exists(LEARNED) else {}; print(json.dumps((d.get("signals", {}).get(a[1]) if len(a) > 1 else d), indent=1))
    elif c == "recall" and len(a) > 1: print(json.dumps(recall(a[1]), indent=1))
    elif c == "demo": demo()
    else: print(__doc__)
