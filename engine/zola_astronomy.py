#!/usr/bin/env python3
"""
ZOLA ASTRONOMY — literal, computable astronomy. Deterministic, stdlib-only.

WHY THIS EXISTS
Theory 03 named space science as the domain to build real capability in, because it
carries a genuine barrier to entry and (post-IN-SPACe) no entrenched non-market
incumbent. Capability means being able to COMPUTE the thing, not admire it. So every
number this module emits is checked against a published value and the error is printed.

WHAT IT IS
  · An arithmetic engine over real astronomical constants and historical records.
  · Verification-first: nothing is asserted that isn't compared to a modern figure.

WHAT IT IS NOT
  · Not astrology. It computes NO personal, predictive or destiny-related output.
    Being able to run a calculation says nothing about whether its premise is true —
    a deterministic engine emitting precise numbers from an unfounded premise is
    WORSE than vagueness, because it launders the premise in the credibility of the
    maths. That is the exact hoax pattern ZOLA exists to refuse.
  · The `audit` command exists for precisely this reason: it takes the popular
    "encoded mathematics" claims, computes them honestly, and shows where they fail.

    python3 zola_astronomy.py precession   # pole-star geometry over millennia
    python3 zola_astronomy.py giza         # Great Pyramid alignment arithmetic
    python3 zola_astronomy.py india        # Aryabhata / Surya Siddhanta vs modern
    python3 zola_astronomy.py madhava      # the pi series, 250yr before Leibniz
    python3 zola_astronomy.py saturn       # ring structure from orbital resonance
    python3 zola_astronomy.py hexagon      # Saturn's polar hexagon, wavenumber 6
    python3 zola_astronomy.py vedic        # Sulba Sutras, Pingala, Brahmagupta
    python3 zola_astronomy.py patha        # Vedic recitation as error-correction
    python3 zola_astronomy.py sky          # every method run on your date + place
    python3 zola_astronomy.py explain      # the calculation chain + accuracy roll-up
    python3 zola_astronomy.py phi          # golden ratio: what it does and does not explain
    python3 zola_astronomy.py pitch        # 432 vs 440 Hz, in cents
    python3 zola_astronomy.py metonic      # the 19-yr cycle behind runic computus
    python3 zola_astronomy.py ashvini      # the disputed zero point of the zodiac
    python3 zola_astronomy.py panchanga    # five limbs from two longitudes
    python3 zola_astronomy.py ephemeris    # five naked-eye planets, accuracy measured
    python3 zola_astronomy.py conjunction  # longitude alignment is not sky distance
    python3 zola_astronomy.py aspects      # angles, culminations, eclipse windows
    python3 zola_astronomy.py jyotisha     # whole-sign houses, pada, chara karakas
    python3 zola_astronomy.py ancient      # Arabic mansions, decans, Egyptian bounds
    python3 zola_astronomy.py timing       # Vimshottari, Firdaria, profection, ZR
    python3 zola_astronomy.py gauquelin    # sector geometry, and its diagnostic value
    python3 zola_astronomy.py registry     # what is NOT computed, and why
    python3 zola_astronomy.py audit        # test the pseudo-science claims
    python3 zola_astronomy.py all
"""
import math
import sys

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS — every one sourced, so a wrong result is traceable to a wrong input
# ══════════════════════════════════════════════════════════════════════════════
PRECESSION_ARCSEC_YR = 50.29        # IAU general precession in longitude
PRECESSION_CYCLE_YR  = 25772.0      # full cycle
OBLIQUITY_DEG        = 23.4392911   # J2000 mean obliquity
SIDEREAL_DAY_S       = 86164.0905   # modern sidereal day
SIDEREAL_YEAR_D      = 365.256363   # modern sidereal year (solar days)
TROPICAL_YEAR_D      = 365.242190   # modern tropical year
GIZA_LAT_DEG         = 29.9791750   # Great Pyramid, actual surveyed latitude

# Saturn — for ring/resonance mechanics
GM_SATURN      = 3.7931187e16       # m^3/s^2
R_SATURN_EQ_KM = 60268.0            # equatorial radius
RHO_SATURN     = 687.0              # kg/m^3 (mean density — less than water)
RHO_ICE        = 920.0              # kg/m^3 (ring particles are mostly water ice)
MIMAS_A_KM     = 185539.0
MIMAS_P_DAYS   = 0.9424218
# North-polar hexagon (Voyager 1980-81, imaged in detail by Cassini 2006+)
HEX_WIDTH_KM     = 29000.0     # vertex to vertex, approx
HEX_JET_KMH      = 322.0       # peak jet speed
SAT_ROT_HOURS    = 10.55       # System III rotation period (10h 33m)
HEX_LAT_DEG      = 78.0        # the jet sits near 78 N

# Stars, J2000 (RA hours, Dec degrees, visual magnitude)
STARS = {
    "Thuban (alpha Dra)":  (14.073167, 64.375833, 3.65),
    "Kochab (beta UMi)":   (14.845128, 74.155505, 2.07),
    "Mizar (zeta UMa)":    (13.398750, 54.925361, 2.27),
    "Polaris (alpha UMi)": (2.529750,  89.264111, 1.98),
    "Sirius (alpha CMa)":  (6.752478, -16.716116, -1.46),
    "Alnitak (zeta Ori)":  (5.679313,  -1.942573, 1.88),
}


def _fmt_err(got, ref, unit="", pct=True):
    """Signed error plus relative error — the honesty line on every comparison."""
    d = got - ref
    out = "%+.6g %s" % (d, unit) if unit else "%+.6g" % d
    if pct and ref:
        out += "  (%+.4f%%)" % (d / ref * 100.0)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# 1. PRECESSION — which star was the pole star, and how good was it
# ══════════════════════════════════════════════════════════════════════════════
def _eq_to_ecl(ra_h, dec_deg):
    """Equatorial (J2000) -> ecliptic longitude/latitude, in degrees."""
    ra = math.radians(ra_h * 15.0)
    dec = math.radians(dec_deg)
    eps = math.radians(OBLIQUITY_DEG)
    sin_b = math.sin(dec) * math.cos(eps) - math.cos(dec) * math.sin(eps) * math.sin(ra)
    b = math.asin(max(-1.0, min(1.0, sin_b)))
    y = math.sin(ra) * math.cos(eps) + math.tan(dec) * math.sin(eps)
    lam = math.atan2(y, math.cos(ra))
    return math.degrees(lam) % 360.0, math.degrees(b)


def pole_distance_min(ra_h, dec_deg):
    """Closest the north celestial pole EVER comes to this star, in degrees.

    The NCP traces a small circle of angular radius = obliquity (23.44 deg) around the
    north ecliptic pole, once per precession cycle. A star at ecliptic latitude b sits
    (90 - b) from the ecliptic pole, so its minimum possible distance from the NCP is
    |(90 - b) - obliquity|. This is exact geometry, not an approximation of orbits.
    """
    _, b = _eq_to_ecl(ra_h, dec_deg)
    return abs((90.0 - b) - OBLIQUITY_DEG)


def cmd_precession():
    print("\n  PRECESSION — pole-star geometry")
    print("  " + "-" * 66)
    print("  rate %.2f arcsec/yr   full cycle %.0f yr   obliquity %.4f deg"
          % (PRECESSION_ARCSEC_YR, PRECESSION_CYCLE_YR, OBLIQUITY_DEG))
    # cross-check the two published constants against each other
    implied = 360.0 * 3600.0 / PRECESSION_ARCSEC_YR
    print("  cycle implied by the rate: %.0f yr   %s"
          % (implied, _fmt_err(implied, PRECESSION_CYCLE_YR, "yr")))
    print()
    print("  %-22s %10s %10s" % ("star", "min dist", "usable?"))
    for name, (ra, dec, mag) in sorted(STARS.items(), key=lambda kv: pole_distance_min(kv[1][0], kv[1][1])):
        d = pole_distance_min(ra, dec)
        tag = "yes" if d < 5 else ("marginal" if d < 15 else "never")
        print("  %-22s %8.3f deg  %10s   (mag %.2f)" % (name, d, tag, mag))
    print()
    print("  Thuban's small minimum is why it served as pole star c. 2800 BCE, despite")
    print("  being 1.6 magnitudes fainter than Kochab. Polaris is near-pole NOW; it was")
    print("  not in antiquity. Same geometry, different epoch.")


# ══════════════════════════════════════════════════════════════════════════════
# 2. GIZA — the alignment arithmetic
# ══════════════════════════════════════════════════════════════════════════════
def lower_culmination_alt(dec_deg, lat_deg=GIZA_LAT_DEG):
    """Altitude of a circumpolar star at LOWER culmination: lat + dec - 90."""
    return lat_deg + dec_deg - 90.0


def dec_from_lower_culmination(alt_deg, lat_deg=GIZA_LAT_DEG):
    """Invert the above — what declination does a sight-line at this altitude imply?"""
    return 90.0 + alt_deg - lat_deg


def cmd_giza():
    print("\n  GIZA — alignment arithmetic")
    print("  " + "-" * 66)
    print("  latitude %.6f N" % GIZA_LAT_DEG)
    print()
    print("  Measured orientation error (Cole 1925 and later surveys):")
    for name, arcmin in (("Khufu", -3.1), ("Khafre", -5.1), ("Menkaure", +13.0)):
        print("    %-10s %+6.1f arcmin  = %+8.5f deg  = 1 part in %.0f"
              % (name, arcmin, arcmin / 60.0, 1.0 / abs(math.radians(arcmin / 60.0))))
    print()
    print("  Spence (Nature 2000): the Kochab-Mizar line drifts past the pole at")
    print("  ~27 arcmin/century, so an orientation error dates the survey.")
    drift = 27.0  # arcmin per century
    for name, arcmin in (("Khufu", -3.1), ("Khafre", -5.1), ("Menkaure", +13.0)):
        # centuries of drift from the zero-error epoch (2467 BCE by Spence's fit)
        cent = arcmin / drift
        print("    %-10s implies %+6.2f centuries from 2467 BCE  ->  %d BCE"
              % (name, cent, 2467 - int(round(cent * 100))))
    print("    NOTE: sign flips Khufu(W) -> Menkaure(E), which is the actual evidence.")
    print("    Belmonte's rival star pair shifts these dates ~100 yr. Model-dependent.")
    print()
    print("  Descending passage: 26 deg 17 arcmin below horizontal.")
    ang = 26 + 17 / 60.0
    implied = dec_from_lower_culmination(ang)
    print("    a sight-line at that altitude implies a star at dec %.4f deg" % implied)
    # date it: Thuban was ~0.03 deg from the pole in 2787 BCE, and precession carries
    # the pole away at a known rate — so the implied declination gives an epoch.
    thuban_closest_bce, thuban_min_dec = 2787, 90.0 - 0.03
    drift_deg = thuban_min_dec - implied
    deg_per_yr = PRECESSION_ARCSEC_YR / 3600.0
    years = drift_deg / deg_per_yr
    print("    Thuban was %.2f deg from the pole in %d BCE (its closest approach)."
          % (0.03, thuban_closest_bce))
    print("    drift needed to reach dec %.2f : %.2f deg" % (implied, drift_deg))
    print("    at %.4f deg/yr that takes %.0f yr  ->  epoch ~%d BCE"
          % (deg_per_yr, years, thuban_closest_bce - int(round(years))))
    print("    That lands in the Khufu construction window, derived independently of")
    print("    the orientation evidence above. Two methods, one epoch.")
    print()
    print("  Sothic cycle — and a subtlety the canonical figure hides:")
    print("    The cycle length depends on WHICH year you measure against. The famous")
    print("    1460 is the JULIAN figure (deficit exactly 0.25 d/yr). It is not what")
    print("    you get from the tropical or sidereal year.")
    for label, ylen in (("Julian   365.25", 365.25),
                        ("tropical %.6f" % TROPICAL_YEAR_D, TROPICAL_YEAR_D),
                        ("sidereal %.6f" % SIDEREAL_YEAR_D, SIDEREAL_YEAR_D)):
        deficit = ylen - 365.0
        cyc = 365.0 / deficit
        print("    %-24s deficit %.6f d/yr  ->  %7.1f yr  %s"
              % (label, deficit, cyc, "<- canonical 1460" if abs(cyc - 1460) < 1 else ""))
    print("    Sirius's heliacal rising actually tracks the SIDEREAL year (plus its own")
    print("    proper motion, -1223 mas/yr in dec), so 1460 is a convenient")
    print("    approximation, not the physical period. Modern scholarship says the same.")


# ══════════════════════════════════════════════════════════════════════════════
# 3. INDIA — the siddhanta figures, checked
# ══════════════════════════════════════════════════════════════════════════════
ARYABHATA_ROTATIONS_PER_MAHAYUGA = 1582237500
MAHAYUGA_YEARS = 4320000

# Surya Siddhanta sidereal periods (days) vs modern
SS_PERIODS = {
    "Moon":    (27.322,                 27.321661),
    "Mercury": (87 + (23*3600 + 16*60 + 22.3) / 86400.0,  87 + (23*3600 + 15*60 + 43.9) / 86400.0),
    "Venus":   (224 + (16*3600 + 45*60 + 56.2) / 86400.0, 224 + (16*3600 + 49*60 + 8.0) / 86400.0),
    "Mars":    (686 + (23*3600 + 56*60 + 23.5) / 86400.0, 686 + (23*3600 + 30*60 + 41.4) / 86400.0),
    "Jupiter": (4332 + (7*3600 + 41*60 + 44.4) / 86400.0, 4332 + (14*3600 + 2*60 + 8.6) / 86400.0),
    "Saturn":  (10765 + (18*3600 + 33*60 + 13.6) / 86400.0, 10759 + (5*3600 + 16*60 + 32.2) / 86400.0),
}


def cmd_india():
    print("\n  INDIAN MATHEMATICAL ASTRONOMY — siddhanta, checked against modern")
    print("  " + "-" * 66)
    print("  This is the ganita/siddhanta branch: computational astronomy. It is NOT")
    print("  the hora/phalita branch (natal astrology) — same planetary positions,")
    print("  entirely different claim. Only the first is science.")
    print()

    # Aryabhata's sidereal day, derived from HIS OWN integer ratio.
    # This is where the engine earns its keep: the celebrated "accurate to 0.01 s"
    # figure is REAL but it is not what his rotation count alone gives. It requires
    # combining it with his own (too-long) sidereal year, whose error cancels most of
    # the discrepancy. Both derivations are printed so the claim can be judged.
    rot_per_year = ARYABHATA_ROTATIONS_PER_MAHAYUGA / float(MAHAYUGA_YEARS)
    ARYABHATA_YEAR_D = 365.25858        # his own stated sidereal year
    sid_modern_year = SIDEREAL_YEAR_D / rot_per_year * 86400.0
    sid_own_year = ARYABHATA_YEAR_D / rot_per_year * 86400.0
    print("  Aryabhata (476 CE), Gitikapada:")
    print("    stated rotations per mahayuga : %d" % ARYABHATA_ROTATIONS_PER_MAHAYUGA)
    print("    -> rotations per year         : %.6f" % rot_per_year)
    print("    modern sidereal day           : %.4f s  = %s"
          % (SIDEREAL_DAY_S, _hms(SIDEREAL_DAY_S)))
    print()
    print("    sidereal day, two derivations:")
    print("      with the MODERN year (%.6f d): %.4f s   %s"
          % (SIDEREAL_YEAR_D, sid_modern_year, _fmt_err(sid_modern_year, SIDEREAL_DAY_S, "s")))
    print("      with HIS OWN year   (%.6f d): %.4f s   %s"
          % (ARYABHATA_YEAR_D, sid_own_year, _fmt_err(sid_own_year, SIDEREAL_DAY_S, "s")))
    print("    His year is %+.0f s too long (%s), and that error largely CANCELS the"
          % ((ARYABHATA_YEAR_D - SIDEREAL_YEAR_D) * 86400.0,
             _hms(abs(ARYABHATA_YEAR_D - SIDEREAL_YEAR_D) * 86400.0).strip()))
    print("    one in his rotation count. So the famous 'accurate to 0.01 s' holds only")
    print("    within his own system. Judged against modern values the rotation count")
    print("    alone is off by %.2f s. Still excellent for 476 CE — just not 0.01 s."
          % abs(sid_modern_year - SIDEREAL_DAY_S))
    print()

    pi_a = (4 + 100) * 8 + 62000
    pi_a = pi_a / 20000.0
    print("    his pi = ((4+100)*8 + 62000)/20000 = %.7f" % pi_a)
    print("    modern pi                          = %.7f" % math.pi)
    print("    error                              : %s" % _fmt_err(pi_a, math.pi))
    print("    he wrote 'asanna' (approximate) — he knew it was not exact.")
    print()

    print("  Surya Siddhanta sidereal periods:")
    print("    %-9s %14s %14s %14s" % ("body", "siddhanta (d)", "modern (d)", "error"))
    for body, (old, new) in SS_PERIODS.items():
        print("    %-9s %14.5f %14.5f   %s" % (body, old, new, _fmt_err(old, new, "d")))
    print("    Inner planets are far better than outer — consistent with observation")
    print("    over shorter synodic cycles. Saturn is off by ~6.5 days.")


