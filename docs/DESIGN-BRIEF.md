# ZOLA Showoff — Design Brief

**One line:** an operating system you can watch think. A static, no-login, 90-second
experience that shows a designer-built, AI-assisted personal OS as a finished product —
not a code dump.

## 1. Audience and job

Hiring managers, founders and creative technologists who open one link and decide in
under two minutes whether this person designs *and* ships. Everything on screen must
reward a skim and survive a deep look.

## 2. One design language, split by layer

The working shell grew two visual dialects. The showoff commits to **one**:

- **Flat UI, deep scene.** Every 2D surface (cards, tables, type, controls) follows the
  Nothing-discipline layer: lightness-stepped surfaces instead of shadows, 1px
  hairlines, outlined secondary shells, no gradient fills, no glass, no glow on UI.
- **The 3D scene is where richness lives:** the orbit, bloom on node cores only, a
  particle field. Depth is allowed in the scene because it is the product's
  signature, and forbidden in the UI because it is decoration there.

## 3. Colour

| Role | Value | Rule |
|---|---|---|
| Ground | `#0a0a0b` | steps to `#101012`, `#17171a`, `#1e1e22` for elevation |
| Text | `#ededf0` / `#a1a1aa` / `#71717a` | every pair audited to WCAG AA 4.5:1 |
| Identity accent | lime `#d6f84a` | the single brand colour; active states, hero numerals |
| Node signals | Finance lime `#d6f84a` · Career steel `#8fb4ff` · Creative coral `#ff7a59` · Intel mint `#5ee6c1` · Engine violet `#c4a8ff` | used ONLY as 3D core light, a 2px top rule on a node page, and sparkline strokes |
| State pair | up `#4ade80` / down `#f87171` / warn `#fbbf24` | money direction and alert tier only; never colour alone |

## 4. Type

Display **Space Grotesk** · body **Inter** · data **JetBrains Mono** (tabular numerals).
Dot-matrix is punctuation only: the logotype and hero numerals. Retire the Courier New
and Segoe UI fallbacks — they are what makes the current shell look unfinished.

## 5. Motion inventory (five moments, nothing else)

1. **Orbit idle:** slow drift, pointer parallax, nodes breathe.
2. **Node ignition:** camera dives through the chosen node (600 ms, ease-in-out).
3. **Data arrival:** numeral rolls linearly over 200 ms with a hairline flash.
4. **Engine pulse:** scheduled jobs fire on a live timeline.
5. **Verdict chain:** stages light in sequence, rules pass or fail visibly.

Rules: mechanical easing only (no spring, no bounce), 140–320 ms for UI, reduced-motion
respected, no decorative loops outside the orbit drift. Loading is a linear scan, never
a spinner.

## 6. The 3D scene

Each node gets its own geometry instead of the shared icosahedron/torus:
Finance = stacked rings, Career = rising helix, Creative = noise-displaced ribbon,
Intel = radar sweep plane, Engine Room = branching crystal. Add an instanced dust field
and selective bloom on cores. Budget: 60 fps on an M-series laptop; static fallback for
reduced motion and low power.

## 7. The five exhibits (demo data only)

| Node | Hero moment | Demo content |
|---|---|---|
| Finance | goal → moves → live calc → verdict, animating left to right | fictional goals and sample numbers; the mechanics are the exhibit |
| Career | ladder with unlock conditions ticking as they are met | a fictional ladder; state machine, not prose |
| Creative | plan / track / analyze board, consistency grid filling in | sample sessions; rhythm made visible |
| Intel | animated radar sweep, a single ping after deliberate silence | sample signal ledger; silence is the feature |
| Engine Room | the backend as the exhibit: stack diagram animating bottom-up, cron timeline firing, learning loop strengthening and decaying moves, a live status terminal | deterministic fake jobs on real scheduler logic |

## 8. What keeps it from looking generated

No gradient headline text, no emoji, no glowing cards, no generic section titles.
Asymmetric tile spans (varied sizes ARE the hierarchy). One memorable moment per page.
Microcopy in a real voice with real constraints and numbers. Small "designer's note"
annotations explaining why a choice exists — visible design thinking.

## 9. Delivery shape

Static site, no server: demo data ships as embedded JSON, so it can be hosted on GitHub
Pages and linked directly from applications as a live demo beside the code.

Milestones, each committed on its own: **M1** tokens, type, demo-data layer, static mode ·
**M2** orbit homepage · **M3** Engine Room · **M4** Finance · **M5** Career + Creative ·
**M6** Intel · **M7** accessibility and contrast audit, performance, README, screenshots.
