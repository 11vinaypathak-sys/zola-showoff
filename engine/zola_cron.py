#!/usr/bin/env python3
"""
ZOLA CRON — the 5th Hermes pillar, ZOLA-shaped: SCRIPT-ONLY, deterministic, $0.

Flips ZOLA from reactive to proactive WITHOUT an LLM at runtime. Two built-in jobs:
  loop_refresh  - pipeline sync -> learn -> extract -> gaps digest (job-search loop)
  finance_scan  - market fetch -> risk/finance READ -> next-actions digest (6h cadence,
                  NOT hourly - an hourly market-watch would itself be scope inflation
                  against the "rules-based, quarterly-rebalance, informs-never-trades"
                  guardrail; this just keeps the READ from going silently stale)
The agentic shell (Claude/relay) only enters when YOU open a chat. Matches the
"deterministic core, agentic shell" doctrine and keeps cost + hoax-risk at zero.

Shaped after Hermes' cron (jobs.json · tick · lock · fresh run · last_status) but
built-in jobs only — NO arbitrary code, NO cron-creates-cron, NO network.

  python3 zola_cron.py tick [--force]     # run due jobs (the ticker calls this)
  python3 zola_cron.py list               # jobs + next_run + last_status
  python3 zola_cron.py run <id>           # run one job now
  python3 zola_cron.py enable|disable <id>
  python3 zola_cron.py kill on|off        # master killswitch
  python3 zola_cron.py status             # last digest

State: ~/.zola/cron.json · lock ~/.zola/cron.lock · digest ~/.zola/loop_digest.json.
Isolate tests with ZOLA_LEARN_DIR.
"""
import json, os, sys, time, fcntl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zola_learn as L

ZDIR   = L.ZDIR
CRON   = os.path.join(ZDIR, "cron.json")
LOCK   = os.path.join(ZDIR, "cron.lock")
DIGEST = os.path.join(ZDIR, "loop_digest.json")
FIN_DIGEST = os.path.join(ZDIR, "finance_digest.json")
ENGDIR = os.path.dirname(os.path.abspath(__file__))
JOBS_JSON = os.path.join(os.path.dirname(ENGDIR), "zola-jobs.json")

def _default():
    return {"killswitch": False, "tick_seconds": 300, "jobs": [
        {"id": "loop_refresh", "name": "Refresh the self-improving loop", "builtin": "loop_refresh",
         "interval_seconds": 10800, "enabled": True,
         "next_run_at": 0, "last_run_at": 0, "last_status": None, "run_count": 0},
        # 6h cadence, NOT hourly — an hourly market-watch would contradict the rules-based,
        # quarterly-rebalance, no-idle-cash guardrail (informs judgment, never trades).
        {"id": "finance_scan", "name": "Scan market + recompute the finance risk read", "builtin": "finance_scan",
         "interval_seconds": 21600, "enabled": True,
         "next_run_at": 0, "last_run_at": 0, "last_status": None, "run_count": 0},
        # Daily, not hourly: ATS boards move on a days cadence. The point is a pipeline
        # that cannot silently dry up again (it sat dead 07 Sep -> 09 Oct), not a ticker.
        {"id": "job_scan", "name": "Scout NL sponsor boards + merge new openings", "builtin": "job_scan",
         "interval_seconds": 86400, "enabled": True,
         "next_run_at": 0, "last_run_at": 0, "last_status": None, "run_count": 0}]}

def _load():
    try:
        d = json.load(open(CRON))
        d.setdefault("killswitch", False); d.setdefault("tick_seconds", 300); d.setdefault("jobs", [])
    except Exception:
        return _default()
    # migrate: any new built-in job (e.g. finance_scan added later) merges into an
    # existing store automatically, without touching jobs already present/customized.
    have = {j["id"] for j in d["jobs"]}
    for job in _default()["jobs"]:
        if job["id"] not in have:
            d["jobs"].append(job)
    return d

def _save(d):
    os.makedirs(ZDIR, exist_ok=True)
    tmp = CRON + ".tmp"
    with open(tmp, "w") as f: json.dump(d, f, indent=1)
    os.replace(tmp, CRON)  # atomic

