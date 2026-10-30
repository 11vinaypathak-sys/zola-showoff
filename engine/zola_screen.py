#!/usr/bin/env python3
"""
ZOLA SCREEN — build a real candidate universe from official AMFI data.

WHY THIS EXISTS
The Finance node knows WHICH CATEGORY the book is missing (zola.html:finNewInvestments)
and the exact criteria a fund must meet (FIN_SELECT). What it lacked was the list of
actual schemes to test. This closes that gap from the official source, so ZOLA names
real funds from live data instead of anyone recalling names from memory.

WHAT IT IS / IS NOT
  · It IS a screener: mechanical filtering of public data by stated criteria.
  · It is NOT advice. It ranks nothing on expected return and asserts no "best" fund.
    Ordering is alphabetical. The decision is the reader's.

WHAT AMFI GIVES, HONESTLY
  ✓ every scheme name in a category, official, free, no key
  ✓ daily NAV  → real return/volatility history can be COMPUTED over time
  ✗ expense ratio, exit load, AUM are NOT in this file. They must come from the AMC
    factsheet/SID. Fields are emitted as null so nothing downstream mistakes an
    absent value for a measured one.

    python3 zola_screen.py                      # arbitrage, direct+growth (default)
    python3 zola_screen.py --category "Index"   # any AMFI category substring
    python3 zola_screen.py --all-plans          # don't restrict to Direct/Growth
    python3 zola_screen.py --json               # machine-readable

Writes engine/zola-screen.local.json (gitignored — same convention as the market store).
Stdlib only.
"""
import json, os, re, ssl, sys, datetime, urllib.request, urllib.error

# AMFI moved this file from www.amfiindia.com to portal.amfiindia.com; the old host now
# answers with an HTML redirect stub, which silently parsed to zero schemes.
NAV_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"
ENGDIR = os.path.dirname(os.path.abspath(__file__))
# One file PER CATEGORY. A single shared output meant the last screen to run clobbered
# the previous one — refreshing the overseas list (name-only) wiped the arbitrage
# metrics that the game plan reads.
def out_path(key):
    return os.path.join(ENGDIR, "zola-screen-%s.local.json" % key)

HEADER_RX = re.compile(r"^(Open|Close) Ended Schemes\((.+)\)\s*$")


TLS_DEGRADED = []          # urls fetched without cert verification, this run


def _get(url, timeout=45):
    """Verified TLS first. If the SERVER's chain is broken, fall back loudly.

    As of 2026-09-07 portal.amfiindia.com stopped sending its intermediate
    certificate, so a verified fetch fails with "unable to get local issuer
    certificate". That is AMFI's misconfiguration, not ours — but it silently
    killed the finance_scan cron, which is the worse failure: the screen just
    stops updating and nothing says so.

    The payload is public, unauthenticated, read-only NAV data, so an
    unverified retry is an acceptable trade to keep the scan alive. It is NOT
    silent: the url is recorded in TLS_DEGRADED and stamped into the output
    JSON as tls_degraded, so a MITM-substituted NAV file would be visible
    rather than trusted.
    """
    # CA bundle, best source first. The system python3 that launchd runs ships
    # with NO usable CA store and cannot pip-install certifi (pip's own download
    # fails the same verification), so without a local bundle EVERY fetch lands
    # in the unverified path below. cacert.pem is exported from the macOS system
    # root keychain by ops/refresh-ca-bundle.sh.
    ctx = None
    for src in (lambda: __import__("certifi").where(),
                lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "cacert.pem")):
        try:
            path = src()
            if path and os.path.exists(path):
                ctx = ssl.create_default_context(cafile=path)
                break
        except Exception:
            continue
    if ctx is None:
        ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "zola-screen/1.0"})
    try:
        return urllib.request.urlopen(req, timeout=timeout, context=ctx).read().decode("utf-8", "ignore")
    except urllib.error.URLError as e:
        if not isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
            raise
        sys.stderr.write(f"  ! TLS chain broken at {url} — retrying UNVERIFIED "
                         f"(public NAV data; flagged in output)\n")
        TLS_DEGRADED.append(url)
        unv = ssl.create_default_context()
        unv.check_hostname = False
        unv.verify_mode = ssl.CERT_NONE
        return urllib.request.urlopen(req, timeout=timeout, context=unv).read().decode("utf-8", "ignore")


