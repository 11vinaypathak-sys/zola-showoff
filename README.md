# ZOLA — a personal operating system

One local web app. Five working domain applications in orbit around one shared
brain. No cloud, no accounts, no telemetry — everything runs on one machine and
nothing leaves it.

**Built solo, AI-assisted end to end** (Claude Code daily), by a designer.
That's the point of the project: current tools let one person design *and*
ship the operating system their life actually needs.

## Architecture

```
DATA    flat JSON, local only (never committed — see .gitignore's allowlist)
ENGINE  Python modules, one job each (scheduler, learning loop, verification)
SERVER  zola-server.py — localhost:3737, serves + computes
SHELL   zola.html — one live-polling surface, Three.js orbit homepage
AGENT   AI reads everything, proposes anything, decides NOTHING
```

The governing principle is **deterministic core, agentic shell**: every rule,
check and verdict is auditable code; the AI layer advises and is never the
decider.

## What's in here

- `zola.html` — the shell: a 3D eye-and-orbit homepage (Three.js) with five
  domain nodes. Ships as a neutral template; real data loads locally at boot.
- `zola-server.py` — the local server and API.
- `engine/zola_cron.py` — tick-based deterministic scheduler ($0, no LLM at
  runtime).
- `engine/zola_learn.py`, `zola_skills.py`, `zola_capture.py`,
  `zola_pipeline.py` — the self-improving loop: real outcomes strengthen or
  decay learned "moves".
- `engine/zola_itshock.py` — a live market event terminal stood up in a single
  session when a sector-moving news event broke: named names vs a control
  group, one spread metric isolating event from macro, live news wire.
- `engine/zola_survivorship.py`, `zola_signaling.py`, `zola_verify.py` — the
  reasoning filters: survivorship-bias math (Wilson bounds), workplace
  signaling-equilibrium reads, and a shared verification kernel so every number
  carries its reference and error band.
- `engine/zola_screen.py`, `zola_fin_confirm.py`, `zola_toolkit.py`,
  `zola_astronomy.py` — domain engines (finance screening runs rules-as-code
  and *informs, never trades*).

## Privacy model

The `.gitignore` ignores **everything** by default and whitelists only code —
so no personal data can reach a commit even by accident. Real data lives in
`*.local.json` files that exist only on the machine.

## Run it

```bash
python3 zola-server.py        # http://127.0.0.1:3737/zola.html
python3 engine/zola_cron.py list
```

---
*This is the public cut of a larger private system. The parts that hold
personal data, and the tooling built on top for private use, stay private.*