def _log(event, detail):
    try:
        os.makedirs(ZDIR, exist_ok=True)
        with open(os.path.join(ZDIR, "events.jsonl"), "a") as f:
            f.write(json.dumps({"ts": time.time(), "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                "job": "cron", "event": event, "level": "info", "detail": detail}) + "\n")
    except Exception: pass

# ── built-in jobs (deterministic; the only things a cron may run) ──
def _builtin_loop_refresh():
    """pipeline sync -> learn -> extract -> gaps digest. Pure deterministic engine calls."""
    import zola_skills as S
    summary = {"pipeline": None, "signals": 0, "proven": 0, "gaps": []}
    try:
        import zola_pipeline as P
        if os.path.exists(JOBS_JSON):
            summary["pipeline"] = P.sync(JOBS_JSON)  # feeds any newly-recorded outcomes
    except Exception as e:
        summary["pipeline"] = {"error": str(e)[:80]}
    learned = L.learn()
    S.extract()
    sigs = learned.get("signals", {})
    skills = S._read()
    prev = {}
    try: prev = json.load(open(DIGEST))
    except Exception: pass
    digest = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "signals": len(sigs),
              "reinforce": [k for k, v in sigs.items() if v.get("verdict") == "reinforce"],
              "avoid": [k for k, v in sigs.items() if v.get("verdict") == "avoid"],
              "proven": [s["name"] for s in skills if s.get("status") == "proven"],
              "needs_playbook": [s["name"] for s in skills if s.get("needs_playbook")]}
    # what CHANGED since last refresh (honest signal, no fabrication)
    def _delta(k): return sorted(set(digest.get(k, [])) - set(prev.get(k, [])))
    digest["changed"] = {k: _delta(k) for k in ("proven", "avoid", "reinforce")
                         if _delta(k)}
    os.makedirs(ZDIR, exist_ok=True)
    json.dump(digest, open(DIGEST, "w"), indent=1)
    summary["signals"] = digest["signals"]; summary["proven"] = len(digest["proven"])
    summary["changed"] = digest["changed"]
    return summary

def _builtin_finance_scan():
    """The scheduled session: fetch -> risk -> finance READ -> a 'next actions' digest.
    Deterministic, no LLM, informs-never-trades (same doctrine as zola_risk/zola_finance).
    This is what makes the Finance node 'active' instead of static client-side logic."""
    import subprocess
    summary = {"fetch": None}
    try:
        r = subprocess.run(["python3", os.path.join(ENGDIR, "zola_fetch.py")],
                           capture_output=True, text=True, timeout=30, cwd=ENGDIR)
        summary["fetch"] = "ok" if r.returncode == 0 else ("error: " + r.stderr[:100])
    except Exception as e:
        summary["fetch"] = "error: " + str(e)[:100]

    # Refresh the fund-candidate universe too, so the game plan's BUY shortlists are
    # current without anyone pressing anything. Only the ARBITRAGE screen carries the
    # NAV-history metrics (--history costs ~36 API calls); index and overseas are
    # refreshed name-only, which is all their BUY lines need until he shortlists there.
    # Timeboxed and non-fatal: a screen failure must never block the risk recompute.
    # NAV history costs ~36 third-party calls per run, and NAVs publish only once a day
    # (~9-11pm IST) — so at a 6h cadence that would be 4x the requests for the same
    # numbers. The history refresh is therefore gated to once every ~20h; the cheap
    # name-only screens still run every cycle.
    summary["screens"] = {}
    # Gate on file CONTENT, not just mtime. A non-history run overwrites the file (and
    # therefore its mtime) with metrics-free candidates, so an mtime-only gate reads
    # that file as "freshly screened" and skips history for a further 20h — silently
    # erasing the numbers this whole feature exists to show. Recomputing history is
    # required whenever the file is missing, stale, OR simply lacks metrics already.
    # Freshness is decided PER CATEGORY. It used to be decided once, from the
    # arbitrage file, and applied to every category — so any category that was
    # behind could never catch up: arbitrage reads fresh, the gate closes, and the
    # stale one is skipped again on every subsequent run. gilt sat a month behind
    # that way. Each screen now answers for itself.
    def _wants_history(k):
        path = os.path.join(ENGDIR, "zola-screen-%s.local.json" % k)
        try:
            age = time.time() - os.path.getmtime(path)
            with open(path, encoding="utf-8") as f:
                cands = json.load(f).get("candidates") or []
        except (OSError, ValueError):
            return True                       # never screened — do the full run
        if not any("ret_3y" in c for c in cands):
            return True                       # metrics-free file, recompute
        return age > 20 * 3600

    for key, cat in (("arbitrage", "Arbitrage"),
                     ("index", "Index Funds - Equity"),
                     ("overseas", "FoF Overseas,Fund of Funds investing overseas"),
                     ("gilt", "Gilt")):
        # metrics for ALL four categories, not just arbitrage: every BUY line in the game
        # plan needs its own measured shortlist, otherwise the rest show a bare
        # alphabetical list. ~156 history calls total, gated to once every 20h.
        #
        # gilt was written as a screen but never added to this tuple, so it froze at
        # whatever the last manual run produced (2026-09-07) while the other three
        # refreshed daily. A stale screen that still renders is worse than a missing
        # one — it reports month-old yields as current.
        #
        # When metrics are still fresh, SKIP the subprocess entirely rather than running
        # a plain (non --history) refresh. A plain run's screen() rebuilds the whole
        # candidates list from AMFI with no ret_3y/vol_1y/max_dd fields at all — running
        # it "for the name/NAV update" would silently overwrite and erase the metrics
        # that were just computed, which is exactly the bug this gate exists to prevent.
        if not _wants_history(key):
            summary["screens"][key] = "skipped — metrics still fresh"
            continue
        cmd = ["python3", os.path.join(ENGDIR, "zola_screen.py"),
               "--category", cat, "--key", key, "--history"]
        try:
            rs = subprocess.run(cmd, capture_output=True, text=True, timeout=420, cwd=ENGDIR)
            summary["screens"][key] = "ok+metrics" if rs.returncode == 0 \
                else ("error: " + rs.stderr[:80])
        except Exception as e:
            summary["screens"][key] = "error: " + str(e)[:80]

    try:
        import zola_finance as F
        r = F.read()
    except Exception as e:
        # even if the fetch failed, still recompute off whatever data exists
        summary["error"] = str(e)[:160]
        r = None

    prev = {}
    try: prev = json.load(open(FIN_DIGEST))
    except Exception: pass

    if r is not None:
        top_name, top_amt, top_cls, top_share = r["top"]
        worst_name, worst_amt, worst_pct = r["worst"]
        actions = []
        if top_share >= 0.35:
            actions.append(f"Trim {top_name} — {top_share*100:.0f}% of portfolio (safe line 35%)")
        if worst_pct <= -0.10:
            actions.append(f"Worst-case exposure: {worst_name} ({worst_pct*100:.1f}% of portfolio) — size against it")
        if r.get("uncorr", 0) >= 0.5 and r.get("belief", 0) < 0.35:
            actions.append("Money is diversified but the FARM GOAL is underfunded — income, not reallocation, closes this")
        mkt = r.get("market") or {}
        headlines = sorted({t for n in (mkt.get("news", []) or []) for t in n.get("tags", [])})
        digest = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "portfolio_total": r["total"],
                  "belief": r["belief"], "top_holding": {"name": top_name, "share": round(top_share, 3)},
                  "worst_scenario": {"name": worst_name, "pct": round(worst_pct, 3)},
                  "regime": r.get("regime"), "uncorrelated_pct": round(r.get("uncorr", 0), 3),
                  "headline_tags": headlines, "next_actions": actions,
                  "fetch_status": summary["fetch"]}
        # what changed since the last scan (honest delta, no fabrication)
        prev_actions = set(prev.get("next_actions", []))
        digest["new_actions"] = [a for a in actions if a not in prev_actions]
        digest["resolved_actions"] = [a for a in prev.get("next_actions", []) if a not in actions]
        os.makedirs(ZDIR, exist_ok=True)
        json.dump(digest, open(FIN_DIGEST, "w"), indent=1)
        summary["actions"] = len(actions); summary["new_actions"] = digest["new_actions"]
        summary["belief"] = r["belief"]
    return summary

def _builtin_job_scan():
    """Daily Black-node pipeline feed: run the sanctioned ATS scout (additive merge,
    backup-first, atomic — zola_jobscout.run never blind-overwrites zola-jobs.json),
    then surface due follow-ups so nothing slips past its date silently."""
    summary = {}
    try:
        import zola_jobscout
        summary["scout"] = zola_jobscout.run()
    except Exception as e:
        summary["scout"] = "error: " + str(e)[:120]
    # follow-up sweep: list leads whose followup_due is today or past, never auto-acts
    try:
        import time as _t
        d = json.load(open(JOBS_JSON))
        today = _t.strftime("%Y-%m-%d")
        due = [dict(company=j.get("company"), role=j.get("role"),
                    due=j.get("followup_due"), status=j.get("status"))
               for j in d.get("research", [])
               if j.get("followup_due") and str(j["followup_due"])[:10] <= today
               and j.get("status") not in ("replied", "dead", "closed")]
        summary["followups_due"] = due
        # drop a tiny digest file for autopilot/UI to read — engine writes, UI reads
        json.dump({"ts": _t.strftime("%Y-%m-%d %H:%M"), "due": due},
                  open(os.path.join(os.path.dirname(ENGDIR), "zola-jobs-due.local.json"), "w"),
                  indent=1)
    except Exception as e:
        summary["followups_due"] = "error: " + str(e)[:120]
    return summary

BUILTINS = {"loop_refresh": _builtin_loop_refresh, "finance_scan": _builtin_finance_scan,
            "job_scan": _builtin_job_scan}

def _run_job(job):
    fn = BUILTINS.get(job.get("builtin"))
    if not fn: return {"error": "unknown builtin " + str(job.get("builtin"))}
    return fn()

def tick(force=False):
    """The 60s-style tick, but cheap: take the lock, run due enabled jobs, update next_run."""
    d = _load()
    if d.get("killswitch"):
        return {"skipped": "killswitch on"}
    os.makedirs(ZDIR, exist_ok=True)
    lf = open(LOCK, "w")
    try:
        fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)  # no overlapping ticks
    except BlockingIOError:
        return {"skipped": "another tick holds the lock"}
    ran = []
    try:
        now = time.time()
        for job in d["jobs"]:
            if not job.get("enabled"): continue
            if not force and now < job.get("next_run_at", 0): continue
            job["state"] = "running"
            try:
                res = _run_job(job); status = "ok"
            except Exception as e:
                res = {"error": str(e)[:120]}; status = "error"
            job["last_run_at"] = now
            job["last_status"] = status
            job["run_count"] = job.get("run_count", 0) + 1
            job["next_run_at"] = now + job.get("interval_seconds", 10800)
            job["state"] = "scheduled"
            _log("job_run", {"id": job["id"], "status": status, "result": res})
            ran.append({"id": job["id"], "status": status, "result": res})
        _save(d)
    finally:
        fcntl.flock(lf, fcntl.LOCK_UN); lf.close()
    return {"ran": ran, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}

