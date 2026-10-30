#!/usr/bin/env python3
"""ZOLA server (Python port). Serves the Zola app if the repo is cloned
alongside this file; otherwise serves a setup-status page on port 3737."""
import json
import os
import re
import urllib.request
import urllib.parse
from http.server import HTTPServer, ThreadingHTTPServer, SimpleHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
# ~/Zola by default. ZOLA_DIR=<path> points a second instance at a git worktree,
# so a branch can be run and looked at before it is merged — the companion to
# --port, which already exists for exactly that "run it alongside" case.
ZOLA_DIR = os.path.abspath(os.path.expanduser(
    os.environ.get("ZOLA_DIR") or "~/Zola"))
def _port():
    """3737 by default; --port=N or ZOLA_PORT runs a second instance alongside it."""
    import sys as _s
    for a in _s.argv[1:]:
        if a.startswith("--port="):
            return int(a.split("=", 1)[1])
    return int(os.environ.get("ZOLA_PORT", "3737"))


PORT = _port()

# Files the CMS control panel may read/write. Exact names only — no path traversal.
CMS_WHITELIST = {
    "zola-data.json", "zola-white.local.json", "zola-ds-library.local.json",
    "zola-intel.local.json", "zola-exit.local.json", "zola-brain.local.json",
    "zola-inbox.local.json", "zola-ds-learnings.local.json",
    "zola-brief.local.json", "zola-profile.local.json", "zola-command.local.json",
    "zola-blue-ship.local.json", "zola-ds-projects.local.json", "zola-finance-assets.local.json",
}


