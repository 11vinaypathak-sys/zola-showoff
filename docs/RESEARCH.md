# Research — what would make the world better, and what we install

Date: 20 Oct 2026. Filter: the ZOLA test (does it close a workstream here?) plus the design law
(flat UI, depth only in the scene, lime as the single accent). Everything below passed both or is
marked why it did not.

## Verdict in one line
Install three things: **fat lines** (already in three.js, just not in this repo), the **pmndrs
postprocessing** library for a proper bloom + soft depth of field, and the **threejs-devtools MCP**
so the live scene can be inspected and tuned without reload cycles. Read the **awwwards-3d skill**
once and steal its numeric rules. Everything else is reference, not dependency.

## Libraries

| What | Why it closes a workstream here | Source | Status |
|---|---|---|---|
| **Fat lines** (`jsm/lines/Line2`, `LineMaterial`) | Edges and the relevance ribbon are 1px today, so they vanish at distance and look cheap close up. Fat lines give world-space thickness and dashes. Already part of three.js. | three.js examples (copied from a local r170 install) | **copied into `jsm/lines/`** — needs an r165 compatibility check |
| **pmndrs/postprocessing** | One merged pass for bloom, depth of field, vignette, SMAA. Our UnrealBloomPass is a blunt instrument; theirs has luminance smoothing and mipmap blur, and DoF would separate the eye from the far clusters. Vanilla three.js, Zlib licence. | github.com/pmndrs/postprocessing | needs an ESM file in the repo (CDN blocked from this sandbox; fetch from your terminal, see below) |
| **troika-three-text** | SDF text in the scene itself, so landmark names and memory titles sit in 3D with depth fade instead of as DOM labels fighting for position. Optional: the DOM labels follow the law already. | github.com/protectwise/troika | **deferred** — only if the label collisions keep bothering us |
| **lygia** | GLSL function library (noise, fbm, sdf). Useful if we go to shader-driven nebulae. Prosperity licence is non-commercial unless you sponsor. | github.com/patriciogonzalezvivo/lygia | **not now** — licence friction for a portfolio piece that might sit beside paid work |
| **3d-force-graph** | A whole graph library. Would replace our hand-rolled nodes. | github.com/vasturiano/3d-force-graph | **no** — we would lose the one thing that is ours |

## Tools (MCP / skills)

| What | Why | Install | Status |
|---|---|---|---|
| **threejs-devtools-mcp** (DmitriyGolub, MIT, ~120 stars) | Inspect the live scene tree, set material and camera values in the running page, get before/after diffs as paste-ready code. Turns every tuning step from edit → reload → screenshot into a live dial. | `claude mcp add threejs-devtools-mcp -- npx threejs-devtools-mcp` | **recommended** — run from your terminal; it opens a browser bridge on localhost:9222. Review `pending_changes` before accepting. |
| **blender-mcp** (ahujasid, MIT, ~17k stars) | Live Blender control from Claude. We already have a scripted, repeatable pipeline; this adds a hand-sculpt loop with viewport screenshots. | Blender add-on + `uvx blender-mcp` | **optional** — only for the eye, if you want to sculpt it by voice |
| **awwwards-3d skill** (tsogjavklann) | 200 lines of concrete rules from the Active Theory / Lusion school: cap pixel ratio at 2, bloom strength ≈0.45, frame-rate-independent lerps, lighting and post before geometry. | github.com/tsogjavklann/awwwards-3d | **read, steal rules, do not install** — it locks a GSAP + Lenis scroll stack we do not want |
| **secondsky/claude-skills · threejs** (MIT, 231 stars) | A general three.js skill: scenes, shaders, post. Broad, not deep. | `/plugin marketplace add https://github.com/secondsky/claude-skills` then `/plugin install threejs@claude-skills` | **skip** — our frontend-design + design-grammar skills already cover the judgement; the API knowledge is in context7 |

## References that are better than us (study, do not copy)

The design law says reference by object, not adjective. Each line says what to look at.

