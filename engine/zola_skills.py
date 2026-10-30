#!/usr/bin/env python3
"""
ZOLA SKILLS — Hermes's "Skills" pillar, evidence-backed + with decay.

A skill is a learned MOVE that reliably closes a workstream. It is NOT authored
by hand and it is NOT immortal:
  • BORN     from a reinforced outcome in zola_learn (verdict=reinforce)
  • MOVE     text comes from the rating note (real evidence, never fabricated)
  • SHAPE    classified via zola_lens
  • STATUS   candidate (n<3) -> proven (n>=3) -> retired (verdict flips to avoid)
  • PLAYBOOK once PROVEN, a skill wants its concrete steps + template attached
             (move-now, playbook-when-proven — the ZOLA analog of Hermes' procedural skill)
  • MATCH    surfaced on a new task by shape + keyword overlap ("push", proven only)
  • GAP      a task with no proven skill + no signal = a capability gap to design + test

No LLM at runtime. Store: ~/.zola/skills.jsonl. Isolate tests with ZOLA_LEARN_DIR.

  python3 zola_skills.py extract                     # promote/decay skills from zola_learn
  python3 zola_skills.py list                        # all skills + status
  python3 zola_skills.py match "<task>"              # proven skills that fire on this task (the push)
  python3 zola_skills.py playbook <id> "s1|s2" ["tmpl"]  # attach steps+template to a proven skill
  python3 zola_skills.py gap "<task>"                # capability gap? (Hermes' Identification stage)
"""
import json, os, sys, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zola_learn as L

def _wb(task_l, phrase):
    """Word-boundary match — 'dm' must not fire inside 'admin', 'reach' not inside 'breach'."""
    return re.search(r"\b" + re.escape(phrase.lower()) + r"\b", task_l) is not None
try: import zola_lens as LENS
except Exception: LENS = None

ZDIR   = L.ZDIR
SKILLS = os.path.join(ZDIR, "skills.jsonl")
PROVEN_N = 3

def _read(): return L._read_jsonl(SKILLS)
def _write(rows):
    os.makedirs(ZDIR, exist_ok=True)
    with open(SKILLS, "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")

def _last_note(target):
    note = ""
    for r in L._read_jsonl(L.RATINGS):
        if r.get("target") == target and r.get("note"): note = r["note"]
    return note

def _shape(target):
    return LENS.classify(target.replace("_", " ")) if LENS else "unclassified"

# Domain aliases: the phrasings a move is really known by, so the deterministic matcher
# survives paraphrase ("approach the role" -> cold_apply). Curated for ZOLA's real moves;
# unknown moves fall back to their own name tokens. This is the offline fallback — the
# agentic shell (chat/relay) does the nuanced semantic match on top (see moves_for_agent).
ALIASES = {
    "warm_intro":      ["warm intro", "intro", "introduction", "referral", "refer", "network", "networking",
                        "mutual", "connection", "get introduced", "who do i know", "reach out through"],
    "cold_apply":      ["cold apply", "apply", "application", "applying", "approach", "go for the role",
                        "job board", "careers page", "submit", "postings", "openings", "get in front of"],
    "cold_dm":         ["cold dm", "dm", "message", "cold email", "cold outreach", "reach out cold",
                        "linkedin message", "slide into", "hit up"],
    "referral":        ["referral", "refer", "get referred", "internal referral"],
    "content_inbound": ["content", "post", "posting", "publish", "portfolio", "behance", "inbound",
                        "let them come", "put work out", "share my work"],
    "ship_case_study": ["case study", "ship the case study", "publish the case study", "behance case"],
}
def _aliases_for(skill):
    # curated phrases are distinctive; bare name-splits (e.g. "cold") are ambiguous across moves,
    # so only fall back to them when a move has NO curated aliases.
    tgt = skill["id"].replace("skill_", "")
    if tgt in ALIASES:
        al = list(ALIASES[tgt]) + [skill.get("name", "").lower()]
    else:
        al = skill.get("name", "").lower().split() + [w for w in skill.get("when", []) if len(w) > 2]
    al += list(skill.get("aliases", []))            # any learned/attached aliases
    return list({a.lower() for a in al if a and len(a) > 2})

def _alias_hit(task_l, skill):
    return [a for a in _aliases_for(skill) if _wb(task_l, a)]

def _target_alias_hit(task_l, target):
    if target in ALIASES:
        al = list(ALIASES[target]) + [target.replace("_", " ")]
    else:
        al = target.replace("_", " ").split() + [target.replace("_", " ")]
    return any(_wb(task_l, a) for a in al if len(a) > 2)

