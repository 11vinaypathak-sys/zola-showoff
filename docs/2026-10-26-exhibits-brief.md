# The six exhibits — what each node IS, what the world draws for that kind of data, what ours becomes

Scope: the inside pages of `world.html`. The scene (eye, sky, planets) is out of scope here. Written after a scan of
instrument design (dials vs bullet charts), habit grids, progression/unlock UIs, trace waterfalls and radar scopes.
Visual references from the net were thin; Vinay's screenshot drops into `refs/` are the stronger input.

## The rule that governs all six
Each node is a **decision machine**: measure → judge against a rule the owner wrote → move. The exhibit must show the
rule and the measure in the same picture, so the verdict is visibly earned. Text under it only names what the picture
already showed. One picture per node; it moves once, in the direction the data moved.

| Node | What it IS (the IP) | What the world draws | What ours becomes |
|---|---|---|---|
| **Finance** | holdings measured against caps the owner wrote; a breach becomes a sized move with a date | car dials (needle motion as feel, [Jalopnik](https://jalopnik.com/1751236122)); bullet charts beat dials for space and avoid red-zone pull ([thoughtbot](https://thoughtbot.com/blog/lets-talk-about-dials)) | **Cap bullets, not one gauge.** One horizontal bullet per holding class: a grey band for the cap, the actual share as a bar that *overshoots* in amber where it breaks the cap, the move amount printed at the overshoot. The whole book on one screen; the breach is the only coloured thing. The needle survives as a small dial in the corner for the one headline number. |
| **Career** | a rung is a state; it lights only when every listed condition is ticked; no partial credit | skill trees: nodes, prerequisite lines, lock/unlock with explicit "can unlock" checks ([wayline](https://www.wayline.io/blog/unity-skill-tree-scriptable-objects), [skill-tree engine](https://brentbruthaa.itch.io/easy-skill-tree-engine)) | **A lock diagram.** Each rung is a bar with its conditions as pins across it; a pin fills when a condition is met; the rung lights only when all pins are in. Lit rungs below are solid, the current one is the only coloured one, the next is outlined with its unmet pins visibly empty. Hope is not a state. |
| **Creative** | planned vs made, six weeks, a floor rate; the gap sets next month's plan | GitHub contribution grid; habit heatmaps need binary done/missed not intensity ([forum](https://forum.bubble.io/t/github-heatmap-graph/326863)) | **Ghost grid.** 42 cells; planned days drawn as outlines first (the ghost), then made days fill in on top as the clock runs; the cells that stay outline *are* the gap. A rate bar beneath with the floor as a tick. Then one line: "next month: 22 planned" drawn from the gap. |
| **Intel** | scheduled sweeps; a signal only when a spread crosses the threshold with a named source; silence is counted | radar scopes exist only as stock motifs; nobody draws **silence** | **A scope that is mostly empty.** The sweep, three pings in 31 days, and silence drawn as width on the month line. Add the threshold as a ring on the scope: a ping inside it is a watch, outside it a signal. The emptiness is the exhibit; the designer's note says so. |
| **Engine** | a question travels out through five stations and returns as a verdict; the model proposes, the rules decide | trace waterfalls: nested spans, errors in red, time attributed per step ([Axiom](https://axiom.co/blog/distributed-tracing-adds-visual-instrumentation-for-microservices), [New Relic](https://docs.newrelic.com/docs/apm/distributed-tracing/ui-data/distributed-tracing-attributes/)) | **A trace waterfall of one question.** Five rows (you, lens, memory, rules, verdict), each a span bar with what it produced printed in it; rules expand into pass/fail sub-spans; the agentic shell is a dashed span that can be switched off and the verdict bar does not change. The stations pipeline we built becomes the overview; the waterfall is the detail when you pick a question. |
| **Centre** (how it's organised) | the layers the system is made of, and the build tooling around them | onboarding "how it works" diagrams; ours must also say what was built *with* | **The rings stay**, but each ring gets one real artefact: the skill file, a memory entry, a module name, a verdict JSON snippet, shown on hover. A diagram that can be opened is a claim that can be checked. |

## Presentation rules for every page
1. **Measure and rule in one picture.** Never a number alone; the cap, floor, threshold or condition is drawn beside it.
2. **One colour = one meaning.** The region hue is state (lit, met, signal, breach). Everything else is tonal glass.
3. **One motion, in the data's direction.** Bars extend, pins fill, cells fill, the sweep turns. No decorative loops.
4. **Hover explains provenance.** Every drawn element says which file and which rule produced it.
5. **Text is caption, not content.** Headline sentence, one designer's note, the verdict feed as real output. Nothing else.

## What this does for the "unique IP"
The IP is not the data, it is the refusal built into the rules: no partial credit, no forecast, silence counted, the
model proposes but decides nothing. Each exhibit above draws the refusal itself: the empty pin, the empty scope, the
dashed span that changes nothing. That is the part no other portfolio can copy.

## Build order
1. Finance cap bullets (data exists: holding shares, caps, moves).
2. Career lock diagram (checklist + rungs exist).
3. Creative ghost grid (planned/made per day exists).
4. Intel threshold ring (threshold exists).
5. Engine trace waterfall for the picked question (QUESTIONS carry rules and verdict).
6. Centre ring artefacts on hover.

## What I need from you
Screenshots of instruments or dashboards you find beautiful, dropped in `refs/` with a one-word filename. I'll read
each against the rules above and adjust the six drawings before building.