- **Lusion — lusion.co and Oryzo (oryzo.ai).** Look at how one object owns the frame and the camera moves through depth on scroll. Our overview now does this from a higher angle; theirs commits harder.
- **Active Theory — Xbox Halo 5 Visualizer, Neon installation (case studies on Medium).** The reference for bloom that reads as light rather than glow filter. Note how little is actually bright.
- **Hello Monday — Google Cloud Infrastructure WebGL (case study).** Nodes and connections across a globe; the closest to our mind-map. Look at edge opacity falling with distance.
- **Buck — Revisualizer (buck.co/research/revisualizer).** Data as constellation. Look at how labels appear only on focus.
- **Stripe — the globe (stripe.com/blog/globe).** Arcs and dots with restraint; one accent colour.
- **Hubtown by Unseen Studio.** A single glowing monolith with mouse reveal. Our eye should carry the frame the way that monolith does.
- **Matt DesLauriers — Audiograph.** Lines and points that move on one clock. Our standby breathing is the same idea.
- **Lacoste Ace Breaker, Cartier Watches & Wonders (Immersive Garden).** Not our genre, but study how each scene is one idea with nothing else on screen.

Case-study index: github.com/luruke/awesome-casestudy.

## Pass 2 (20 Oct, evening) — what the reference scenes actually do, and what we took

The brief was "proper 3D renders, real-looking galaxies, the effects people have already built". Scouted the
public recipes rather than screenshots. What they share, and where we now stand:

| Technique in the reference work | What it does for the look | Status here |
|---|---|---|
| **Shader point galaxy** (Three.js Journey "animated galaxy"; the same recipe in a dozen CodePens): branch angle + spin ∝ radius + randomness^3 that tightens at the core, per-point size, soft radial falloff, additive, no depth write | Stars that cluster into arms instead of confetti | **done** — `STAR_VS/STAR_FS`; differential rotation in the vertex shader (inner turns faster), per-point twinkle |
| **Procedural gas disc**: fbm noise shaped by `cos(arms·θ − twist·log r)` into spiral arms, a hot bulge, filament detail at two higher octaves, darker between the arms | The photograph quality — gas, not dots | **done** — `GAS_FS` on a disc under each star cloud; the nebula look the fog never had |
| **Film grain under 5 % + a hair of chromatic aberration at the edges** (every Active Theory / Lusion piece) | "Camera", not "canvas" | **done** — pmndrs `NoiseEffect` (premultiplied, 4.5 %) + `ChromaticAberrationEffect` radial 0.0009 in its own pass (convolution effects cannot share a pass) |
| **Volumetric clouds / nebula by raymarching a 3D noise texture** (leoawen volumetric-clouds, discourse thread) | True depth inside the gas: parallax when the camera moves | **not yet** — the disc is 2D; a raymarched slab is the next step if the galaxies need to be flown through |
| **God rays from the core** (pmndrs `GodRaysEffect`) | The eye casts light into the dust | **not yet** — needs the eye as a sun mesh; worth a test |
| **PBR solids with an environment map, ACES tone mapping, N8AO ambient occlusion** | "Rendered" solids with real reflections | **deliberately no** — our material rule is emitter + wire; solids are matte black by design. Revisit only if the landmarks become physical objects |
| **Lens flare on the brightest emitter** (`LensflareMesh` is WebGPU-only in r183; for WebGL a sprite stack) | The one blown highlight | **not yet** — one sprite stack on the pupil, if it stays restrained |

Lesson recorded: a `pow()` on a value that dips a hair under zero yields NaN; one NaN pixel inside the bloom
mip chain blacks out the whole frame. Every shader output is now clamped.

What "that level" needs beyond code, honestly: the award sites spend most of their effort on **assets**
(sculpted, textured, baked in Blender or Houdini) and on **one camera idea**, not on more effects. Our next lever
is the asset pass for the other four landmarks to the Finance standard, then a single committed camera move.

## What to do with this, in order
1. Fat lines on the relevance ribbon and the core links. Verify r165 compatibility first.
2. Swap UnrealBloomPass for pmndrs bloom + a gentle depth of field keyed to the focus point.
3. Wire the devtools MCP and spend one session tuning live: bloom, fog, node sizes, contact glow.
4. Only then revisit geometry.

## Sources
- pmndrs/postprocessing: https://github.com/pmndrs/postprocessing
- threejs-devtools-mcp: https://github.com/DmitriyGolub/threejs-devtools-mcp
- blender-mcp: https://github.com/ahujasid/blender-mcp
- awwwards-3d skill: https://github.com/tsogjavklann/awwwards-3d/blob/main/SKILL.md
- secondsky/claude-skills: https://github.com/secondsky/claude-skills
- lygia: https://github.com/patriciogonzalezvivo/lygia
- troika-three-text: https://www.npmjs.com/package/troika-three-text
- 3d-force-graph: https://github.com/vasturiano/3d-force-graph
- awesome-casestudy: https://github.com/luruke/awesome-casestudy/blob/master/README.md
- Best three.js sites 2026 (Utsubo): https://www.utsubo.com/blog/best-threejs-websites-2026
- Agencies roundups: https://www.psychoactive.co.nz/content-hub/best-webgl-interactive-3d-agencies · https://www.hontran.dev/blog/best-award-winning-websites-2026
- Selective bloom thread: https://discourse.threejs.org/t/pmndrs-post-processing-how-to-get-selective-bloom/58452
- Lusion case study: https://www.awwwards.com/case-study-for-lusion-by-lusion-winner-of-site-of-the-month-may.html