def parse_navall(text):
    """Yield dicts for every scheme line, across BOTH row formats AMFI actually uses.

    The file is grouped by category headers like:
        Open Ended Schemes(Hybrid Scheme - Arbitrage Fund)
    Carrying the current header down the rows is the only way to know a scheme's
    category — the NAME alone is unreliable ("Axis Income Plus Arbitrage Omni FOF" is
    a fund of funds, not an arbitrage fund).

    TWO ROW LAYOUTS, verified against the live file:
      6 fields  code;isin;isin;NAME (plan+option baked into the name);NAV;DATE
      8 fields  code;isin;isin;NAME;PLAN;OPTION;NAV;DATE
    Assuming the 6-field shape everywhere made p[4] read as 'Regular Plan' for the
    8-field sections, so NAV parsed as None and every scheme was filtered out — which
    is why the index and overseas categories came back empty while arbitrage worked.
    """
    category = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = HEADER_RX.match(line)
        if m:
            category = m.group(2).strip()
            continue
        if ";" not in line:
            continue
        p = [x.strip() for x in line.split(";")]
        if len(p) < 6 or p[0].lower() == "scheme code":
            continue

        if len(p) >= 8:
            name, plan, option, nav_s, date_s = p[3], p[4], p[5], p[6], p[7]
        else:
            name, plan, option, nav_s, date_s = p[3], "", "", p[4], p[5]
        try:
            nav = float(nav_s)
        except ValueError:
            nav = None            # some schemes legitimately publish "N.A."
        yield {"category": category, "scheme_code": p[0], "name": name,
               "plan": plan, "option": option, "nav": nav, "date": date_s}


def is_direct_growth(row):
    """Direct plan AND Growth option, excluding income-distribution variants.

    Uses the explicit plan/option columns when the row supplies them, and falls back to
    reading them out of the name otherwise. Naming is not standardised across AMCs —
    "Growth - Direct Plan", "Direct Plan - Growth Option", "DIRECT - GROWTH" and
    "-Direct Growth" all occur — so match on presence, not order.
    """
    hay = " ".join([row.get("name", ""), row.get("plan", ""), row.get("option", "")]).lower()
    if "direct" not in hay:
        return False
    if not re.search(r"\bgrowth\b", hay):
        return False
    # IDCW / dividend variants are a different option even when "growth" also appears
    if re.search(r"idcw|dividend|payout|reinvest", hay):
        return False
    return True


def display_name(row):
    """Full identity including plan/option, so two rows never look identical."""
    n = row["name"]
    extra = " ".join(x for x in (row.get("plan"), row.get("option")) if x)
    if extra and extra.lower() not in n.lower():
        n = "%s - %s" % (n, extra)
    return n


def screen(category_substr="Arbitrage", direct_growth_only=True):
    text = _get(NAV_URL)
    rows = list(parse_navall(text))
    if not rows:
        raise RuntimeError("AMFI file parsed to zero schemes — format may have changed")

    cats = sorted({r["category"] for r in rows if r["category"]})
    # Comma-separated substrings, matched with OR. Necessary because AMFI splits one
    # real-world category across differently-worded headers — overseas fund-of-funds
    # appear under both "Other Scheme - FoF Overseas" and "Overseas Fund of Funds -
    # Fund of Funds investing overseas", and arbitrage under both "Hybrid Scheme -"
    # and "Hybrid Schemes -". A single substring silently drops half the universe.
    wants = [w.strip().lower() for w in str(category_substr).split(",") if w.strip()]
    hits = [r for r in rows if r["category"] and any(w in r["category"].lower() for w in wants)]
    matched_cats = sorted({r["category"] for r in hits})

    if direct_growth_only:
        hits = [r for r in hits if is_direct_growth(r)]

    out = []
    for r in sorted(hits, key=lambda r: display_name(r).lower()):
        out.append({
            "scheme_code": r["scheme_code"],
            "name": display_name(r),
            "amfi_category": r["category"],
            "nav": r["nav"],
            "nav_date": r["date"],
            # NOT in the AMFI file — must be filled from the AMC factsheet/SID.
            # Explicitly null so the scorer treats them as unknown, never as measured.
            "er": None,
            "aum": None,
            "exit": None,
            "equity": None,
        })
    return {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "source": NAV_URL,
        "query": {"category": category_substr, "direct_growth_only": direct_growth_only},
        "matched_categories": matched_cats,
        "all_categories": cats,
        "count": len(out),
        "candidates": out,
        "missing_fields": ["er", "aum", "exit", "equity"],
        "note": ("AMFI publishes name/NAV only. Expense ratio, AUM, exit load and equity "
                 "share must be read off the AMC factsheet or SID. Ordering here is "
                 "alphabetical — this is a screen, not a ranking."),
        # Non-empty means at least one fetch skipped cert verification because the
        # SERVER's chain was broken. Surface it in any UI that shows this data.
        "tls_degraded": list(TLS_DEGRADED),
    }


