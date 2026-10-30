#!/usr/bin/env python3
"""
ZOLA MOVES (showoff build) — the Verdict feed, run on a neutral demo book. INFORMS.

The Verdict contract (one rule): a node's output is a NUMBER with a MOVE attached.
    { metric, value, unit, threshold, rule, basis{source,n,asof,level},
      move{what, amount, unit, by}, confidence, changes_if, verdict }
    verdict ∈ ACT · WAIT · DATA (an input is missing) · SETTLED

What this module computes, from the book alone:
    TRIM     rupees above the holding cap (own rule)
    DEPLOY   for each asset CLASS the book lacks, a size from the class caps and the
             per-move risk budget, capped by stated monthly capacity, ranked by the
             effect on book structure (effective holdings), with the stress downside
    DATA     what could not be computed and why
Names asset classes, never instruments. Issues no return forecast. Deterministic.
Reads engine/demo-book.json — synthetic numbers, nobody's real money.

    python3 engine/zola_moves.py --json > assets/demo-moves.json
"""
import json, os, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = os.path.join(HERE, "demo-book.json")

RULES = {"holding_cap": 0.35, "per_move_risk_pct": 0.05, "min_history": 10, "eff_n_floor": 5,
         "class_caps": {"crypto": 0.10, "commodity": 0.15, "equity": 0.40, "equity_global": 0.20,
                        "fixed_income": 0.55, "arbitrage": 0.30, "sovereign_debt": 0.30, "real_assets": 0.15}}
SHOCK = {"crypto": -0.50, "equity": -0.20, "equity_global": -0.20, "commodity": -0.15, "fixed_income": -0.40,
         "arbitrage": -0.02, "sovereign_debt": -0.08, "real_assets": -0.25}
LABEL = {"equity": "broad equity", "equity_global": "overseas equity", "arbitrage": "arbitrage / liquid",
         "commodity": "commodity", "crypto": "crypto", "fixed_income": "fixed income", "sovereign_debt": "sovereign debt",
         "real_assets": "real assets"}
CANDIDATES = ["fixed_income", "equity", "commodity", "crypto", "equity_global", "real_assets", "sovereign_debt", "arbitrage"]
ILLIQUID = {"insurance"}


def load():
    with open(BOOK) as fh:
        return json.load(fh)


def next_working_day(d):
    d += dt.timedelta(days=1)
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    return d.isoformat()


def concentration(assets):
    total = sum(a["amount"] for a in assets)
    rows = sorted(((a["name"], a["amount"], a["cls"], a["amount"] / total) for a in assets), key=lambda r: -r[3])
    hhi = sum(r[3] ** 2 for r in rows)
    return rows, hhi, (1 / hhi if hhi else 0), total


def deployment_fit(assets, amount):
    """Rank destination classes by resulting effective holdings. Concentration, not return."""
    by = {}
    for a in assets:
        by[a["cls"]] = by.get(a["cls"], 0.0) + a["amount"]
    total = sum(by.values())
    rows = []
    for c in CANDIDATES:
        nb = dict(by); nb[c] = nb.get(c, 0.0) + amount; t = total + amount
        hhi = sum((v / t) ** 2 for v in nb.values() if v > 0)
        rows.append(dict(cls=c, is_hole=by.get(c, 0.0) == 0, eff_n=1 / hhi))
    rows.sort(key=lambda r: -r["eff_n"])
    return rows


def size(assets, cls, conviction=0.5, recent_move=0.0):
    by = {}
    for a in assets:
        by[a["cls"]] = by.get(a["cls"], 0.0) + a["amount"]
    total = sum(by.values())
    cur = by.get(cls, 0.0) / total
    cap = RULES["class_caps"].get(cls, 0.25)
    room = max(0.0, cap - cur) * total
    base = RULES["per_move_risk_pct"] * total
    tilt = max(0.5, min(1.5, 1 - recent_move * 3))
    suggested = max(0.0, min(base * tilt * conviction, room))
    return dict(cur=cur, cap=cap, room=room, base=base, tilt=tilt, suggested=suggested)


def volatility_drawdown(hist):
    if len(hist) < 3:
        return None
    s = [hist[k] for k in sorted(hist)]
    peak, mdd = s[0], 0.0
    for v in s:
        peak = max(peak, v); mdd = min(mdd, v / peak - 1)
    return dict(mdd=mdd)