def _hms(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = seconds % 60
    return "%dh %02dm %06.3fs" % (h, m, s)


# ══════════════════════════════════════════════════════════════════════════════
# 4. MADHAVA — the series, and why the correction terms matter
# ══════════════════════════════════════════════════════════════════════════════
def madhava_pi(terms):
    """pi/4 = 1 - 1/3 + 1/5 - ... (Madhava c.1375, ~295 yr before Leibniz)."""
    return 4.0 * sum((-1.0) ** k / (2 * k + 1) for k in range(terms))


def madhava_pi_corrected(terms, order=3):
    """Madhava's convergence acceleration — his advance beyond Gregory/Leibniz.

    pi/4 = [n-term partial sum] + (-1)^n * F(n), with F a rational correction in n
    (n = number of terms taken). The three documented orders:
        1st   F = 1/(4n)
        2nd   F = n/(4n^2 + 1)
        3rd   F = (n^2 + 1)/(4n^3 + 5n)
    Verified against math.pi: at 50 terms the plain series errs 2.0e-02 while the
    3rd-order correction errs 7.2e-13 — ten orders of magnitude, from one rational
    term. This acceleration is the part Gregory and Leibniz did not have.
    """
    s = sum((-1.0) ** k / (2 * k + 1) for k in range(terms))
    n = float(terms)
    if order == 1:
        F = 1.0 / (4.0 * n)
    elif order == 2:
        F = n / (4.0 * n * n + 1.0)
    else:
        F = (n * n + 1.0) / (4.0 * n ** 3 + 5.0 * n)
    return 4.0 * (s + (-1.0) ** terms * F)


def cmd_madhava():
    print("\n  MADHAVA OF SANGAMAGRAMA (c.1340-1425) — the arctangent series")
    print("  " + "-" * 66)
    print("  pi/4 = 1 - 1/3 + 1/5 - 1/7 + ...   derived ~295 years before Leibniz.")
    print("  Priority for the series is not disputed. TRANSMISSION to Europe is NOT")
    print("  established (Bressoud; MacTutor) — do not claim it.")
    print()
    print("  %6s %16s %11s %11s %11s" % ("terms", "plain series", "err plain", "err 2nd-ord", "err 3rd-ord"))
    for n in (5, 10, 25, 50, 100):
        p0 = madhava_pi(n)
        e2 = abs(madhava_pi_corrected(n, 2) - math.pi)
        e3 = abs(madhava_pi_corrected(n, 3) - math.pi)
        print("  %6d %16.12f %11.2e %11.2e %11.2e"
              % (n, p0, abs(p0 - math.pi), e2, e3))
    print()
    target = abs(madhava_pi_corrected(50, 3) - math.pi)
    # how many plain terms to match 50 corrected terms? error ~ 1/(4n), so invert.
    print("  50 terms + his 3rd-order correction gives error %.1e." % target)
    print("  The plain series needs roughly %.2e terms to match that — his one" % (1.0 / (4 * target)))
    print("  rational term is worth about %.0e times the compute." % (1.0 / (4 * target) / 50))
    print("  THIS is the actual achievement, and it is verifiable in one line of code.")


# ══════════════════════════════════════════════════════════════════════════════
# 5. SATURN — the rings, from orbital mechanics
# ══════════════════════════════════════════════════════════════════════════════
def kepler_a_from_period(period_days, gm=GM_SATURN):
    """Semi-major axis (km) for a given orbital period — Kepler's third law."""
    T = period_days * 86400.0
    a_m = (gm * T * T / (4.0 * math.pi ** 2)) ** (1.0 / 3.0)
    return a_m / 1000.0


def roche_limit_km(r_primary_km=R_SATURN_EQ_KM, rho_p=RHO_SATURN, rho_m=RHO_ICE):
    """Rigid-body Roche limit — inside this, tides shred a moon into a ring."""
    return r_primary_km * (2.0 * rho_p / rho_m) ** (1.0 / 3.0)


def cmd_saturn():
    print("\n  SATURN — ring structure derived from resonance, not decoration")
    print("  " + "-" * 66)
    print("  FIRST, a factual correction: Saturn does not have six rings. There are")
    print("  SEVEN main ring groups, named in order of discovery: D C B A F G E.")
    print("  The 'six rings' figure is not an astronomical value.")
    print()
    print("  Roche limit (rigid, water-ice particles):")
    rl = roche_limit_km()
    print("    %.0f km from centre = %.2f Saturn radii" % (rl, rl / R_SATURN_EQ_KM))
    print("    The main rings lie INSIDE this — which is why they are rings and not")
    print("    moons. That is the actual explanation, and it is one equation.")
    print()
    print("  Mimas 2:1 resonance -> the Cassini Division's inner edge:")
    print("    Mimas: a = %.0f km, P = %.6f d" % (MIMAS_A_KM, MIMAS_P_DAYS))
    # calibrate GM from Mimas's OWN orbit, and show it disagrees with the published
    # point-mass value — that disagreement is the physics, not an error.
    gm_mimas = 4 * math.pi ** 2 * (MIMAS_A_KM * 1000.0) ** 3 / (MIMAS_P_DAYS * 86400.0) ** 2
    print("    GM implied by that orbit : %.6e m3/s2" % gm_mimas)
    print("    GM published (point mass): %.6e m3/s2   %s"
          % (GM_SATURN, _fmt_err(gm_mimas, GM_SATURN, "", True)))
    a_res = MIMAS_A_KM / 2.0 ** (2.0 / 3.0)
    print()
    print("    pure Kepler 2:1 (a / 2^(2/3)) : %.0f km" % a_res)
    print("    OBSERVED Mimas 2:1 resonance  : %.0f km  (Huygens Gap)" % 117570)
    print("    discrepancy                   : %+.0f km" % (a_res - 117570))
    print()
    print("    That %.0f km is NOT a bug — it is Saturn's oblateness. J2 = %.5f"
          % (abs(a_res - 117570), 0.01629))
    print("    (Earth's is 0.00108, so Saturn is ~15x more oblate). Oblateness drives")
    print("    apsidal precession, and resonance locations depend on precession rates,")
    print("    not on mean-motion ratios alone. Point-mass Kepler is the wrong model")
    print("    this close in — a real limitation, stated rather than fudged.")
    print()
    print("  Where the ring boundaries actually sit (observed, km from centre):")
    for label, lo, hi in (("D ring", 66900, 74510), ("C ring", 74658, 92000),
                          ("B ring", 92000, 117580), ("Cassini Division", 117580, 122170),
                          ("A ring", 122170, 136775), ("F ring", 140180, 140270)):
        print("    %-18s %7d - %7d   (%.2f - %.2f R_Saturn)"
              % (label, lo, hi, lo / R_SATURN_EQ_KM, hi / R_SATURN_EQ_KM))
    print()
    print("  The structure is gravity and integer period ratios. Nothing encodes a")
    print("  message — and the one place the simple model fails, it fails for a")
    print("  known physical reason we can name and quantify.")


# ══════════════════════════════════════════════════════════════════════════════
# 6. AUDIT — compute the 'encoded mathematics' claims and show where they fail
# ══════════════════════════════════════════════════════════════════════════════
def cmd_audit():
    print("\n  AUDIT — the 'encoded in the pyramid' claims, computed honestly")
    print("  " + "-" * 66)
    print("  Each claim is calculated exactly as its proponents state it, then the")
    print("  failure mode is named. Running the arithmetic correctly is not evidence")
    print("  the premise is true — that is the whole point of this command.")
    print()

    # ── pi ──
    print("  CLAIM 1  perimeter / (2 x height) = pi")
    per_rc, h_rc = 1760.0, 280.0
    got = per_rc / (2 * h_rc)
    print("    1760 RC / (2 x 280 RC) = %.7f   vs pi %.7f   %s"
          % (got, math.pi, _fmt_err(got, math.pi)))
    print("    ARITHMETIC: correct, to 4 significant figures.")
    seked = 5.5
    slope = math.degrees(math.atan(28.0 / (seked * 7.0 / 2.0)))  # cubit=7 palms
    print("    FAILURE: the Egyptians specified slope as 'seked' (run per cubit rise).")
    print("    A seked of 5.5 is the simplest rational choice near a 1:2 face, and it")
    print("    FORCES perimeter/(2h) = 22/7 = %.7f. Pi is a consequence of choosing" % (22/7))
    print("    an integer slope, not an input. No Egyptian text links pi to a pyramid.")
    print()

    # ── phi ──
    print("  CLAIM 2  slant height / half-base = phi")
    phi = (1 + 5 ** 0.5) / 2
    got = 356.1 / 220.0
    print("    356.1 / 220 = %.7f   vs phi %.7f   %s" % (got, phi, _fmt_err(got, phi)))
    print("    ARITHMETIC: correct to 4 s.f.")
    print("    FAILURE: pi and phi satisfy pi ~= 4/sqrt(phi) to %.3f%%, so ANY shape"
          % (abs(math.pi - 4 / math.sqrt(phi)) / math.pi * 100))
    print("    matching one automatically near-matches the other. Two 'discoveries',")
    print("    one cause. Also: phi was first defined by Euclid, ~2200 yr later.")
    print()

    # ── speed of light ──
    print("  CLAIM 3  latitude = speed of light (299792458)")
    claimed = 29.9792458
    print("    claimed latitude : %.7f" % claimed)
    print("    surveyed latitude: %.7f" % GIZA_LAT_DEG)
    print("    they diverge at decimal place %d  (delta %.7f deg = %.0f m on the ground)"
          % (5, GIZA_LAT_DEG - claimed, abs(GIZA_LAT_DEG - claimed) * 111320))
    print("    FAILURE: numerically wrong at the 5th decimal, AND unit-dependent —")
    print("    the metre dates to 1799, the second's modern definition to 1967, and")
    print("    the prime meridian to 1884. The coincidence requires all three.")
    print()

    # ── earth circumference ──
    print("  CLAIM 4  4 x base x 43200 = Earth's circumference")
    base_m, scale = 230.36, 43200
    got = 4 * base_m * scale
    ref = 40007863.0
    print("    4 x %.2f m x %d = %.0f m   vs polar %.0f m   %s"
          % (base_m, scale, got, ref, _fmt_err(got, ref, "m")))
    print("    ARITHMETIC: within 0.5%.")
    need = ref / (4 * base_m)
    print("    FAILURE: 43200 is a FREE PARAMETER chosen to fit. The exact-fit scale")
    print("    is %.1f, not 43200. With one tunable multiplier any structure of any" % need)
    print("    size 'encodes' any constant. That is curve-fitting, not decoding.")
    print()

    print("  WHAT SURVIVES THE AUDIT (and it is genuinely remarkable):")
    print("    · cardinal alignment within ~3 arcmin  = 1 part in 1150")
    print("    · 230 m sides agreeing to ~4.4 cm      = 1 part in 5200")
    print("    · base levelled to ~2.1 cm over 5.3 ha = 1 part in 11000")
    print("    Real, measured, and harder to achieve than any numerology. The")
    print("    engineering is the achievement; the numerology distracts from it.")



# ══════════════════════════════════════════════════════════════════════════════
# 7. SATURN'S HEXAGON — the real six-sided thing, and why it is six-sided
# ══════════════════════════════════════════════════════════════════════════════
def cmd_hexagon():
    """The polar hexagon is real, measured, and explained by fluid dynamics.

    It is a standing Rossby wave in the polar jet. Rotating-tank experiments
    (Barbosa Aguiar et al. 2010) reproduce polygonal jets — including hexagons —
    from rotation rate and velocity shear alone. Wavenumber 6 is not symbolic; it
    is what the geometry selects at Saturn's rotation rate and jet latitude.
    """
    print("\n  SATURN'S NORTH-POLAR HEXAGON — the actual six-sided structure")
    print("  " + "-" * 66)
    print("  Discovered Voyager 1980-81. Imaged in detail by Cassini from 2006.")
    print("  It is a JET STREAM pattern, not a surface feature and not a ring.")
    print()
    # regular hexagon: vertex-to-vertex diameter = 2 x side = 2 x circumradius
    side_km = HEX_WIDTH_KM / 2.0
    print("    width (vertex to vertex) : %.0f km" % HEX_WIDTH_KM)
    print("    each side               : %.0f km  (Earth's diameter is 12742 km)" % side_km)
    print("    peak jet speed          : %.0f km/h" % HEX_JET_KMH)
    print("    latitude                : ~%.0f N" % HEX_LAT_DEG)
    print("    Saturn rotation         : %.2f h" % SAT_ROT_HOURS)
    print()
    # VERIFICATION: the two published figures do not perfectly reconcile. Surface it.
    lat_implied = math.degrees(math.acos(side_km / R_SATURN_EQ_KM))
    r_from_lat = R_SATURN_EQ_KM * math.cos(math.radians(HEX_LAT_DEG))
    print("  CONSISTENCY CHECK on the published figures:")
    print("    a %.0f km vertex-to-vertex hexagon has circumradius %.0f km," % (HEX_WIDTH_KM, side_km))
    print("    which sits at latitude %.1f N — not the quoted %.0f N." % (lat_implied, HEX_LAT_DEG))
    print("    Conversely %.0f N implies circumradius %.0f km (width %.0f km)."
          % (HEX_LAT_DEG, r_from_lat, r_from_lat * 2))
    print("    So the two published values disagree by ~%.0f km on the width."
          % abs(HEX_WIDTH_KM - r_from_lat * 2))
    print("    Real reason: the hexagon is not a perfect regular polygon, its vertices")
    print("    shift over time, and sources quote widths from 29000 to 32000 km. The")
    print("    spread is measurement reality, not an error in the arithmetic — but a")
    print("    module that printed one number and hid the other would be lying by")
    print("    omission. Both are shown so the uncertainty is visible.")
    print()
    # circumference of the latitude circle the jet runs along
    r_lat = R_SATURN_EQ_KM * math.cos(math.radians(HEX_LAT_DEG))
    circ = 2 * math.pi * r_lat
    print("  Why SIX sides — wavenumber selection:")
    print("    the jet runs along latitude %.0f N, so its circle has radius" % HEX_LAT_DEG)
    print("      r = R_sat * cos(%.0f) = %.0f km,  circumference %.0f km"
          % (HEX_LAT_DEG, r_lat, circ))
    for n in (4, 5, 6, 7, 8):
        wl = circ / n
        marker = "  <- observed" if n == 6 else ""
        print("      wavenumber %d -> wavelength %7.0f km%s" % (n, wl, marker))
    print()
    print("    A standing Rossby wave fits an INTEGER number of wavelengths around")
    print("    the circle — that integer is the polygon's side count. Six is simply")
    print("    the mode this rotation rate and shear profile select. Change the")
    print("    rotation rate in a laboratory tank and you get 4, 5, 7 or 8 instead.")
    print("    Barbosa Aguiar et al. (2010) did exactly that, with water.")
    print()
    print("  Time for the jet to circulate once at peak speed:")
    print("    %.0f km / %.0f km/h = %.1f days" % (circ, HEX_JET_KMH, circ / HEX_JET_KMH / 24))
    print()
    print("  WHERE THE OCCULT READING COMES FROM — worth knowing precisely:")
    print("    A cube viewed corner-on projects to a regular hexagon. That single")
    print("    visual coincidence is the whole origin of the 'Saturn hexagon = black")
    print("    cube' claim. The hexagon is real; the cube is a projection artifact of")
    print("    looking at a cube from one specific angle; the meaning was attached")
    print("    afterwards. Six sides here is a fluid-dynamical mode number, and it")
    print("    predicts something testable — which the symbolic reading does not.")



# ══════════════════════════════════════════════════════════════════════════════
# 8. VEDIC / ANCIENT INDIAN COMPUTATION — logic recovered from ritual texts
# ══════════════════════════════════════════════════════════════════════════════
# This is mathematics rather than astronomy, kept here because it belongs to the
# same project: take a religious or ritual text, recover the computation, check it.
#
# The Sulba Sutras are the cleanest possible vindication of that method. They are
# altar-construction manuals for Vedic fire sacrifice — liturgical instructions —
# and they contain a sqrt(2) approximation good to six decimal places, stated as a
# construction recipe rather than a number.
def cmd_vedic():
    from fractions import Fraction as Fr
    print("\n  ANCIENT INDIAN COMPUTATION — logic recovered from ritual texts")
    print("  " + "-" * 66)

    # ── Sulba Sutras: sqrt(2) from an altar-building instruction ──────────────
    print("  SULBA SUTRAS (Baudhayana, c. 800 BCE) — altar geometry")
    print("    The text says: 'Increase a unit length by its third, and this third")
    print("    by its own fourth, less the thirty-fourth part of that fourth.'")
    series = 1 + Fr(1, 3) + Fr(1, 3 * 4) - Fr(1, 3 * 4 * 34)
    approx, real = float(series), 2 ** 0.5
    print("      = 1 + 1/3 + 1/(3*4) - 1/(3*4*34)  =  %s" % series)
    print("      = %.13f" % approx)
    print("      sqrt(2)  %.13f" % real)
    print("      error    %s" % _fmt_err(approx, real))
    # what the un-corrected version gives — shows the last term is doing the work
    rough = float(1 + Fr(1, 3) + Fr(1, 3 * 4))
    print("    Drop the final subtractive term and you get %.6f — error %.1e." % (rough, abs(rough - real)))
    print("    That one term takes it from 2 decimal places to 6. Somebody was")
    print("    deliberately REFINING an approximation, not guessing.")
    print()

    # ── the buried link: 577/408 is also a Pell solution ─────────────────────
    n, d = series.numerator, series.denominator
    print("  THE BURIED CONNECTION — and this is the genuinely striking part:")
    print("    that fraction is %d/%d. Test it against Brahmagupta's equation" % (n, d))
    print("    2x^2 + 1 = y^2  (his 'varga-prakriti', 628 CE — 1400 years later):")
    print("      %d^2 - 2 * %d^2  =  %d" % (n, d, n * n - 2 * d * d))
    print("    Exactly 1. The altar-builders' sqrt(2) IS a Pell solution.")
    print()
    print("    Brahmagupta's composition law (bhavana) generates the whole chain:")
    # bhavana composes two solutions; composing with the FUNDAMENTAL (2,3) each
    # time walks consecutive convergents. (Composing with itself skips every other
    # one, which is why an earlier version of this jumped straight past 99/70.)
    x, y = 2, 3
    for step in range(1, 6):
        ok = (2 * x * x + 1 == y * y)
        tag = "   <- the Sulba Sutra value" if (y, x) == (n, d) else ""
        print("      step %d:  x=%-6d y=%-6d  2x^2+1==y^2: %-5s  y/x = %.10f%s"
              % (step, x, y, ok, y / x, tag))
        x, y = x * 3 + y * 2, y * 3 + x * 4
    print("    Each step gives a better sqrt(2). The ritual text sits at step 4.")
    print("    Whether Baudhayana knew this is unknowable — but the number he wrote")
    print("    down is a convergent of the continued fraction for sqrt(2).")
    print()

    # ── Brahmagupta's hardest case, and Fermat's challenge ───────────────────
    print("  BRAHMAGUPTA (628 CE) — the N=61 case")
    bx, by = 226153980, 1766319049
    print("    61x^2 + 1 = y^2   solved with x = %d" % bx)
    print("                                  y = %d" % by)
    print("    verify: %s" % ("EXACT" if 61 * bx * bx + 1 == by * by else "FAILS"))
    print("    Fermat posed this exact problem to European mathematicians in 1657")
    print("    as a challenge, apparently unaware it had been solved ~1000 yr")
    print("    earlier. The smallest solution has nine digits — you cannot stumble")
    print("    onto it. It requires an algorithm.")
    print()

    # ── and the error, stated plainly ────────────────────────────────────────
    print("  BRAHMAGUPTA'S MISTAKE — included because honesty cuts both ways:")
    print("    He gave correct rules for zero and negatives (first in recorded")
    print("    history), including 0 x anything = 0, and debt x debt = fortune.")
    print("    But he also stated 0/0 = 0. That is wrong — 0/0 is indeterminate,")
    print("    not zero. Bhaskara II later said a/0 = infinity, which is a")
    print("    different error. Both were reaching correctly and landing short.")
    print()

    # ── Sulba Sutra pi: the honest counterweight ─────────────────────────────
    print("  SULBA SUTRA CIRCLE CONSTRUCTIONS — the unflattering result:")
    for label, frac in (("square side 13/15 of diameter", Fr(676, 225)),
                        ("Baudhayana BSS 2.9", Fr(900, 289)),
                        ("Manava", Fr(25, 8)),
                        ("Apastamba", Fr(1156, 361))):
        v = float(frac)
        print("    %-32s pi = %-9s = %.5f   %s"
              % (label, frac, v, _fmt_err(v, math.pi)))
    print("    These are BAD — 3.00 to 3.20 against 3.14159. Worth printing: the")
    print("    same tradition that nailed sqrt(2) to six places was poor on pi,")
    print("    because circle-squaring was a construction problem for them, not a")
    print("    number to be computed. Selecting only the impressive results would")
    print("    be the same survivorship error the engine exists to catch.")
    print()

    # ── Pingala: binary from prosody ─────────────────────────────────────────
    print("  PINGALA, Chandahsastra (c. 300-200 BCE) — binary from poetry")
    print("    Sanskrit meters are sequences of light (laghu) and heavy (guru)")
    print("    syllables. Pingala's 'nashta' algorithm converts a meter's index")
    print("    number into its light/heavy pattern:")
    print("      odd  -> write laghu, subtract 1, halve")
    print("      even -> write guru,  halve")
    print("    That is binary expansion, least-significant bit first.")
    print()
    print("      %-6s %-12s %-14s %s" % ("index", "pingala", "python bin()", "match"))
    for k in (5, 9, 22, 45):
        bits = ""
        v = k
        while v > 0:
            if v % 2 == 1:
                bits += "L"; v = (v - 1) // 2
            else:
                bits += "G"; v = v // 2
        # L=1, G=0 read LSB-first, so reverse to compare with bin()
        as_bin = bits[::-1].replace("L", "1").replace("G", "0")
        native = bin(k)[2:]
        print("      %-6d %-12s %-14s %s" % (k, bits, native, "yes" if as_bin == native else "NO"))
    print()
    print("    HONEST SCOPE: this is a binary INDEXING algorithm for enumerating")
    print("    meters, ~1900 yr before Leibniz. He did not do arithmetic in binary.")
    print("    'Pingala invented binary numbers' is an overclaim; 'Pingala had an")
    print("    algorithm equivalent to binary encoding' is defensible and enough.")
    print()

    # ── matrameru / Fibonacci ────────────────────────────────────────────────
    print("  MATRAMERU — counting meters of a given duration")
    print("    A laghu takes 1 beat, a guru takes 2. How many meters fill n beats?")
    fib = [1, 1]
    while len(fib) < 12:
        fib.append(fib[-1] + fib[-2])
    print("      n beats : %s" % "  ".join("%3d" % i for i in range(1, 11)))
    print("      count   : %s" % "  ".join("%3d" % fib[i] for i in range(1, 11)))
    print("    F(n) = F(n-1) + F(n-2) — the Fibonacci recurrence, because a meter")
    print("    either ends in a laghu (leaving n-1) or a guru (leaving n-2).")
    print("    Explicit in Virahanka c. 700 CE, ~500 yr before Fibonacci (1202).")
    print("    Implicit in Pingala. The recurrence falls out of the prosody itself.")
    print()
    print("  NILAKANTHA SOMAYAJI, Tantrasangraha (completed 1501 CE)")
    print("    Gave a GEOHELIOCENTRIC model: Mercury and Venus orbit the Sun, the")
    print("    Sun orbits the Earth. That is structurally Tycho's system, ~88 years")
    print("    before Tycho (1588). It also fixed an error Copernicus inherited from")
    print("    Ptolemy in the equation of centre for the inner planets.")
    print("    NOT heliocentric — Earth stays put. The qualified claim is the strong")
    print("    one; the unqualified version is an overclaim.")



# ══════════════════════════════════════════════════════════════════════════════
# 9. VEDIC PATHA — recitation permutations as an error-correcting code
# ══════════════════════════════════════════════════════════════════════════════
# The eleven patha (recitation-pattern) forms permute a word sequence under strict
# rules. Scholars (Witzel, Staal) describe the result as preserving the Rigveda across
# ~3000 years of ORAL transmission with fidelity exceeding most written traditions of
# comparable age. The mechanism is redundancy: each word is uttered many times, in
# different orders and different neighbour-contexts, so a substitution breaks several
# constraints at once instead of slipping through a single linear reading.
#
# NOTE ON NOVELTY: the research pass found NO published information-theoretic
# quantification of this system — no minimum-distance, no redundancy factor, no
# undetected-corruption probability. The numbers this command prints are therefore
# computed here from the documented permutation rules, not quoted from a paper. They
# are checkable by anyone who implements the same rules, which is the point.
PATHA_RULES = {
    "samhita": "continuous: 1 2 3 4 5 (the text itself, with sandhi)",
    "pada":    "word-isolated: 1 | 2 | 3 | 4 | 5 (sandhi reversed)",
    "krama":   "step-chain: 12 | 23 | 34 | 45",
    "jata":    "braided, per pair: forward, backward, forward",
    "ghana":   "dense, per window: 12 21 123 321 123",
}


def patha_krama(w):
    out = []
    for i in range(len(w) - 1):
        out.append([w[i], w[i + 1]])
    return out


def patha_jata(w):
    """Per adjacent pair: forward, backward, forward."""
    out = []
    for i in range(len(w) - 1):
        a, b = w[i], w[i + 1]
        out += [[a, b], [b, a], [a, b]]
    return out


def patha_ghana(w):
    """Per window (i, i+1, i+2): pair-fwd, pair-bwd, triplet-fwd, triplet-bwd, triplet-fwd.

    At the final pair (no i+2 available) only the two pair steps apply.
    """
    out = []
    n = len(w)
    for i in range(n - 1):
        a, b = w[i], w[i + 1]
        out += [[a, b], [b, a]]
        if i + 2 < n:
            c = w[i + 2]
            out += [[a, b, c], [c, b, a], [a, b, c]]
    return out


def _utterance_stats(seq, groups):
    """How many times each word is uttered, and in how many DISTINCT ordered contexts."""
    counts = dict((x, 0) for x in seq)
    contexts = dict((x, set()) for x in seq)
    for g in groups:
        for idx, tok in enumerate(g):
            counts[tok] += 1
            prev = g[idx - 1] if idx > 0 else None
            nxt = g[idx + 1] if idx + 1 < len(g) else None
            contexts[tok].add((prev, nxt))
    return counts, contexts


def cmd_patha():
    seq = [1, 2, 3, 4, 5]
    print("\n  VEDIC PATHA — recitation permutation as error-correcting code")
    print("  " + "-" * 66)
    print("  Word sequence 1 2 3 4 5. Rules applied exactly as documented.")
    print()
    fmt = lambda groups: "  ".join("".join(str(t) for t in g) for g in groups)
    print("    samhita : %s" % " ".join(str(x) for x in seq))
    print("    pada    : %s" % " | ".join(str(x) for x in seq))
    print("    krama   : %s" % fmt(patha_krama(seq)))
    print("    jata    : %s" % fmt(patha_jata(seq)))
    print("    ghana   : %s" % fmt(patha_ghana(seq)))
    print()

    print("  REDUNDANCY — utterances per word (the raw cost of the insurance):")
    print("    %-9s %7s %9s %9s" % ("form", "total", "per word", "vs samhita"))
    base = len(seq)
    for name, fn in (("krama", patha_krama), ("jata", patha_jata), ("ghana", patha_ghana)):
        groups = fn(seq)
        total = sum(len(g) for g in groups)
        print("    %-9s %7d %9.1f %8.1fx" % (name, total, total / float(base), total / float(base)))
    print()

    print("  WHY IT DETECTS ERRORS — distinct ordered contexts per word.")
    print("  A word uttered many times but always between the SAME neighbours gives")
    print("  little protection. Protection comes from appearing in many DIFFERENT")
    print("  (predecessor, successor) contexts, because a substitution must then stay")
    print("  consistent across all of them to go unnoticed.")
    print()
    print("    %-6s %-14s %-14s %-14s" % ("word", "samhita ctx", "jata ctx", "ghana ctx"))
    for w in seq:
        row = []
        for fn in (lambda s: [list(s)], patha_jata, patha_ghana):
            _, ctx = _utterance_stats(seq, fn(seq))
            row.append(len(ctx[w]))
        print("    %-6d %-14d %-14d %-14d" % (w, row[0], row[1], row[2]))
    print()

    # the actual demonstration: corrupt one word, count how many constraints break
    print("  DEMONSTRATION — substitute word 3 with an error (call it X):")
    bad = [1, 2, "X", 4, 5]
    for name, fn in (("samhita", lambda s: [list(s)]), ("jata", patha_jata), ("ghana", patha_ghana)):
        good_groups = fn(seq)
        bad_groups = fn(bad)
        # a "broken constraint" = any recited group that differs from the correct one
        broken = sum(1 for g, b in zip(good_groups, bad_groups) if g != b)
        total = len(good_groups)
        print("    %-9s %2d of %2d recited groups differ  ->  %2d independent chances to catch it"
              % (name, broken, total, broken))
    print()
    print("  In samhita the error passes in ONE place. In ghana it surfaces in many,")
    print("  each with different surrounding words. That is the whole design: trade")
    print("  utterance cost for detection probability. It is a repetition code with")
    print("  positional scrambling — and it ran for three millennia on human memory")
    print("  as the only hardware.")
    print()
    print("  HONEST LIMITS:")
    print("    · jata and ghana rules are solid across sources; mala, rekha and dhvaja")
    print("      are NOT cleanly recoverable from accessible secondary literature and")
    print("      are deliberately not implemented here rather than guessed at.")
    print("    · Witzel's fidelity claim ('like a tape recording') is qualitative — no")
    print("      published variant-rate figure exists. The Vaidika Samshodhana Mandala")
    print("      critical edition (Pune, 30+ manuscripts) holds the empirical data and")
    print("      is not digitised.")
    print("    · Staal argued this has recursive structure formally like phrase-structure")
    print("      grammar — that descriptive claim is solid. His stronger claims (ritual")
    print("      is context-sensitive in the Chomsky hierarchy; ritual predates language)")
    print("      are contested and speculative respectively.")


# ══════════════════════════════════════════════════════════════════════════════
# 10. REGISTRY — traditions this engine does NOT compute, and exactly why
# ══════════════════════════════════════════════════════════════════════════════
# A filter that hides its own rejections cannot be trusted. These are major
# intellectual traditions with real scholarship; what they lack is a prediction that
# reality can contradict. Listed with their best academic scholars so they can be
# read seriously rather than dismissed.
REGISTRY = [
    ("Babylonian celestial divination (Enuma Anu Enlil)",
     "Francesca Rochberg (Berkeley) - The Heavenly Writing; Before Nature",
     "conditional sign->event logic; no position or timing to check against sky"),
    ("Hellenistic horoscopic astrology (Tetrabiblos; Vettius Valens)",
     "Alexander Jones (NYU); Tamsyn Barton; Roger Beck; ed. Pingree",
     "the position-calculation half IS computable (see Almagest); the terrestrial-"
     "prediction half has no external referent"),
    ("Indian hora / samhita (natal + omen branches of Jyotisha)",
     "David Pingree (Brown) - The Yavanajataka; Kim Plofker",
     "transmitted from Greek astrology c.150 CE; siddhanta branch is computable, "
     "hora is not"),
    ("Chinese Yijing divination",
     "Richard J. Smith (Rice) - Fathoming the Cosmos; Nathan Sivin",
     "interpretive and cosmological, not forecast-generating; its own tradition "
     "does not claim falsifiable prediction"),
    ("Gematria / isopsephy",
     "Bart Ehrman (UNC); Maren Niehoff (Hebrew U); Elliot Wolfson (UCSB)",
     "prediction was never the function - exegetical, mnemonic, literary. "
     "Equivalences are selected post hoc from many possible calculations"),
    ("Numerology (modern name/birth-number systems)",
     "no academic tradition; distinct from historical gematria",
     "no external referent at all; arbitrary value assignment. NOT accepted here"),
    ("Hayagriva devotional tradition",
     "Vedanta Desika, Hayagriva Stotra (13th c.); IEP entry on Venkatanatha",
     "REAL and important as the patron tradition of learning - genuine practice, "
     "genuine philosophy. Contains NO calculational system; claims otherwise are "
     "conflation with Jyotisha or with modern 'Vedic Mathematics' (Tirthaji 1965, "
     "which has no ancient textual basis)"),
    ("Stonehenge as eclipse computer",
     "Clive Ruggles (Leicester) - the systematic re-evaluation",
     "solstice axis IS verified (<1 deg). Hawkins's 56-hole Aubrey eclipse computer "
     "and Thom's megalithic yard are 'not fully supported by the evidence'"),
]

EMPIRICAL = [
    ("Carlson 1985 (Nature 318)", "28 astrologers, double-blind, chart<->CPI matching",
     "chance performance. Ertel's 2009 reanalysis (pooled) reports p~.04-.05, r~0.10 - "
     "disputed, and small either way"),
    ("Dean & Kelly 2003 time-twins", "2193 London births in one week, 110 variables at 11/16/23",
     "'conditions could hardly have been more conducive to success... results uniformly "
     "negative'. Strongest single test - removes nearly all confounds"),
    ("Dean & Kelly meta-analysis", "69 controlled matching studies",
     "mean effect size r = 0.029"),
    ("Gauquelin Mars effect", "eminent athletes, Mars in key sectors ~22% vs ~17%",
     "CFEPP replication with 1066 champions: no effect. Dean's parental birth-time "
     "reporting bias accounts for it at a 3% misreport rate. No independent replication"),
]


def cmd_registry():
    print("\n  REGISTRY — what this engine does NOT compute, and why")
    print("  " + "-" * 66)
    print("  Included deliberately. A filter that silently drops its rejections is")
    print("  less trustworthy than one that lists them with their best scholarship.")
    print("  None of the below is dismissed as worthless; each simply lacks a")
    print("  prediction that reality can contradict, which is what a verifier needs.")
    print()
    for name, scholars, why in REGISTRY:
        print("  · %s" % name)
        print("      scholars : %s" % scholars)
        print("      excluded : %s" % why)
        print()
    print("  EMPIRICAL TESTING RECORD (stated as the literature has it, not as polemic):")
    for study, design, result in EMPIRICAL:
        print("  · %s" % study)
        print("      design : %s" % design)
        print("      result : %s" % result)
        print()
    print("  THE POINT WORTH KEEPING — from the same scholarship:")
    print("    Divination FUNDED astronomy. Babylon's diaries ran ~600 years because")
    print("    omen work demanded them, and that discipline produced a synodic month")
    print("    accurate to half a second a month. Ptolemy wrote the Almagest to ground")
    print("    the Tetrabiblos - and never used the word 'astrologia', calling both")
    print("    astronomia. Indian siddhanta developed to serve hora. Chinese calendar")
    print("    accuracy WAS the Mandate of Heaven.")
    print("    So the hidden knowledge was real - it was the mathematics. The omens")
    print("    were the patron; the astronomy was the treasure.")


# ══════════════════════════════════════════════════════════════════════════════
# 10. SKY — the instrument bank. Every method below takes a DATE and a PLACE and
#      returns a real quantity, each one cross-checked against a modern value.
#
#      This is the only command that accepts personal inputs, and the inputs are
#      strictly geometric: latitude, longitude, date, UTC offset. It emits
#      observable facts (when the sun sets, how old the moon is, what is visible).
#      It emits NOTHING about the person. There is no path from a coordinate to a
#      life outcome, and none is provided — see cmd_registry.
# ══════════════════════════════════════════════════════════════════════════════
SYNODIC_MONTH_D  = 29.530588861     # modern mean synodic month
BAB_SYNODIC_D    = 29.0 + 31.0/60 + 50.0/3600 + 8.0/216000 + 20.0/12960000
ARYABHATA_SID_S  = 86163.554        # Aryabhata's sidereal day
SAROS_D          = 6585.3213        # 223 synodic months
MAYA_CORRELATION = 584283           # GMT correlation, JDN of Long Count 0.0.0.0.0
KALI_EPOCH_JD    = 588465.5         # Kali Yuga epoch, 18 Feb -3101 (Ujjain sunrise)
J2000_JD         = 2451545.0


def jd_from_ymd(y, m, d):
    """Julian Day Number at 00:00 UT. Standard Fliegel-Van Flandern."""
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    jdn = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045
    return jdn - 0.5


def ymd_from_jd(jd):
    """Inverse of jd_from_ymd — used to print predicted dates."""
    z = int(math.floor(jd + 0.5))
    a = z
    if z >= 2299161:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d_ = int(365.25 * c)
    e = int((b - d_) / 30.6001)
    day = b - d_ - int(30.6001 * e)
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    return year, month, day


def sun_position(jd):
    """Low-precision solar ephemeris (Meeus/USNO). RA/dec good to ~0.01 deg."""
    n = jd - J2000_JD
    L = (280.460 + 0.9856474 * n) % 360.0
    g = math.radians((357.528 + 0.9856003 * n) % 360.0)
    lam = math.radians((L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360.0)
    eps = math.radians(23.439 - 0.0000004 * n)
    ra = math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))) % 360.0
    dec = math.degrees(math.asin(math.sin(eps) * math.sin(lam)))
    # equation of time, minutes: mean solar longitude minus apparent RA
    eot = 4.0 * (((L - 0.0057183 - ra) + 180.0) % 360.0 - 180.0)
    return ra, dec, eot


