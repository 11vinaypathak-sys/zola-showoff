#!/usr/bin/env python3
"""
ZOLA FIN CONFIRM — chat-based confirmation for a Move, writing the SAME store the
in-app checkbox writes (zola-data.json -> nodes.finance.plan). This is the "tell me
you did it" half of the accountability loop: if you mention in chat "I bought SBI
Contra on Aug 20", Claude runs this to log it. If you never say it, it stays open —
nothing is silently assumed done, matching the in-app confirm-or-missed rule.

  python3 zola_fin_confirm.py list                              # moves + status + due
  python3 zola_fin_confirm.py done "<name substring>" <YYYY-MM-DD>   # confirm done
  python3 zola_fin_confirm.py due "<name substring>" <YYYY-MM-DD>    # set/replace deadline
  python3 zola_fin_confirm.py status "<name substring>" <planned|active|watch|done>

Matches by case-insensitive substring against the move's name (fails loudly with
close-match suggestions if ambiguous or not found — never guesses silently).
Backs up before writing; atomic write. Never touches anything else in zola-data.json.
"""
import json, os, sys, time, shutil

ZOLA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ZOLA_DIR, "zola-data.json")

def _load():
    return json.load(open(DATA, encoding="utf-8"))

def _save(d):
    bkdir = os.path.expanduser("~/.zola/backups"); os.makedirs(bkdir, exist_ok=True)
    if os.path.exists(DATA):
        shutil.copyfile(DATA, os.path.join(bkdir, "zola-data.json." + time.strftime("%Y%m%d-%H%M%S") + ".finconfirm.bak"))
    tmp = DATA + ".tmp"
    json.dump(d, open(tmp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    os.replace(tmp, DATA)

def _plan(d):
    return d.setdefault("nodes", {}).setdefault("finance", {}).setdefault("plan", [])

def _find(plan, name_sub):
    name_sub = name_sub.strip().lower()
    hits = [p for p in plan if name_sub in (p.get("name") or "").lower()]
    return hits

def list_moves():
    d = _load()
    for p in _plan(d):
        print(f"  {p.get('name'):30} status={p.get('status'):8} due={p.get('due') or '-':10} confirmedOn={p.get('confirmedOn') or '-'}")

def _resolve(name_sub):
    d = _load()
    plan = _plan(d)
    hits = _find(plan, name_sub)
    if not hits:
        print(json.dumps({"error": f"no move matching '{name_sub}'", "moves": [p.get("name") for p in plan]}))
        sys.exit(1)
    if len(hits) > 1:
        print(json.dumps({"error": f"ambiguous — {len(hits)} moves match '{name_sub}'", "matches": [p.get("name") for p in hits]}))
        sys.exit(1)
    return d, plan, hits[0]

def confirm_done(name_sub, date):
    d, plan, p = _resolve(name_sub)
    p["status"] = "done"
    p["confirmedOn"] = date
    _save(d)
    return {"confirmed": p["name"], "status": "done", "on": date}

def set_due(name_sub, date):
    d, plan, p = _resolve(name_sub)
    p["due"] = date
    _save(d)
    return {"move": p["name"], "due": date}

def set_status(name_sub, status):
    if status not in ("planned", "active", "watch", "done"):
        return {"error": "status must be planned|active|watch|done"}
    d, plan, p = _resolve(name_sub)
    p["status"] = status
    if status != "done":
        p.pop("confirmedOn", None)
    _save(d)
    return {"move": p["name"], "status": status}

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    c = a[0]
    if c == "list": list_moves()
    elif c == "done" and len(a) >= 3: print(json.dumps(confirm_done(a[1], a[2]), indent=1))
    elif c == "due" and len(a) >= 3: print(json.dumps(set_due(a[1], a[2]), indent=1))
    elif c == "status" and len(a) >= 3: print(json.dumps(set_status(a[1], a[2]), indent=1))
    else: print(__doc__)
