# Showcase roadmap (as of 27 Oct 2026)

Ordered by what a visitor notices first. Each item is one commit. Verify with the `?still` harness and `node --check`
on the extracted module before committing. Specs: `docs/superpowers/specs/`, exhibits: `docs/2026-10-26-exhibits-brief.md`.

## Scene
1. **Boot timing** — god rays open a fraction before the pupil lights; sky rises under them. (~0.5 s choreography)
2. **Eye detail** — faint Milky Way reflection on the sclera; lid edges catch the key light when closing.
3. **Planets sit in space** — soft contact shadow from each body onto its own dust cloud.
4. **Labels as a chart** — mono leader lines from each name to its object (observatory-plate style).
5. **Dive transition** — ease-in then brake into frame; the page slides in during the last third of the move, not after.
6. **Sound, off by default** — one tone on dive, one on verdict; a button to enable.

## Pages
7. **The six exhibits** (see exhibits brief): Finance cap bullets · Career lock diagram · Creative ghost grid ·
   Intel threshold ring · Engine trace waterfall · Centre ring artefacts on hover. Build in that order.
8. **Interactivity** — one control per exhibit that changes the verdict live (drag the cap, tick a condition,
   mark a day made, drag the threshold).
9. **Hover provenance** — every drawn element names the file and rule that produced it.

## System
10. **Ask it anything** — question picker moves to the overview; light travels the wires to the regions touched;
    the verdict card drops in.
11. **Live engine strip** — scheduler ticks at the foot of the page against the real cron table.
12. **Guided 90-second cut** — one caption and one camera move per stop, ending on the pipeline.
13. **Proof layer** — repo link, module count, commit count from a generated JSON.

## Hygiene
14. **Performance budget** — measure fps on a mid-range machine (backdrop blur + god rays + bloom); add a quality switch.
15. **Mobile** — phone layout pass for the pages.
16. **Stills harness** — re-capture before/after in `docs/shots`.

## This week's three
7 (exhibits) · 5 (dive + page slide-in) · 10 (ask it anything).

## Standing rules
Light hierarchy: pupil → focused core → ring lights → other cores → galactic haze → stars/dust/wires (never bloomed).
One clock for every idle. Hue is state, glass is tonal. Blender runs outside the sandbox. Comments go on their own line.
