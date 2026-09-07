# Session Notes

Date: 2026-09-06. Branch: codex/world-scenery-distance. User authorized ongoing
fixes until they return, with separate commits and pushes. Physical automated FFB
stays OFF. Native pushes go to fork/poc/quadlog, never mamedev/origin.

## Built and deployed

Native abe4b98aa38, root vunit.exe SHA256
55578f8a06a81a78391119e4bad29b673b90e7e67ea2d6d29907adec1fe8ee90.
Distant Scenery remains OFF by default, World 2.4 / widescreen / scale>1 only.
It now covers five mountains, four tree cards and one grouped forest strip.
Canonical native/world_scenery.h syncs to MAME. Forest CB2375 uses original
clamped projection and its own counter, never the small-tree reciprocal path.
No guest RAM writes. Strict model/radius/flags/code guards; direct backing RAM
inside taps avoids nested-read corruption. See expanded-scenery review.

Full derived Germany candidate/repeat: 8,783 input/time rows and 146 native images
match. Parent has ten changed images; no original-route claim. Driving ratios
100.0041%/100.0048%; counts 912 mountain,3964 tree,277 forest admissions,
31712 reciprocal reads,max8120. Native GL201 completed frames vs first native
build:143 changed,max1234pixels,last2192; all2196..2400 match. Two new mountains
show earlier through bridge. New three-model native geometry matches boundedLua;
complete scenes preserve all original geometry/order. Strict frame comparison
retains two HUD quads spilling2171->2172.112patches reconstruct ae27265e06a1da7ae7646c9ea888857a538ad12f.

## Running / next

- All seven scenery-expanded-default-regressions cases PASS at55578f8a, including
  timing gates and Exotica21completed GL images.71Python tests pass.
- CI34070790847 at e81bc4a all four jobs PASS. New docs/harness cadence changes need
  final CI; ff master after checkpoint. User's Stream Deck uses this checkout.
- Strong next candidate: CB1A8B returns at6093 already inside original far (53744),
  plainly visible above road around game elapsed1:15. Native snapshots6060/6120
  show huge mountain arrival. Prepared read-only probe
  results/diagnostics/mountain-return-activation.lua, first6000,last6140,
  slot11A7C/modelCB1A8B. Read-only run started (one emulator at a time), --until-frame6142
  --capture-state, then inspect field assignment and pending->active timing.
- Earlier diagnostic CCF288/slot12668: allocated2991, pending2000->active1000 at3017,
  firstdraw3019 inside80k. lua/world_scenery_early_activation.lua intercepts one
  object's section atPC7B69, lead1, guest performs list transfer. Activates2999,
  draws3001,adds54quads but original order changes3019. Only22visiblepixels;
  most occluded by trees. NOT PROMOTED.41GL every2 captures omit odd3019 concern.
- Pending comparison: object+0x1B low16 vs player section+wordD58C, program7B58.
  List61EC -> activeD50B. Factory625C/626D through7B9A/7CA2. Read-only field probe
  captures internal CPU stack809800..809FFF. RuntimeWorld24asm under
  results/diagnostics/scenery-activation/run/program.asm. No game code dumps committed.

## Evidence and harness

Latest docs/reviews/2026-09-06-expanded-scenery.md. Proof expanded-scenery/activation.
Previous scenery-coverage review documents four-tree build and failed Lua capture
(timeout2252/164images, explicitly not accepted; native full runs completed).
scenery-events full read-only8783/146PASS:3584complete runs,16323events. Ranking
bounds is not visibility; slot reuse is notLOD and first gate isn't creation.
compare_scenery --alignment scene preserves stricter frame differences separately.
gl_frames --frames FIRST:LAST --every N --details --contact-sheet PNG validates
global frame multiples, missing/duplicate receipts and reused filenames; reports
changed pixels/bounds. Latest suite71 Python tests (run final complete set).

Original attended world-germany-extended-20260906 is immutable. No fresh recording
needed for current probes. Continue graphics/activation, then cross-game adapters,
weakWorldimpacts (ImpactCues OFF pending attended acceptance), Cheats submenu.
Toolkit v0.11.1 unchanged. MAME XMLcheatmanager is the right engine; downloaded
cheat0279 has all games, not installed/enabled here. No frontend Lua cheat API yet.
README corrected: USA numeric HUD with OCR fallback,World OCR; RPM unavailable.
Never racing mame.exe; never rebuild root executable while it is in use.
