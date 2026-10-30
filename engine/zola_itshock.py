#!/usr/bin/env python3
"""
ZOLA · SHOCK DESK v8  —  PERM-1008 war-room terminal (08 Oct 2026)

v8: compact layout · 4 live TVs simultaneous w/ per-tile audio (YT postMessage)
· wire as drop-in cards · precedent panel removed · ACTION PANEL per card with
deterministic states (STAND DOWN / WATCH / WINDOW) computed from live numbers,
finance-node style · fear layer = India VIX (live) + desk-sentiment needle with
its formula printed on the board.

Line unchanged: states are rule outputs, not trade instructions. He decides.

Run live:   python3 ~/Zola/engine/zola_itshock.py --live
Out:        ~/Zola/zola-itshock.html  +  ~/Zola/zola-itshock-data.json
"""
import json, os, re, ssl, sys, time, statistics, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_HTML = os.path.join(ROOT, "zola-itshock.html")
OUT_JSON = os.path.join(ROOT, "zola-itshock-data.json")
LOG = os.path.join(ROOT, "zola-itshock.log")

ctx = None
for src in (lambda: __import__("certifi").where(),
            lambda: os.path.join(HERE, "cacert.pem")):
    try:
        p = src()
        if p and os.path.exists(p):
            ctx = ssl.create_default_context(cafile=p); break
    except Exception:
        continue
if ctx is None:
    ctx = ssl.create_default_context()

NAMED_IN = [("INFY.NS", "INFOSYS"), ("TCS.NS", "TCS"),
            ("WIPRO.NS", "WIPRO"), ("HCLTECH.NS", "HCL TECH")]
PEERS = [("TECHM.NS", "TECH MAHINDRA"), ("LTTS.NS", "L&T TECH"),
         ("MPHASIS.NS", "MPHASIS"), ("COFORGE.NS", "COFORGE"),
         ("PERSISTENT.NS", "PERSISTENT"), ("HEXT.NS", "HEXAWARE"),
         ("BSOFT.NS", "BIRLASOFT"), ("ZENSARTECH.NS", "ZENSAR"),
         ("TATAELXSI.NS", "TATA ELXSI"), ("KPITTECH.NS", "KPIT"),
         ("SONATSOFTW.NS", "SONATA"), ("MASTEK.NS", "MASTEK")]
IDX = [("^CNXIT", "NIFTY IT"), ("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX"),
       ("^INDIAVIX", "INDIA VIX"), ("USDINR=X", "USD/INR")]

EXPO = {"WIPRO.NS": (62.2, "AMERICAS 1+2 · FY26"),
        "INFY.NS": (56.1, "NORTH AMERICA · FY26"),
        "HCLTECH.NS": (56.0, "UNITED STATES · FY26"),
        "TCS.NS": (48.6, "NORTH AMERICA · FY26")}
ADR_ECHO = {"INFY.NS": 1.42, "WIPRO.NS": 0.00}
CLOSE_8OCT = {"INFY.NS": 997.00, "TCS.NS": 2076.00,
              "WIPRO.NS": 158.38, "HCLTECH.NS": 1176.90}

NEWS_QS = ['Infosys OR Wipro OR TCS OR "HCL Tech" OR "Nifty IT" PERM OR H-1B OR "green card" OR stocks',
           'Sensex OR "Nifty 50" today market']
SPILL = [("MPHASIS.NS", "US-HEAVY"), ("PERSISTENT.NS", "US-HEAVY"),
         ("HEXT.NS", "US-HEAVY"), ("TECHM.NS", "US-MOD"),
         ("COFORGE.NS", "US-MOD"), ("LTTS.NS", "US-MOD")]
TV_CHANNELS = [("ET NOW", "ETNOW"), ("NDTV PROFIT", "NDTVProfitIndia"),
               ("CNBC AWAAZ", "CNBCAwaaz"), ("ZEE BUSINESS", "ZeeBusiness")]
_TV_CACHE = {"ts": 0, "list": []}


def fetch(sym, rng="1mo", iv="1d"):
    u = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
         f"?range={rng}&interval={iv}")
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(r, context=ctx, timeout=25))
    res = d["chart"]["result"][0]
    ts = res.get("timestamp") or []
    cl = res["indicators"]["quote"][0].get("close") or []
    return res["meta"], [(t, c) for t, c in zip(ts, cl) if c is not None]


