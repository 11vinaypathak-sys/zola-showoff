#!/usr/bin/env python3
"""
ZOLA VERIFY — the shared verification kernel. Deterministic, stdlib-only.

WHY THIS EXISTS
The astronomy engine was not special. Read the other modules' own docstrings:

  zola_survivorship  "'3 replies' is meaningless without 'out of how many sent'"
  zola_signaling     grounded in Akerlof 1976; Landers, Rebitzer & Taylor 1996
  zola_screen        candidate universe built from official AMFI data
  zola_learn         learns only from outcomes that were actually RECORDED

That is one method in four places: denominators before ratios, named sources,
comparison against published data, and refusing to count only the flattering
results. Astronomy is simply where it got forced hardest, because it is the one
domain whose reference values are unambiguous enough to make cheating obvious.

So the primitives below are not new. They are the ones that survived being used
in anger in zola_astronomy.py, lifted out so every node can report the same way:
A NUMBER, ITS REFERENCE, AND ITS ERROR BAND.

THE FIVE
  verify()        a number against a reference: signed and relative error
  amplify()       how input uncertainty becomes output uncertainty
  undetermined()  is this too close to a boundary to call?
  likelihood()    observed vs base rate, and what it does to a prior
  LEVELS          A / B / C / D / X, so a claim carries its own confidence

WHAT THIS IS NOT
Not a statistics library. Each function is a few lines of arithmetic whose value
is that it is used CONSISTENTLY and that its output is honest about error. A
point estimate with no band is the failure mode this module exists to remove.

    python3 zola_verify.py selftest    # every primitive, checked
    python3 zola_verify.py demo        # worked examples from real ZOLA numbers
"""
import math
import sys

# ══════════════════════════════════════════════════════════════════════════════
# EVIDENCE LEVELS — a claim that does not carry its level is a claim pretending
# to a confidence it has not earned. Taken from the Grand Codex ladder.
# ══════════════════════════════════════════════════════════════════════════════
LEVELS = {
    "A": "measured or computed, checkable against a reference",
    "B": "documented method or source, reproducible from a stated convention",
    "C": "traditional or conventional interpretation, no external referent",
    "D": "integrated hypothesis — must become a measurable action",
    "X": "later correspondence or context — never load-bearing alone",
}
LEVEL_RULES = (
    "No decision rests on an X-level claim alone.",
    "Every D-level claim must become a measurable action.",
    "A and B carry error bands. C, D and X carry none and must not imply one.",
)


def level_ok(level, load_bearing=False):
    """Is this claim allowed to carry a decision on its own?"""
    if level not in LEVELS:
        raise ValueError("unknown evidence level %r" % level)
    return not (load_bearing and level in ("C", "D", "X"))


# ══════════════════════════════════════════════════════════════════════════════
# 1. VERIFY — a number against a reference
# ══════════════════════════════════════════════════════════════════════════════
def verify(got, ref, unit="", tol=None):
    """Compare a computed value to a reference. Returns a dict, never a bare bool.

    The signed error matters as much as its size: a consistent sign is a BIAS and
    points at a systematic fault, while alternating signs point at noise. That
    distinction is what found the missing precession term in the astronomy
    ephemeris — every residual leaned the same way.
    """
    err = got - ref
    rel = (err / ref) if ref else None
    out = {"got": got, "ref": ref, "error": err, "relative": rel, "unit": unit}
    if tol is not None:
        out["within"] = abs(err) <= tol
        out["tolerance"] = tol
        out["headroom"] = tol - abs(err)
    return out


def fmt_verify(v):
    """One line, always showing the error. Never print `got` without it."""
    s = "%.6g%s" % (v["got"], (" " + v["unit"]) if v["unit"] else "")
    s += "  vs ref %.6g" % v["ref"]
    s += "   err %+.4g" % v["error"]
    if v["relative"] is not None:
        s += " (%+.4f%%)" % (v["relative"] * 100.0)
    if "within" in v:
        s += "   %s" % ("WITHIN" if v["within"] else "EXCEEDS")
        s += " tol %.4g" % v["tolerance"]
        if v["within"]:
            s += ", headroom %.4g" % v["headroom"]
    return s


# ══════════════════════════════════════════════════════════════════════════════
# 2. AMPLIFY — input uncertainty into output uncertainty
# ══════════════════════════════════════════════════════════════════════════════
def amplify(fn, x, dx, *args):
    """Propagate an input error through any function, numerically.

    THE LESSON THIS ENCODES. In the astronomy engine the Moon's position is known
    to ~6 arcmin, which sounds tight — until you notice a Vimshottari date is
    seeded by it and runs for 7-20 years. Measured gain: ~3.2 days of date shift
    per arcmin, so the dates are good to +/- 19 days and no better.

    A projection is the same shape. A goal trajectory built on an assumed return
    rate compounds that assumption for years. Quoting either as a single number
    is the same error in two domains.

    Returns low/high/spread plus the local gain, so the amplification itself is
    visible rather than buried.
    """
    lo, hi = fn(x - dx, *args), fn(x + dx, *args)
    if lo > hi:
        lo, hi = hi, lo
    mid = fn(x, *args)
    gain = ((hi - lo) / (2.0 * dx)) if dx else 0.0
    return {"mid": mid, "low": lo, "high": hi, "spread": hi - lo,
            "gain": gain, "input": x, "input_error": dx}