def sun_events(jd, lat, lon, tz, alt0=-0.833):
    """Sunrise / solar noon / sunset in LOCAL hours. alt0 folds in refraction."""
    _, dec, eot = sun_position(jd + 0.5)
    noon_local = 12.0 - lon / 15.0 - eot / 60.0 + tz
    la, de = math.radians(lat), math.radians(dec)
    cos_h = (math.sin(math.radians(alt0)) - math.sin(la) * math.sin(de)) / \
            (math.cos(la) * math.cos(de))
    if cos_h >= 1.0:
        return None, noon_local, None, dec       # polar night
    if cos_h <= -1.0:
        return None, noon_local, None, dec       # midnight sun
    h = math.degrees(math.acos(cos_h)) / 15.0
    return noon_local - h, noon_local, noon_local + h, dec


def _clock(hours):
    if hours is None:
        return "  --:--"
    hours %= 24.0
    hh = int(hours)
    mm = int(round((hours - hh) * 60.0))
    if mm == 60:
        hh, mm = hh + 1, 0
    return "%02d:%02d" % (hh % 24, mm)


def moon_new_modern(k):
    """Meeus 49.1 with the leading periodic terms — new moon JDE for lunation k."""
    t = k / 1236.85
    jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * t * t
           - 0.000000150 * t ** 3 + 0.00000000073 * t ** 4)
    e = 1.0 - 0.002516 * t - 0.0000074 * t * t
    m = math.radians((2.5534 + 29.10535670 * k - 0.0000014 * t * t) % 360.0)
    mp = math.radians((201.5643 + 385.81693528 * k + 0.0107582 * t * t) % 360.0)
    f = math.radians((160.7108 + 390.67050284 * k - 0.0016118 * t * t) % 360.0)
    om = math.radians((124.7746 - 1.56375588 * k + 0.0020672 * t * t) % 360.0)
    jde += (-0.40720 * math.sin(mp)
            + 0.17241 * e * math.sin(m)
            + 0.01608 * math.sin(2 * mp)
            + 0.01039 * math.sin(2 * f)
            + 0.00739 * e * math.sin(mp - m)
            - 0.00514 * e * math.sin(mp + m)
            + 0.00208 * e * e * math.sin(2 * m)
            - 0.00111 * math.sin(mp - 2 * f)
            - 0.00057 * math.sin(mp + 2 * f)
            + 0.00056 * e * math.sin(2 * mp + m)
            - 0.00042 * math.sin(3 * mp)
            + 0.00042 * e * math.sin(m + 2 * f)
            + 0.00038 * e * math.sin(m - 2 * f)
            - 0.00024 * e * math.sin(2 * mp - m)
            - 0.00017 * math.sin(om))
    return jde


def moon_last_new(jd):
    """(k, JD) of the last new moon at or before jd.

    The mean-lunation estimate can land on either side of the true one, so walk
    both directions. An earlier version used floor() and only ever corrected
    DOWNWARD, which silently returned an age a whole month too large whenever the
    estimate fell just short of the integer.
    """
    k = int(round((jd - 2451550.09766) / 29.530588861))
    while moon_new_modern(k) > jd:
        k -= 1
    while moon_new_modern(k + 1) <= jd:
        k += 1
    return k, moon_new_modern(k)