def row(sym, label, named=False):
    try:
        m, ser = fetch(sym)
        if len(ser) < 2:
            return dict(sym=sym, label=label, err="no history")
        last_t, last_c = ser[-1]
        prev_c = ser[-2][1]
        live = m.get("regularMarketPrice")
        if live and abs(live - last_c) / last_c > 1e-6:
            base = (prev_c if dt.datetime.utcfromtimestamp(last_t).date()
                    == dt.datetime.utcnow().date() else last_c)
            d1 = (live - base) / base * 100
            last_c = live
        else:
            d1 = (last_c - prev_c) / prev_c * 100
        w = ser[-6][1] if len(ser) >= 6 else ser[0][1]
        hi = max(c for _, c in ser)
        return dict(sym=sym, label=label, named=named,
                    last=round(last_c, 2), d1=round(d1, 2),
                    d5=round((last_c - w) / w * 100, 2),
                    frm_hi=round((last_c - hi) / hi * 100, 1),
                    spark=[round(c, 2) for _, c in ser[-20:]])
    except Exception as e:
        return dict(sym=sym, label=label, named=named, err=str(e)[:60])


def news():
    seen, out, ok = set(), [], False
    for q in NEWS_QS:
        try:
            u = (f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}"
                 f"&hl=en-IN&gl=IN&ceid=IN:en")
            r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            x = urllib.request.urlopen(r, context=ctx, timeout=20).read()
            for it in ET.fromstring(x).findall(".//item")[:12]:
                title = (it.findtext("title") or "").strip()
                if not title or title[:60] in seen:
                    continue
                seen.add(title[:60])
                pub = it.findtext("pubDate") or ""
                try:
                    ts = dt.datetime.strptime(pub[:25], "%a, %d %b %Y %H:%M:%S")
                except Exception:
                    ts = dt.datetime.utcnow()
                parts = title.rsplit(" - ", 1)
                t, s = (parts[0], parts[1]) if len(parts) == 2 else (title, "")
                out.append(dict(ts=ts.isoformat(), t=t[:120], s=s[:26],
                                l=it.findtext("link") or "#"))
            ok = True
        except Exception:
            continue
    out.sort(key=lambda i: i["ts"], reverse=True)
    return out[:18], ok


def live_tv():
    if time.time() - _TV_CACHE["ts"] < 600 and _TV_CACHE["list"]:
        return _TV_CACHE["list"]
    out = []
    for name, handle in TV_CHANNELS:
        try:
            u = f"https://www.youtube.com/@{handle}/live"
            r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            html = urllib.request.urlopen(r, context=ctx, timeout=15).read().decode("utf-8", "ignore")
            m = (re.search(r'<link rel="canonical" href="https://www\.youtube\.com/watch\?v=([\w-]{6,})"', html)
                 or re.search(r'"videoId":"([\w-]{6,})"', html))
            if m:
                out.append(dict(name=name, vid=m.group(1)))
        except Exception:
            continue
    if out:
        _TV_CACHE["ts"] = time.time(); _TV_CACHE["list"] = out
    return _TV_CACHE["list"]


def build_data():
    named = [row(s, n, True) for s, n in NAMED_IN]
    peers = [row(s, n) for s, n in PEERS]
    idx = [row(s, n) for s, n in IDX]
    wire, wire_ok = news()
    nmd = [r["d1"] for r in named if "err" not in r]
    ctl = [r["d1"] for r in peers if "err" not in r]
    med_n = round(statistics.median(nmd), 2) if nmd else 0.0
    med_c = round(statistics.median(ctl), 2) if ctl else 0.0
    sprd = round(med_n - med_c, 2)
    if abs(sprd) < 0.4:
        sig, sigc = "NO EVENT PREMIUM — TAPE PRICING MACRO, NOT PERM", "flat"
    elif sprd < 0:
        sig, sigc = f"PERM PREMIUM LIVE — NAMED LAGGING {abs(sprd):.2f} PTS", "neg"
    else:
        sig, sigc = f"EVENT FADED — NAMED LEADING {sprd:.2f} PTS", "pos"
    for r in named:
        if "err" in r:
            continue
        pct, basis = EXPO[r["sym"]]
        r["expo"], r["basis"] = pct, basis
        r["adr"] = ADR_ECHO.get(r["sym"])
        r["c8"] = CLOSE_8OCT.get(r["sym"])
        if r["adr"] is not None and r["c8"]:
            r["impl"] = round(r["c8"] * (1 + r["adr"] / 100), 1)
    # fear layer — India VIX live + deterministic desk sentiment
    vix = next((r for r in idx if r["sym"] == "^INDIAVIX" and "err" not in r), None)
    allit = [r["d1"] for r in named + peers if "err" not in r]
    breadth = round(100 * sum(1 for d in allit if d >= 0) / len(allit)) if allit else 50
    vixchg = vix["d1"] if vix else 0.0
    senti = max(5, min(95, round(50 + 10 * sprd + 0.5 * (breadth - 50) - 2 * vixchg)))
    byp = {r["sym"]: r for r in peers}
    spill = [dict(byp[s], tier=t) for s, t in SPILL if s in byp]
    errs = [r["sym"] for r in named + peers + idx if "err" in r]
    return dict(ts=dt.datetime.now().strftime("%H:%M:%S"),
                date=dt.datetime.now().strftime("%a %d %b %Y").upper(),
                named=named, peers=peers, idx=idx, wire=wire, spill=spill,
                wire_ok=wire_ok, med_n=med_n, med_c=med_c, sprd=sprd,
                sig=sig, sigc=sigc, errs=errs, tv=live_tv(),
                vix=(dict(last=vix["last"], d1=vix["d1"], spark=vix["spark"])
                     if vix else None),
                breadth=breadth, senti=senti, nfeeds=21 - len(errs))