def extract():
    """Promote reinforced outcomes to skills; decay ones that turned bad. Returns a summary."""
    try: learned = json.load(open(L.LEARNED)).get("signals", {})
    except Exception: learned = {}
    skills = {s["id"]: s for s in _read()}
    born, promoted, retired = [], [], []
    for target, sig in learned.items():
        sid = "skill_" + target
        move = _last_note(target) or "(no captured move — add a note when you rate)"
        if sig["verdict"] == "reinforce":
            new = "proven" if sig["n"] >= PROVEN_N else "candidate"
            if sid not in skills:
                skills[sid] = {"id": sid, "name": target.replace("_", " "), "shape": _shape(target),
                               "when": target.replace("_", " ").split(), "move": move,
                               "evidence_n": sig["n"], "confidence": sig["bias"], "status": new,
                               "playbook": {"steps": [], "template": ""},
                               "needs_playbook": new == "proven",
                               "uses": 0, "created": time.strftime("%Y-%m-%d")}
                born.append(sid)
            else:
                s = skills[sid]; s["evidence_n"] = sig["n"]; s["confidence"] = sig["bias"]; s["move"] = move or s["move"]
                if s["status"] != new and new == "proven": promoted.append(sid)
                s["status"] = new
                s.setdefault("playbook", {"steps": [], "template": ""})
                # proven skill with no steps yet -> flag it wants a playbook (the move->playbook prompt)
                s["needs_playbook"] = (new == "proven" and not s["playbook"]["steps"])
        elif sig["verdict"] == "avoid" and sid in skills:
            skills[sid]["status"] = "retired"; retired.append(sid)
    _write(list(skills.values()))
    return {"born": born, "promoted": promoted, "retired": retired, "total": len(skills)}

def match(task, proven_only=True):
    task_l = task.lower()
    shape = LENS.classify(task) if LENS else None
    out = []
    for s in _read():
        if proven_only and s.get("status") != "proven": continue
        hits = _alias_hit(task_l, s)                          # name tokens + domain aliases (word-boundary)
        # alias hit is the trigger. shape only DISAMBIGUATES among alias hits — it never triggers
        # on its own (a Black question like "data breach policy" must NOT surface an outreach move).
        if hits:
            pb = s.get("playbook") or {}
            out.append({"skill": s["name"], "move": s["move"], "why": "alias:" + ",".join(sorted(hits)[:3]),
                        "confidence": s.get("confidence"), "_shape_bonus": 1 if (shape and s.get("shape") == shape) else 0,
                        "playbook": pb.get("steps") or None, "template": pb.get("template") or None})
    out.sort(key=lambda x: (-(x.get("_shape_bonus", 0)), -(x.get("confidence") or 0)))
    for o in out: o.pop("_shape_bonus", None)
    return out

def set_playbook(skill_id, steps, template=""):
    """Attach the concrete how (steps + template) to a proven skill — the move->playbook step."""
    rows = _read(); hit = None
    for s in rows:
        if s.get("id") == skill_id or s.get("name") == skill_id:
            s["playbook"] = {"steps": [x.strip() for x in steps if x.strip()], "template": template}
            s["needs_playbook"] = False
            hit = s["id"]; break
    if not hit: return {"error": f"no skill '{skill_id}'"}
    _write(rows)
    return {"skill": hit, "playbook_steps": len(steps)}

def gaps(task=None):
    """Hermes 'Identification': a task with no proven skill AND no learned signal = a capability gap.
    With no task, returns proven skills still missing a playbook (the standing to-design list)."""
    if task:
        proven_hit = [m for m in match(task, proven_only=True)]
        if proven_hit: return {"task": task, "gap": False, "have": proven_hit}
        shape = LENS.classify(task) if LENS else "unclassified"
        return {"task": task, "gap": True, "shape": shape,
                "note": f"no proven move for this ({shape}) — design one, run it, capture the outcome"}
    return {"needs_playbook": [s["id"] for s in _read() if s.get("needs_playbook")]}