# ── measured performance ─────────────────────────────────────────────────────
# NAV history source. This is a third-party mirror of AMFI's own published NAV data,
# not AMFI itself — noted here because provenance matters. It exposes full history per
# AMFI scheme code, which is what makes the metrics below computable at all.
HIST_URL = "https://api.mfapi.in/mf/%s"
TRADING_DAYS = 252


def _nav_series(scheme_code, timeout=25):
    """Ascending [(date, nav)] for a scheme, or [] on any failure."""
    try:
        raw = json.loads(_get(HIST_URL % scheme_code, timeout=timeout))
    except Exception:
        return []
    out = []
    for row in reversed(raw.get("data") or []):        # API returns newest-first
        try:
            out.append((datetime.datetime.strptime(row["date"], "%d-%m-%Y").date(),
                        float(row["nav"])))
        except (ValueError, KeyError, TypeError):
            continue                                    # skip "N.A." rows
    return out


def _metrics(series):
    """Annualised return over 1y/3y, annualised volatility, and max drawdown.

    All computed from the real NAV series — no assumed rates. Returns None for any
    window the fund has not actually existed through, rather than extrapolating one.
    """
    if len(series) < 30:
        return {}
    navs = [n for _, n in series]
    end_d, end_n = series[-1]

    def cagr(years):
        target = end_d - datetime.timedelta(days=int(365.25 * years))
        past = [(d, n) for d, n in series if d <= target]
        if not past or past[-1][1] <= 0:
            return None                                 # fund is younger than the window
        start_n = past[-1][1]
        actual_yrs = (end_d - past[-1][0]).days / 365.25
        if actual_yrs <= 0:
            return None
        return ((end_n / start_n) ** (1 / actual_yrs) - 1) * 100

    # daily log-ish returns over the trailing year for volatility
    yr_ago = end_d - datetime.timedelta(days=365)
    recent = [n for d, n in series if d >= yr_ago]
    vol = None
    if len(recent) > 20:
        rets = [(recent[i] - recent[i - 1]) / recent[i - 1]
                for i in range(1, len(recent)) if recent[i - 1] > 0]
        if rets:
            mean = sum(rets) / len(rets)
            var = sum((r - mean) ** 2 for r in rets) / len(rets)
            vol = (var ** 0.5) * (TRADING_DAYS ** 0.5) * 100

    # Max drawdown, with a DATA-INTEGRITY guard. A fund's NAV cannot halve in a
    # single day — when the series says it did, that is a bad print or an
    # unadjusted structural change, not a market move. Without this guard one
    # glitched NAV drags max_dd to ~100% and the screen reports a fund that
    # "went to zero": Axis Greater China Equity FoF did exactly that on
    # 2026-09-07. A screen that shows an impossible loss is worse than no screen.
    peak, mdd, suspect = navs[0], 0.0, False
    prev = navs[0]
    for n in navs:
        if prev > 0 and n / prev < 0.5:
            suspect = True
            prev = n
            continue                        # drop the glitched print
        prev = n
        peak = max(peak, n)
        if peak > 0:
            mdd = max(mdd, (peak - n) / peak)

    return {"ret_1y": cagr(1), "ret_3y": cagr(3), "vol_1y": vol,
            # NEGATIVE by convention, because a drawdown IS a loss. This was a
            # positive magnitude, so any UI that prefixes '+' rendered a 33.6%
            # loss as "+33.6%" — a gain. Sign now carries the meaning.
            "max_dd": -mdd * 100, "history_days": len(series),
            "data_suspect": suspect,
            "first_nav_date": series[0][0].isoformat()}


# ── CONFIDENCE ON A SCREEN METRIC ────────────────────────────────────────────
# FIN_SELECT already says it in prose: "one-year league tables mostly reflect
# luck in this category". This makes that arithmetic instead of advice.
#
# A return estimated from a noisy price series carries a standard error. For an
# annualised return measured over T years from a series with annualised
# volatility V, SE ~ V / sqrt(T). The consequence is blunt: at one year, the
# standard error of the return estimate is roughly the volatility itself. An
# arbitrage fund at 1% vol can be told apart from zero; an equity fund at 15%
# vol cannot be told apart from anything, and its position in a one-year table
# is very largely luck.
def return_stderr(vol_pct, years):
    """Standard error of an annualised return estimate, in percentage points."""
    if vol_pct is None or not years or years <= 0:
        return None
    return vol_pct / (years ** 0.5)