SHELL = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>ZOLA DESK · PERM-1008</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
<noscript><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"></noscript>
<script defer src="https://cdn.jsdelivr.net/npm/motion@10.18.0/dist/motion.min.js" onerror="window.Motion=null"></script>
<style>
:root{--bg:#E4EAE5;--card:#FFFFFF;--ink:#113A2D;--ink2:#3A5A4D;--mu:#84998D;--ln:#D7E0D9;
--lime:#CDEA79;--limeink:#2A4A14;--deep:#124B3B;--red:#D8604F;--redbg:#F8E7E3;--grn:#1D9E75;
--rad:22px;--sh:0 1px 2px rgba(17,58,45,.05),0 10px 30px rgba(17,58,45,.08)}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font:13px/1.5 Inter,-apple-system,sans-serif;
-webkit-font-smoothing:antialiased;padding:22px clamp(14px,3vw,38px) 60px;position:relative}
body::before{content:"";position:fixed;top:-180px;left:12%;width:560px;height:420px;border-radius:50%;
background:radial-gradient(closest-side,rgba(205,234,121,.5),transparent 70%);
filter:blur(70px);pointer-events:none;z-index:0;animation:drift 14s ease-in-out infinite alternate}
body::after{content:"";position:fixed;bottom:-220px;right:6%;width:520px;height:400px;border-radius:50%;
background:radial-gradient(closest-side,rgba(18,75,59,.14),transparent 70%);
filter:blur(80px);pointer-events:none;z-index:0;animation:drift 18s ease-in-out infinite alternate-reverse}
@keyframes drift{from{transform:translate(0,0) scale(1)}to{transform:translate(60px,30px) scale(1.12)}}
.top,.bento,.sect,.acts,.tapec,.ft{position:relative;z-index:1}
a{color:inherit;text-decoration:none}
.num{font-family:"JetBrains Mono",monospace;font-variant-numeric:tabular-nums}
.top{display:flex;align-items:center;gap:14px;margin-bottom:18px;max-width:1280px;margin-inline:auto}
.lg{font-weight:800;letter-spacing:-.02em;font-size:17px}
.lg span{color:var(--grn)}
.pill{font-size:11px;font-weight:600;padding:4px 12px;border-radius:999px;background:var(--card);
box-shadow:var(--sh);color:var(--ink2)}
.pill.open{background:var(--lime);color:var(--limeink)}
.pill.pre{background:#FBEFD4;color:#8A5E12}
.dot{width:8px;height:8px;border-radius:50%;background:var(--grn);animation:pulse 1.8s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(29,158,117,.45)}50%{box-shadow:0 0 0 7px rgba(29,158,117,0)}}
.ck{margin-left:auto;font-size:15px;font-weight:700}
.bento{display:grid;grid-template-columns:repeat(12,1fr);gap:14px;max-width:1280px;margin:0 auto}
.c{background:var(--card);border-radius:var(--rad);box-shadow:var(--sh);padding:20px 22px;min-width:0}
.k{font-size:11px;font-weight:600;color:var(--mu);letter-spacing:.02em}
.big{font-size:clamp(26px,2.6vw,36px);font-weight:800;letter-spacing:-.03em;margin:2px 0 0;transition:color .4s}
.chg{display:inline-flex;align-items:center;gap:4px;font-size:12px;font-weight:700;
padding:3px 10px;border-radius:999px;margin-top:8px}
.chg.up{background:#E2F3D9;color:#2F6E1A}.chg.dn{background:var(--redbg);color:#A8392B}
.up{color:var(--grn)}.dn{color:var(--red)}
.flash{animation:fl .8s}
@keyframes fl{0%{transform:scale(1.025)}100%{}}
.s3{grid-column:span 3}.s4{grid-column:span 4}.s5{grid-column:span 5}.s6{grid-column:span 6}
.s7{grid-column:span 7}.s8{grid-column:span 8}.s12{grid-column:span 12}
.limec{background:var(--lime);color:var(--limeink)}
.limec .k{color:#5A7A34}.limec .chg.dn{background:#B8D45E;color:#6E2A1E}.limec .chg.up{background:#B8D45E;color:#2F5E14}
.deepc{background:var(--deep);color:#F2F7F0;box-shadow:0 1px 2px rgba(17,58,45,.2),0 14px 34px rgba(17,58,45,.3)}
.deepc .k{color:#9DBFAE}
.four{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.fc{background:var(--card);border-radius:18px;box-shadow:var(--sh);padding:15px 17px;transition:outline .4s;outline:2px solid transparent}
.fc.hot{outline-color:var(--red)}.fc.hotup{outline-color:var(--grn)}
.fc .nm{font-size:12px;font-weight:700}
.fc .pv{font-size:24px;font-weight:800;letter-spacing:-.03em;margin:3px 0 1px;transition:color .4s}
.fc .px{font-size:11px;color:var(--mu)}
.spk{margin-top:9px;opacity:.9}
.verd{font-size:16.5px;font-weight:700;line-height:1.55;letter-spacing:-.01em;display:flex;align-items:center;min-height:72px}
.focus .track{position:relative;height:12px;border-radius:999px;margin-top:16px;
background:linear-gradient(90deg,#E7B3AA,#F0DCA8 45%,#CBE6A8 65%,#9FD98A)}
.focus .pin{position:absolute;top:-4px;width:20px;height:20px;border-radius:50%;background:var(--ink);
border:3px solid #fff;box-shadow:0 2px 8px rgba(17,58,45,.35);transition:left 1.4s cubic-bezier(.25,.9,.3,1);transform:translateX(-50%)}
.focus .lb{display:flex;justify-content:space-between;font-size:10px;font-weight:600;color:var(--mu);margin-top:8px}
.tvg{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.tvc{position:relative;aspect-ratio:16/9;border-radius:14px;overflow:hidden;background:#0A0F0C}
.tvc iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.tvtag{position:absolute;left:0;right:0;bottom:0;display:flex;align-items:center;gap:6px;
padding:4px 9px;background:linear-gradient(transparent,rgba(5,12,8,.85));font-size:9px;
font-weight:700;letter-spacing:.06em;color:#DCE9DF;z-index:2}
.aud{margin-left:auto;cursor:pointer;border:0;border-radius:999px;background:rgba(255,255,255,.18);
color:#fff;font:700 9px Inter;letter-spacing:.05em;padding:3px 9px;backdrop-filter:blur(4px)}
.aud.on{background:var(--lime);color:var(--limeink)}
.news{display:flex;flex-direction:column;gap:9px;overflow-y:auto;max-height:352px;padding-right:4px}
.wi{background:#F4F8F3;border-radius:14px;padding:10px 13px;font-size:12px;line-height:1.5;font-weight:500}
.wi.fresh{animation:drop .6s cubic-bezier(.2,.9,.3,1.15) backwards}
@keyframes drop{0%{transform:translateY(-14px) scale(.97);opacity:0}100%{}}
.wi .age{font-size:10px;font-weight:700;color:var(--grn);margin-right:7px}
.wi .src{display:block;font-size:10px;color:var(--mu);margin-top:3px}
.sect{max-width:1280px;margin:26px auto 12px;display:flex;align-items:baseline;gap:12px}
.sect h2{font-size:17px;font-weight:800;letter-spacing:-.02em}
.sect .k{font-weight:500}
.acts{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;max-width:1280px;margin:0 auto}
.ac{background:var(--card);border-radius:var(--rad);box-shadow:var(--sh);padding:19px 22px;transition:outline .5s;outline:2px solid transparent}
.ac.win{outline-color:var(--red)}
.ahd{display:flex;align-items:center;gap:11px}
.ahd .nm{font-size:15px;font-weight:800}
.st{font-size:10px;font-weight:800;letter-spacing:.06em;padding:4px 11px;border-radius:999px}
.st.sd{background:#EDF2EC;color:var(--mu)}
.st.wa{background:#FBEFD4;color:#8A5E12;animation:blink 2.2s infinite}
.st.wi2{background:var(--red);color:#fff;animation:blink 1.1s infinite}
@keyframes blink{50%{opacity:.5}}
.ahd .pv{margin-left:auto;font-size:23px;font-weight:800;transition:color .4s}
.band{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:14px}
.bd{background:#F4F8F3;border-radius:12px;padding:8px 11px}
.bd .k{font-size:9.5px}
.bd .v{font-size:13.5px;font-weight:700;margin-top:1px}
.note{font-size:11px;color:var(--mu);margin-top:11px;font-weight:500}
.tapec{max-width:1280px;margin:0 auto}
table{width:100%;border-collapse:collapse}
th{text-align:right;font-size:10px;font-weight:700;color:var(--mu);padding:0 0 10px 14px;
border-bottom:1px solid var(--ln);letter-spacing:.03em}
th:nth-child(1){text-align:left;padding-left:0}
td{padding:10px 0 10px 14px;text-align:right;border-bottom:1px solid #EDF2EC;font-size:13px}
td:nth-child(1){text-align:left;padding-left:0;font-weight:700}
tr:last-child td{border-bottom:none}
tr.perm td{background:#FCF7EA}
tr.perm td:first-child{border-radius:12px 0 0 12px}tr.perm td:last-child{border-radius:0 12px 12px 0}
.tag{font-size:9px;font-weight:800;color:var(--red);background:var(--redbg);
border-radius:999px;padding:2px 8px;margin-left:8px;vertical-align:1px}
.dbar{display:inline-block;height:8px;border-radius:999px;vertical-align:0;transition:width .8s}
.ft{max-width:1280px;margin:22px auto 0;text-align:center;font-size:11px;color:var(--mu);font-weight:500}
@media(max-width:1080px){.s3,.s4,.s5{grid-column:span 6}.s7,.s8{grid-column:span 12}
.four{grid-template-columns:1fr 1fr}.acts{grid-template-columns:1fr}}
</style></head><body>

<div class="top">
<span class="dot"></span><span class="lg">ZOLA <span>Desk</span></span>
<span class="pill">Green-card order · 8 Oct</span>
<span class="pill" id="phase">—</span>
<span class="pill" id="feeds">—</span>
<span class="ck num" id="clock">--:--:--</span>
</div>

<div class="bento">
<div class="c s3"><div class="k">Nifty 50 · the market</div>
<div class="big num" id="n50">—</div><span class="chg num" id="n50c">—</span><div class="spk" id="n50s"></div></div>
<div class="c s3"><div class="k">Sensex</div>
<div class="big num" id="sx">—</div><span class="chg num" id="sxc">—</span><div class="spk" id="sxs"></div></div>
<div class="c s3 limec"><div class="k">Nifty IT · the sector</div>
<div class="big num" id="nit">—</div><span class="chg num" id="nitc">—</span><div class="spk" id="nits"></div></div>
<div class="c s3"><div class="k">India VIX · nervousness</div>
<div class="big num" id="vixv">—</div><span class="chg num" id="vixc">—</span><div class="spk" id="vixs"></div></div>

<div class="s12"><div class="four" id="four"></div></div>

<div class="c s8 deepc"><div class="k">What today means</div>
<div class="verd" id="verdict">Reading the market…</div></div>
<div class="c s4 focus"><div class="k">Fear ↔ Greed</div>
<div class="track"><div class="pin" id="npin" style="left:50%"></div></div>
<div class="lb"><span>FEAR</span><span>GREED</span></div></div>

<div class="c s12"><div class="k" style="margin-bottom:12px">The plan for today — step by step</div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px">
<div style="background:#F4F8F3;border-radius:14px;padding:12px 15px">
<div style="font-weight:800;font-size:12px;margin-bottom:3px">1 · Before 09:00</div>
<div style="font-size:12px;color:var(--ink2)">Generate the CDSL TPIN (edis.cdslindia.com) so your planned sells of existing holdings authorize without delay. The only pre-open action.</div></div>
<div style="background:#F4F8F3;border-radius:14px;padding:12px 15px">
<div style="font-weight:800;font-size:12px;margin-bottom:3px">2 · 09:15 – 09:30</div>
<div style="font-size:12px;color:var(--ink2)">Touch nothing. First prints lie — every US instrument that traded this news gapped down and was bought back within the session. Watch the verdict card only.</div></div>
<div style="background:#F4F8F3;border-radius:14px;padding:12px 15px">
<div style="font-weight:800;font-size:12px;margin-bottom:3px">3 · 09:45 first read</div>
<div style="font-size:12px;color:var(--ink2)">If the verdict still says the news is not moving the four, today is a normal market day — proceed with your planned sells on your own terms, or wait.</div></div>
<div style="background:#F4F8F3;border-radius:14px;padding:12px 15px">
<div style="font-weight:800;font-size:12px;margin-bottom:3px">4 · If a card turns WATCH</div>
<div style="font-size:12px;color:var(--ink2)">The news is starting to bite. Do not act on the first flip — it must hold through two refreshes (30 min) to mean anything.</div></div>
<div style="background:#FCF7EA;border-radius:14px;padding:12px 15px">
<div style="font-weight:800;font-size:12px;margin-bottom:3px">5 · If a card turns DECIDE</div>
<div style="font-size:12px;color:var(--ink2)">That is a decision point, not an instruction. Your rules apply: nothing past the 35% concentration line, size only what the exit-runway goal can absorb, exit known before entry.</div></div>
<div style="background:#F4F8F3;border-radius:14px;padding:12px 15px">
<div style="font-weight:800;font-size:12px;margin-bottom:3px">6 · 15:30 close</div>
<div style="font-size:12px;color:var(--ink2)">Whatever happened, record the outcome in the loop tonight — win or loss. That is how this becomes a learned play instead of a one-off punt.</div></div>
</div></div>

<div class="c s7"><div class="k" style="margin-bottom:12px">Live TV — tap audio to listen</div>
<div class="tvg" id="tvgrid"></div></div>
<div class="c s5"><div class="k" style="margin-bottom:12px">Latest on the sector <span id="wst"></span></div>
<div class="news" id="wire"></div></div>
</div>

<div class="sect"><h2>The four, up close</h2><span class="k">reference prints, not targets — the call is yours</span></div>
<div class="acts" id="cards"></div>

<div class="sect"><h2>The whole sector</h2><span class="k">sorted worst first · amber rows are the named four</span></div>
<div class="c tapec"><table><thead><tr><th>Name</th><th>Price</th><th>Today</th><th></th><th>5 days</th></tr></thead>
<tbody id="tape"></tbody></table></div>

<div class="ft">Live prices · updates every minute · states are rule outputs, the decision is yours</div>

<script>
const $=id=>document.getElementById(id);
let prev={};
const STAKE=Math.max(0,parseInt(new URLSearchParams(location.search).get("stake"))||0);
const cls=v=>v>=0?"up":"dn";
const fmt=(v,p=2)=>(v>=0?"+":"")+v.toFixed(p);
const inr=v=>v.toLocaleString("en-IN");
function flash(el){if(!el)return;el.classList.remove("flash");void el.offsetWidth;el.classList.add("flash")}
function phase(){const m=new Date().getHours()*60+new Date().getMinutes();
if(m<540)return["Pre-market",""];if(m<555)return["Opening auction","pre"];
if(m<930)return["Market open","open"];return["Closed",""]}
function tick(){$("clock").textContent=new Date().toTimeString().slice(0,8);
const[p,c]=phase();$("phase").textContent=p;$("phase").className="pill "+c}
setInterval(tick,1000);tick();
function spark(vals,w,h,col){if(!vals||vals.length<2)return"";
const lo=Math.min(...vals),hi=Math.max(...vals),r=(hi-lo)||1;
const pts=vals.map((v,i)=>`${(i*w/(vals.length-1)).toFixed(1)},${(h-((v-lo)/r)*(h-3)-1.5).toFixed(1)}`).join(" ");
const c=col||(vals[vals.length-1]>=vals[0]?"#1D9E75":"#D8604F");
return `<svg width="${w}" height="${h}"><polyline points="${pts}" fill="none" stroke="${c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`}
function setNum(el,val,render){if(!el)return;
const from=el._v===undefined?val:el._v;el._v=val;
if(from===val||!window.Motion){el.textContent=render(val);return}
try{Motion.animate(from,val,{duration:.7,easing:[.22,.9,.3,1],onUpdate:v=>el.textContent=render(v)})}
catch(e){el.textContent=render(val)}}
const age=iso=>{const s=(Date.now()-new Date(iso+"Z").getTime())/1e3;
return s<3600?Math.max(1,Math.round(s/60))+"m":s<86400?Math.round(s/3600)+"h":Math.round(s/86400)+"d"};

let tvlist=[],audioOn=null;
function renderTV(list){
if(!list||!list.length){$("tvgrid").innerHTML='<div class="k">Streams resolving — retries each minute</div>';return}
if(JSON.stringify(list)===JSON.stringify(tvlist))return;
tvlist=list;
$("tvgrid").innerHTML=list.map((c,i)=>`<div class="tvc">
<iframe id="yt${i}" src="https://www.youtube.com/embed/${c.vid}?autoplay=1&mute=1&playsinline=1&enablejsapi=1&controls=0"
allow="autoplay; encrypted-media"></iframe>
<div class="tvtag">${c.name}<button class="aud" id="aud${i}" onclick="audio(${i})">AUDIO</button></div></div>`).join("");
audioOn=null}
function ytCmd(i,f2,a){const f=$("yt"+i);if(f)f.contentWindow.postMessage(JSON.stringify({event:"command",func:f2,args:a||[]}),"*")}
function audio(i){tvlist.forEach((_,j)=>{ytCmd(j,"mute");const b=$("aud"+j);if(b)b.classList.remove("on")});
if(audioOn===i){audioOn=null;return}
ytCmd(i,"unMute");ytCmd(i,"setVolume",[80]);$("aud"+i).classList.add("on");audioOn=i}

function state(sprd,r){
if(sprd<=-0.7&&r.impl&&r.last<=r.impl)return["wi2","DECIDE","The news is fully in the price and this stock is at the level the US market set. If you were ever going to act, this is the moment you assess."];
if(sprd<=-0.4)return["wa","WATCH","The news is starting to bite these four more than the rest. Not confirmed yet."];
return["sd","WAIT","Nothing special is happening to this stock beyond the whole market. Acting now = betting on the market, not the news."]}

function idxCard(d,sym,v,c,sp,spcol){const r=d.idx.find(x=>x.sym===sym);
if(!r||r.err){$(v).textContent="—";return null}
setNum($(v),r.last,x=>inr(Math.round(x)));
const el=$(c);el.textContent=fmt(r.d1)+"%";el.className="chg num "+cls(r.d1);
if(sp&&$(sp))$(sp).innerHTML=spark(r.spark,150,30,spcol);
if(prev[v]!==undefined&&prev[v]!==r.d1)flash($(v).parentElement);prev[v]=r.d1;return r}

async function load(){
try{
const d=await(await fetch("/zola-itshock-data.json?t="+Date.now())).json();
$("feeds").textContent=d.errs.length?("Feeds "+d.nfeeds+"/21"):"All feeds live";
idxCard(d,"^NSEI","n50","n50c","n50s");idxCard(d,"^BSESN","sx","sxc","sxs");
const nit=idxCard(d,"^CNXIT","nit","nitc","nits","#2A4A14");
const vx=d.idx.find(x=>x.sym==="^INDIAVIX");
if(vx&&!vx.err){setNum($("vixv"),vx.last,x=>x.toFixed(2));
const vc=$("vixc");vc.textContent=fmt(vx.d1)+"%";
vc.className="chg num "+(vx.d1>=0?"dn":"up");
if($("vixs"))$("vixs").innerHTML=spark(vx.spark,150,30,vx.d1>=0?"#D8604F":"#1D9E75");
if(prev.vixv!==undefined&&prev.vixv!==vx.d1)flash($("vixv").parentElement);prev.vixv=vx.d1}
renderTV(d.tv);
$("four").innerHTML=d.named.map(r=>{
if(r.err)return`<div class="fc"><div class="nm">${r.label}</div><div class="k">no data</div></div>`;
const hot=Math.abs(r.d1)>=2?(r.d1<0?" hot":" hotup"):"";
return`<div class="fc${hot}" id="t_${r.sym}"><div class="nm">${r.label}</div>
<div class="pv num ${cls(r.d1)}" id="tp_${r.sym}">${fmt(r.d1)}%</div>
<div class="px num">₹ ${inr(r.last)}</div>
<div class="spk">${spark(r.spark,120,24)}</div></div>`}).join("");
d.named.forEach(r=>{if(!r.err)setNum($("tp_"+r.sym),r.d1,x=>fmt(x)+"%")});
d.named.forEach(r=>{if(!r.err&&prev["t_"+r.sym]!==undefined&&prev["t_"+r.sym]!==r.d1)flash($("t_"+r.sym));prev["t_"+r.sym]=r.d1});
const V={flat:"The green-card news is not moving these stocks. Whatever rise or fall you see today is the whole market — not the order.",
neg:"The news is hitting. The four named stocks are falling harder than the rest of the sector.",
pos:"The news has been shrugged off — the four named stocks are doing better than the rest of the sector."};
$("verdict").textContent=V[d.sigc]||d.sig;
$("npin").style.left=d.senti+"%";
$("cards").innerHTML=d.named.filter(r=>!r.err).sort((a,b)=>b.expo-a.expo).map(r=>{
const[sc,sl,st]=state(d.sprd,r);
return`<div class="ac${sc==="wi2"?" win":""}" id="c_${r.sym}"><div class="ahd">
<span class="nm">${r.label}</span><span class="st ${sc}">${sl}</span>
<span class="pv num ${cls(r.d1)}">${fmt(r.d1)}%</span></div>
<div class="band">
<div class="bd"><div class="k">Price now</div><div class="v num">₹ ${inr(r.last)}</div></div>
<div class="bd"><div class="k">US-session level</div><div class="v num">${r.impl?"₹ "+inr(r.impl):"—"}</div></div>
<div class="bd"><div class="k">Close before news</div><div class="v num">₹ ${inr(r.c8)}</div></div>
<div class="bd"><div class="k">Off 1-month high</div><div class="v num dn">${r.frm_hi.toFixed(1)}%</div></div>
</div>
${STAKE>0?`<div class="note" style="margin-top:8px;font-weight:600;color:var(--ink)">Your stake: ₹${STAKE.toLocaleString("en-IN")} ≈ ${Math.floor(STAKE/r.last)} shares at the live price — arithmetic, not a recommendation. Split and moment are yours.</div>`:""}
<div class="note">${st}</div></div>`}).join("");
d.named.forEach(r=>{if(!r.err&&prev["c_"+r.sym]!==undefined&&prev["c_"+r.sym]!==r.d1)flash($("c_"+r.sym));prev["c_"+r.sym]=r.d1});
const merged=[...d.named,...d.peers];
const ok=merged.filter(r=>!r.err).sort((a,b)=>a.d1-b.d1);
const maxab=Math.max(.5,...ok.map(r=>Math.abs(r.d1)));
$("tape").innerHTML=ok.map(r=>{
const w=Math.abs(r.d1)/maxab*64;
return`<tr class="${r.named?"perm":""}">
<td>${r.label}${r.named?'<span class="tag">NAMED</span>':''}</td>
<td class="num">₹ ${inr(r.last)}</td>
<td class="num" style="font-weight:800" ><span class="${cls(r.d1)}">${fmt(r.d1)}%</span></td>
<td style="text-align:left;width:76px"><span class="dbar" style="width:${w.toFixed(0)}px;background:${r.d1>=0?"#9FD98A":"#E7A79B"}"></span></td>
<td class="num ${cls(r.d5)}">${fmt(r.d5)}%</td></tr>`}).join("");
$("wst").textContent=d.wire_ok?"· live":"· paused";
const seen=prev.wire||new Set();let fi=0;
$("wire").innerHTML=d.wire.slice(0,12).map(i=>{
const fresh=!seen.has(i.t.slice(0,60));
return`<div class="wi${fresh?" fresh":""}"${fresh?` style="animation-delay:${(fi++)*100}ms"`:""}>
<span class="age">${age(i.ts)}</span><a href="${i.l}" target="_blank">${i.t}</a>
<span class="src">${i.s}</span></div>`}).join("");
prev.wire=new Set(d.wire.map(i=>i.t.slice(0,60)));
if(!prev._entered&&window.Motion){prev._entered=1;
try{document.querySelectorAll(".c,.fc,.ac").forEach((el,i)=>{
Motion.animate(el,{opacity:[0,1],transform:["translateY(16px)","translateY(0)"]},
{duration:.55,delay:i*0.045,easing:[.22,.9,.3,1]})})}catch(e){}}
}catch(e){}}
load();setInterval(load,15000);
</script></body></html>"""


def main():
    live = "--live" in sys.argv

    def emit(line):
        print(line, flush=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(SHELL)

    if not live:
        d = build_data()
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(d, f)
        print(f"v8 written · spread {d['sprd']:+.2f} · senti {d['senti']} · "
              f"vix {'OK' if d['vix'] else 'ERR'} · errs {d['errs'] or 'none'}")
        return

    emit("LIVE mode v8 — 60s cycles until 15:45 IST.")
    while True:
        try:
            d = build_data()
            with open(OUT_JSON, "w", encoding="utf-8") as f:
                json.dump(d, f)
            okn = [r for r in d["named"] if "err" not in r]
            worst = min(okn, key=lambda r: r["d1"]) if okn else None
            nit = next((r for r in d["idx"] if r["sym"] == "^CNXIT" and "err" not in r), None)
            emit(f"[{dt.datetime.now():%d %b %Y · %H:%M:%S} IST] spread {d['sprd']:+.2f} pts · "
                 f"it {nit['d1']:+.2f}% · worst {worst['label']} {worst['d1']:+.2f}% · "
                 f"senti {d['senti']} · errs {d['errs'] or 'none'} · "
                 f"wire {'OK' if d['wire_ok'] else 'BLOCKED'}"
                 if worst and nit else
                 f"[{dt.datetime.now():%d %b %Y · %H:%M:%S} IST] spread {d['sprd']:+.2f} pts · "
                 f"senti {d['senti']} · errs {d['errs'] or 'none'}")
        except Exception as e:
            emit(f"cycle failed: {str(e)[:80]} — retrying in 60s")
        now = dt.datetime.now()
        if now.hour > 15 or (now.hour == 15 and now.minute >= 45):
            emit("market closed — live loop ended.")
            break
        time.sleep(60)


if __name__ == "__main__":
    main()
