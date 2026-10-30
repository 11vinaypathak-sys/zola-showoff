#!/usr/bin/env python3
"""
ZOLA PIPELINE — second real signal into the self-improving loop (the Black-node link).

Turns the job pipeline's RECORDED outcomes into loop ratings, so which outreach
*channel* actually works is learned from real replies — not from a feeling.

  channel of a lead -> the "move" that gets rated:
    warmIntro:true        -> warm_intro
    explicit "channel"    -> <channel>            (e.g. "referral")
    else tier             -> applyNow=cold_apply · coldDM=cold_dm

  recorded "outcome" on a lead -> score:
    reply|intro|interview|offer -> +1.0   (it worked)
    reject                      -> -0.5   (it closed, badly)
    silent                      -> -0.5   (no answer = a soft no)
    (no outcome)                -> NOT rated — we never invent a result

Only leads with a real recorded outcome are rated, each counted ONCE
(a seen-ledger at ~/.zola/pipeline_seen.json dedupes across runs).

  python3 zola_pipeline.py sync [jobs.json]                 # feed recorded outcomes -> loop
  python3 zola_pipeline.py set "<company>" <outcome> [chan] # record an outcome on a lead (app/you)
  python3 zola_pipeline.py preview [jobs.json]              # what WOULD be rated, no writes

NEVER rewrites zola-jobs.json except the surgical field-set in `set` (read-modify-write,
everything else preserved). Isolate tests with ZOLA_LEARN_DIR + a temp jobs file.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zola_learn as L
import zola_capture as C

JOBS_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "zola-jobs.json")
SEEN = os.path.join(L.ZDIR, "pipeline_seen.json")

SCORE = {"reply": 1.0, "intro": 1.0, "interview": 1.0, "offer": 1.0, "reject": -0.5, "silent": -0.5}
MOVE_BY_TIER = {"applyNow": "cold_apply", "coldDM": "cold_dm", "watch": "watch"}

def _move(lead, tier):
    if lead.get("warmIntro"): return "warm_intro"
    if lead.get("channel"):   return str(lead["channel"]).strip().lower().replace(" ", "_")
    if tier == "research" and lead.get("engage"):     # research leads carry an engage type
        return ENGAGE_MOVE.get(lead["engage"], "cold_apply")
    return MOVE_BY_TIER.get(tier, "unknown_channel")

def _seen():
    try: return set(json.load(open(SEEN)))
    except Exception: return set()

def _save_seen(s):
    os.makedirs(L.ZDIR, exist_ok=True)
    json.dump(sorted(s), open(SEEN, "w"))

ENGAGE_MOVE = {"apply": "cold_apply", "pitch": "cold_dm", "watch": "cold_apply"}

def _leads(path):
    d = json.load(open(path))
    for tier, arr in d.get("tiers", {}).items():
        for lead in arr:
            yield tier, lead
    for lead in d.get("research", []):   # research leads can be marked applied in the UI too
        yield "research", lead

def preview(path=JOBS_DEFAULT):
    seen, wins, losses, skipped = _seen(), [], [], 0
    for tier, lead in _leads(path):
        out = str(lead.get("outcome", "")).strip().lower()
        if out not in SCORE: continue
        key = f"{lead.get('company')}|{lead.get('role')}|{out}"
        if key in seen: skipped += 1; continue
        move = _move(lead, tier)
        (wins if SCORE[out] > 0 else losses).append({"company": lead.get("company"), "move": move, "outcome": out})
    return {"would_win": wins, "would_loss": losses, "already_counted": skipped}

def sync(path=JOBS_DEFAULT):
    seen = _seen()
    wins, losses, note_by = [], [], {}
    for tier, lead in _leads(path):
        out = str(lead.get("outcome", "")).strip().lower()
        if out not in SCORE: continue
        key = f"{lead.get('company')}|{lead.get('role')}|{out}"
        if key in seen: continue
        move = _move(lead, tier)
        (wins if SCORE[out] > 0 else losses).append(move)
        note_by[move] = f"{lead.get('company')}: {out} via {move}"
        seen.add(key)
    for m in wins:   L.rate(m, 1.0, note_by.get(m, "pipeline"))
    for m in losses: L.rate(m, -0.5, note_by.get(m, "pipeline"))
    _save_seen(seen)
    learned = L.learn(); skills = C.S.extract()
    return {"rated_wins": wins, "rated_losses": losses,
            "signals_now": list(learned.get("signals", {}).keys()), "skills": skills}

def set_outcome(company, outcome, channel=None, path=JOBS_DEFAULT):
    """Surgical record of a real outcome on a lead — preserves the rest of the file."""
    outcome = outcome.strip().lower()
    if outcome not in SCORE: return {"error": f"outcome must be one of {list(SCORE)}"}
    d = json.load(open(path))
    hit = None
    arrays = list(d.get("tiers", {}).values()) + [d.get("research", [])]  # incl. research leads
    for arr in arrays:
        for lead in arr:
            if str(lead.get("company", "")).lower() == company.strip().lower():
                lead["outcome"] = outcome
                lead["outcomeOn"] = time.strftime("%Y-%m-%d")
                if channel: lead["channel"] = channel
                hit = lead.get("company"); break
        if hit: break
    if not hit: return {"error": f"no lead matching company '{company}'"}
    d["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    json.dump(d, open(path, "w"), indent=1, ensure_ascii=False)
    return {"set": hit, "outcome": outcome, "channel": channel}

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    if a[0] == "sync":     print(json.dumps(sync(a[1] if len(a) > 1 else JOBS_DEFAULT), indent=1))
    elif a[0] == "preview": print(json.dumps(preview(a[1] if len(a) > 1 else JOBS_DEFAULT), indent=1))
    elif a[0] == "set" and len(a) >= 3:
        # set <company> <outcome> [channel] [path]  (channel "" = none)
        chan = a[3] if len(a) > 3 and a[3] else None
        path = a[4] if len(a) > 4 else JOBS_DEFAULT
        print(json.dumps(set_outcome(a[1], a[2], chan, path), indent=1))
    else: print(__doc__)