## Pass 3 (26 Oct 2026) — the inside-page look: tinted dark, tonal text, diffused accent

Brief from Vinay: subtle hue-tinted background per node, less text and more visual, no pure white / pure black, a tonal
hierarchy that can be defended, cards and buttons diffused in the node hue with a faint ring, text in the same hue family.

What the sources agree on (and what we take):
- **Surfaces, not shadows, carry hierarchy on dark.** Material's dark-theme guidance: dark grey over black, elevation as a
  thin lighter overlay. → page bg = surface mixed with 6–8% of the node hue; cards one step lighter, no shadow.
- **Text as emphasis levels, not pure white.** Material's 87 / 60 / 38% emphasis; Superhuman and others: off-white tinted
  toward the accent. → t1 = off-white mixed 10% toward the hue, t2 ≈ 62%, t3 ≈ 40% of that; body contrast kept ≥ 4.5:1,
  the faintest level reserved for labels and timestamps (the Linear analysis notes its faintest grey fails AA for body).
- **Accent diffused into surfaces with color-mix().** 8% hue for a tinted panel, 12% on hover, a ring at ~35–40% hue; mix
  against the SURFACE token, never white. (DEV Community color-mix patterns; flaviocopes oklch/color-mix.)
- **Tinted greys.** Shift neutral greys a few degrees toward the accent so they stop reading dead.
- **Showcase process notes worth stealing:** animate only transform/opacity, pause the WebGL loop when off-screen, honour
  reduced motion (hontran case study of an Awwwards SOTD portfolio); frosted panels by blurring the already-rendered frame in
  a shader (futamura.dev, three.js forum); one pinned world the user scrolls through (HxnDev/Portfolio); the awwwards-3d
  skill's numeric rules (pixel ratio ≤ 2, bloom ≈ 0.45, frame-rate-independent lerps).

Sources
- https://m2.material.io/design/color/dark-theme · https://blog.superhuman.com/how-to-design-delightful-dark-themes/
- https://uxplanet.org/8-tips-for-dark-theme-design-8dfc2f8f7ab6 · https://netguru.com/blog/tips-dark-mode-ui
- https://www.buildmvpfast.com/blog/linear-aesthetic-tokens-density-keyboard-first-ux-2026 · https://making.close.com/posts/light-and-dark-our-color-systems-journey/
- https://dev.to/raxxostudios/the-css-color-mix-patterns-i-use-across-every-raxxo-theme-4009 · https://flaviocopes.com/css-oklch-color-mix/
- https://www.hontran.dev/blog/minh-pham-portfolio-case-study · https://discourse.threejs.org/t/futamura-dev-personal-portfolio-where-every-page-is-a-different-webgl-experiment/93642
- https://github.com/HxnDev/Portfolio · https://github.com/tsogjavklann/awwwards-3d · https://tympanus.net/codrops/2026/03/05/inside-corentin-bernadous-portfolio-swiss-inspired-layouts-webgl-geometry-and-thoughtful-motion/

### Design-law amendment (26 Oct 2026, Vinay's refs)
The Nothing discipline's "no glass, no shadow on UI" is lifted for the showcase inside pages. Refs supplied: neumorphic soft UI
(tonal surfaces, paired soft shadows, inset pressed state), liquid glass (specular edge, refraction, inner glow), glassmorphism
over a scene. Dark translation: page = frosted glass over the live sky (backdrop blur 26px, saturate 1.3); cards = thinner glass
with a specular top edge, inner highlight top-left, soft shadow bottom-right; controls = soft pills with paired shadows and an
inset pressed state; the hero numeral carries a light-to-tone gradient. Hue remains the single colour; depth cues replace colour
cues. The orbit/scene law is unchanged.


## 2026-10-27 — celestial field research and implementation

The requested direction is a divine whole galaxy: each world has a distinct harmonic aura, while the collective field stays smooth and easy to navigate. Implemented abstract astronomical geometry rather than symbols tied to a particular faith. Finance gold sixfold, Career blue threefold, Creative coral eightfold, Intel jade twelvefold, Engine amethyst sixfold; the eye is the pale solar center.