def verdicts(book=None, today=None):
    book = book or load()
    today = today or dt.date.today()
    asof = today.isoformat()
    assets = [a for a in book["assets"] if a["amount"] > 0]
    rows, hhi, eff_n, total = concentration(assets)
    basis = {"source": "engine/demo-book.json", "n": len(rows), "asof": asof, "level": "A"}
    out = []
    out.append(dict(node="finance", id="fin.structure", metric="effective holdings", value=round(eff_n, 2), unit="count",
                    threshold=RULES["eff_n_floor"], rule="a book with under 5 effective positions is one event away from a bad year",
                    basis=basis, move=None, confidence=0.95, changes_if="any holding changes by more than 5% of the book",
                    verdict="ACT" if eff_n < RULES["eff_n_floor"] else "SETTLED"))
    for name, amt, cls, share in rows:
        if cls in ILLIQUID:
            continue
        if share > RULES["holding_cap"]:
            excess = (share - RULES["holding_cap"]) * total
            slug = "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")
            out.append(dict(node="finance", id="fin.cap." + slug, metric="holding share · " + name, value=round(share, 4), unit="share",
                            threshold=RULES["holding_cap"], rule="holding cap", basis=basis, confidence=0.9,
                            move=dict(what="trim " + name, amount=round(excess), unit="INR", by=next_working_day(today)),
                            changes_if="the cap is edited or the book total moves more than 5%", verdict="ACT"))
    cap_amt = float(book.get("capacity", {}).get("monthly", 0) or 0)
    # class-level effective count, so "before → after" compares like with like: the deploy
    # ranking is by CLASS structure, while the headline effective-holdings figure is per holding
    by_cls = {}
    for a in assets:
        by_cls[a["cls"]] = by_cls.get(a["cls"], 0.0) + a["amount"]
    eff_cls = 1 / sum((v / total) ** 2 for v in by_cls.values())
    holes = [r for r in deployment_fit(assets, cap_amt if cap_amt > 0 else 0.05 * total) if r["is_hole"]]
    for rank, r in enumerate(holes[:3], 1):
        s = size(assets, r["cls"])
        amount = min(s["suggested"], cap_amt) if cap_amt > 0 else s["suggested"]
        v = dict(node="finance", id="fin.deploy." + r["cls"], metric="exposure · " + LABEL[r["cls"]], value=0.0, unit="share",
                 threshold=None, rule="a class at zero is a hole, not a view", basis=basis, confidence=0.8,
                 detail=dict(rank=rank, eff_n_now=round(eff_cls, 2), eff_n_after=round(r["eff_n"], 2), class_cap=s["cap"],
                             room=round(s["room"]), per_move_budget=round(s["base"]), downside=round(amount * SHOCK[r["cls"]])),
                 changes_if="capacity, class caps or conviction are edited; the book total moves more than 5%")
        if amount <= 0:
            v.update(move=None, verdict="WAIT")
        else:
            v.update(move=dict(what="deploy into " + LABEL[r["cls"]], amount=round(amount), unit="INR", by=next_working_day(today)), verdict="ACT")
        out.append(v)
    if cap_amt <= 0:
        out.append(dict(node="finance", id="fin.data.capacity", metric="monthly deployable capacity", value=None, unit="INR", threshold=None,
                        rule="deploy sizes are capped by stated capacity", basis=dict(basis, level="D"),
                        move=dict(what="state a monthly capacity", amount=None, unit=None, by=None), confidence=1.0,
                        changes_if="the figure is entered", verdict="DATA"))
    hist = book.get("valueHist", {})
    if len(hist) < RULES["min_history"]:
        out.append(dict(node="finance", id="fin.data.history", metric="book value history", value=len(hist), unit="points",
                        threshold=RULES["min_history"], rule="volatility and drawdown need 10 points", basis=dict(basis, level="B"),
                        move=dict(what="log the book total weekly, one number", amount=None, unit=None, by=None), confidence=1.0,
                        changes_if="10 or more points exist", verdict="DATA"))
    else:
        vd = volatility_drawdown(hist)
        out.append(dict(node="finance", id="fin.drawdown", metric="max drawdown", value=round(vd["mdd"], 4), unit="share", threshold=-0.15,
                        rule="drawdown limit", basis=dict(basis, source="valueHist", n=len(hist), level="B"), move=None, confidence=0.7,
                        changes_if="a new book value is logged", verdict="ACT" if vd["mdd"] < -0.15 else "SETTLED"))
    order = {"ACT": 0, "DATA": 1, "WAIT": 2, "SETTLED": 3}
    out.sort(key=lambda v: (order[v["verdict"]], -((v.get("move") or {}).get("amount") or 0)))
    return dict(asof=asof, node="finance", total=round(total), eff_n=round(eff_n, 2), hhi=round(hhi, 4), capacity=round(cap_amt),
                rules=RULES, verdicts=out)


if __name__ == "__main__":
    feed = verdicts()
    if "--json" in sys.argv:
        print(json.dumps(feed, indent=1)); sys.exit()
    print(f"\n  ZOLA MOVES · demo book · {feed['asof']} · effective holdings {feed['eff_n']} · total ₹{feed['total']:,}")
    for v in feed["verdicts"]:
        m = v.get("move") or {}
        print(f"  {v['verdict']:<8} {v['metric']:<36} {str(v['value']):>8} {v['unit']:<6} → {m.get('what','')} "
              f"{('₹%s' % format(m['amount'], ',')) if m.get('amount') else ''} {m.get('by') or ''}")