def fmt_amplify(a, unit="", inunit=""):
    return ("%.6g%s  [%.6g .. %.6g]  spread %.6g%s   from +/-%.4g%s in  (gain %.4g)"
            % (a["mid"], (" " + unit) if unit else "", a["low"], a["high"],
               a["spread"], (" " + unit) if unit else "",
               a["input_error"], (" " + inunit) if inunit else "", a["gain"]))


# ══════════════════════════════════════════════════════════════════════════════
# 3. UNDETERMINED — too close to a boundary to call
# ══════════════════════════════════════════════════════════════════════════════
def undetermined(value, residual, boundaries=None, period=None):
    """Is `value` within `residual` of a boundary? Then the bucket is NOT known.

    Reporting a bucket you cannot resolve is worse than reporting nothing,
    because it looks identical to a bucket you can. The astronomy engine flags
    nakshatra padas, Gauquelin sectors and subdivision edges this way; a screen
    or a filter needs exactly the same state and usually lacks it.

    boundaries: explicit edges. period: regularly spaced edges (e.g. every 3.333
    degrees). Give one or the other.
    """
    if period:
        r = (value % period)
        dist = min(r, period - r)
    elif boundaries:
        dist = min(abs(value - b) for b in boundaries)
    else:
        raise ValueError("give boundaries or period")
    return {"value": value, "distance": dist, "residual": residual,
            "determined": dist > residual}


# ══════════════════════════════════════════════════════════════════════════════
# 4. LIKELIHOOD — observed rate vs base rate, and what it does to a prior
# ══════════════════════════════════════════════════════════════════════════════
def likelihood(observed, base):
    """Likelihood ratio of an observed rate against a base rate.

    This is the machinery that settled the Gauquelin question: 22% of champions
    vs 16.7% expected is LR 1.32, which moves a 50/50 belief to 56.9% and moves
    a realistic base rate by thousandths of a point. An edge that cannot survive
    that arithmetic is not an edge.

    Same test applies to a backtest, a reply rate, or a learned signal: the
    question is never "is it above chance" but "what does it do to my prior".
    """
    if not base:
        raise ValueError("base rate must be non-zero")
    return observed / base


def posterior(prior, lr):
    """Bayes on odds. The honest counterpart to any claimed edge."""
    o = prior / (1.0 - prior) if prior < 1.0 else float("inf")
    o *= lr
    return o / (1.0 + o)


def diagnostic_table(lr, priors=(0.05, 0.25, 0.5, 0.75)):
    """What an LR actually does across plausible priors. Usually: very little."""
    return [{"prior": p, "posterior": posterior(p, lr),
             "shift": posterior(p, lr) - p} for p in priors]


# ══════════════════════════════════════════════════════════════════════════════
# 5. DENOMINATOR — the survivorship guard, stated as a primitive
# ══════════════════════════════════════════════════════════════════════════════
def rate(successes, attempts):
    """A ratio that REFUSES to exist without its denominator.

    zola_survivorship already says it: "'3 replies' is meaningless without 'out
    of how many sent'". This makes that structural rather than a comment — and
    returns the sample size alongside, because a 100% rate from 2 attempts and
    from 200 are different facts wearing the same number.
    """
    if attempts is None or attempts <= 0:
        return {"rate": None, "successes": successes, "attempts": attempts,
                "usable": False, "why": "no denominator — the ratio is undefined"}
    r = successes / float(attempts)
    # Wilson-free rough guide: a rate from a small n is not a rate yet.
    return {"rate": r, "successes": successes, "attempts": attempts,
            "usable": attempts >= 20,
            "why": None if attempts >= 20 else
                   "n=%d is too small to read as a rate" % attempts}