def distinguishable(value, other, se, z=2.0):
    """Is `value` separated from `other` by more than z standard errors?

    Returns None when there is no SE — unknown is not the same as no, and a
    screen that renders one as the other is the fault this exists to prevent.
    """
    if value is None or other is None or se is None:
        return None
    return abs(value - other) > z * se


def criterion(value, threshold, cmp_, se=None, z=2.0):
    """Test a value against a hard threshold, with a third UNDETERMINED state.

    A fund 0.1pt the wrong side of a 0.40% expense cap has failed. A fund 0.1pt
    the RIGHT side of it, measured with a 0.5pt error, has not passed — it is
    inside the noise, and the pass is an artifact of the measurement.
    """
    if value is None:
        return {"state": "unmeasured", "value": None, "threshold": threshold,
                "why": "no measured value — absent is not passing"}
    ok = (value <= threshold) if cmp_ == "lte" else (value >= threshold)
    margin = abs(value - threshold)
    if se is not None and margin <= z * se:
        return {"state": "undetermined", "value": value, "threshold": threshold,
                "margin": round(margin, 4), "se": round(se, 4),
                "why": "within %.1f standard errors of the threshold" % z}
    return {"state": "pass" if ok else "fail", "value": value,
            "threshold": threshold, "margin": round(margin, 4),
            "se": None if se is None else round(se, 4)}


def peer_verdict(candidates, field="ret_1y", years=1.0):
    """Is the SPREAD across peers bigger than the error on any one of them?

    This is the question a league table never asks. If the best and worst fund
    in a category differ by less than the typical standard error, the ordering
    is noise and picking the top one is picking a coin flip with extra steps.
    """
    vals = [(c.get(field), c.get("vol_1y")) for c in candidates
            if c.get(field) is not None]
    if len(vals) < 3:
        return {"usable": False,
                "why": "fewer than 3 funds carry a measured %s" % field}
    rets = [v for v, _ in vals]
    ses = [return_stderr(vo, years) for _, vo in vals if vo is not None]
    spread = max(rets) - min(rets)
    typ_se = (sum(ses) / len(ses)) if ses else None
    out = {"usable": True, "n": len(rets), "field": field,
           "spread": round(spread, 3), "best": round(max(rets), 3),
           "worst": round(min(rets), 3),
           "typical_se": None if typ_se is None else round(typ_se, 3)}
    # Three bands, not two. A spread that clears 2x SE by a hair (arbitrage came
    # out at 2.61pt against a 2.58pt threshold on real data) is not the same
    # finding as one that clears it several times over, and reporting both as
    # "carries signal" is the false-confidence this module is meant to remove.
    if typ_se is None:
        out["ordering_meaningful"] = None
        out["verdict"] = "no volatility measured — cannot judge the ordering"
    elif spread > 3 * typ_se:
        out["ordering_meaningful"] = True
        out["verdict"] = ("spread %.2fpt is over 3x the typical %.2fpt standard error "
                          "— the ordering carries signal" % (spread, typ_se))
    elif spread > 2 * typ_se:
        out["ordering_meaningful"] = "marginal"
        out["verdict"] = ("spread %.2fpt only just clears 2x the typical %.2fpt standard "
                          "error (%.2fpt) — MARGINAL; the top few and bottom few may be "
                          "separable but neighbouring ranks are not"
                          % (spread, typ_se, 2 * typ_se))
    else:
        out["ordering_meaningful"] = False
        out["verdict"] = ("spread %.2fpt is inside 2x the typical %.2fpt standard error "
                          "— this league table is noise; do not rank on it"
                          % (spread, typ_se))
    return out


def assess(res, years=1.0):
    """Attach per-candidate confidence and a category-level ordering verdict."""
    for c in res.get("candidates", []):
        se = return_stderr(c.get("vol_1y"), years)
        c["ret_1y_se"] = None if se is None else round(se, 3)
        c["ret_1y_vs_zero"] = distinguishable(c.get("ret_1y"), 0.0, se)
        # A fund whose one-year return cannot be told apart from zero has not
        # demonstrated a return, whatever the headline number says.
        if c.get("ret_1y") is None:
            c["level"] = "X"
        elif c.get("data_suspect"):
            c["level"] = "D"
        elif c["ret_1y_vs_zero"] is False:
            c["level"] = "C"
        elif c["ret_1y_vs_zero"] is True:
            c["level"] = "A"
        else:
            c["level"] = "D"
    res["peer_verdict"] = peer_verdict(res.get("candidates", []), "ret_1y", years)
    return res