def _find(d, jid):
    for j in d["jobs"]:
        if j["id"] == jid: return j
    return None

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    c = a[0]
    if c == "tick": print(json.dumps(tick("--force" in a), indent=1))
    elif c == "list":
        d = _load()
        for j in d["jobs"]:
            nxt = j.get("next_run_at", 0)
            due = "due now" if nxt <= time.time() else time.strftime("%H:%M:%S", time.localtime(nxt))
            print(f"  {j['id']}: {'on' if j.get('enabled') else 'OFF'} · every {j.get('interval_seconds',0)//3600}h · "
                  f"last={j.get('last_status')} · runs={j.get('run_count',0)} · next={due}")
        print(f"  [killswitch: {'ON' if d.get('killswitch') else 'off'} · tick every {d.get('tick_seconds')}s]")
    elif c == "run" and len(a) > 1:
        d = _load(); j = _find(d, a[1])
        if not j:
            print(json.dumps({"error": "no job " + a[1]}))
        else:
            now = time.time()
            try:
                res = _run_job(j); status = "ok"
            except Exception as e:
                res = {"error": str(e)[:120]}; status = "error"
            # manual run still updates bookkeeping (last_run_at/status) so the UI/`list`
            # reflects it, without touching next_run_at's schedule position
            j["last_run_at"] = now; j["last_status"] = status; j["run_count"] = j.get("run_count", 0) + 1
            _save(d); _log("job_run_manual", {"id": j["id"], "status": status})
            print(json.dumps(res, indent=1))
    elif c in ("enable", "disable") and len(a) > 1:
        d = _load(); j = _find(d, a[1])
        if j: j["enabled"] = (c == "enable"); _save(d); print(json.dumps({"id": a[1], "enabled": j["enabled"]}))
        else: print(json.dumps({"error": "no job " + a[1]}))
    elif c == "kill" and len(a) > 1:
        d = _load(); d["killswitch"] = (a[1] == "on"); _save(d); print(json.dumps({"killswitch": d["killswitch"]}))
    elif c == "status":
        which = a[1] if len(a) > 1 else "loop"
        path = FIN_DIGEST if which == "finance" else DIGEST
        try: print(json.dumps(json.load(open(path)), indent=1))
        except Exception: print(json.dumps({"digest": "none yet — run a tick"}))
    else: print(__doc__)