Visual sources: [NASA Cat’s Eye](https://science.nasa.gov/asset/hubble/cats-eye-nebula/) for nested bright shell edges; [NASA planetary nebulae](https://www.nasa.gov/planetary-nebulae/) for radial filaments. These inform artistic patterns, not measured spiritual frequencies.

Performance sources: [Three.js object optimization](https://threejs.org/manual/pages/optimize-lots-of-objects.html), [CubeCamera](https://threejs.org/docs/pages/CubeCamera.html), [renderer statistics](https://threejs.org/docs/pages/WebGLRenderer.html), and [MDN Page Visibility](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API). The distant expensive cloud shader is cached once in a half-float cube texture; nearby auras and particles animate. Six analytic aura planes, six light shells, and a single draw for 460 orbiting grains replace any need for volumetric simulation. Auto omits depth blur and god rays, Cinematic enables them, and Light caps pixel ratio. Hidden documents pause, reduced motion freezes incidental motion, and navigation uses frame-rate independent damping.

Asset audit: repeated embedded maps moved to three shared runtime JPEGs, retaining all mesh geometry and pivots. Models plus runtime textures shrink from 15,331,968 to 10,184,742 bytes (33.6%). Packed Blender sources keep original maps. The runtime GLBs now depend on adjacent `assets/materials/` files.

Hardware Chrome, 1600×1000, device scale 1, warmed local samples: previous build 85.4 fps / p95 17.3 ms; celestial Auto 120 fps / p95 8.6 ms. Total render calls 161 → 155, triangles 354,708 → 358,315. These short samples are not a guarantee on other devices. All five pages, unchanged verdict with AI switch, drag, keyboard, home, reduced motion and emulated phone pinch passed without JavaScript/shader errors. A mobile footer grid-placement issue that blocked canvas input was fixed.

Implementation: `divine-field.js`, `world.html`, six runtime GLBs and shared material maps. Deliverable includes the full static website, packed Blender files, original/source materials, rebuild optimizer, screenshots and validation.json.


## 2026-10-27 — working local product pass

Added a conventional workspace alongside the galaxy: editable Career, Creative, Allocation and Intel inputs, deterministic processing, visible rule checks and next steps, immutable input/result snapshots, recorded outcomes, JSON/text export, and journal backup/restore. Career and Creative call the existing ladder/sessions Python engines with submitted input. Allocation and Intel evaluate explicit rules in workspace_server.py. The private application on port 3737 and Claude remain separate.

The new server binds to loopback, restricts static paths, requires a per-launch write token and accepted origin/host, blocks cross-site requests, and uses revision-checked SQLite transactions. Runtime databases are excluded from the package. UI checks cover real result changes, reload persistence, outcome persistence, export/restore, stale writes, request protection, input escaping, mobile layout, and workspace use without WebGL. Saved results now replace illustrative content on the corresponding world; the Engine world shows actual journal activity.

Visual changes: distinct aura aspects and tilt, shaped light shells, quieter neighbors and memory links, restrained compass in focus views, and a clearer workspace entry. The galaxy pauses behind the workspace.


## 2026-10-27 — business context pilot

Added a local, single-operator business pilot with client-scoped profiles, project briefs, extracted documents, SQLite FTS5 retrieval, reviewed memory, persistent conversation snapshots and editable model outputs. Confirmed profile/project/memory are selected before bounded source passages; conversation history is limited to the chosen thread. The UI exposes exact source context and its hash. A changed preview is rejected before external generation. Memory suggestions remain proposed until reviewed. Approved outputs are style references, not verified factual sources.

The model adapter supports installed Claude CLI in safe/restricted mode without tools, MCP, skills or persisted sessions, plus an environment-configured Anthropic API adapter. Live drafting requires a configured account and an explicit send action. During verification the CLI was signed out, no API credentials were configured, and live generation was not verified. Local context briefs are clearly labeled as extractive retrieval, not AI output. A sign-in helper was provided and opened in Terminal.

Seventeen context/processing unit tests passed, including cross-client/project retrieval isolation, confirmed/proposed/superseded memory behavior, retained snapshots, duplicate request IDs, stale previews, citation rejection and TXT/DOCX/PDF extraction. Provider contract tests use mocks and do not establish live output quality. Browser tests passed for profile edits, knowledge upload, recall in new conversations, persistence, export and mobile layout. The app is not yet a hosted multi-user service. Private port-3737 ZOLA data was not ingested.