def _get_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ZOLA)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def finance_quotes(qs):
    """Live prices for the Finance node. crypto=CoinGecko, mf=mfapi.in, eq=Yahoo (best-effort).
    Returns {crypto:{id:{inr,chg}}, equity:{ticker:{price,prev}}, mf:{code:{nav}}}."""
    p = urllib.parse.parse_qs(qs)
    crypto_ids = [x for x in p.get("crypto", [""])[0].split(",") if x]
    eqs = [x for x in p.get("eq", [""])[0].split(",") if x]
    mfs = [x for x in p.get("mf", [""])[0].split(",") if x]
    out = {"crypto": {}, "equity": {}, "mf": {}}
    if crypto_ids:
        try:
            ids = ",".join(crypto_ids)
            d = _get_json("https://api.coingecko.com/api/v3/simple/price?ids=" + ids +
                          "&vs_currencies=inr&include_24hr_change=true")
            for k, v in d.items():
                out["crypto"][k] = {"inr": v.get("inr", 0), "chg": v.get("inr_24h_change", 0)}
        except Exception:
            pass
    for code in mfs:
        try:
            d = _get_json("https://api.mfapi.in/mf/" + urllib.parse.quote(code))
            data = d.get("data") or []
            if len(data) >= 2:
                nav = float(data[0]["nav"]); prev = float(data[1]["nav"])
                chg = ((nav - prev) / prev * 100) if prev else 0
                out["mf"][code] = {"nav": nav, "prev": prev, "chg": chg}
            elif data:
                out["mf"][code] = {"nav": float(data[0]["nav"]), "chg": 0}
        except Exception:
            pass
    for t in eqs:
        try:
            d = _get_json("https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(t))
            meta = d["chart"]["result"][0]["meta"]
            out["equity"][t] = {"price": meta.get("regularMarketPrice", 0),
                                 "prev": meta.get("chartPreviousClose") or meta.get("previousClose") or 0}
        except Exception:
            pass
    import time
    out["ts"] = int(time.time() * 1000)
    return out


def market_history(qs):
    """Daily OHLC for the candlestick chart + holding sparklines (Yahoo)."""
    p = urllib.parse.parse_qs(qs)
    sym = p.get("sym", [""])[0]
    rng = p.get("range", ["3mo"])[0]
    if not sym:
        return {"ok": False}
    try:
        d = _get_json("https://query1.finance.yahoo.com/v8/finance/chart/" +
                      urllib.parse.quote(sym) + "?range=" + urllib.parse.quote(rng) + "&interval=1d")
        res = d["chart"]["result"][0]
        ts = res.get("timestamp", []) or []
        q = res["indicators"]["quote"][0]
        o, h, l, c = q.get("open", []), q.get("high", []), q.get("low", []), q.get("close", [])
        T, O, H, L, C = [], [], [], [], []
        for i in range(len(c)):
            if i >= len(o) or c[i] is None or o[i] is None:
                continue
            T.append(ts[i]); O.append(o[i]); H.append(h[i]); L.append(l[i]); C.append(c[i])
        return {"ok": True, "sym": sym, "t": T, "o": O, "h": H, "l": L, "c": C}
    except Exception:
        return {"ok": False}

STATUS_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>ZOLA — setup pending</title>
<style>
body{background:#0a0a0f;color:#cfd6e4;font-family:ui-monospace,Menlo,monospace;
display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
.card{max-width:560px;padding:40px;border:1px solid #232a3a;border-radius:12px}
h1{color:#7aa2ff;font-size:20px;letter-spacing:.2em;margin:0 0 16px}
li{margin:10px 0;line-height:1.5}
code{background:#161c2a;padding:2px 6px;border-radius:4px;color:#9ecbff}
.done{color:#5dd39e}.todo{color:#e8b34b}
</style></head><body><div class="card">
<h1>ZOLA — ORBIT OFFLINE</h1>
<p>The server is running, but the Zola repo is not on this machine yet.</p>
<ol>
<li class="todo">Authenticate GitHub: <code>brew install gh &amp;&amp; gh auth login</code></li>
<li class="todo">Tell Claude to clone <code>1vinaypathak/Zola</code> and finish the Python port</li>
<li class="done">Server scaffold + launch config — done</li>
</ol>
<p>Once cloned, this page is replaced by the orbital system.</p>
</div></body></html>"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        directory = ZOLA_DIR if os.path.isdir(ZOLA_DIR) else HERE
        super().__init__(*args, directory=directory, **kwargs)

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # never cache the app — every reload serves the fresh build (kills stale-code reloads)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def _control_summary(self):
        """Unified state for the control plane: honest engine + every ZOLA node."""
        import glob, time
        zdir = os.path.expanduser("~/.zola")

        def _jsonl(path):
            out = []
            if os.path.exists(path):
                for line in open(path, encoding="utf-8"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
            return out

        events = _jsonl(os.path.join(zdir, "events.jsonl"))
        ratings = _jsonl(os.path.join(zdir, "ratings.jsonl"))
        good = len([r for r in ratings if r.get("rating") == 2])
        bad = len([r for r in ratings if r.get("rating") == 0])
        cands = sorted(glob.glob(os.path.join(zdir, "skillopt", "best_skill.*.md")))
        cyc = [e for e in events if e.get("event") == "cycle_done"]
        files = [
            ("finance", "zola-data.json", "Finance + core state"),
            ("white", "zola-white.local.json", "Studio career"),
            ("ds_library", "zola-ds-library.local.json", "DS foundation library"),
            ("radar", "zola-intel.local.json", "System / market radar"),
            ("exit", "zola-exit.local.json", "Exit job tracker"),
            ("brain", "zola-brain.local.json", "Second brain"),
            ("inbox", "zola-inbox.local.json", "Agent inbox"),
            ("ds_learnings", "zola-ds-learnings.local.json", "DS learnings network"),
        ]
        nodes = []
        for key, fn, desc in files:
            p = os.path.join(ZOLA_DIR, fn)
            ex = os.path.exists(p)
            nodes.append({"key": key, "file": fn, "desc": desc, "exists": ex,
                          "size": os.path.getsize(p) if ex else 0,
                          "updated": int(os.path.getmtime(p)) if ex else 0})
        return {"engine": {"events": len(events),
                           "last_cycle": (cyc[-1].get("iso") if cyc else None),
                           "ratings": len(ratings), "good": good, "bad": bad,
                           "candidates": [os.path.basename(c) for c in cands],
                           "recent": events[-8:][::-1]},
                "nodes": nodes, "ts": int(time.time() * 1000)}

    def _finance_summary(self):
        """Read-only readout of the finance_scan cron: the digest + when it last ran +
        the standing cadence. Never recomputes here — that's the cron's job (or the
        explicit ?scan=1 trigger in do_GET), so a page load stays instant."""
        zdir = os.path.expanduser("~/.zola")
        digest = {}
        try:
            digest = json.load(open(os.path.join(zdir, "finance_digest.json"), encoding="utf-8"))
        except Exception:
            pass
        last_run, interval, paused = None, None, False
        try:
            cj = json.load(open(os.path.join(zdir, "cron.json"), encoding="utf-8"))
            job = next((j for j in cj.get("jobs", []) if j.get("id") == "finance_scan"), None)
            if job:
                last_run = job.get("last_run_at"); interval = job.get("interval_seconds")
                paused = not job.get("enabled", True)  # per-job pause, not the global killswitch —
                # pausing Finance must not silently also pause the unrelated job-search loop
            paused = paused or bool(cj.get("killswitch"))  # global kill (if ever set) still shows as paused
        except Exception:
            pass
        return {"digest": digest, "last_run_at": last_run, "interval_seconds": interval, "paused": paused}

    def _loop_summary(self):
        """Read-only readout of the self-improving loop: learned signals + skills + open gaps.
        Reads the engine's own files (~/.zola) — never recomputes, never writes."""
        zdir = os.path.expanduser("~/.zola")
        learned = {}
        try:
            learned = json.load(open(os.path.join(zdir, "learned.json"), encoding="utf-8")).get("signals", {})
        except Exception:
            pass
        skills = []
        sp = os.path.join(zdir, "skills.jsonl")
        if os.path.exists(sp):
            for line in open(sp, encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    skills.append(json.loads(line))
                except Exception:
                    pass
        proven = [s for s in skills if s.get("status") == "proven"]
        best = sorted(proven, key=lambda s: -(s.get("confidence") or 0))[:5]
        digest = {}
        try:
            digest = json.load(open(os.path.join(zdir, "loop_digest.json"), encoding="utf-8"))
        except Exception:
            pass
        surv = {}
        try:
            import subprocess
            eng = os.path.join(ZOLA_DIR, "engine")
            r = subprocess.run(["python3", os.path.join(eng, "zola_survivorship.py")],
                               capture_output=True, text=True, timeout=8, cwd=eng)
            surv = json.loads(r.stdout or "{}")
        except Exception:
            pass
        return {
            "proven": [{"name": s["name"], "move": s.get("move"), "shape": s.get("shape"),
                        "confidence": s.get("confidence"),
                        "playbook": (s.get("playbook") or {}).get("steps") or None,
                        "needs_playbook": s.get("needs_playbook", False)} for s in best],
            "decaying": [s["name"] for s in skills if s.get("status") == "retired"],
            "candidates": [s["name"] for s in skills if s.get("status") == "candidate"],
            "needs_playbook": [s["name"] for s in skills if s.get("needs_playbook")],
            # Verdict ALONE is not enough to publish. A level-D signal is one
            # rating, or a verdict that flips when the newest rating is dropped;
            # surfacing it as "avoid" is how a single bad outcome becomes advice.
            # Trusted lists are level A/B only; the rest are carried separately
            # as provisional so nothing is hidden, just not acted on.
            "reinforce": [k for k, v in learned.items()
                          if v.get("verdict") == "reinforce"
                          and v.get("level", "D") in ("A", "B")],
            "avoid": [k for k, v in learned.items()
                      if v.get("verdict") == "avoid"
                      and v.get("level", "D") in ("A", "B")],
            # level defaults to "D" here for the same reason the filters above
            # default it: a learned.json written before levels existed must be
            # treated as untrusted, and the display must agree with the filter.
            "provisional": [{"target": k, "verdict": v.get("verdict"),
                             "level": v.get("level") or "D", "n": v.get("n"),
                             "warnings": v.get("warnings") or
                                         ["written before levels existed — re-run learn"]}
                            for k, v in learned.items()
                            if v.get("level", "D") not in ("A", "B")],
            "counts": {"skills": len(skills), "proven": len(proven), "signals": len(learned)},
            "last_refresh": digest.get("ts"), "changed": digest.get("changed") or None,
            # base_rate / verdict / actionable are the kernel additions: a move's
            # rate is only an edge if its interval EXCLUDES the pooled base rate.
            # Passing tried+untested alone would drop the one field that says
            # whether any of it is distinguishable from noise.
            "survivorship": {"tried": surv.get("tried", []),
                             "untested": surv.get("untested", []),
                             "base_rate": surv.get("base_rate"),
                             "actionable": surv.get("actionable", []),
                             "verdict": surv.get("verdict")},
        }

    # ── cockpit (the control board) ──
    def _cockpit_read(self):
        p = os.path.join(ZOLA_DIR, "zola-cockpit.local.json")
        if os.path.exists(p):
            try:
                return json.load(open(p, encoding="utf-8"))
            except Exception:
                pass
        return {"killswitch": False, "entities": {}, "dials": {}, "scenes": {}, "_undo": []}

    def _cockpit_write(self, d):
        with open(os.path.join(ZOLA_DIR, "zola-cockpit.local.json"), "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)

    def _cockpit_audit(self, event, detail):
        import time as _t
        try:
            ev = {"ts": _t.time(), "iso": _t.strftime("%Y-%m-%dT%H:%M:%S"),
                  "job": "cockpit", "event": event, "level": "info", "detail": detail}
            with open(os.path.expanduser("~/.zola/events.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(ev) + "\n")
        except Exception:
            pass

    def _body_json(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n)
            return json.loads(raw) if raw else {}
        except Exception:
            return {}

    def do_GET(self):
        if not os.path.isdir(ZOLA_DIR):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(STATUS_PAGE.encode())
            return
        if self.path.startswith("/api/quotes"):
            qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            try:
                self._json(finance_quotes(qs))
            except Exception:
                self._json({"crypto": {}, "equity": {}, "mf": {}})
            return
        if self.path.startswith("/api/history"):
            qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            try:
                self._json(market_history(qs))
            except Exception:
                self._json({"ok": False})
            return
        if self.path.startswith("/api/news"):
            import re, html
            qp = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            query = (qp.get("q") or ["Nifty OR Sensex OR silver price OR bitcoin OR IREDA OR India mutual fund"])[0]
            items = []
            try:
                url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ZOLA)"})
                xml = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", "ignore")
                for block in re.findall(r"<item>(.*?)</item>", xml, re.S)[:10]:
                    t = re.search(r"<title>(.*?)</title>", block, re.S)
                    l = re.search(r"<link>(.*?)</link>", block, re.S)
                    d = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
                    src = re.search(r"<source[^>]*>(.*?)</source>", block, re.S)
                    if t and l:
                        title = html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip()
                        items.append({"title": title, "link": l.group(1).strip(),
                                      "date": (d.group(1).strip() if d else ""),
                                      "source": (html.unescape(src.group(1)).strip() if src else "")})
            except Exception:
                items = []
            self._json({"items": items})
            return
        if self.path.startswith("/api/reason"):
            import subprocess
            q = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            engine = os.path.join(ZOLA_DIR, "engine", "zola-reason.py")
            cmd = ["python3", engine, "--json", q["q"][0]] if q.get("q") else ["python3", engine, "--state", "--json"]
            try:
                out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip() or "{}"
            except Exception:
                out = '{"error":"reason engine failed"}'
            body = out.encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith("/api/run"):
            import subprocess, datetime
            REPO = os.path.expanduser("~/zola-core")
            ran = []
            for script, to in (("zola_daemon.py", 20), ("zola_research.py", 15),
                               ("zola_command.py", 15), ("zola_fetch.py", 20)):
                try:
                    r = subprocess.run(["python3", os.path.join(REPO, script)],
                                       capture_output=True, text=True, timeout=to, cwd=REPO)
                    ran.append({"step": script[5:-3], "ok": r.returncode == 0})
                except Exception as e:
                    ran.append({"step": script[5:-3], "ok": False, "err": str(e)[:80]})
            body = json.dumps({"ran": ran, "at": datetime.datetime.now().isoformat(timespec="seconds")}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith("/api/ask"):
            import subprocess
            qs = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            q = (qs.get("q") or [""])[0].strip()
            REPO = os.path.expanduser("~/zola-core")
            if q:
                try:
                    subprocess.run(["python3", os.path.join(REPO, "zola_ask.py"), q],
                                   capture_output=True, text=True, timeout=25, cwd=REPO)
                except Exception:
                    pass
            try:
                with open(os.path.join(ZOLA_DIR, "zola-inbox.local.json")) as fh:
                    recent = (json.load(fh).get("asks") or {}).get("recent") or []
                out = recent[-1] if recent else {"error": "no answer"}
            except Exception:
                out = {"error": "ask failed"}
            body = json.dumps(out).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body); return
        if self.path.startswith("/api/confirm"):
            import subprocess
            qs = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            kind = (qs.get("kind") or ["scenario"])[0]; cid = (qs.get("id") or [""])[0]
            REPO = os.path.expanduser("~/zola-core")
            script = "zola_research.py" if kind == "research" else "zola_daemon.py"
            ok = False
            if cid:
                try:
                    r = subprocess.run(["python3", os.path.join(REPO, script), "--confirm", cid],
                                       capture_output=True, text=True, timeout=15, cwd=REPO)
                    ok = r.returncode == 0
                except Exception:
                    pass
            body = json.dumps({"ok": ok, "kind": kind, "id": cid}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body); return
        if self.path.startswith("/api/control"):
            try:
                self._json(self._control_summary())
            except Exception as e:
                self._json({"error": str(e)[:160]})
            return
        if self.path.startswith("/api/loop"):
            try:
                self._json(self._loop_summary())
            except Exception as e:
                self._json({"error": str(e)[:160]})
            return
        if self.path.startswith("/api/sky"):
            # The instrument bank. Read-only, no state, no personal data: the only
            # inputs are geometric (lat / lon / date / tz) and they arrive in the
            # query string, so nothing about a place is ever persisted server-side.
            from urllib.parse import parse_qs
            qs = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            eng = os.path.join(ZOLA_DIR, "engine")
            args = ["python3", os.path.join(eng, "zola_astronomy.py"), "sky", "--json=1"]
            for k in ("lat", "lon", "date", "tz", "place"):
                if k in qs and qs[k][0]:
                    args.append("--%s=%s" % (k, qs[k][0][:40]))
            try:
                import subprocess
                r = subprocess.run(args, capture_output=True, text=True, timeout=15, cwd=eng)
                if r.returncode != 0:
                    self._json({"error": (r.stderr or "sky failed")[:200]})
                    return
                self._json(json.loads(r.stdout))
            except Exception as e:
                self._json({"error": str(e)[:160]})
            return
        if self.path.startswith("/api/daytracker"):
            # THE REAL-LIFE SIDE. Every node in ZOLA measures work — money,
            # jobs, learning, output — so the wheel could only ever talk about
            # work. Body & Energy, Home, Rest: nothing recorded them.
            #
            # ~/tools/daytracker has been logging for days and nothing here has
            # ever read it. This reads ONLY the daily aggregates: hours at the
            # screen, session count, churn, time away. It deliberately does not
            # return the `activities` or `categories` maps, because those name
            # applications and documents, and how long he spent in a specific
            # file is not a fact this wheel needs to make its point.
            import glob
            import datetime as _dt
            base = os.path.expanduser("~/tools/daytracker/data")
            try:
                days = []
                for p in sorted(glob.glob(os.path.join(base, "summary", "summary-*.json")))[-14:]:
                    try:
                        with open(p) as f:
                            s = json.load(f)
                    except Exception:
                        continue
                    gaps = s.get("gap_seconds") or {}
                    away = sum(v for v in gaps.values() if isinstance(v, (int, float)))
                    day = {
                        "date": s.get("date"),
                        "hours": round(float(s.get("tracked_hours") or 0), 2),
                        "sessions": s.get("sessions"),
                        "churn_min": int(round((s.get("churn_seconds") or 0) / 60.0)),
                        "away_min": int(round(away / 60.0)),
                        "last_active": None,
                    }
                    # WHEN HE STARTED AND WHEN HE STOPPED. The only rhythm
                    # signal in this dataset, and the file edges do not give it:
                    # the log opens and closes with a midnight-spanning event,
                    # so both the first and the last line read 00:00 on five of
                    # six days. Reading either edge would have reported a
                    # bedtime of midnight every night, which he did not have.
                    #
                    # `session` events are real activity with real start/end.
                    # The earliest session start and the latest session end are
                    # the honest answer, and 00:00 is discarded as the artifact.
                    j = os.path.join(base, "activity-%s.jsonl" % (s.get("date") or ""))
                    first = last = None
                    try:
                        with open(j) as f:
                            for line in f:
                                try:
                                    ev = json.loads(line)
                                except Exception:
                                    continue
                                if ev.get("type") != "session":
                                    continue
                                st = (ev.get("start") or "")[11:16]
                                en = (ev.get("end") or "")[11:16]
                                if st and st != "00:00" and (first is None or st < first):
                                    first = st
                                if en and en != "00:00" and (last is None or en > last):
                                    last = en
                    except Exception:
                        pass
                    day["first_session"] = first
                    day["last_session"] = last
                    day["last_active"] = last
                    days.append(day)
                # WHICH HOURS HE IS ACTUALLY GOOD IN. The one question the
                # astronomy genuinely cannot answer, and his own log can.
                #
                # Four buckets, not two, so "good" is not a single opaque
                # score: MAKING is the work that produces an artifact, TALKING
                # is other people, DRIFTING is the browser, ADMIN is upkeep.
                # Category labels only — the underlying events name specific
                # applications and documents and those do not leave here.
                MAKING = {"build", "docs", "decks", "motion"}
                TALKING = {"comms", "meetings"}
                DRIFTING = {"browsing"}
                hours = {}
                for p in sorted(glob.glob(os.path.join(base, "activity-*.jsonl")))[-14:]:
                    try:
                        fh = open(p)
                    except Exception:
                        continue
                    with fh:
                        for line in fh:
                            try:
                                ev = json.loads(line)
                            except Exception:
                                continue
                            if ev.get("type") != "session":
                                continue
                            st = ev.get("start") or ""
                            if len(st) < 13:
                                continue
                            try:
                                h = int(st[11:13])
                            except Exception:
                                continue
                            mins = (ev.get("seconds") or 0) / 60.0
                            cat = ev.get("category") or "unsorted"
                            b = hours.setdefault(h, {"making": 0.0, "talking": 0.0,
                                                     "drifting": 0.0, "admin": 0.0})
                            if cat in MAKING:
                                b["making"] += mins
                            elif cat in TALKING:
                                b["talking"] += mins
                            elif cat in DRIFTING:
                                b["drifting"] += mins
                            else:
                                b["admin"] += mins
                hour_rows = []
                for h in sorted(hours):
                    b = hours[h]
                    tot = sum(b.values())
                    if tot < 1:
                        continue
                    hour_rows.append({
                        "h": h,
                        "total_min": int(round(tot)),
                        "making": int(round(b["making"])),
                        "talking": int(round(b["talking"])),
                        "drifting": int(round(b["drifting"])),
                        "admin": int(round(b["admin"])),
                        "making_pct": int(round(b["making"] / tot * 100)),
                    })

                self._json({
                    "days": days,
                    "hours": hour_rows,
                    "n": len(days),
                    "source": "~/tools/daytracker daily summaries + session log",
                    "note": ("aggregates only — no application names, no document titles, "
                             "no window contents leave this route"),
                })
            except Exception as e:
                self._json({"error": str(e)[:160]})
            return
        # Registered as /api/live-sky, not /api/skynow: the existing /api/sky
        # route above is a prefix match and would swallow it.
        if self.path.startswith("/api/live-sky"):
            # THE SKY AS IT IS, RIGHT NOW. Not his chart — nobody's chart.
            #
            # The wheel has never drawn because it waits on a birth moment, and
            # a birth moment is personal data that cannot travel through a
            # tracked path. But a geocentric ecliptic longitude needs only a
            # TIME. It is the same number for every person alive, so computing
            # it requires nothing private and reveals nothing private.
            #
            # That is the whole trick: the zodiac rings can run today, live,
            # for anyone. The rings that need a PLACE — ascendant, midheaven,
            # the Gauquelin diurnal sectors, anything horizon-relative — still
            # cannot, and this route returns them as absent rather than
            # defaulting a location and drawing a wheel for a person standing
            # somewhere he is not.
            try:
                import datetime as _dt, sys as _sys
                _sys.path.insert(0, os.path.join(ZOLA_DIR, "engine"))
                import zola_astronomy as A
                now = _dt.datetime.now(_dt.timezone.utc)
                jd = (A.jd_from_ymd(now.year, now.month, now.day)
                      + (now.hour + now.minute / 60.0 + now.second / 3600.0) / 24.0)
                ayan = 23.85  # Lahiri, the same constant the codex reference uses
                bodies = []
                for name in ("Sun",) + tuple(A.PLANETS):
                    bl, bb, r = A.geocentric_ecl(name, jd)
                    bodies.append({"name": name, "lon": round(bl, 4),
                                   "lat": round(bb, 4), "dist": round(r, 4),
                                   "sid": round((bl - ayan) % 360, 4)})
                self._json({
                    "kind": "skynow",
                    "jd_ut": round(jd, 6),
                    "utc": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "ayanamsha_lahiri_deg": ayan,
                    "bodies": bodies,
                    # Stated, not implied. A consumer must not be able to read
                    # this payload as a personal chart just because it drew.
                    "asc": None, "mc": None, "sectors": None,
                    "place_bound": False,
                    "note": ("geocentric longitudes for this instant. Identical "
                             "for every observer on Earth. No location, so no "
                             "ascendant, midheaven or diurnal sector."),
                })
            except Exception as e:
                self._json({"error": str(e)[:160]})
            return
        if self.path.startswith("/api/wheel"):
            # The A-layer sheet for the private baseline, for the wheel renderer.
            # Takes NO query parameters on purpose: the baseline lives in the
            # gitignored zola-private.local.json and is never addressable from
            # the URL, so a crafted request cannot ask this route about anyone.
            # The runner emits geometry only — no date, time or place — so the
            # tracked template that consumes it stays neutral.
            eng = os.path.join(ZOLA_DIR, "engine")
            runner = os.path.join(eng, "zola_codex.py")
            if not os.path.exists(runner):
                self._json({"error": "no local codex runner; the wheel is a "
                                     "private-side feature and this install has none."})
                return
            try:
                import subprocess
                r = subprocess.run(["python3", runner, "json"], capture_output=True,
                                   text=True, timeout=15, cwd=eng)
                if r.returncode != 0:
                    # A Python traceback puts the useful line LAST. Slicing the
                    # first 200 characters kept the banner and the outermost
                    # frame and threw away the only sentence that says what went
                    # wrong, so the UI rendered a source path as the reason.
                    err = (r.stderr or "").strip()
                    lines = [x.strip() for x in err.splitlines() if x.strip()]
                    named = [x for x in lines
                             if ("Error" in x or "Exception" in x)
                             and not x.startswith("File ")]
                    msg = (named[-1] if named else (lines[-1] if lines else "wheel failed"))
                    self._json({"error": msg[:220]})
                    return
                self._json(json.loads(r.stdout))
            except Exception as e:
                self._json({"error": str(e)[:160]})
            return
        if self.path.startswith("/api/finance"):
            # ?scan=1 forces the scheduled session now (fetch+recompute); ?pause=1/?resume=1
            # actually enable/disable the finance_scan cron job (real control, not decorative —
            # this is the "kill switch" a person can trust). Default = read-only digest.
            qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            import subprocess
            eng = os.path.join(ZOLA_DIR, "engine")
            if "scan=1" in qs:
                try:
                    subprocess.run(["python3", os.path.join(eng, "zola_cron.py"), "run", "finance_scan"],
                                   capture_output=True, text=True, timeout=40, cwd=eng)
                except Exception:
                    pass
            if "pause=1" in qs or "resume=1" in qs:
                action = "disable" if "pause=1" in qs else "enable"
                try:
                    subprocess.run(["python3", os.path.join(eng, "zola_cron.py"), action, "finance_scan"],
                                   capture_output=True, text=True, timeout=10, cwd=eng)
                except Exception:
                    pass
            try:
                self._json(self._finance_summary())
            except Exception as e:
                self._json({"error": str(e)[:160]})
            return
        if self.path.startswith("/api/screen"):
            # Candidate universe for a fund CATEGORY, from official AMFI data, with
            # performance metrics computed from real NAV history. Read-only: returns the
            # last written screen file. ?run=1 regenerates it (slow — 38 history pulls),
            # ?category=<substr> picks the category.
            qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            import subprocess, urllib.parse
            eng = os.path.join(ZOLA_DIR, "engine")
            key = (urllib.parse.parse_qs(qs).get("key") or [None])[0]
            if not key:
                c = (urllib.parse.parse_qs(qs).get("category") or ["Arbitrage"])[0]
                key = re.sub(r"[^a-z0-9]+", "-", c.split(",")[0].strip().lower()).strip("-") or "screen"
            f = os.path.join(eng, "zola-screen-%s.local.json" % key)
            if "run=1" in qs:
                params = urllib.parse.parse_qs(qs)
                cat = (params.get("category") or ["Arbitrage"])[0]
                cmd = ["python3", os.path.join(eng, "zola_screen.py"),
                       "--category", cat, "--key", key, "--history"]
                try:
                    subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=eng)
                except Exception:
                    pass
            try:
                with open(f, encoding="utf-8") as fh:
                    data = json.load(fh)
                # Screens written before assess() existed carry no confidence
                # fields. Recompute them on read — it is pure arithmetic over
                # numbers already in the file, so there is no reason to make the
                # reader sit through a 300s re-screen to see them.
                if "peer_verdict" not in data and data.get("candidates"):
                    try:
                        # sys is only imported locally in this module (see _port),
                        # so import it here rather than relying on a global.
                        import sys as _sys
                        if eng not in _sys.path:
                            _sys.path.insert(0, eng)
                        import zola_screen as _zs
                        _zs.assess(data)
                    except Exception:
                        pass
                self._json(data)
            except FileNotFoundError:
                self._json({"error": "no screen yet — run zola_screen.py", "candidates": []})
            except Exception as e:
                self._json({"error": str(e)[:160], "candidates": []})
            return
        if self.path.startswith("/api/jobrank"):
            # The NL sponsor pool as decision CLASSES, not a ranking. In-process
            # rather than subprocess: it is local file reads plus arithmetic, so
            # there is nothing to pay a fork for.
            # READ-ONLY on purpose. jobrank.promote() writes 22 rows into
            # zola-jobs.json, and a GET must not mutate a store the scraper and a
            # second editor share — promotion stays a deliberate CLI call.
            eng = os.path.join(ZOLA_DIR, "engine")
            try:
                import sys as _sys
                if eng not in _sys.path:
                    _sys.path.insert(0, eng)
                import zola_jobrank as _jr
                # Point it at THIS instance's store rather than trusting the env to
                # have propagated, so a --port worktree instance reads its own data.
                _jr.JOBS = os.path.join(ZOLA_DIR, "zola-jobs.json")
                self._json(_jr.web())
            except Exception as e:
                self._json({"error": str(e)[:160], "classes": []})
            return
        if self.path.startswith("/api/jobscout"):
            # run the sanctioned live ATS scraper -> merge verified openings into zola-jobs.json
            import subprocess
            eng = os.path.join(ZOLA_DIR, "engine")
            mode = "run" if "run" in (self.path.split("?", 1)[1] if "?" in self.path else "") else "preview"
            arg = "run" if mode == "run" else "preview-json"
            try:
                if arg == "run":
                    r = subprocess.run(["python3", os.path.join(eng, "zola_jobscout.py"), "run"],
                                       capture_output=True, text=True, timeout=45, cwd=eng)
                    out = r.stdout.strip() or '{"error":"scout failed"}'
                else:
                    r = subprocess.run(["python3", "-c",
                        "import zola_jobscout,json;print(json.dumps(zola_jobscout.preview()))"],
                        capture_output=True, text=True, timeout=45, cwd=eng)
                    out = r.stdout.strip() or '{"error":"scout failed"}'
            except Exception as e:
                out = json.dumps({"error": str(e)[:120]})
            body = out.encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body); return
        if self.path.startswith("/api/advise"):
            # natural-language decision: alias-aware match -> USE/LEAN/AVOID-ONLY/GAP
            import subprocess
            qs = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            q = (qs.get("q") or [""])[0].strip()
            if not q:
                self._json({"error": "pass ?q=<question>"}); return
            eng = os.path.join(ZOLA_DIR, "engine")
            try:
                r = subprocess.run(["python3", os.path.join(eng, "zola_skills.py"), "advise", q],
                                   capture_output=True, text=True, timeout=10, cwd=eng)
                out = r.stdout.strip() or '{"error":"advise failed"}'
            except Exception as e:
                out = json.dumps({"error": str(e)[:120]})
            body = out.encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body); return
        if self.path.startswith("/api/cms"):
            q = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            fn = (q.get("file") or [""])[0]
            if fn not in CMS_WHITELIST:
                self._json({"error": "file not allowed", "file": fn}); return
            try:
                with open(os.path.join(ZOLA_DIR, fn), encoding="utf-8") as fh:
                    self._json({"file": fn, "data": json.load(fh)})
            except Exception as e:
                self._json({"error": str(e)[:140], "file": fn})
            return
        if self.path.startswith("/api/cockpit"):
            d = self._cockpit_read()
            ev = []
            lp = os.path.expanduser("~/.zola/events.jsonl")
            if os.path.exists(lp):
                for line in open(lp, encoding="utf-8"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev.append(json.loads(line))
                    except Exception:
                        pass
            jobs = [k for k, v in d.get("entities", {}).items() if v.get("enabled")]
            self._json({"killswitch": d.get("killswitch", False),
                        "entities": d.get("entities", {}), "dials": d.get("dials", {}),
                        "scenes": d.get("scenes", {}),
                        "mode": {"active_count": len(jobs), "active": jobs,
                                 "paused": d.get("killswitch", False)},
                        "undo_available": len(d.get("_undo", [])) > 0,
                        "recent": [e for e in ev if e.get("job") == "cockpit"][-8:][::-1]})
            return
        if self.path in ("/", "/index.html"):
            self.path = "/zola.html"
        super().do_GET()

    def _persist(self, filename):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        json.loads(body)  # validate before writing
        with open(os.path.join(ZOLA_DIR, filename), "wb") as f:
            f.write(body)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def do_POST(self):
        if os.path.isdir(ZOLA_DIR):
            # whitelisted local files the app may persist
            if self.path == "/save":
                self._persist("zola-data.json"); return
            if self.path == "/save-exit":
                self._persist("zola-exit.local.json"); return
            if self.path == "/save-ds-learnings":
                self._persist("zola-ds-learnings.local.json"); return
            if self.path.startswith("/api/pipeline-outcome"):
                # record a REAL outreach outcome on a job lead, then feed it to the loop.
                # {company, outcome: reply|intro|interview|offer|reject|silent, channel?}
                import subprocess
                d = self._body_json()
                company = (d.get("company") or "").strip()
                outcome = (d.get("outcome") or "").strip()
                channel = (d.get("channel") or "").strip() or None
                if not company or not outcome:
                    self.send_response(400); self.send_header("Content-Type", "application/json")
                    self.end_headers(); self.wfile.write(b'{"ok":false,"error":"need company+outcome"}'); return
                eng = os.path.join(ZOLA_DIR, "engine")
                try:
                    args = ["python3", os.path.join(eng, "zola_pipeline.py"), "set", company, outcome]
                    if channel: args.append(channel)
                    subprocess.run(args, capture_output=True, text=True, timeout=10, cwd=eng)
                    r = subprocess.run(["python3", os.path.join(eng, "zola_pipeline.py"), "sync"],
                                       capture_output=True, text=True, timeout=15, cwd=eng)
                    out = r.stdout.strip() or '{"ok":true}'
                except Exception as e:
                    out = json.dumps({"ok": False, "error": str(e)[:120]})
                body = out.encode()
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body))); self.end_headers()
                self.wfile.write(body); return
            if self.path.startswith("/api/cms-save"):
                q = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
                fn = (q.get("file") or [""])[0]
                if fn not in CMS_WHITELIST:
                    self.send_response(403); self.end_headers()
                    self.wfile.write(b'{"ok":false,"error":"file not allowed"}'); return
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    json.loads(body)  # validate before writing
                except Exception:
                    self.send_response(400); self.end_headers()
                    self.wfile.write(b'{"ok":false,"error":"invalid json"}'); return
                import time as _t, shutil
                p = os.path.join(ZOLA_DIR, fn)
                bkdir = os.path.expanduser("~/.zola/backups"); os.makedirs(bkdir, exist_ok=True)
                if os.path.exists(p):
                    shutil.copyfile(p, os.path.join(bkdir, fn + "." + _t.strftime("%Y%m%d-%H%M%S") + ".bak"))
                with open(p, "wb") as f:
                    f.write(body)
                try:  # audit trail — every CMS write shows in the control-plane activity feed
                    ev = {"ts": _t.time(), "iso": _t.strftime("%Y-%m-%dT%H:%M:%S"),
                          "job": "cms", "event": "edit", "level": "info", "detail": fn}
                    with open(os.path.expanduser("~/.zola/events.jsonl"), "a", encoding="utf-8") as ef:
                        ef.write(json.dumps(ev) + "\n")
                except Exception:
                    pass
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.end_headers(); self.wfile.write(b'{"ok":true}'); return
            if self.path.startswith("/api/cockpit-"):
                import copy
                body = self._body_json()
                d = self._cockpit_read()

                def push_undo():
                    d.setdefault("_undo", []).append({
                        "entities": copy.deepcopy(d.get("entities", {})),
                        "dials": copy.deepcopy(d.get("dials", {})),
                        "killswitch": d.get("killswitch", False)})
                    d["_undo"] = d["_undo"][-10:]

                if self.path.startswith("/api/cockpit-set"):
                    kind = body.get("kind"); key = body.get("key"); val = body.get("value")
                    push_undo()
                    if kind == "entity":
                        d.setdefault("entities", {}).setdefault(key, {})["enabled"] = bool(val)
                        self._cockpit_audit("toggle", key + " -> " + ("on" if val else "off"))
                    elif kind == "dial":
                        d.setdefault("dials", {})[key] = val
                        self._cockpit_audit("dial", key + " = " + str(val))
                    elif kind == "kill":
                        d["killswitch"] = bool(val)
                        self._cockpit_audit("killswitch", "ARMED" if val else "released")
                    self._cockpit_write(d); self._json({"ok": True}); return
                if self.path.startswith("/api/cockpit-scene"):
                    sc = body.get("scene"); scene = d.get("scenes", {}).get(sc)
                    if scene:
                        push_undo()
                        for k, v in scene.get("sets", {}).items():
                            if k in d.get("entities", {}):
                                d["entities"][k]["enabled"] = bool(v)
                        self._cockpit_audit("scene", "applied " + sc); self._cockpit_write(d)
                    self._json({"ok": True}); return
                if self.path.startswith("/api/cockpit-undo"):
                    u = d.get("_undo", [])
                    if u:
                        snap = u.pop()
                        d["entities"] = snap["entities"]; d["dials"] = snap["dials"]
                        d["killswitch"] = snap["killswitch"]
                        self._cockpit_audit("undo", "reverted last change"); self._cockpit_write(d)
                    self._json({"ok": True}); return
                if self.path.startswith("/api/cockpit-action"):
                    import subprocess
                    key = body.get("key"); ent = d.get("entities", {}).get(key, {})
                    self._cockpit_audit("action", "triggered " + str(key))
                    script = ent.get("script")
                    if script:
                        try:
                            subprocess.Popen(["bash", os.path.expanduser(script)])
                        except Exception:
                            pass
                    self._json({"ok": True, "ran": key}); return
        self.send_response(404)
        self.end_headers()


def _cron_ticker():
    """In-app cron ticker (the 5th Hermes pillar): while the app is open, run the
    deterministic loop-refresh cron on its cadence. Script-only, no LLM, no network.
    Stops when the app closes — no rogue daemon. launchd is the separate opt-in."""
    import time, subprocess
    eng = os.path.join(ZOLA_DIR, "engine")
    cron = os.path.join(eng, "zola_cron.py")
    if not os.path.exists(cron):
        return
    # read the configured tick cadence once (default 300s)
    try:
        import json as _j
        tick_s = _j.load(open(os.path.expanduser("~/.zola/cron.json"))).get("tick_seconds", 300)
    except Exception:
        tick_s = 300
    time.sleep(20)  # let the server settle before the first tick
    while True:
        try:
            subprocess.run(["python3", cron, "tick"], capture_output=True, text=True, timeout=120, cwd=eng)
        except Exception:
            pass
        time.sleep(max(60, tick_s))

if __name__ == "__main__":
    import threading
    print(f"ZOLA server on http://localhost:{PORT} (app dir: {ZOLA_DIR if os.path.isdir(ZOLA_DIR) else 'NOT CLONED — status page'})")
    if os.path.isdir(ZOLA_DIR):
        threading.Thread(target=_cron_ticker, daemon=True).start()
        print("  ↻ cron ticker on (in-app, script-only) — python3 engine/zola_cron.py list")
    # ThreadingHTTPServer: subprocess-backed endpoints (loop/advise/jobscout/reason) must NOT
    # block data-file requests — a single-threaded server freezes the whole app (orbit collapses).
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