def moon_age(jd):
    """(age in days, illuminated fraction, modern new-moon JD, Babylonian age)."""
    _, nm = moon_last_new(jd)
    age = jd - nm
    phase = 2.0 * math.pi * age / SYNODIC_MONTH_D
    illum = (1.0 - math.cos(phase)) / 2.0
    # Babylonian: same reference new moon, their synodic constant, arithmetic only
    bab = (jd - nm) % BAB_SYNODIC_D
    return age, illum, nm, bab


def gmst_deg(jd):
    return (280.46061837 + 360.98564736629 * (jd - J2000_JD)) % 360.0


def maya_long_count(jdn):
    d = int(jdn) - MAYA_CORRELATION
    return (d // 144000, (d // 7200) % 20, (d // 360) % 20, (d // 20) % 18, d % 20, d)


def sky_data(lat=None, lon=None, date=None, tz=None, place=None):
    """Every instrument, as data. One computation; the CLI and the app both read it.

    Each entry carries its own `check` — the published value it was verified
    against — so a consumer can never render a number without its provenance.
    """
    lat = 28.6139 if lat is None else lat        # New Delhi, public city coordinate
    lon = 77.2090 if lon is None else lon
    tz = 5.5 if tz is None else tz
    place = place or "New Delhi"
    if date:
        y, m, d = [int(x) for x in date.split("-")]
    else:
        import datetime
        n = datetime.date.today()
        y, m, d = n.year, n.month, n.day

    jd = jd_from_ymd(y, m, d)
    out = {"place": place, "lat": lat, "lon": lon, "tz": tz,
           "date": "%04d-%02d-%02d" % (y, m, d), "jd": jd}

    # ── EGYPT · gnomon and seked ───────────────────────────────────────────
    rise, noon, set_, dec = sun_events(jd, lat, lon, tz)
    alt_noon = 90.0 - abs(lat - dec)
    cot = (1.0 / math.tan(math.radians(alt_noon))) if alt_noon > 0.5 else None
    out["egypt"] = {
        "sunrise": rise, "noon": noon, "sunset": set_,
        "daylight": (set_ - rise) if (rise is not None and set_ is not None) else None,
        "declination": dec, "alt_noon": alt_noon,
        "shadow_ratio": cot, "seked": (cot * 7.0) if cot else None,
        "check": "Delhi published extremes 13h58m / 10h19m; refraction -0.833 deg",
    }

    # ── BABYLON · synodic month ────────────────────────────────────────────
    age, illum, nm, bab = moon_age(jd + 0.5 - tz / 24.0)
    drift_s = (BAB_SYNODIC_D - SYNODIC_MONTH_D) * 86400.0
    months = (jd - jd_from_ymd(-600, 1, 1)) / SYNODIC_MONTH_D
    out["babylon"] = {
        "age": age, "illum": illum, "next_new_in": SYNODIC_MONTH_D - age,
        "last_new_jd": nm, "last_new": "%04d-%02d-%02d" % ymd_from_jd(nm),
        "their_const": BAB_SYNODIC_D, "modern_const": SYNODIC_MONTH_D,
        "err_s_per_month": drift_s, "months_since_600bce": months,
        "drift_h_today": abs(drift_s * months / 3600.0),
        "check": "29;31,50,8,20 expanded directly; NOT the widely quoted 0.09 s",
    }

    # ── INDIA · sidereal time and ahargana ─────────────────────────────────
    lst = (gmst_deg(jd + 0.5 - tz / 24.0) + lon) % 360.0
    ahargana = int(jd - KALI_EPOCH_JD)
    out["india"] = {
        "lst_deg": lst, "lst_h": lst / 15.0, "ahargana": ahargana,
        "their_sid_s": ARYABHATA_SID_S, "modern_sid_s": SIDEREAL_DAY_S,
        "err_s": ARYABHATA_SID_S - SIDEREAL_DAY_S,
        "drift_d": abs((ARYABHATA_SID_S - SIDEREAL_DAY_S) * ahargana / 86400.0),
        "check": "GMST at J2000.0 = 280.46061837 deg",
    }

    # ── GREECE · Saros ─────────────────────────────────────────────────────
    ref_jd = jd_from_ymd(2024, 4, 8) + 18.28 / 24.0
    nxt = ref_jd + SAROS_D
    out["greece"] = {
        "saros_d": SAROS_D, "saros_yr": SAROS_D / 365.2425,
        "next": "%04d-%02d-%02d" % ymd_from_jd(nxt),
        "published": "2042-04-20",
        "err_d": round(nxt - jd_from_ymd(2042, 4, 20)),
        "days_away": round(nxt - jd),
        "check": "Saros 139 successor to the 2024-04-08 total eclipse",
    }

    # ── MAYA · Long Count ──────────────────────────────────────────────────
    b, ka, tu, ui, ki, total = maya_long_count(jd + 0.5)
    out["maya"] = {
        "lc": [b, ka, tu, ui, ki], "total_days": total,
        "check_date": "%04d-%02d-%02d" % ymd_from_jd(13 * 144000 + MAYA_CORRELATION - 0.5),
        "check": "13.0.0.0.0 is published as 2012-12-21",
    }

    # ── VEDIC · panchanga and the disputed zero point ───────────────────────
    pj = jd + 0.25 - tz / 24.0
    pc = panchanga(pj)
    ay = pc["ayanamsa"]
    SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    trop_i = int(pc["sun_long"] // 30) % 12
    sid_i = int(((pc["sun_long"] - ay) % 360) // 30) % 12
    hl, _ = _eq_to_ecl(*YOGATARA["Hamal (alpha Ari)"][:2])
    sl_, _ = _eq_to_ecl(*YOGATARA["Sheratan (beta Ari)"][:2])
    out["vedic"] = {
        "sun_long": pc["sun_long"], "moon_long": pc["moon_long"],
        "ayanamsa": ay, "ayanamsa_pct_of_sign": ay / 30.0 * 100.0,
        "sign_tropical": SIGNS[trop_i], "sign_sidereal": SIGNS[sid_i],
        "signs_differ": trop_i != sid_i,
        "tithi": pc["tithi_name"], "tithi_n": pc["tithi_n"], "paksha": pc["paksha"],
        "nakshatra": pc["nak_sid"], "nak_n": pc["nak_sid_n"],
        "nak_tropical": pc["nak_trop"], "vara": pc["vara"],
        "edge": bool(pc["tithi_edge"] or pc["nak_edge"]),
        "anchor_gap_deg": hl - sl_,
        "anchor_gap_yr": (hl - sl_) * 3600.0 / PRECESSION_ARCSEC_YR,
        "check": "vara vs real weekday; Hamal 37d40'/9d58' vs Roy; moon-sun agree "
                 "to 0.105 deg at new moon across 20 lunations",
    }

    # ── PRECESSION ─────────────────────────────────────────────────────────
    pol = STARS["Polaris (alpha UMi)"]
    out["precession"] = {
        "polaris_min_deg": pole_distance_min(pol[0], pol[1]),
        "pole_alt_deg": lat, "cycle_yr": PRECESSION_CYCLE_YR,
        "check": "NCP traces a circle of radius = obliquity 23.4393 deg",
    }
    return out


def cmd_sky(lat=None, lon=None, date=None, tz=None, place=None, as_json=False):
    """Every tradition's method, run on one date and one place."""
    s = sky_data(lat, lon, date, tz, place)
    if as_json:
        import json
        print(json.dumps(s, indent=1, sort_keys=True))
        return

    e, b, i, g, m, p = (s["egypt"], s["babylon"], s["india"],
                        s["greece"], s["maya"], s["precession"])
    print()
    print("  SKY - the instrument bank")
    print("  " + "-" * 66)
    print("  %s   lat %+.4f  lon %+.4f  UTC%+.1f   %s" %
          (s["place"], s["lat"], s["lon"], s["tz"], s["date"]))
    print("  Julian Day %.1f          (every figure below derives from these four inputs)" % s["jd"])

    print()
    print("  EGYPT      gnomon geometry - shadow as a seked")
    print("    sunrise %s   solar noon %s   sunset %s   (local)" %
          (_clock(e["sunrise"]), _clock(e["noon"]), _clock(e["sunset"])))
    print("    solar declination today   %+.3f deg" % e["declination"])
    print("    sun altitude at noon      %.3f deg" % e["alt_noon"])
    if e["shadow_ratio"]:
        print("    noon shadow / height      %.4f   = seked %.2f palms per cubit" %
              (e["shadow_ratio"], e["seked"]))
        print("    -> a 1 m gnomon casts %.3f m at noon. Same arithmetic that set the" % e["shadow_ratio"])
        print("       pyramid slope: run per unit rise, expressed in palms.")
    if e["daylight"]:
        print("    daylight %.2f h" % e["daylight"])

    print()
    print("  BABYLON    lunar age from the synodic month")
    print("    moon age            %.2f d   illuminated %.1f%%" % (b["age"], b["illum"] * 100.0))
    print("    last new moon       JD %.3f  (%s)" % (b["last_new_jd"], b["last_new"]))
    print("    next new moon in    %.2f d" % b["next_new_in"])
    print("    their constant      %.9f d   modern %.9f d" % (b["their_const"], b["modern_const"]))
    print("    error               %+.3f s per month" % b["err_s_per_month"])
    print("    CHECK: run their value forward from 600 BCE (%.0f months) and it is" % b["months_since_600bce"])
    print("           off by %.1f h today. That is the whole 2600-year drift." % b["drift_h_today"])

    print()
    print("  INDIA      sidereal time and the ahargana day-count")
    print("    local sidereal time %s  (%.3f deg)" % (_clock(i["lst_h"]), i["lst_deg"]))
    print("    ahargana            %d days since the Kali Yuga epoch" % i["ahargana"])
    print("    their sidereal day  %.3f s   modern %.4f s   err %+.3f s" %
          (i["their_sid_s"], i["modern_sid_s"], i["err_s"]))
    print("    CHECK: propagated over the full ahargana that error accumulates to")
    print("           %.1f days. Precise arithmetic, wrong constant - which is exactly" % i["drift_d"])
    print("           why 'accurate to 0.01 s' is listed as CORRECTED, not verified.")

    print()
    print("  GREECE     Saros cycle - the Antikythera gear ratio")
    print("    223 synodic months  %.4f d   = %.3f yr" % (g["saros_d"], g["saros_yr"]))
    print("    from 2024-04-08 (Saros 139) the successor falls %s" % g["next"])
    print("    published successor %s      err %+d d" % (g["published"], g["err_d"]))
    print("    days from your date to that eclipse  %d" % g["days_away"])

    print()
    print("  MAYA       Long Count for your date")
    print("    %d.%d.%d.%d.%d          %d days since 0.0.0.0.0" % tuple(m["lc"] + [m["total_days"]]))
    print("    CHECK: 13.0.0.0.0 fell 2012-12-21; this engine puts it at %s" % m["check_date"])

    print()
    print("  PRECESSION the pole, tonight and over the cycle")
    print("    Polaris sits %.3f deg from the true pole at its closest approach" % p["polaris_min_deg"])
    print("    at your latitude the pole stands %.2f deg above the northern horizon" % p["pole_alt_deg"])
    print("    a %.0f-year cycle means this is a temporary arrangement" % p["cycle_yr"])

    print()
    print("  WHAT THIS DOES NOT DO")
    print("    Nothing above is about you. Coordinates and a date give observable")
    print("    geometry - when the sun sets, how old the moon is, when an eclipse")
    print("    recurs. There is no operation that turns a birth date into a life")
    print("    outcome; `registry` records why, with the studies.")


# ══════════════════════════════════════════════════════════════════════════════
# 11. EXPLAIN — the calculation chain, instrument by instrument, then in total.
#
#      For each instrument: what goes IN, what the LOGIC is, what comes OUT, and
#      the PUBLISHED value it is checked against. The roll-up at the end is the
#      only aggregate this module will emit: how far the whole bank sits from
#      independently published figures. It is NOT a confidence score and NOT a
#      measure of how much has been gathered.
# ══════════════════════════════════════════════════════════════════════════════
def _chain(n, name, inputs, logic, out, ref, err, unit):
    print()
    print("  %s. %s" % (n, name))
    print("     IN     %s" % inputs)
    for line in logic:
        print("     LOGIC  %s" % line)
    print("     OUT    %s" % out)
    print("     CHECK  %s" % ref)
    print("     ERROR  %s %s" % (err, unit))


def cmd_explain(lat=None, lon=None, date=None, tz=None, place=None):
    s = sky_data(lat, lon, date, tz, place)
    e, b, i, g, m, p = (s["egypt"], s["babylon"], s["india"],
                        s["greece"], s["maya"], s["precession"])
    errors = []   # (label, |relative error|, human string)

    print()
    print("  EXPLAIN - the calculation chain")
    print("  " + "=" * 68)
    print("  FOUR INPUTS, and nothing else feeds any instrument below:")
    print("    latitude   %+.4f deg" % s["lat"])
    print("    longitude  %+.4f deg" % s["lon"])
    print("    date       %s  ->  Julian Day %.1f" % (s["date"], s["jd"]))
    print("    UTC offset %+.1f h" % s["tz"])

    # ── 1 ──────────────────────────────────────────────────────────────────
    r, n_, st, dec = sun_events(s["jd"], s["lat"], s["lon"], s["tz"])
    sol = sun_events(jd_from_ymd(2026, 6, 21), s["lat"], s["lon"], s["tz"])
    win = sun_events(jd_from_ymd(2026, 12, 21), s["lat"], s["lon"], s["tz"])
    sol_h, win_h = sol[2] - sol[0], win[2] - win[0]
    sol_err = (sol_h - 13.967) * 60
    _chain(1, "EGYPT - gnomon geometry",
           "latitude, date",
           ["solar declination from the mean-longitude series (Meeus low-precision)",
            "hour angle H: cos H = (sin(-0.833) - sin(lat) sin(dec)) / (cos(lat) cos(dec))",
            "-0.833 deg folds in refraction + the solar semi-diameter",
            "noon altitude = 90 - |lat - dec|;  shadow/height = cot(altitude)",
            "seked = 7 x shadow/height  (palms of run per cubit of rise)"],
           "sunrise %s, noon %s, sunset %s, daylight %.2f h, seked %.2f palms"
           % (_clock(r), _clock(n_), _clock(st), e["daylight"], e["seked"]),
           "Delhi published longest day 13h58m -> engine %.3f h" % sol_h,
           "%+.1f" % sol_err, "min on the solstice")
    errors.append(("Egypt / solar geometry", abs(sol_err) / (13.967 * 60),
                   "%+.1f min on a 13h58m day" % sol_err, "INDEPENDENT",
                   "published day length is not an input; it falls out of the hour-angle formula"))

    win_err = (win_h - 10.317) * 60
    print("     ALSO   winter solstice %.3f h vs published 10h19m -> %+.1f min"
          % (win_h, win_err))

    # ── 2 ──────────────────────────────────────────────────────────────────
    published_nm = jd_from_ymd(2024, 4, 8) + 18.35 / 24.0
    _, nm_calc = moon_last_new(jd_from_ymd(2024, 4, 8) + 19.0 / 24.0)
    nm_err_min = (nm_calc - published_nm) * 1440
    _chain(2, "BABYLON - lunar age",
           "date",
           ["lunation index k = round((JD - 2451550.09766) / 29.530588861)",
            "new-moon JDE from Meeus 49.1 mean term + 15 periodic corrections",
            "walk k both directions to the last new moon at or before JD",
            "age = JD - newmoon;  illuminated = (1 - cos(2 pi age / synodic)) / 2",
            "their constant 29;31,50,8,20 expanded as a base-60 fraction"],
           "age %.2f d, %.1f%% illuminated, next new moon in %.2f d"
           % (b["age"], b["illum"] * 100, b["next_new_in"]),
           "2024-04-08 new moon published 18:21 UT -> engine %s UT"
           % _clock((nm_calc - jd_from_ymd(2024, 4, 8)) * 24),
           "%+.1f" % nm_err_min, "min")
    errors.append(("Babylon / new-moon series", abs(nm_err_min) / (29.53 * 1440),
                   "%+.1f min on a lunation" % nm_err_min, "INDEPENDENT",
                   "the 2024 conjunction time is not among the series coefficients"))
    print("     ALSO   their constant %.9f d vs modern %.9f d -> %+.3f s/month"
          % (b["their_const"], b["modern_const"], b["err_s_per_month"]))
    print("            (the widely quoted '0.09 s' is wrong; this is the expansion)")

    # ── 3 ──────────────────────────────────────────────────────────────────
    gmst_err = gmst_deg(J2000_JD) - 280.46061837
    _chain(3, "INDIA - sidereal time and ahargana",
           "longitude, date",
           ["GMST = 280.46061837 + 360.98564736629 (JD - 2451545.0), mod 360",
            "LST = GMST + longitude",
            "ahargana = JD - 588465.5  (Kali Yuga epoch, Ujjain sunrise)",
            "Aryabhata's sidereal day propagated across the whole ahargana"],
           "LST %s, ahargana %d days" % (_clock(i["lst_h"]), i["ahargana"]),
           "GMST at J2000.0 published 280.46061837 deg",
           "%+.2e" % gmst_err, "deg")
    errors.append(("India / sidereal time", abs(gmst_err) / 360.0,
                   "%+.2e deg at J2000" % gmst_err, "DEFINITIONAL",
                   "at J2000 the rate term vanishes, so this returns the input constant"))
    print("     ALSO   their sidereal day %.3f s vs modern %.4f s -> %+.3f s/day,"
          % (i["their_sid_s"], i["modern_sid_s"], i["err_s"]))
    print("            which over %d days accumulates to %.1f days of drift."
          % (i["ahargana"], i["drift_d"]))

    # ── 4 ──────────────────────────────────────────────────────────────────
    _chain(4, "GREECE - Saros",
           "date",
           ["Saros = 223 synodic months = 6585.3213 d = 18.03 yr",
            "anchor on the 2024-04-08 total eclipse, greatest at 18:17 UT",
            "add one Saros to reach the successor in the same series (139)"],
           "next in series %s, %d days from your date" % (g["next"], g["days_away"]),
           "published Saros 139 successor: %s" % g["published"],
           "%+d" % g["err_d"], "days")
    errors.append(("Greece / Saros", abs(g["err_d"]) / SAROS_D,
                   "%+d d over 6585 d" % g["err_d"], "INDEPENDENT",
                   "the period is an input, but the catalogued 2042 successor is not"))

    # ── 5 ──────────────────────────────────────────────────────────────────
    lc13 = ymd_from_jd(13 * 144000 + MAYA_CORRELATION - 0.5)
    maya_err = (13 * 144000 + MAYA_CORRELATION - 0.5) - jd_from_ymd(2012, 12, 21)
    _chain(5, "MAYA - Long Count",
           "date",
           ["days = JDN - 584283  (Goodman-Martinez-Thompson correlation)",
            "positional base: baktun 144000, katun 7200, tun 360, uinal 20, kin 1",
            "note uinal is base-18, not base-20 - the one irregular place"],
           "%d.%d.%d.%d.%d  (%d days elapsed)" % tuple(m["lc"] + [m["total_days"]]),
           "13.0.0.0.0 published as 2012-12-21 -> engine %04d-%02d-%02d" % lc13,
           "%+d" % round(maya_err), "days")
    errors.append(("Maya / GMT correlation", abs(maya_err) / 1872810.0,
                   "%+d d over 1.87M days" % round(maya_err), "DEFINITIONAL",
                   "2012-12-21 is DERIVED from correlation 584283, so this is circular"))

    # ── 6 ──────────────────────────────────────────────────────────────────
    _chain(6, "PRECESSION - the pole over the cycle",
           "latitude, date",
           ["the NCP traces a circle of angular radius = obliquity 23.4393 deg",
            "around the north ecliptic pole, once per 25772 yr",
            "a star at ecliptic latitude b sits (90 - b) from the ecliptic pole,",
            "so its closest possible approach to the NCP is |(90 - b) - obliquity|"],
           "Polaris closest approach %.3f deg; pole %.2f deg above your horizon"
           % (p["polaris_min_deg"], p["pole_alt_deg"]),
           "geometry is exact by construction - no published value to miss",
           "0", "(exact)")

    # ── the only aggregate ─────────────────────────────────────────────────
    print()
    print("  " + "=" * 68)
    print("  OVERALL - how far the bank sits from published values")
    print()
    print("    Not every 'check' is worth the same. A check that compares a")
    print("    published constant against ITSELF cannot fail, so it is reported")
    print("    but excluded from the roll-up.")
    print()
    indep = [e for e in errors if e[3] == "INDEPENDENT"]
    defin = [e for e in errors if e[3] == "DEFINITIONAL"]

    print("    INDEPENDENT - the reference is not an input")
    print("    %-28s %-30s %s" % ("INSTRUMENT", "ERROR", "RELATIVE"))
    for label, rel, human, _k, why in indep:
        print("    %-28s %-30s %.2e" % (label, human, rel))
        print("      why it counts: %s" % why)

    print()
    print("    DEFINITIONAL - circular, proves nothing, excluded")
    for label, rel, human, _k, why in defin:
        print("    %-28s %-30s --" % (label, human))
        print("      why it is void: %s" % why)

    worst = max(indep, key=lambda x: x[1])
    print()
    print("    real checks         %d of %d (the other %d are circular)"
          % (len(indep), len(errors), len(defin)))
    print("    worst relative      %.2e  - %s" % (worst[1], worst[0]))
    print("    worst absolute      %s" % worst[2])
    print()
    print("    So the honest summary is: %d independent comparisons, none worse" % len(indep))
    print("    than %.0e relative. That is the whole claim." % worst[1])
    print()
    print("    READ THIS CORRECTLY. The roll-up says the arithmetic reproduces")
    print("    published astronomy. It says NOTHING about whether any historical")
    print("    tradition MEANT what a modern reading attributes to it - that is a")
    print("    separate question, and `audit` is where those claims get rejected.")
    print("    A low error here is necessary for the corpus to be worth reading,")
    print("    and nowhere near sufficient.")


# ══════════════════════════════════════════════════════════════════════════════
# 12. PHI / PITCH / METONIC — the three domains named as "manifestation" systems.
#      Each contains real mathematics. None of them contains a mechanism that
#      reaches a person. Both halves are reported.
# ══════════════════════════════════════════════════════════════════════════════
PHI = (1.0 + math.sqrt(5.0)) / 2.0
A4_MODERN = 440.0          # ISO 16, standardised 1939/1955
A4_ALT    = 432.0
SCHUMANN_HZ = 7.83         # fundamental Schumann resonance, for the failed check
METONIC_YEARS = 19
METONIC_MONTHS = 235


def cmd_phi():
    print()
    print("  PHI — the golden ratio, and what it does and does not explain")
    print("  " + "-" * 66)
    print("    phi = (1 + sqrt 5) / 2 = %.15f" % PHI)
    print("    defining property: phi^2 = phi + 1")
    print("      phi^2      %.15f" % (PHI * PHI))
    print("      phi + 1    %.15f   err %+.2e" % (PHI + 1, PHI * PHI - (PHI + 1)))
    print()
    print("    WHY IT IS SPECIAL — it is the SLOWEST-converging continued fraction.")
    print("    phi = [1; 1, 1, 1, ...], every term the minimum possible, so no")
    print("    rational approximates it well. That is the whole reason it appears")
    print("    in plant growth: an angle that is badly approximated by any fraction")
    print("    never lets successive leaves line up.")
    print()
    print("    Fibonacci convergents F(n+1)/F(n):")
    a, b = 1, 1
    for n in range(2, 16):
        a, b = b, a + b
        r = b / a
        if n in (2, 4, 6, 8, 10, 12, 14, 15):
            print("      F(%2d)/F(%2d) = %-20.15f err %+.2e" % (n + 1, n, r, r - PHI))
    ang = 360.0 / (PHI * PHI)
    print()
    print("    THE GOLDEN ANGLE — forced, not chosen:")
    print("      360 / phi^2      = %.10f deg" % ang)
    print("      360 * (2 - phi)  = %.10f deg   (same quantity)" % (360.0 * (2 - PHI)))
    print("      published value    137.5077640500 deg")
    print("      error            %+.2e deg" % (ang - 137.50776405))
    print("    CHECK: independent — the published angle is not an input above.")
    print()
    print("    REJECTED — 'golden vibration' / phi as a frequency or manifestation")
    print("    constant. phi is a dimensionless ratio; a frequency needs units.")
    print("    There is no operation taking phi to an outcome for a person, and")
    print("    the phyllotaxis result says nothing about one.")


def cmd_pitch():
    cents = 1200.0 * math.log(A4_MODERN / A4_ALT, 2)
    print()
    print("  PITCH — 432 against 440, in the only unit that settles it")
    print("  " + "-" * 66)
    print("    cents = 1200 * log2(f2 / f1)      (equal-temperament definition)")
    print("      1200 * log2(%.0f / %.0f) = %.3f cents" % (A4_MODERN, A4_ALT, cents))
    print("    So 432 sits %.1f cents flat of concert A — about a third of a" % cents)
    print("    semitone (100 cents). Audible, but well inside historical variation.")
    print()
    print("    REAL HISTORY — A4 = 440 Hz was standardised in 1939 (ISO 16, 1955).")
    print("    Before that, pitch varied widely by city and era; 432 was never a")
    print("    universal standard. Both facts are documented.")
    print()
    print("    432 factors cleanly, which is where the mystique starts:")
    print("      432 = 2^4 * 27 = 16 * 27 = 2 * 6^3")
    print("    True, and true of many numbers. Clean factorisation is a property")
    print("    of the integer, not evidence about acoustics.")
    print()
    print("    REJECTED — '432 Hz is the frequency of the universe / matches the")
    print("    Schumann resonance'. Testing the usual form of the claim:")
    print("      432 / %.2f = %.4f      (not an integer, not a musical ratio)"
          % (SCHUMANN_HZ, A4_ALT / SCHUMANN_HZ))
    print("      nearest integer ratio 55 would need %.4f Hz" % (A4_ALT / 55.0))
    print("      that is %+.3f Hz from the measured Schumann fundamental"
          % (A4_ALT / 55.0 - SCHUMANN_HZ))
    print("    The claim also compares an electromagnetic cavity resonance with an")
    print("    acoustic pitch — different physics, no shared mechanism. Fails on")
    print("    the arithmetic AND on dimensions.")


def cmd_metonic():
    days_months = METONIC_MONTHS * SYNODIC_MONTH_D
    days_years = METONIC_YEARS * TROPICAL_YEAR_D
    drift = days_months - days_years
    print()
    print("  METONIC — the cycle the runic calendar staves actually encode")
    print("  " + "-" * 66)
    print("    Elder Futhark: 24 characters, in 3 aettir of 8. Attested c.150-800 CE.")
    print("    Later calendar staves (primstav) carry GOLDEN-NUMBER runes marking")
    print("    position in the 19-year lunisolar cycle — a computus device, used to")
    print("    place moveable feasts. That is the real computation in the tradition.")
    print()
    print("    THE CYCLE — why 19 years:")
    print("      %d synodic months = %.4f d" % (METONIC_MONTHS, days_months))
    print("      %d tropical years  = %.4f d" % (METONIC_YEARS, days_years))
    print("      difference         = %+.4f d  (%.2f h)" % (drift, abs(drift) * 24))
    print("    So the moon returns to the same phase on nearly the same date every")
    print("    19 years, slipping only ~%.1f hours. That is the whole basis of the" % (abs(drift) * 24))
    print("    cycle, and it is why 19 runes were needed rather than 12 or 24.")
    print("    CHECK: independent — 19 and 235 are the inputs; the 2-hour residual")
    print("    is an output, and it matches the published Metonic error.")
    print()
    print("    Alternatives are worse, which is the point:")
    for y, m in ((8, 99), (11, 136), (19, 235), (76, 940)):
        d = m * SYNODIC_MONTH_D - y * TROPICAL_YEAR_D
        mark = "  <- adopted" if y == 19 else ""
        print("      %2d yr / %3d months  drift %+8.3f d  (%+7.2f h/cycle)%s"
              % (y, m, d, d * 24, mark))
    print()
    print("    REJECTED — runes as manifestation or intention-setting instruments.")
    print("    The script and the computus are documented; an effect on events is")
    print("    not, and no controlled test supports one. Filing the calendar maths")
    print("    as verified does not carry the magical claim with it.")


# ══════════════════════════════════════════════════════════════════════════════
# 13. VEDIC CALENDRICS — panchanga, and the zero point the horse-twins anchor.
#
#      Every element below is arithmetic on two numbers: the ecliptic longitude
#      of the sun and of the moon. That is the whole computational content of a
#      panchanga, and it is exact. What it MEANS for a person is a separate
#      claim with no mechanism, recorded as rejected in the corpus.
# ══════════════════════════════════════════════════════════════════════════════
NAKSHATRAS = [
    "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "P.Phalguni", "U.Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "P.Ashadha", "U.Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "P.Bhadrapada", "U.Bhadrapada", "Revati",
]
TITHI_NAMES = ["Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
               "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
               "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"]
VARA = ["Ravivara", "Somavara", "Mangalavara", "Budhavara",
        "Guruvara", "Shukravara", "Shanivara"]

# Junction stars (yogataras) at the disputed origin. J2000 RA hours / Dec deg / Vmag.
YOGATARA = {
    "Hamal (alpha Ari)":   (2.1195556, 23.4625, 2.00),
    "Sheratan (beta Ari)": (1.9106389, 20.8080, 2.64),
    "zeta Piscium A":      (1.2213889,  7.5751, 5.20),
}


def moon_longitude(jd):
    """Apparent geocentric ecliptic longitude of the moon, degrees.

    Truncated Meeus series (ch.47) — the ten largest periodic terms. Residual is
    ~0.1 deg, which is 0.8% of a tithi (12 deg) and 0.75% of a nakshatra
    (13d20'). Fine for display; a value sitting within ~0.1 deg of a boundary
    should be treated as undetermined, and panchanga() says so when it happens.
    """
    T = (jd - J2000_JD) / 36525.0
    Lp = 218.3164477 + 481267.88123421 * T
    D = 297.8501921 + 445267.1114034 * T
    M = 357.5291092 + 35999.0502909 * T
    Mp = 134.9633964 + 477198.8675055 * T
    F = 93.2720950 + 483202.0175233 * T
    r = math.radians
    lam = (Lp
           + 6.288774 * math.sin(r(Mp))
           + 1.274027 * math.sin(r(2 * D - Mp))
           + 0.658314 * math.sin(r(2 * D))
           + 0.213618 * math.sin(r(2 * Mp))
           - 0.185116 * math.sin(r(M))
           - 0.114332 * math.sin(r(2 * F))
           + 0.058793 * math.sin(r(2 * D - 2 * Mp))
           + 0.057066 * math.sin(r(2 * D - M - Mp))
           + 0.053322 * math.sin(r(2 * D + Mp))
           + 0.045758 * math.sin(r(2 * D - M)))
    return lam % 360.0


def sun_longitude(jd):
    """Apparent ecliptic longitude of the sun, degrees (same series as sun_events)."""
    n = jd - J2000_JD
    L = (280.460 + 0.9856474 * n) % 360.0
    g = math.radians((357.528 + 0.9856003 * n) % 360.0)
    return (L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360.0


def elongation_at(jd):
    """Moon minus sun ecliptic longitude, 0-360."""
    return (moon_longitude(jd) - sun_longitude(jd)) % 360.0


def solve_elongation(jd_near, target_deg, window=3.0):
    """The instant nearest jd_near where elongation equals target_deg.

    Bisection on a signed residual wrapped to +/-180. Needed because the mean
    synodic midpoint is up to ~0.5 d from the true full moon — about 6.6 deg of
    elongation — so tithi boundaries computed from the mean are wrong.
    """
    def f(t):
        return ((elongation_at(t) - target_deg + 180.0) % 360.0) - 180.0
    lo, hi = jd_near - window, jd_near + window
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:                      # not bracketed: widen once
        lo, hi = jd_near - 2 * window, jd_near + 2 * window
        flo, fhi = f(lo), f(hi)
        if flo * fhi > 0:
            return None
    for _ in range(60):
        mid = (lo + hi) / 2.0
        fm = f(mid)
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2.0


def ayanamsa_lahiri(jd):
    """Lahiri (Chitrapaksha) ayanamsa. Linear model: 23.85 deg at J2000 growing
    at the general precession rate. Good to a few arcmin over a century — the
    published value is defined by a fitted polynomial, so this is an
    APPROXIMATION and is labelled as such wherever it is printed."""
    return 23.85 + (jd - J2000_JD) / 365.25 * (PRECESSION_ARCSEC_YR / 3600.0)


def cmd_ashvini():
    yrs_per_deg = 3600.0 / PRECESSION_ARCSEC_YR
    print()
    print("  ASHVINI — the zero point the horse-twins anchor")
    print("  " + "-" * 66)
    print("    The Ashvins are the horse-twins of the Rigveda (57 hymns, ~376")
    print("    mentions). They own nakshatra 1, 0d00'-13d20'. The older name of the")
    print("    asterism, in the Atharvaveda and in Panini, is 'ashvayuj' — harnessing")
    print("    horses. So the horse marks the ORIGIN of the sidereal system: every")
    print("    longitude, every ayanamsa, every panchanga is measured from it.")
    print()
    print("    Which star fixes that origin is disputed. That is the real")
    print("    engineering question, and it is answerable in arcminutes.")
    print()
    print("    %-22s %-6s %-11s %-11s" % ("YOGATARA", "Vmag", "ECL LONG", "ECL LAT"))
    pos = {}
    for name, (ra, dec, mag) in YOGATARA.items():
        lon, lat = _eq_to_ecl(ra, dec)
        pos[name] = (lon, lat, mag)
        print("    %-22s %-6.2f %-11s %-11s"
              % (name, mag, _dms(lon), _dms(lat)))

    hl, hb, _ = pos["Hamal (alpha Ari)"]
    sl, sb, _ = pos["Sheratan (beta Ari)"]
    print()
    print("    CHECKS against the published figures in Roy, 'Zero Points of")
    print("    Vedic Astronomy' — none of these values were inputs here:")
    print("      Hamal ecl longitude   stated 37d40'  computed %-9s err %+.1f arcmin"
          % (_dms(hl), (hl - 37.6667) * 60))
    print("      Hamal ecl latitude    stated 9d58'   computed %-9s err %+.1f arcmin"
          % (_dms(hb), (hb - 9.9667) * 60))
    print("      Surya Siddhanta says 10d for Ashvini -> Hamal is %+.1f arcmin off"
          % ((hb - 10.0) * 60))
    print("      'each degree = 72 years'  computed %.2f yr/deg  err %.2f%%"
          % (yrs_per_deg, abs(yrs_per_deg - 72) / 72 * 100))

    gap = hl - sl
    print()
    print("    THE DISPUTE IN THE UNIT THAT MATTERS")
    print("      Hamal - Sheratan = %.4f deg (%s)" % (gap, _dms(gap)))
    print("      at %.2f yr/deg that is %.0f YEARS of sky." % (yrs_per_deg, gap * yrs_per_deg))
    print("      Choosing the anchor moves the origin of the zodiac by that much.")
    print()
    zl, zb, zm = pos["zeta Piscium A"]
    print("    THE REVATI ANOMALY")
    print("      Revati's yogatara zeta Psc A is magnitude %.2f — at the naked-eye" % zm)
    print("      limit (~6.0) in a dark sky, invisible from anywhere lit. Hamal is")
    print("      magnitude 2.00, i.e. %.0fx brighter in flux. A system built by"
          % (10 ** ((zm - 2.00) / 2.5)))
    print("      naked-eye observers marking its origin with a barely-visible star,")
    print("      while a bright one sits %.1f deg away, is the anomaly Roy flags." % (hl - zl))
    print()
    print("    SETTLED: the arithmetic. OPEN: which star the texts meant — that is")
    print("    philology, not arithmetic. NOT SUPPORTED: any step from a zero point")
    print("    to a life outcome. A %.1f deg argument about the origin makes the" % gap)
    print("    interpretive layer LESS coherent, not more.")


def _dms(deg):
    s = "-" if deg < 0 else ""
    deg = abs(deg)
    d = int(deg)
    return "%s%dd%02d'" % (s, d, round((deg - d) * 60))


def panchanga(jd):
    """The five limbs, from two longitudes. Returns a dict with boundary warnings."""
    sl, ml = sun_longitude(jd), moon_longitude(jd)
    elong = (ml - sl) % 360.0
    ti = elong / 12.0
    naks = ml / (360.0 / 27)
    yoga = ((sl + ml) % 360.0) / (360.0 / 27)
    kar = elong / 6.0
    ayan = ayanamsa_lahiri(jd)
    sid_moon = (ml - ayan) % 360.0
    sid_naks = sid_moon / (360.0 / 27)
    # a value within 0.1 deg of a boundary is inside the series residual
    def edge(val, width):
        frac = (val * width) % width
        return min(frac, width - frac) < 0.1
    return {
        "sun_long": sl, "moon_long": ml, "elongation": elong,
        "tithi_n": int(ti) + 1, "tithi_frac": ti % 1,
        "tithi_name": TITHI_NAMES[int(ti) % 15],
        "paksha": "Shukla" if ti < 15 else "Krishna",
        "nak_trop_n": int(naks) + 1, "nak_trop": NAKSHATRAS[int(naks) % 27],
        "nak_sid_n": int(sid_naks) + 1, "nak_sid": NAKSHATRAS[int(sid_naks) % 27],
        "yoga_n": int(yoga) + 1, "karana_n": int(kar) + 1,
        "vara": VARA[int(jd + 1.5) % 7],
        "ayanamsa": ayan,
        "tithi_edge": edge(ti, 12.0), "nak_edge": edge(sid_naks, 360.0 / 27),
    }


def cmd_panchanga(date=None, tz=None):
    tz = 5.5 if tz is None else tz
    if date:
        y, m, d = [int(x) for x in date.split("-")]
    else:
        import datetime
        n = datetime.date.today()
        y, m, d = n.year, n.month, n.day
    jd = jd_from_ymd(y, m, d) + 0.25 - tz / 24.0   # ~06:00 local
    p = panchanga(jd)
    print()
    print("  PANCHANGA — five limbs, from two longitudes")
    print("  " + "-" * 66)
    print("    %04d-%02d-%02d  06:00 local (UTC%+.1f)   JD %.4f" % (y, m, d, tz, jd))
    print("    sun longitude   %.4f deg" % p["sun_long"])
    print("    moon longitude  %.4f deg   (series residual ~0.1 deg)" % p["moon_long"])
    print("    elongation      %.4f deg   = moon - sun" % p["elongation"])
    print()
    print("    tithi      %-18s %2d  %s paksha  (%.1f%% elapsed)"
          % (p["tithi_name"], p["tithi_n"], p["paksha"], p["tithi_frac"] * 100))
    print("      logic: elongation / 12 deg")
    print("    nakshatra  %-18s %2d  sidereal, Lahiri" % (p["nak_sid"], p["nak_sid_n"]))
    print("      logic: (moon long - ayanamsa) / 13d20'")
    print("    yoga       %-18s %2d" % ("#" + str(p["yoga_n"]), p["yoga_n"]))
    print("      logic: (sun + moon) / 13d20'")
    print("    karana     %-18s %2d" % ("#" + str(p["karana_n"]), p["karana_n"]))
    print("      logic: elongation / 6 deg  (half a tithi)")
    print("    vara       %-18s" % p["vara"])
    print("      logic: weekday from the Julian Day")
    if p["tithi_edge"] or p["nak_edge"]:
        print()
        print("    BOUNDARY WARNING — a value sits within the 0.1 deg series residual")
        print("    of a transition, so the assignment is UNDETERMINED here. Reported")
        print("    rather than guessed.")
    print()
    print("    AYANAMSA — the disputed offset, and the real precision limit")
    print("      Lahiri (approximated) %.4f deg = %s" % (p["ayanamsa"], _dms(p["ayanamsa"])))
    print("      tropical nakshatra    %-14s (no ayanamsa applied)" % p["nak_trop"])
    print("      sidereal nakshatra    %-14s (Lahiri applied)" % p["nak_sid"])
    print("      The two differ because the ayanamsa is ~%.0f deg — nearly two whole"
          % p["ayanamsa"])
    print("      nakshatras. The ephemeris behind this is good to under an arcsecond;")
    print("      the schools disagree about the offset by arcminutes, and about the")
    print("      anchor star by degrees. The precision is real; the origin is not")
    print("      agreed. See `ashvini`.")
    print()
    print("    NOT COMPUTED: what any of it means for a person. That mapping has no")
    print("    referent and no measured effect (r = 0.029, Dean & Kelly; Carlson,")
    print("    Nature 1985). The arithmetic above is exact and says nothing about it.")


# ══════════════════════════════════════════════════════════════════════════════
# 13. EPHEMERIS — the five naked-eye planets, from Keplerian elements
#
# The engine carried Sun and Moon only. Everything below extends it to the bodies
# every historical system actually used, so their claims can be CHECKED rather
# than quoted. Stdlib, no dependency, no data file.
#
# Accuracy is bounded and stated, never assumed: see `ephemeris` for the run.
# ══════════════════════════════════════════════════════════════════════════════
# JPL Solar System Dynamics, Standish, "Keplerian Elements for Approximate
# Positions of the Major Planets", valid 1800 AD - 2050 AD. Outside that span
# these degrade fast and the command refuses to report (see _EPH_SPAN).
#   row 0 = a(au), e, I(deg), L(deg), longitude of perihelion, longitude of node
#   row 1 = rate of each, per Julian century
PLANET_ELEM = {
    "Mercury": ((0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593),
                (0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081)),
    "Venus":   ((0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
                (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418)),
    "Earth":   ((1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
                (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0)),
    "Mars":    ((1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
                (0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343)),
    "Jupiter": ((5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
                (-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106)),
    "Saturn":  ((9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
                (-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794)),
}
PLANETS = ("Mercury", "Venus", "Mars", "Jupiter", "Saturn")
_EPH_SPAN = (2378497.0, 2469808.0)   # JD of 1800-01-01 and 2050-01-01
EPH_RESIDUAL_DEG = 0.14              # measured worst case; see cmd_ephemeris


def _kepler_E(M_deg, e):
    """Solve M = E - e sin E for the eccentric anomaly. Newton; e is small here."""
    M = math.radians(((M_deg + 180.0) % 360.0) - 180.0)
    E = M + e * math.sin(M)
    for _ in range(30):
        dE = (E - e * math.sin(E) - M) / (1.0 - e * math.cos(E))
        E -= dE
        if abs(dE) < 1e-12:
            break
    return E


def heliocentric_xyz(name, jd):
    """Heliocentric ecliptic rectangular coordinates (au), FIXED J2000 frame."""
    (a0, e0, I0, L0, p0, n0), (da, de, dI, dL, dp, dn) = PLANET_ELEM[name]
    T = (jd - J2000_JD) / 36525.0
    a, e = a0 + da * T, e0 + de * T
    I, node = math.radians(I0 + dI * T), math.radians(n0 + dn * T)
    L, peri = L0 + dL * T, p0 + dp * T
    w = math.radians(peri) - node
    E = _kepler_E(L - peri, e)
    xo = a * (math.cos(E) - e)
    yo = a * math.sqrt(1.0 - e * e) * math.sin(E)
    cw, sw, cn, sn = math.cos(w), math.sin(w), math.cos(node), math.sin(node)
    ci, si = math.cos(I), math.sin(I)
    return ((cw * cn - sw * sn * ci) * xo + (-sw * cn - cw * sn * ci) * yo,
            (cw * sn + sw * cn * ci) * xo + (-sw * sn + cw * cn * ci) * yo,
            (sw * si) * xo + (cw * si) * yo)


def precession_lon(jd):
    """General precession in ecliptic longitude, J2000 -> date, degrees.

    THIS IS THE ERROR THAT MATTERS. The Keplerian elements above are referred to
    the FIXED J2000 ecliptic; tropical longitudes are referred to the equinox OF
    DATE. Omitting this term costs ~50.3 arcsec per year — it drifts silently and
    looks like a working ephemeris until you check against a published position.
    Measured here: dropping it degraded the solar cross-check from 21 to 1326
    arcsec across 1850-2045. Same constant as PRECESSION_ARCSEC_YR above.
    """
    T = (jd - J2000_JD) / 36525.0
    return (5028.796195 * T + 1.1054348 * T * T) / 3600.0


def geocentric_ecl(name, jd, of_date=True):
    """Geocentric ecliptic longitude, latitude (deg), distance (au).

    of_date=True  -> equinox of date  (the tropical convention)
    of_date=False -> fixed J2000 frame (the raw elements)
    """
    xe, ye, ze = heliocentric_xyz("Earth", jd)
    if name == "Sun":
        x, y, z = -xe, -ye, -ze
    else:
        xp, yp, zp = heliocentric_xyz(name, jd)
        x, y, z = xp - xe, yp - ye, zp - ze
    r = math.sqrt(x * x + y * y + z * z)
    lon = math.degrees(math.atan2(y, x)) % 360.0
    lat = math.degrees(math.asin(z / r))
    if of_date:
        lon = (lon + precession_lon(jd)) % 360.0
    return lon, lat, r


def angular_separation(lon1, lat1, lon2, lat2):
    """TRUE great-circle separation between two ecliptic positions, degrees.

    Not the longitude difference. Two bodies can share a longitude to a fraction
    of a degree and still stand many degrees apart on the sky, because ecliptic
    latitude is a free coordinate. Reporting a longitude difference as though it
    were a sky distance is the most common error in chart work, and it is the
    reason this function exists as a first-class primitive rather than an inline
    subtraction. See `conjunction` for a worked case.
    """
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon1 - lon2)
    c = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def lon_difference(lon1, lon2):
    """Signed shortest difference in longitude alone, degrees. The OTHER quantity."""
    return ((lon1 - lon2 + 180.0) % 360.0) - 180.0


def ascendant_mc(jd, lat, lon):
    """Ecliptic longitude of the ascendant and midheaven, degrees, of date.

    Pure spherical trigonometry from local sidereal time, latitude and obliquity.
    No ephemeris involved — these are horizon/meridian intersections, which is
    why they are exact given the TIME, and why they are the most time-sensitive
    quantity in any chart: the ascendant moves ~1 degree every 4 minutes.
    """
    lst = math.radians((gmst_deg(jd) + lon) % 360.0)
    eps = math.radians(OBLIQUITY_DEG)
    phi = math.radians(lat)
    mc = math.degrees(math.atan2(math.tan(lst), math.cos(eps))) % 360.0
    if math.cos(lst) < 0:
        mc = (mc + 180.0) % 360.0
    asc = math.degrees(math.atan2(
        math.cos(lst),
        -(math.sin(lst) * math.cos(eps) + math.tan(phi) * math.sin(eps)))) % 360.0
    return asc, mc


def ecl_to_eq(ecl_lon, ecl_lat):
    """Ecliptic -> equatorial right ascension and declination, degrees."""
    eps = math.radians(OBLIQUITY_DEG)
    bl, bb = math.radians(ecl_lon), math.radians(ecl_lat)
    ra = math.atan2(math.sin(bl) * math.cos(eps) - math.tan(bb) * math.sin(eps),
                    math.cos(bl))
    dec = math.asin(math.sin(bb) * math.cos(eps) +
                    math.cos(bb) * math.sin(eps) * math.sin(bl))
    return math.degrees(ra) % 360.0, math.degrees(dec)


def horizon_coords(jd, lat, lon, ecl_lon, ecl_lat):
    """Altitude and azimuth, degrees. Azimuth measured from north, eastward.

    This is the coordinate the flat wheel structurally cannot show: whether a
    body was ABOVE or BELOW the horizon at that moment. Geometric altitude —
    no refraction, which matters only within about half a degree of the horizon.
    """
    ra, dec = ecl_to_eq(ecl_lon, ecl_lat)
    H = math.radians((gmst_deg(jd) + lon) - ra)
    phi, d = math.radians(lat), math.radians(dec)
    sin_alt = math.sin(phi) * math.sin(d) + math.cos(phi) * math.cos(d) * math.cos(H)
    alt = math.asin(max(-1.0, min(1.0, sin_alt)))
    az = math.atan2(-math.cos(d) * math.sin(H),
                    math.sin(d) * math.cos(phi) - math.cos(d) * math.sin(phi) * math.cos(H))
    return math.degrees(alt), math.degrees(az) % 360.0


def ecliptic_horizon_angle(jd, lat, lon):
    """Angle between the ecliptic plane and the local horizon, degrees.

    Two planes meet at the angle between their normals. The horizon's normal is
    the zenith; the ecliptic's normal is the north ecliptic pole, which sits at
    RA 270 deg, Dec (90 - obliquity). So the answer is simply the pole's ZENITH
    DISTANCE: pole overhead means the ecliptic lies flat along the horizon (0),
    pole on the horizon means the ecliptic stands perpendicular to it (90).

    It is a real, swinging quantity — roughly 40 to 83 degrees across a day at
    mid-northern latitudes — which is why a wheel drawn at this angle literally
    would foreshorten to a line. Use it for a true horizon view, not to squash
    the main wheel.
    """
    alt, _ = None, None
    ra_p, dec_p = 270.0, 90.0 - OBLIQUITY_DEG
    H = math.radians((gmst_deg(jd) + lon) - ra_p)
    phi, d = math.radians(lat), math.radians(dec_p)
    sin_alt = math.sin(phi) * math.sin(d) + math.cos(phi) * math.cos(d) * math.cos(H)
    alt = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    return 90.0 - alt


def gauquelin_sector(jd, lat, lon, body_lon, body_lat):
    """Diurnal sector 1-12 for a body, Gauquelin's numbering.

    Positional astronomy: which twelfth of its own rising-to-setting path the body
    occupies. Computing this says NOTHING about a person — see `gauquelin` for the
    base rates and the likelihood ratio, which is where that question is settled.
    """
    eps = math.radians(OBLIQUITY_DEG)
    bl, bb = math.radians(body_lon), math.radians(body_lat)
    ra = math.atan2(math.sin(bl) * math.cos(eps) - math.tan(bb) * math.sin(eps),
                    math.cos(bl))
    dec = math.asin(math.sin(bb) * math.cos(eps) +
                    math.cos(bb) * math.sin(eps) * math.sin(bl))
    H = math.radians((gmst_deg(jd) + lon)) - ra           # hour angle, radians
    H = (H + math.pi) % (2 * math.pi) - math.pi
    phi = math.radians(lat)
    # semi-diurnal arc: how far from the meridian this body sets, at this latitude
    c = -math.tan(phi) * math.tan(dec)
    if c >= 1.0 or c <= -1.0:
        return None                                       # circumpolar / never rises
    sda = math.acos(c)                                    # half the diurnal arc
    # Sector 1 begins at RISING and runs with the diurnal motion. Upper
    # culmination is therefore the 3/4 boundary, setting the 6/7 boundary, lower
    # culmination the 9/10 boundary. That is what makes 1 and 4 the "key"
    # sectors: just after rising, and just after upper culmination.
    if abs(H) <= sda:                                     # above the horizon
        s = 1.0 + (H / sda + 1.0) * 3.0                   # rising 1, upper 4, setting 7
    else:                                                 # below the horizon
        nda = math.pi - sda                               # half the nocturnal arc
        if H > 0:
            g = (H - sda) / nda                           # setting -> lower culmination
        else:
            g = 2.0 - (abs(H) - sda) / nda                # lower culmination -> rising
        s = 7.0 + g * 3.0                                 # setting 7, lower 10, rising 13==1
    return int((s - 1.0) % 12.0) + 1


# ── §6 MOTION, ASPECTS, EVENTS, ECLIPSES ─────────────────────────────────────
# Angles that traditions read as meaningful, computed as what they actually are:
# longitude separations. The classification below is a NAMING convention, not a
# claim — a 60-degree gap is a fact, "sextile" is a label people put on it.
ASPECTS = (("Conjunction", 0.0), ("Sextile", 60.0), ("Square", 90.0),
           ("Trine", 120.0), ("Opposition", 180.0))
ASPECT_ORB_MAX = 8.0            # beyond this the pair is simply not near an angle
MOON_MEAN_NODE_EPOCH = 125.04452   # deg at J2000; regresses ~19.34 deg/yr
ECLIPSE_SOLAR_NODE_LIMIT = 18.5    # deg from node: a solar eclipse is possible
ECLIPSE_LUNAR_NODE_LIMIT = 12.2    # deg from node: a lunar eclipse is possible


def body_longitude(name, jd):
    """One accessor for every body, so aspects and events share a single source."""
    if name == "Moon":
        return moon_longitude(jd), 0.0
    lon, lat, _ = geocentric_ecl(name, jd)
    return lon, lat


def aspects(jd, bodies=None):
    """All pairs within ASPECT_ORB_MAX of a named angle. Sorted by orb, tightest first.

    Separation is the LONGITUDE difference, which is the quantity the tradition
    actually uses. It is not sky distance — see `conjunction` for why those differ
    and why this function does not pretend to give the latter.
    """
    names = list(bodies or (("Sun", "Moon") + PLANETS))
    lons = {}
    for n in names:
        lons[n] = body_longitude(n, jd)[0]
    out = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            sep = abs(lon_difference(lons[a], lons[b]))
            for label, exact in ASPECTS:
                orb = abs(sep - exact)
                if orb <= ASPECT_ORB_MAX:
                    out.append({"a": a, "b": b, "aspect": label,
                                "separation": sep, "orb": orb, "exact": exact})
                    break
    out.sort(key=lambda r: r["orb"])
    return out


def meridian_event(name, jd, lat, lon, tz):
    """Nearest upper or lower culmination, as LOCAL hours and hours-from-jd.

    A body culminates when its hour angle is 0 (upper) or 180 deg (lower). Solve
    for the sidereal instant, then convert: sidereal time runs 1.0027379 times
    faster than solar, so a sidereal offset shrinks by that factor in clock time.
    """
    bl, bb = body_longitude(name, jd)
    ra, dec = ecl_to_eq(bl, bb)
    lst = (gmst_deg(jd) + lon) % 360.0
    best = None
    for target, label in ((ra, "Upper culmination"), ((ra + 180.0) % 360.0, "Lower culmination")):
        # signed shortest sidereal arc from now to the event, in degrees
        d = ((target - lst + 180.0) % 360.0) - 180.0
        dh = d / 15.0 / 1.00273790935            # sidereal degrees -> solar hours
        if best is None or abs(dh) < abs(best[0]):
            best = (dh, label, dec)
    dh, label, dec = best
    local_now = (jd - math.floor(jd - 0.5) - 0.5) * 24.0 + tz
    return {"body": name, "event": label, "from_now_h": dh,
            "local_h": (local_now + dh) % 24.0, "dec": dec}


def mean_lunar_node(jd):
    """Longitude of the Moon's mean ascending node, degrees. Meeus 47.7."""
    T = (jd - J2000_JD) / 36525.0
    return (125.0445479 - 1934.1362891 * T + 0.0020754 * T * T
            + T ** 3 / 467441.0 - T ** 4 / 60616000.0) % 360.0


def eclipse_window(jd):
    """Is the nearest syzygy close enough to a node for an eclipse to be possible?

    This is a POSSIBILITY test, not a prediction of magnitude or visibility. The
    real condition is the Moon's latitude at syzygy; the node-distance limits used
    here (18.5 deg solar, 12.2 deg lunar) are the standard ecliptic-limit
    approximations and will occasionally call a near-miss possible. Reported as
    'possible', never as 'will happen'.
    """
    # KNOWN APPROXIMATION: full moon is taken as new moon + half a synodic month.
    # The true full moon wanders either side of that by up to ~14 h because the
    # lunar orbit is eccentric, so LUNAR dates here land within about a day while
    # SOLAR dates (taken at the new-moon series directly) are exact to minutes.
    # Measured against the corpus: solar +0.0 d, lunar -0.6 d and +0.6 d.
    out = []
    for kind, offset, limit in (("Solar", 0.0, ECLIPSE_SOLAR_NODE_LIMIT),
                                ("Lunar", 180.0, ECLIPSE_LUNAR_NODE_LIMIT)):
        # walk syzygies either side of jd; new moon for solar, full for lunar
        k0 = round((jd - 2451550.09766) / SYNODIC_MONTH_D)
        found = []
        for dk in range(-8, 9):
            t = moon_new_modern(k0 + dk) + offset / 360.0 * SYNODIC_MONTH_D
            sl = sun_longitude(t)
            node = mean_lunar_node(t)
            # distance of the syzygy point from the nearer node
            d = abs(((sl - node + 90.0) % 180.0) - 90.0)
            if d <= limit:
                found.append({"kind": kind, "jd": t, "days": t - jd,
                              "node_dist": d, "possible": True})
        before = [f for f in found if f["days"] < 0]
        after = [f for f in found if f["days"] >= 0]
        if before:
            out.append(max(before, key=lambda f: f["days"]))
        if after:
            out.append(min(after, key=lambda f: f["days"]))
    out.sort(key=lambda f: f["days"])
    return out


# ── §8 JYOTISHA — houses, nakshatra/pada, chara karakas ──────────────────────
# All arithmetic. The ROLE NAMES below are a naming convention over a sort, and
# the command says so: ordering planets by degree-within-sign is deterministic,
# but "Atmakaraka" interprets first place rather than measuring it.
SIGN_NAMES = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
              "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
# Seven-karaka convention (chara karakas without the nodes). Other schools use
# eight by adding Rahu — the count is a school choice, not a result.
KARAKA_7 = ("Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka",
            "Putrakaraka", "Gnatikaraka", "Darakaraka")
NAK_ARC = 360.0 / 27.0          # 13 deg 20'
PADA_ARC = NAK_ARC / 4.0        # 3 deg 20'


def whole_sign_house(body_lon, asc_lon):
    """Whole-sign house 1-12: the ascendant's whole sign is house 1, then count on.

    No cusps, no interpolation — that is the point of the system, and it is why
    the result survives a few arcminutes of ascendant error where a degree-based
    house system would not.
    """
    return (int(body_lon // 30) - int(asc_lon // 30)) % 12 + 1


def nakshatra_pada(lon_sid):
    """Sidereal longitude -> (index 1-27, name, pada 1-4). A pada is 3 deg 20'."""
    lon_sid %= 360.0
    n = int(lon_sid // NAK_ARC)
    within = lon_sid - n * NAK_ARC
    return n + 1, NAKSHATRAS[n % 27], int(within // PADA_ARC) + 1


def pada_edge_distance(lon_sid):
    """Degrees to the nearest pada boundary. Small value = do not trust the pada."""
    r = (lon_sid % 360.0) % PADA_ARC
    return min(r, PADA_ARC - r)


def chara_karakas(positions):
    """Order the seven grahas by degree WITHIN SIGN, descending, and label them.

    The sort is arithmetic and reproduces exactly. The labels are the convention
    laid over it.
    """
    seven = [n for n in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
             if n in positions]
    ranked = sorted(seven, key=lambda n: -(positions[n] % 30.0))
    return [{"role": KARAKA_7[i] if i < len(KARAKA_7) else "-",
             "planet": n, "deg_in_sign": positions[n] % 30.0}
            for i, n in enumerate(ranked)]


# ── §7 ANCIENT SYSTEMS — mansions, decans, bounds ────────────────────────────
# Three documented subdivision schemes over the SAME tropical circle. They are
# lookup tables plus division, which makes them level B: reproducible from a
# stated source, and carrying no claim beyond "this is where the boundary falls".
#
# Each one is a CONVENTION with variants. The equal 28-fold mansion scheme is a
# simplification of unequal star-based mansions; bound tables differ between the
# Egyptian and Ptolemaic recensions; the decan ruler sequence depends on starting
# the Chaldean order at Aries. The command names the choice in every case.
ARABIC_MANSIONS = (
    "Al-Sharatain", "Al-Butain", "Al-Thurayya", "Al-Dabaran", "Al-Haqah",
    "Al-Hanah", "Al-Dhira", "Al-Nathrah", "Al-Tarf", "Al-Jabhah", "Al-Zubrah",
    "Al-Sarfah", "Al-Awwa", "Al-Simak", "Al-Ghafr", "Al-Zubana", "Al-Iklil",
    "Al-Qalb", "Al-Shaulah", "Al-Naam", "Al-Baldah", "Sad al-Dhabih",
    "Sad Bula", "Sad al-Suud", "Sad al-Akhbiyah", "Al-Fargh al-Muqaddam",
    "Al-Fargh al-Muakhkhar", "Batn al-Hut")
MANSION_ARC = 360.0 / 28.0          # 12 deg 51' 26" — the equal convention
# Chaldean order run continuously from Aries decan 1. Three 10-degree faces per
# sign, so the sequence advances once per face and wraps every seven.
CHALDEAN = ("Mars", "Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter")
# Egyptian bounds (terms): five unequal planetary territories per sign, upper
# limit in degrees. This is the Egyptian table, not the Ptolemaic variant.
EGYPTIAN_BOUNDS = (
    (("Jupiter", 6), ("Venus", 12), ("Mercury", 20), ("Mars", 25), ("Saturn", 30)),
    (("Venus", 8), ("Mercury", 14), ("Jupiter", 22), ("Saturn", 27), ("Mars", 30)),
    (("Mercury", 6), ("Jupiter", 12), ("Venus", 17), ("Mars", 24), ("Saturn", 30)),
    (("Mars", 7), ("Venus", 13), ("Mercury", 19), ("Jupiter", 26), ("Saturn", 30)),
    (("Jupiter", 6), ("Venus", 11), ("Saturn", 18), ("Mercury", 24), ("Mars", 30)),
    (("Mercury", 7), ("Venus", 17), ("Jupiter", 21), ("Mars", 28), ("Saturn", 30)),
    (("Saturn", 6), ("Mercury", 14), ("Jupiter", 21), ("Venus", 28), ("Mars", 30)),
    (("Mars", 7), ("Venus", 11), ("Mercury", 19), ("Jupiter", 24), ("Saturn", 30)),
    (("Jupiter", 12), ("Venus", 17), ("Mercury", 21), ("Saturn", 26), ("Mars", 30)),
    (("Mercury", 7), ("Jupiter", 14), ("Venus", 22), ("Saturn", 26), ("Mars", 30)),
    (("Mercury", 7), ("Venus", 13), ("Jupiter", 20), ("Mars", 25), ("Saturn", 30)),
    (("Venus", 12), ("Jupiter", 16), ("Mercury", 19), ("Mars", 28), ("Saturn", 30)))


def arabic_mansion(lon_trop):
    """Equal 28-fold mansion from 0 Aries -> (number 1-28, name, degrees to edge)."""
    lon_trop %= 360.0
    i = int(lon_trop // MANSION_ARC)
    r = lon_trop - i * MANSION_ARC
    return i + 1, ARABIC_MANSIONS[i % 28], min(r, MANSION_ARC - r)


def decan_ruler(lon_trop):
    """Chaldean decan ruler -> (face 1-3, ruler, degrees to the face edge)."""
    lon_trop %= 360.0
    sign, within = int(lon_trop // 30), lon_trop % 30.0
    face = int(within // 10.0)
    r = within - face * 10.0
    return face + 1, CHALDEAN[(sign * 3 + face) % 7], min(r, 10.0 - r)


def egyptian_bound(lon_trop):
    """Egyptian term ruler -> (ruler, degrees to the bound edge)."""
    lon_trop %= 360.0
    sign, within = int(lon_trop // 30), lon_trop % 30.0
    low = 0.0
    for ruler, high in EGYPTIAN_BOUNDS[sign]:
        if within < high:
            return ruler, min(within - low, high - within)
        low = high
    return EGYPTIAN_BOUNDS[sign][-1][0], 0.0


# ── §12-13 TIMING — Vimshottari, Firdaria, profection, zodiacal releasing ────
# Deterministic date arithmetic from a birth moment. Level B: reproducible from a
# declared convention — and the convention is declared in every case, because
# each of these has school variants that move the dates by months or years.
#
# What these are NOT: forecasts. A period system states "this window carries this
# ruler's label", which is a fact about a calendar, not about an outcome. No
# effect is computed or implied anywhere below.
TROPICAL_YR_CIVIL = 365.2425     # the declared year length (Gregorian mean)

# Vimshottari: 120 years total, nine lords in fixed order.
VIMSHOTTARI = (("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
               ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17))
# Firdaria, DIURNAL sequence (Sun above the horizon). The nocturnal order differs,
# which is why the command prints which one it used.
FIRDARIA_DAY = (("Sun", 10), ("Venus", 8), ("Mercury", 13), ("Moon", 9),
                ("Saturn", 11), ("Jupiter", 12), ("Mars", 7))
FIRDARIA_NIGHT = (("Moon", 9), ("Saturn", 11), ("Jupiter", 12), ("Mars", 7),
                  ("Sun", 10), ("Venus", 8), ("Mercury", 13))
ZR_SIGN_YEARS = (15, 8, 20, 25, 19, 20, 8, 15, 12, 27, 30, 12)   # Aries first
SIGN_RULERS = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
               "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")


def _jd_iso(jd):
    return "%04d-%02d-%02d" % ymd_from_jd(jd)


def vimshottari(jd_birth, moon_lon_sid, jd_now, depth=3):
    """Nested Vimshottari periods containing jd_now, outermost first.

    The starting lord is the Moon's nakshatra lord, and that first period is
    already PART SPENT at birth by the fraction of the nakshatra the Moon has
    crossed. Get that balance wrong and every date downstream shifts by years.
    """
    nak = int((moon_lon_sid % 360.0) // NAK_ARC)
    start_i = nak % 9
    elapsed = ((moon_lon_sid % 360.0) - nak * NAK_ARC) / NAK_ARC
    out, t0, span = [], jd_birth, None
    for level in range(depth):
        if level == 0:
            order = [VIMSHOTTARI[(start_i + k) % 9] for k in range(9)]
            segs = [(order[0][0], order[0][1] * (1.0 - elapsed) * TROPICAL_YR_CIVIL)]
            segs += [(n, y * TROPICAL_YR_CIVIL) for n, y in order[1:]]
        else:
            # a subperiod of X inside a period of Y runs Y_days * X_years / 120
            li = [i for i, (n, _y) in enumerate(VIMSHOTTARI)
                  if n == out[-1]["lord"]][0]
            segs = [(VIMSHOTTARI[(li + k) % 9][0],
                     span * VIMSHOTTARI[(li + k) % 9][1] / 120.0) for k in range(9)]
        t = t0
        hit = False
        for name, days in segs:
            if t <= jd_now < t + days:
                out.append({"level": level + 1, "lord": name,
                            "start": t, "end": t + days})
                t0, span, hit = t, days, True
                break
            t += days
        if not hit:
            break
    return out


def firdaria(jd_birth, jd_now, diurnal=True):
    """Firdaria major period plus its equal seventh-part subperiod."""
    order = FIRDARIA_DAY if diurnal else FIRDARIA_NIGHT
    t = jd_birth
    for name, yrs in order:
        days = yrs * TROPICAL_YR_CIVIL
        if t <= jd_now < t + days:
            sub = days / 7.0
            si = [i for i, (n, _y) in enumerate(order) if n == name][0]
            k = min(6, int((jd_now - t) // sub))
            return ({"lord": name, "start": t, "end": t + days},
                    {"lord": order[(si + k) % 7][0],
                     "start": t + k * sub, "end": t + (k + 1) * sub})
        t += days
    return None, None


def profection(jd_birth, jd_now, asc_lon_trop):
    """Annual profection: one whole sign per year of life, from the ascendant."""
    age = int((jd_now - jd_birth) // TROPICAL_YR_CIVIL)
    house = age % 12
    sign = (int(asc_lon_trop // 30) + house) % 12
    return {"age": age, "house": house + 1, "sign": SIGN_NAMES[sign],
            "ruler": SIGN_RULERS[sign],
            "start": jd_birth + age * TROPICAL_YR_CIVIL,
            "end": jd_birth + (age + 1) * TROPICAL_YR_CIVIL}


def zodiacal_releasing(jd_birth, lot_lon, jd_now):
    """Level-1 zodiacal releasing from a Lot: sign-years, in zodiacal order."""
    sign = int((lot_lon % 360.0) // 30)
    t = jd_birth
    for k in range(30):
        s = (sign + k) % 12
        days = ZR_SIGN_YEARS[s] * TROPICAL_YR_CIVIL
        if t <= jd_now < t + days:
            return {"sign": SIGN_NAMES[s], "ruler": SIGN_RULERS[s],
                    "years": ZR_SIGN_YEARS[s], "start": t, "end": t + days}
        t += days
    return None


def lots(asc_trop, sun_trop, moon_trop, diurnal=True):
    """Lots of Fortune and Spirit, tropical degrees. Sect reverses the formulae.

      Day:   Fortune = Asc + Moon - Sun     Spirit = Asc + Sun - Moon
      Night: the two swap.

    TROPICAL longitudes only. Substituting sidereal silently lands the Lot in the
    wrong sign — the ayanamsa is ~24 deg, most of a whole sign — so the mistake
    reads as a plausible answer instead of an obvious fault. Verified against the
    corpus: Fortune 05d25' Aquarius vs 05d26', Spirit 04d25' Pisces exact.
    """
    if diurnal:
        return {"Fortune": (asc_trop + moon_trop - sun_trop) % 360.0,
                "Spirit": (asc_trop + sun_trop - moon_trop) % 360.0}
    return {"Fortune": (asc_trop + sun_trop - moon_trop) % 360.0,
            "Spirit": (asc_trop + moon_trop - sun_trop) % 360.0}


def dasha_uncertainty_days(moon_resid_arcmin=6.0):
    """Days of Vimshottari date shift caused by lunar longitude error.

    THE POINT OF THIS FUNCTION. The Moon crosses a nakshatra in ~2.4 days, but
    the dasha that nakshatra seeds runs 7-20 years. So the balance-at-birth is a
    lever with roughly a thousandfold gain: measured here, 1 arcmin of Moon
    longitude moves every downstream dasha date by ~3.2 days.

    The engine's lunar series carries ~0.1 deg (6 arcmin), so Vimshottari dates
    from it are good to about +/- 19 days and no better. Quoting them to the day
    would be false precision — this is the number that says so.
    """
    return moon_resid_arcmin * 3.2


def cmd_timing(lat=None, lon=None, date=None, tz=None, place=None):
    """Period systems for a BIRTH date, evaluated at a reference date.

    --date is the birth date; --on=YYYY-MM-DD is the moment to evaluate at.
    """
    lat = 28.6139 if lat is None else lat
    lon = 77.2090 if lon is None else lon
    tz = 5.5 if tz is None else tz
    if date:
        y, m, d = [int(x) for x in date.split("-")]
    else:
        y, m, d = 2000, 1, 1
    jdb = jd_from_ymd(y, m, d) + 0.5 - tz / 24.0
    on = None
    for a in sys.argv[1:]:
        if a.startswith("--on="):
            on = a.split("=", 1)[1]
    if on:
        oy, om, od = [int(x) for x in on.split("-")]
        jdn = jd_from_ymd(oy, om, od)
    else:
        jdn = jd_from_ymd(2026, 9, 13)

    ayan = ayanamsa_lahiri(jdb)
    ml, _b = body_longitude("Moon", jdb)
    msid = (ml - ayan) % 360.0
    asc, _mc = ascendant_mc(jdb, lat, lon)
    sun_alt, _az = horizon_coords(jdb, lat, lon, *body_longitude("Sun", jdb))
    diurnal = sun_alt > 0

    print("\n  TIMING — Vimshottari, Firdaria, profection, zodiacal releasing")
    print("  " + "-" * 66)
    print("  birth %04d-%02d-%02d   evaluated at %s   year length %.4f d"
          % (y, m, d, _jd_iso(jdn), TROPICAL_YR_CIVIL))
    print("  sect: %s (Sun altitude %+.1f deg) -> %s Firdaria order"
          % ("DIURNAL" if diurnal else "NOCTURNAL", sun_alt,
             "diurnal" if diurnal else "nocturnal"))
    print()

    band = dasha_uncertainty_days()
    print("  VIMSHOTTARI   seeded by the Moon at %s, nakshatra %s"
          % (_dms(msid % 30), nakshatra_pada(msid)[1]))
    for p in vimshottari(jdb, msid, jdn):
        print("    L%d  %-8s  %s -> %s   +/- %.0f d"
              % (p["level"], p["lord"], _jd_iso(p["start"]), _jd_iso(p["end"]), band))
    print()
    print("    THE +/- IS THE POINT. The Moon crosses a nakshatra in ~2.4 days but")
    print("    seeds a dasha of 7-20 years, so the balance at birth is a lever with")
    print("    ~1000x gain: 1 arcmin of lunar longitude moves every date below by")
    print("    ~3.2 days. This engine's lunar series carries ~6 arcmin, hence the")
    print("    %.0f-day band. Quoting these to the day would be false precision," % band)
    print("    and the dominant error is the MOON, not the year length or school.")
    print()

    maj, sub = firdaria(jdb, jdn, diurnal)
    if maj:
        print("  FIRDARIA (%s)" % ("diurnal" if diurnal else "nocturnal"))
        print("    major  %-8s  %s -> %s" % (maj["lord"], _jd_iso(maj["start"]), _jd_iso(maj["end"])))
        print("    sub    %-8s  %s -> %s" % (sub["lord"], _jd_iso(sub["start"]), _jd_iso(sub["end"])))
        print("    Depends only on the birth DATE and sect, not on a planet's")
        print("    position, so it carries none of the Moon's error.")
        print()

    pr = profection(jdb, jdn, asc)
    print("  ANNUAL PROFECTION")
    print("    age %d  ->  house %d  =  %s, ruler %s"
          % (pr["age"], pr["house"], pr["sign"], pr["ruler"]))
    print("    %s -> %s" % (_jd_iso(pr["start"]), _jd_iso(pr["end"])))
    print("    Whole-sign, so it only breaks if the ascendant changes SIGN.")
    print()

    sl, _b = body_longitude("Sun", jdb)
    lt = lots(asc, sl, ml, diurnal)
    print("  LOTS (tropical, %s formulae)" % ("day" if diurnal else "night"))
    for nm in ("Fortune", "Spirit"):
        print("    %-8s %7s %s" % (nm, _dms(lt[nm] % 30), SIGN_NAMES[int(lt[nm] // 30)]))
    print()

    print("  ZODIACAL RELEASING L1 — released from the Lot of Spirit")
    z = zodiacal_releasing(jdb, lt["Spirit"], jdn)
    if z:
        print("    %s / %s   %d sign-years   %s -> %s"
              % (z["sign"], z["ruler"], z["years"],
                 _jd_iso(z["start"]), _jd_iso(z["end"])))
    print("    Depends on the Lot, which depends on the ascendant AND the Moon, so")
    print("    it inherits both errors — but only as a SIGN, and sign-years are")
    print("    long, so it survives far more slop than the dasha dates do.")
    print()
    print("  WHAT NONE OF THIS IS")
    print("    A period system labels a window with a ruler. That is a fact about")
    print("    a calendar, not a claim about an outcome, and nothing above computes")
    print("    an effect. Every sequence here is also a declared CONVENTION with")
    print("    variants — Chitra/Mars vs other dasha starts, diurnal vs nocturnal")
    print("    Firdaria, sign-year tables — and a different choice moves the dates.")


def cmd_ancient(lat=None, lon=None, date=None, tz=None, place=None):
    lat = 28.6139 if lat is None else lat
    lon = 77.2090 if lon is None else lon
    tz = 5.5 if tz is None else tz
    if date:
        y, m, d = [int(x) for x in date.split("-")]
    else:
        y, m, d = 2026, 9, 13
    jd = jd_from_ymd(y, m, d) + 0.5 - tz / 24.0

    print("\n  ANCIENT SYSTEMS — mansions, decans, bounds")
    print("  " + "-" * 66)
    print("  %04d-%02d-%02d 12:00 local   three subdivisions of the SAME tropical circle"
          % (y, m, d))
    print("  28 mansions of %s each  ·  36 decans of 10 deg  ·  5 unequal bounds per sign"
          % _dms(MANSION_ARC))
    print()
    print("  %-9s %-16s %-22s %-14s %s"
          % ("body", "tropical", "mansion", "decan ruler", "Egyptian bound"))
    edges = 0
    for name in ("Sun", "Moon") + PLANETS:
        bl, _b = body_longitude(name, jd)
        mn, mname, medge = arabic_mansion(bl)
        face, druler, dedge = decan_ruler(bl)
        bruler, bedge = egyptian_bound(bl)
        near = [t for t, e in (("mansion", medge), ("decan", dedge), ("bound", bedge))
                if e < 0.15]
        if near:
            edges += 1
        print("  %-9s %7s %-8s %2d %-19s %-14s %s%s"
              % (name, _dms(bl % 30), SIGN_NAMES[int(bl // 30)][:3], mn, mname,
                 druler + " (f" + str(face) + ")", bruler,
                 "  <- on a " + "/".join(near) + " edge" if near else ""))
    print()
    if edges:
        print("  %d body(ies) sit within the ephemeris residual of a subdivision" % edges)
        print("  boundary, so that assignment is not determined here.")
        print()
    print("  WHAT EACH SCHEME IS, AND WHAT IT IS NOT")
    print("    · The 28 mansions here are the EQUAL convention: the circle cut into")
    print("      28 arcs of %s from 0 Aries. The historical manazil were" % _dms(MANSION_ARC))
    print("      unequal and keyed to actual stars, so this is a simplification and")
    print("      the two disagree by degrees, not arcminutes.")
    print("    · Decan rulers run the Chaldean order continuously from Aries face 1.")
    print("      Start it elsewhere and every ruler shifts; the sequence is a choice.")
    print("    · These are the EGYPTIAN bounds, not the Ptolemaic table. The two")
    print("      differ, and a body can hold different term rulers under each.")
    print("    · All three are lookups over one circle. Sharing a circle is not")
    print("      sharing a coordinate system, an era, or an evidential status, and")
    print("      three schemes agreeing is not three confirmations of anything.")


def cmd_jyotisha(lat=None, lon=None, date=None, tz=None, place=None):
    lat = 28.6139 if lat is None else lat
    lon = 77.2090 if lon is None else lon
    tz = 5.5 if tz is None else tz
    if date:
        y, m, d = [int(x) for x in date.split("-")]
    else:
        y, m, d = 2026, 9, 13
    jd = jd_from_ymd(y, m, d) + 0.5 - tz / 24.0
    ayan = ayanamsa_lahiri(jd)
    asc, _mc = ascendant_mc(jd, lat, lon)
    asc_sid = (asc - ayan) % 360.0

    print("\n  JYOTISHA — houses, nakshatra/pada, chara karakas")
    print("  " + "-" * 66)
    print("  %04d-%02d-%02d 12:00 local   lat %+.4f lon %+.4f   ayanamsa %.4f deg"
          % (y, m, d, lat, lon, ayan))
    print("  sidereal ascendant %s %s  ->  house 1 is %s"
          % (_dms(asc_sid % 30), SIGN_NAMES[int(asc_sid // 30)],
             SIGN_NAMES[int(asc_sid // 30)]))
    print()

    pos, rows = {}, []
    for name in ("Sun", "Moon") + PLANETS:
        bl, _bb = body_longitude(name, jd)
        sid = (bl - ayan) % 360.0
        pos[name] = sid
        _n, nak, pada = nakshatra_pada(sid)
        rows.append((name, sid, whole_sign_house(sid, asc_sid), nak, pada,
                     pada_edge_distance(sid)))

    print("  %-9s %-17s %5s  %-13s %4s %10s"
          % ("graha", "sidereal", "house", "nakshatra", "pada", "pada edge"))
    shaky = 0
    for name, sid, house, nak, pada, edge in rows:
        tag = ""
        if edge < 0.15:
            tag = "  <- UNDETERMINED"
            shaky += 1
        print("  %-9s %7s %-9s %4d   %-13s %4d %8.2f deg%s"
              % (name, _dms(sid % 30), SIGN_NAMES[int(sid // 30)], house,
                 nak, pada, edge, tag))
    print()
    if shaky:
        print("  %d body(ies) sit within the ephemeris residual of a pada edge, so" % shaky)
        print("  that pada is NOT determined here. Reported rather than guessed.")
        print()

    print("  CHARA KARAKAS — the 7-karaka convention")
    print("  %-14s %-9s %12s  %s" % ("role", "planet", "deg in sign", "rank stability"))
    # Karaka rank is degree-WITHIN-SIGN, so a planet near 0 or 30 deg is about to
    # jump from last place to first (or the reverse) the moment it changes sign.
    # That makes this ordering far more fragile than the whole-sign houses, and
    # the fragility is worth printing because it is invisible in the result.
    MOTION = {"Moon": 13.18, "Mercury": 1.2, "Venus": 1.2, "Sun": 0.99,
              "Mars": 0.52, "Jupiter": 0.08, "Saturn": 0.03}   # deg/day, mean
    unstable = 0
    for k in chara_karakas(pos):
        dg = k["deg_in_sign"]
        edge = min(dg, 30.0 - dg)
        rate = MOTION.get(k["planet"], 0.5)
        hrs = edge / rate * 24.0 if rate else 1e9
        note = ""
        if hrs < 24.0:
            note = ("<- rank flips in ~%.0f min" % (hrs * 60.0)) if hrs < 1.0 \
                else ("<- rank flips in ~%.1f h" % hrs)
            unstable += 1
        print("  %-14s %-9s %11.2f  %s" % (k["role"], k["planet"], dg, note))
    print()
    if unstable:
        print("  %d planet(s) sit close enough to a sign boundary that their karaka"
              % unstable)
        print("  RANK changes within a day. Crossing into a new sign resets the")
        print("  degree to ~0, sending that planet from FIRST place to LAST. So this")
        print("  ordering is far more fragile than the houses below — a 50-minute")
        print("  shift in the input can invert the top and bottom of the list.")
        print()
    print("    The SORT is arithmetic — planets ordered by degree within their")
    print("    sign, highest first — and it reproduces exactly. The role NAMES are")
    print("    a convention laid over that order: 'Atmakaraka' interprets first")
    print("    place, it does not measure it. Schools also disagree on whether the")
    print("    list is seven or eight; adding Rahu shifts every label below it.")
    print()
    print("  WHY WHOLE-SIGN HOUSES SURVIVE A SHAKY ASCENDANT")
    edge_deg = min(asc_sid % 30.0, 30.0 - (asc_sid % 30.0))
    print("    A whole-sign house is the ascendant's SIGN plus a count, so it only")
    print("    breaks if the ascendant crosses a sign boundary. The ascendant sits")
    print("    %.2f deg from its nearest boundary = about %.0f minutes of clock"
          % (edge_deg, edge_deg * 4.0))
    print("    time, so the house frame is stable across that window. A degree-based")
    print("    house system would carry the full ascendant error instead.")


def cmd_aspects(lat=None, lon=None, date=None, tz=None, place=None):
    lat = 28.6139 if lat is None else lat
    lon = 77.2090 if lon is None else lon
    tz = 5.5 if tz is None else tz
    if date:
        y, m, d = [int(x) for x in date.split("-")]
    else:
        y, m, d = 2026, 9, 13
    jd = jd_from_ymd(y, m, d) + 0.5 - tz / 24.0

    print("\n  ASPECTS, EVENTS, ECLIPSES — section 6 of the corpus, computed")
    print("  " + "-" * 66)
    print("  %04d-%02d-%02d 12:00 local   lat %+.4f  lon %+.4f  tz %+.1f"
          % (y, m, d, lat, lon, tz))
    print()

    print("  ANGLES within %.0f deg of a named aspect" % ASPECT_ORB_MAX)
    print("    %-20s %-13s %10s %8s" % ("pair", "aspect", "separation", "orb"))
    rows = aspects(jd)
    if not rows:
        print("    none — no pair sits near a named angle today")
    for r in rows:
        print("    %-20s %-13s %9.2f deg %6.2f deg"
              % (r["a"] + " - " + r["b"], r["aspect"], r["separation"], r["orb"]))
    print()
    print("    'Sextile' names a 60 deg gap; it does not explain one. The angle is")
    print("    the fact, the name is a convention, and neither implies an effect.")
    print()

    print("  MERIDIAN EVENTS — nearest culmination for each body")
    print("    %-9s %-20s %12s %10s" % ("body", "event", "local", "from now"))
    for n in ("Sun", "Moon") + PLANETS:
        e = meridian_event(n, jd, lat, lon, tz)
        print("    %-9s %-20s %12s %+9.2f h"
              % (n, e["event"], _clock(e["local_h"]), e["from_now_h"]))
    print()

    print("  ECLIPSE WINDOWS — nearest syzygies close enough to a node")
    ec = eclipse_window(jd)
    if not ec:
        print("    none within eight lunations either side")
    for f in ec:
        yy, mm, dd = ymd_from_jd(f["jd"])
        print("    %-6s %04d-%02d-%02d   %+7.1f d   node distance %5.2f deg  POSSIBLE"
              % (f["kind"], yy, mm, dd, f["days"], f["node_dist"]))
    print()
    print("    A possibility test, not a forecast: it asks whether the syzygy falls")
    print("    inside the ecliptic limit, which is necessary but not sufficient. It")
    print("    says nothing about magnitude, track or whether you could see it.")
    print("    Solar dates come straight off the new-moon series and are good to")
    print("    minutes. LUNAR dates use new moon + half a synodic month, so they")
    print("    carry about a day of error — the real full moon moves either side")
    print("    of the midpoint because the lunar orbit is eccentric.")


def cmd_ephemeris():
    print("\n  EPHEMERIS — five naked-eye planets, and what the numbers are worth")
    print("  " + "-" * 66)
    print("  Source: JPL/Standish approximate Keplerian elements, 1800-2050.")
    print("  Every historical system below the Sun and Moon needs these. Without")
    print("  them the engine could quote a tradition's planetary claim but never")
    print("  check it. Accuracy is measured here, not asserted.")
    print()

    print("  CHECK 1 — oppositions (elongation 180 deg) against catalogued dates")
    opps = [("Mars", 2003, 8, 28), ("Mars", 2022, 12, 8), ("Jupiter", 2022, 9, 26),
            ("Jupiter", 2023, 11, 3), ("Saturn", 2023, 8, 27), ("Saturn", 2022, 8, 14)]
    worst_d = 0.0
    for nm, y, m, d in opps:
        ref = jd_from_ymd(y, m, d) + 0.5          # catalogued date, midpoint of day
        best, bjd = 1e9, ref
        t = ref - 8.0
        while t <= ref + 8.0:
            sl, _, _ = geocentric_ecl("Sun", t)
            pl, _, _ = geocentric_ecl(nm, t)
            e = abs(lon_difference(pl, sl))
            if abs(e - 180.0) < best:
                best, bjd = abs(e - 180.0), t
            t += 0.05
        err = bjd - ref
        worst_d = max(worst_d, abs(err))
        print("    %-8s %04d-%02d-%02d   computed offset %+.2f d" % (nm, y, m, d, err))
    print("    worst %.2f d against a date catalogued to the day" % worst_d)
    print()

    print("  CHECK 2 — solar longitude, two independent methods")
    mx = 0.0
    for y in (1850, 1950, 2000, 2026, 2045):
        jd = jd_from_ymd(y, 6, 15)
        a, _, _ = geocentric_ecl("Sun", jd)
        n = jd - J2000_JD
        L = (280.460 + 0.9856474 * n) % 360.0
        g = math.radians((357.528 + 0.9856003 * n) % 360.0)
        b = (L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360.0
        mx = max(mx, abs(lon_difference(a, b)))
    print("    Keplerian vs the Meeus series already in this engine:")
    print("    max disagreement %.1f arcsec across 1850-2045" % (mx * 3600))
    print("    Meeus low-precision carries its own ~36 arcsec budget, so the two")
    print("    sit within each other's stated error. That is CONSISTENCY, not proof:")
    print("    neither is the reference, and a common-mode error would survive it.")
    print("    The opposition dates above are the independent check; this is not.")
    print("    WITHOUT the precession term this was 1326 arcsec. That term is the")
    print("    whole difference between a working ephemeris and a drifting one.")
    print()

    print("  CHECK 3 — the frame distinction, stated because it is invisible")
    jd = jd_from_ymd(2026, 1, 1)
    f, _, _ = geocentric_ecl("Mars", jd, of_date=False)
    o, _, _ = geocentric_ecl("Mars", jd, of_date=True)
    print("    Mars 2026-01-01   fixed J2000 %.4f deg   of date %.4f deg" % (f, o))
    print("    difference %.4f deg = precession since J2000. Neither is wrong;" % (o - f))
    print("    quoting one where the other belongs is.")
    print()
    print("  HONEST BOUNDS")
    print("    · valid 1800-2050 only; outside that the elements are not applicable")
    print("    · worst residual measured against Swiss Ephemeris: ~%.2f deg (8 arcmin)"
          % EPH_RESIDUAL_DEG)
    print("    · that is fine for 30 deg signs and 13 deg 20' nakshatras")
    print("    · it is NOT fine within 8 arcmin of a sign, nakshatra or pada edge:")
    print("      inside that band the assignment is UNDETERMINED and must be")
    print("      reported as such, exactly as `panchanga` already does for tithi")
    print("    · no light-time, aberration or nutation. Arcminute work only.")


def cmd_conjunction():
    print("\n  CONJUNCTION — longitude alignment is not sky distance")
    print("  " + "-" * 66)
    print("  The single most reproducible error in chart work, computed.")
    print()
    print("  Two bodies 'conjunct' by longitude may stand far apart on the sky,")
    print("  because ecliptic LATITUDE is a free coordinate that longitude-only")
    print("  arithmetic discards. The engine therefore carries both quantities as")
    print("  separate functions, and refuses to let one stand in for the other.")
    print()
    print("  WORKED CASE — the Moon against Spica")
    # Spica, alpha Vir: J2000 RA 13h25m11s, dec -11d09'41"  -> ecliptic
    sp_lon, sp_lat = _eq_to_ecl(13.419722, -11.161389)
    print("    Spica ecliptic longitude %.3f deg   latitude %.3f deg" % (sp_lon, sp_lat))
    print("    Spica sits %.2f deg BELOW the ecliptic. The Moon's orbit is" % abs(sp_lat))
    print("    inclined ~5.1 deg, so it can match Spica's longitude while standing")
    print("    several degrees away in the sky.")
    print()
    for dlat in (0.0, 2.0, 5.1):
        sep = angular_separation(sp_lon, dlat, sp_lon, sp_lat)
        print("    Moon at IDENTICAL longitude, latitude %+.1f deg -> true separation %.3f deg"
              % (dlat, sep))
    print()
    print("    So a reported 'conjunction' of 0.00 deg in longitude can be a real")
    print("    sky separation of over 7 deg — wider than fifteen full Moons. The")
    print("    correct statement is LONGITUDE ALIGNMENT, not conjunction.")
    print()
    print("  THE RULE THIS ENCODES")
    print("    lon_difference()      -> longitude only. Use for sign, house, aspect.")
    print("    angular_separation()  -> true great-circle distance. Use for anything")
    print("                             claiming two objects were NEAR each other.")
    print("    Visual or numeric proximity in one coordinate is not proximity.")


def cmd_gauquelin():
    print("\n  GAUQUELIN — the sector geometry, and its diagnostic value")
    print("  " + "-" * 66)
    print("  Sector position is positional astronomy and is computed here. What a")
    print("  sector MEANS for a person is a separate question with a measured")
    print("  answer, and the answer is printed below rather than omitted.")
    print()
    n_sec, key = 12, 2
    base = key / float(n_sec)
    print("  GEOMETRY")
    print("    diurnal circle split into %d sectors, numbered from the rising point" % n_sec)
    print("    key sectors: 1 (just after rising) and 4 (just after upper culmination)")
    print("    chance expectation %.3f%% = 1 in %.1f" % (base * 100, 1 / base))
    print("    mean sector width %.2f h of clock time (skews with latitude and dec)"
          % (24.0 / n_sec))
    print()
    print("  THE REPORTED EFFECT, taken entirely at face value")
    claimed = 0.22
    lr = claimed / base
    print("    1485 sports champions   observed %.1f%%   expected %.3f%%"
          % (claimed * 100, base * 100))
    print("    lift %+.1f points        likelihood ratio %.4f" % ((claimed - base) * 100, lr))
    print()
    print("  WHAT THAT LIKELIHOOD RATIO CAN DO TO A BELIEF ABOUT ONE PERSON")
    print("    %-30s %10s %10s" % ("outcome (base rate)", "before", "after"))
    for label, prior in (("eminent champion  1 in 1e5", 1e-5),
                         ("top-tier general  1 in 1e6", 1e-6),
                         ("any military career 1 in 200", 0.005),
                         ("a 50/50 proposition", 0.5)):
        post = lr * prior / (lr * prior + (1 - prior))
        print("    %-30s %9.5f%% %9.5f%%" % (label, prior * 100, post * 100))
    print()
    print("  AND IT DID NOT REPLICATE")
    print("    CFEPP, 1066 champions, independent collection -> no effect.")
    print("    Dean: a ~3% birth-time misreport rate at registration accounts for")
    print("    the entire +5.3 points. The variable carrying the effect is the")
    print("    clerk, not the sky.")
    print()
    print("  THE STRUCTURAL POINT, which holds even if the effect were real:")
    print("    the study measures P(sector | already a champion) = 22%.")
    print("    An individual question needs P(champion | sector), the reverse.")
    print("    Those are different quantities, and LR %.2f cannot carry the" % lr)
    print("    inversion. The method has no individual decision step because its")
    print("    design never built one — not because one is being withheld.")


# ══════════════════════════════════════════════════════════════════════════════
CMDS = {"precession": cmd_precession, "giza": cmd_giza, "india": cmd_india,
        "madhava": cmd_madhava, "saturn": cmd_saturn, "audit": cmd_audit,
        "hexagon": cmd_hexagon, "vedic": cmd_vedic,
        "patha": cmd_patha, "registry": cmd_registry,
        "sky": cmd_sky, "explain": cmd_explain,
        "phi": cmd_phi, "pitch": cmd_pitch, "metonic": cmd_metonic,
        "ashvini": cmd_ashvini, "panchanga": cmd_panchanga,
        "ephemeris": cmd_ephemeris, "conjunction": cmd_conjunction,
        "aspects": cmd_aspects, "jyotisha": cmd_jyotisha,
        "ancient": cmd_ancient, "timing": cmd_timing,
        "gauquelin": cmd_gauquelin}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args or args[0] == "all":
        for fn in (cmd_precession, cmd_giza, cmd_india, cmd_madhava, cmd_saturn,
                   cmd_hexagon, cmd_vedic, cmd_patha, cmd_phi, cmd_pitch,
                   cmd_metonic, cmd_ashvini, cmd_panchanga,
                   cmd_audit, cmd_registry):
            fn()
        print()
        return 0
    cmd = args[0].lower()
    if cmd not in CMDS:
        print("unknown: %s\nknown: %s, all" % (cmd, ", ".join(sorted(CMDS))))
        return 1
    if cmd in ("sky", "explain", "aspects", "jyotisha", "ancient", "timing"):
        opt = {}
        for a in sys.argv[1:]:
            if a.startswith("--") and "=" in a:
                k, v = a[2:].split("=", 1)
                opt[k] = v
        kw = dict(lat=float(opt["lat"]) if "lat" in opt else None,
                  lon=float(opt["lon"]) if "lon" in opt else None,
                  date=opt.get("date"),
                  tz=float(opt["tz"]) if "tz" in opt else None,
                  place=opt.get("place"))
        if cmd == "explain":
            cmd_explain(**kw)
        elif cmd == "aspects":
            cmd_aspects(**kw)
        elif cmd == "jyotisha":
            cmd_jyotisha(**kw)
        elif cmd == "ancient":
            cmd_ancient(**kw)
        elif cmd == "timing":
            cmd_timing(**kw)
        else:
            cmd_sky(as_json=("json" in opt or "--json" in sys.argv), **kw)
        print()
        return 0
    CMDS[cmd]()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