def advise(task):
    """CLOSE THE LOOP: turn learned signals into a directive decision that CHANGES as evidence
    changes. Recommends the best proven move (+ its playbook), warns off moves the loop has
    learned to avoid, or declares a capability gap. This is recall feeding the next decision —
    not a scoreboard. Pure read of learned.json/skills.jsonl; no LLM."""
    try: signals = json.load(open(L.LEARNED)).get("signals", {})
    except Exception: signals = {}
    task_l = task.lower()
    def _relevant(target):  # does this learned target overlap the task? (name tokens OR domain aliases)
        return _target_alias_hit(task_l, target)
    def _surv(target):  # survivorship correction — the honest floor + read, never crash if module absent
        try:
            import zola_survivorship as SV
            return SV.move_view(target)
        except Exception:
            return None
    proven = match(task, proven_only=True)
    avoid = [t for t, s in signals.items() if s.get("verdict") == "avoid" and _relevant(t)]
    if proven:
        best = proven[0]
        tgt = best["skill"].replace(" ", "_")
        sv = _surv(tgt)
        return {"task": task, "decision": "USE", "move": best["skill"],
                "because": f"proven by real outcomes (confidence {best.get('confidence')})",
                "playbook": best.get("playbook"), "template": best.get("template"),
                "survivorship": sv, "avoid": avoid or None}
    # thin-but-real: a positive signal that hasn't hit proven (n<3) yet — surface it honestly, don't hide it
    lean = [(t, s) for t, s in signals.items() if s.get("verdict") == "reinforce" and _relevant(t)]
    if lean:
        lean.sort(key=lambda x: -x[1].get("n", 0)); t, s = lean[0]
        sv = _surv(t)
        return {"task": task, "decision": "LEAN", "move": t.replace("_", " "),
                "because": f"early real signal (n={s.get('n')}, not proven yet — needs {max(0,3-s.get('n',0))} more)",
                "survivorship": sv, "avoid": avoid or None}
    shape = LENS.classify(task) if LENS else "unclassified"
    if avoid:
        return {"task": task, "decision": "AVOID-ONLY", "move": None,
                "because": f"the loop has learned to avoid {avoid} here, but nothing proven yet",
                "avoid": avoid, "next": f"design a different ({shape}) move, run it, capture the outcome"}
    return {"task": task, "decision": "GAP", "move": None, "shape": shape,
            "because": "no proven move and no signal — capability gap",
            "next": "design one, run it once, record the outcome so the loop can learn"}

def moves_for_agent():
    """The agentic-shell contract: hand a chat/relay the learned moves in compact form so IT
    can do the nuanced semantic match a keyword matcher can't. The deterministic core learns +
    exposes; the agentic shell reasons. Pair with advise() to confirm the mechanical verdict."""
    try: signals = json.load(open(L.LEARNED)).get("signals", {})
    except Exception: signals = {}
    moves = []
    for s in _read():
        tgt = s["id"].replace("skill_", "")
        sig = signals.get(tgt, {})
        moves.append({"move": tgt, "name": s.get("name"), "status": s.get("status"),
                      "verdict": sig.get("verdict"), "n": sig.get("n"), "confidence": s.get("confidence"),
                      "shape": s.get("shape"), "aliases": _aliases_for(s)[:12],
                      "playbook": (s.get("playbook") or {}).get("steps") or None,
                      "evidence": s.get("move")})
    # learned targets that never became skills (thin signals) still matter to an agent
    for tgt, sig in signals.items():
        if not any(m["move"] == tgt for m in moves):
            moves.append({"move": tgt, "name": tgt.replace("_", " "), "status": "signal-only",
                          "verdict": sig.get("verdict"), "n": sig.get("n"),
                          "aliases": (ALIASES.get(tgt, []) or tgt.replace("_", " ").split())[:12]})
    return {"how": "read these moves, map the user's question to the best-fitting one by MEANING "
                   "(not keywords), then call advise(task) to confirm status/verdict before recommending.",
            "moves": sorted(moves, key=lambda m: -(m.get("confidence") or 0))}

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    if a[0] == "extract": print(json.dumps(extract(), indent=1))
    elif a[0] == "list": print(json.dumps(_read(), indent=1))
    elif a[0] == "match" and len(a) > 1: print(json.dumps(match(" ".join(a[1:])), indent=1))
    elif a[0] == "advise" and len(a) > 1: print(json.dumps(advise(" ".join(a[1:])), indent=1))
    elif a[0] == "playbook" and len(a) >= 3:
        print(json.dumps(set_playbook(a[1], a[2].split("|"), a[3] if len(a) > 3 else ""), indent=1))
    elif a[0] == "gap": print(json.dumps(gaps(" ".join(a[1:]) or None), indent=1))
    elif a[0] == "moves": print(json.dumps(moves_for_agent(), indent=1))
    else: print(__doc__)