# ══════════════════════════════════════════════════════════════════════════════
def cmd_selftest():
    print("\n  SELFTEST — every primitive, against a known answer")
    print("  " + "-" * 66)
    fails, total = [], []

    def check(name, got, want, tol=1e-9):
        total.append(name)
        ok = abs(got - want) <= tol
        print("    %-46s %s" % (name, "ok" if ok else "FAIL got %.10g want %.10g"
                                % (got, want)))
        if not ok:
            fails.append(name)

    v = verify(24.841200, 24.841202, "h", tol=1e-5)
    check("verify: lunar day error", v["error"], -2e-6, 1e-7)
    check("verify: within tolerance", 1.0 if v["within"] else 0.0, 1.0)

    # amplify against the measured astronomy result: 1 arcmin -> ~3.2 days
    a = amplify(lambda mins: mins * 3.2, 0.0, 6.0)
    check("amplify: dasha band from 6 arcmin", a["spread"], 38.4, 1e-9)
    check("amplify: gain", a["gain"], 3.2, 1e-9)

    u = undetermined(180.14, 0.15, period=360.0 / 27.0 / 4.0)
    check("undetermined: Moon on a pada edge", 0.0 if u["determined"] else 1.0, 1.0)
    u2 = undetermined(14.70, 0.15, period=360.0 / 27.0 / 4.0)
    check("undetermined: Sun clear of an edge", 1.0 if u2["determined"] else 0.0, 1.0)

    lr = likelihood(0.22, 2.0 / 12.0)
    check("likelihood: Gauquelin LR", lr, 1.32, 1e-9)
    check("posterior: 0.5 prior under LR 1.32", posterior(0.5, lr), 0.5689655172, 1e-9)

    r = rate(3, None)
    check("rate: no denominator is unusable", 0.0 if r["usable"] else 1.0, 1.0)
    r2 = rate(3, 4)
    check("rate: n=4 is not a rate yet", 0.0 if r2["usable"] else 1.0, 1.0)
    r3 = rate(30, 200)
    check("rate: n=200 is usable", 1.0 if r3["usable"] else 0.0, 1.0)

    check("level: X cannot be load-bearing", 0.0 if level_ok("X", True) else 1.0, 1.0)
    check("level: A can be load-bearing", 1.0 if level_ok("A", True) else 0.0, 1.0)

    print()
    # Counted, not hardcoded. A selftest that lies about how many tests it ran
    # is the exact failure this module exists to prevent.
    print("  %d checks, %d failed" % (len(total), len(fails)))
    return 1 if fails else 0


def cmd_demo():
    print("\n  DEMO — the same primitives on numbers from three different nodes")
    print("  " + "-" * 66)

    print("\n  ASTRONOMY — a lunar day, derived vs published")
    print("    " + fmt_verify(verify(24.8412000, 24.8412006, "h", tol=1e-5)))

    print("\n  ASTRONOMY — why a dasha date cannot be quoted to the day")
    print("    " + fmt_amplify(amplify(lambda m: m * 3.2, 0.0, 6.0), "d", "arcmin"))
    print("    6 arcmin of Moon becomes a 38-day window. The date was never the")
    print("    problem; the confidence attached to it was.")

    print("\n  FINANCE — the same shape, on a goal projection")

    def fv(annual_pct, current, monthly, months):
        rm = annual_pct / 100.0 / 12.0
        g = (1.0 + rm) ** months
        return current * g + monthly * ((g - 1.0) / rm)

    # Target chosen so the verdict is genuinely ambiguous across the band — that
    # is the case worth showing, and the prose below is derived from the result
    # rather than asserted, so it cannot contradict the number above it.
    target, months = 4500000.0, 120
    a = amplify(lambda r: fv(r, 500000.0, 15000.0, months), 9.0, 3.0)
    print("    " + fmt_amplify(a, "INR", "%/yr"))
    lo_ok, hi_ok = a["low"] >= target, a["high"] >= target
    mid_ok = a["mid"] >= target
    if lo_ok:
        verdict = "on track across the whole range"
    elif hi_ok:
        verdict = "AMBIGUOUS — on track only at the optimistic end"
    else:
        verdict = "off track across the whole range"
    print("    target %.0f -> %s" % (target, verdict))
    print("    point estimate alone would have said: %s"
          % ("on track" if mid_ok else "off track"))
    if hi_ok and not lo_ok:
        print("    The single assumed return prints one number and one verdict. The")
        print("    band shows the verdict FLIPS inside the range — so the honest")
        print("    answer is 'depends on the return', which is the actual answer.")
    else:
        print("    Here the verdict survives the whole band, so the point estimate")
        print("    happened to be safe. That is a result, not a guarantee — it has")
        print("    to be checked, which is the entire point of computing the band.")

    print("\n  JOBS — a reply rate without its denominator")
    for s, n in ((3, None), (3, 4), (30, 200)):
        r = rate(s, n)
        print("    %d / %-4s -> %s" % (s, str(n),
              ("%.1f%%  usable" % (r["rate"] * 100)) if r["usable"]
              else ("unusable: " + r["why"])))

    print("\n  ANY EDGE — what a claimed edge does to a prior")
    lr = likelihood(0.22, 2.0 / 12.0)
    print("    observed 22.0%%  base 16.7%%  ->  LR %.4f" % lr)
    for row in diagnostic_table(lr):
        print("      prior %5.1f%%  ->  %5.1f%%   (%+.1f points)"
              % (row["prior"] * 100, row["posterior"] * 100, row["shift"] * 100))
    print("    An edge that moves a 50/50 to 57 is not a strategy. Same arithmetic")
    print("    for a planet, a fund and a cover letter.")
    return 0


CMDS = {"selftest": cmd_selftest, "demo": cmd_demo}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    cmd = (args[0] if args else "selftest").lower()
    if cmd == "all":
        rc = cmd_selftest()
        cmd_demo()
        print()
        return rc
    if cmd not in CMDS:
        print("unknown: %s\nknown: %s, all" % (cmd, ", ".join(sorted(CMDS))))
        return 1
    rc = CMDS[cmd]()
    print()
    return rc or 0


if __name__ == "__main__":
    sys.exit(main())