def enrich_with_history(res, limit=None, quiet=False):
    cands = res["candidates"][:limit] if limit else res["candidates"]
    for i, c in enumerate(cands, 1):
        if not quiet:
            sys.stderr.write("\r  history %d/%d …" % (i, len(cands)))
            sys.stderr.flush()
        c.update(_metrics(_nav_series(c["scheme_code"])))
    if not quiet:
        sys.stderr.write("\r" + " " * 40 + "\r")
    res["metrics_note"] = ("ret_1y / ret_3y / vol_1y / max_dd are COMPUTED from real NAV "
                           "history. They are measurements of the past, not forecasts. "
                           "Cost (er) and exit load are still required and are not here.")
    res["metrics_source"] = HIST_URL % "<scheme_code>"
    return res


def slug_for(category_substr):
    """Stable filename key from the category filter's first segment."""
    first = str(category_substr).split(",")[0].strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", first).strip("-")
    return s or "screen"


def main():
    args = sys.argv[1:]
    cat = "Arbitrage"
    if "--category" in args:
        cat = args[args.index("--category") + 1]
    dg = "--all-plans" not in args
    as_json = "--json" in args
    want_hist = "--history" in args
    # explicit key wins, so the app can address a file by the name it already uses
    key = args[args.index("--key") + 1] if "--key" in args else slug_for(cat)

    try:
        res = screen(cat, dg)
        if want_hist:
            enrich_with_history(res, quiet=as_json)
            # Confidence is only meaningful once there is a NAV history to
            # measure it from, so it rides with --history rather than pretending
            # to assess a name-only list.
            assess(res)
    except Exception as e:
        print("screen failed: %s" % e)
        return 1

    res["key"] = key
    OUT = out_path(key)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    if as_json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    print("ZOLA SCREEN · %s" % res["generated_at"])
    print("category filter : %s%s" % (cat, "  (Direct + Growth only)" if dg else "  (all plans)"))
    print("AMFI categories : %s" % (", ".join(res["matched_categories"]) or "none matched"))
    print("schemes         : %d" % res["count"])
    print("NAV as of       : %s" % (res["candidates"][0]["nav_date"] if res["candidates"] else "-"))
    print("")
    if want_hist:
        # order by measured 3yr return where available — a real computation on real
        # history. Funds without a 3yr track record sort last rather than being
        # silently treated as zero.
        def key(c):
            r3 = c.get("ret_3y")
            return (0 if r3 is None else 1, r3 or 0)
        ranked = sorted(res["candidates"], key=key, reverse=True)
        print("  %-46s %7s %7s %7s %7s %5s %4s"
              % ("scheme (Direct/Growth)", "3y%", "1y%", "vol%", "maxDD%", "1ySE", "lvl"))
        print("  " + "-" * 92)
        for c in ranked:
            f = lambda x: ("%6.2f" % x) if isinstance(x, (int, float)) else "     -"
            print("  %-46s %7s %7s %7s %7s %5s %4s"
                  % (c["name"][:46], f(c.get("ret_3y")), f(c.get("ret_1y")),
                     f(c.get("vol_1y")), f(c.get("max_dd")),
                     ("%4.1f" % c["ret_1y_se"]) if c.get("ret_1y_se") is not None else "   -",
                     c.get("level", "-")))
        print("")
        pv = res.get("peer_verdict") or {}
        if pv.get("usable"):
            print("  ORDERING: %s" % pv["verdict"])
        elif pv:
            print("  ORDERING: not assessable — %s" % pv.get("why"))
        print("")
        print("  1ySE is the standard error on the one-year return: at a one-year window it is")
        print("  roughly the volatility itself, so a 7%% return on a 15%% vol fund cannot be told")
        print("  apart from zero. LEVEL reads: A the 1y return clears zero, C it does not, D the")
        print("  series is suspect, X no measured return at all. FIN_SELECT already says")
        print("  one-year league tables mostly reflect luck — these two columns are that,")
        print("  as arithmetic.")
        print("")
        print("  Ordered by measured 3-year return. This is realised history, NOT a forecast,")
        print("  and it ignores cost — expense ratio and exit load are still required and are")
        print("  not in any of these feeds. Highest past return is not automatically the pick.")
    else:
        for c in res["candidates"]:
            print("  %-72s  NAV %s" % (c["name"][:72], c["nav"]))
    print("")
    print("Still needed per candidate (NOT in the AMFI file): %s" % ", ".join(res["missing_fields"]))
    print("Read them off the AMC factsheet/SID, then score in the Finance node.")
    print("written: %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
