# Session Notes

Date: 2026-09-06. User approved steps 1â€“3: global native World distance trial,
controlled comparisons, then a short-term/native-path decision. Continue authorized
improvements with separate commits/pushes. Automated physical FFB OFF. Native
pushes fork/poc/quadlog only; never mamedev/origin. Never touch racing mame.exe.

## Current build and decision

Read docs/reviews/2026-09-06-global-distance-trial.md first.
Native 9ea71f601b3, root E:/Source/mame-src/vunit.exe SHA256
050cf6ea393f1d44a1662ad191a5fc6d38be3084f49603ce8d7de2b379f736ce.
The 114-patch export reconstructs tree cb136368d9bcdbebc482fab6e27d1e702b95715b
from mame0286. Native helper sync and real-program guard/arithmetic tests pass.
Code commits: cc9687e (global trial/export), deb5c82 (camera/ADC diagnostics),
42f1635 (attended trial recording). All 79 Python tests PASS; CI34080307060 at
42f1635 passes all four jobs. Documentation/evidence is committed separately.
All seven global-distance-default-regressions PASS: USA original/widescreen,
World2.4 synthetic/Germany, World2.5, Off-Road, Exotica (21 completed GL frames).
184 proof archive entries verified; six full trial summaries recompute exactly.

Global World 2.4 experiment is built, not enabled in normal launcher settings.
MIDV_WORLD_FAR=80000/100000/160000 requires the composed checked RAM patch;
MIDV_WORLD_LEAD=0..8, MIDV_WORLD_CPU_PERCENT=100/125/150/200. No per-model/level
allowlist. Far/clamp instruction patches plus host reciprocal cache, shared
pending threshold. Never combine with selective scenery. Unset FAR is inert.
Canonical native/world_distance.h; harness/sync_native.py copies it into MAME.
Wrong revision/profile or bad diagnostic output fails. Cold-start replay tested;
interactive reset/save-state behavior not certified for the experiment.

Decision: 2x far / lead8 / NORMAL CPU is useful enough for an attended trial.
It visibly brings in the mountain earlier, including full-resolution evidence.
Do not call it pop-in elimination or promote it to default yet. Fresh Germany
and a second World 2.4 level are next. Longer-term: host static transform oracle,
then pending/future-section drawing independent of guest simulation. Do not
resume growing per-model allowlists as the main strategy or jump to a full port.

## Evidence and repeatability

results/diagnostics/global-distance-trial: six complete 8783-frame Germany runs.
Original control matches all 146 native images. Each has 321 completed GL images
1600..8000 every20 at512x451/internal4, 7281 camera samples, 21843 actual ADC reads.
All frame input/time comparisons match; all native guard logs cover0..8782.
Far/lead axes separated: original,far125,lead4,far125-lead4,far2-lead4,far2-lead8.
All ~100% emulation speed. 2x/8 has7425141 extended reciprocal reads,347915 extra
far-gate tests (repeated operations, NOT unique/visible objects). Original-camera
match fails in every extension. Far-only1.25 rejoins until3099; then route differs.
Lead4 first actual wheel difference at2299: 105->104 after a5.8us sample-time
shift; camera differs2300. Far-only actual ADC values all match, so interpolation
is not the whole explanation. Traffic/render phase can differ even with equal
camera words. Motion reports now expose matching intervals and ADC differences.

Bounded-original/bounded-far125-lead4/bounded-far2-lead8 preserve history to5900;
Lua intervention5900..6140 plus read-only provenance; 201 GL frames5900..6300/2.
Control prefix6304 PASS. Both candidate cameras match5880..6183;1263 actual ADC
frame/value/PC sequences match, timestamps differ; camera first differs6184.
Projection restore6141 does not undo earlier object activation. Later pictures
are mixed-state evidence. Heavy Lua traces are NOT native performance evidence.
First attributed mountainCB1A8B submission6093 ->6037 ->5981 (original/1.25x4/2x8).
BackgroundCB2314 and forestCB2375:6119 ->6071 ->6005. Object addresses change with
allocation order, so this compares observed model presence, not stable instances.
2x brings the mountain into view before original; 1.25x shows more far-clamp shape
change. Future oracle should identify static placements by model+world transform.
Fullsize-original/fullsize-far2-lead8 deliver8/8 GL images6000..6140/20 at3824x2073;
frame6040 inspected in both. This does not clear all late black-road/texture bugs.

results/diagnostics/global-distance-cpu125: normal-distance and2x/8 clock controls
at125%. Clock alone changes138/146 native images and route; both100/125 controls
still have1150 camera updates over2300 intervals3500..5800. No reason to ship it.
results/diagnostics/world-global2x-germany/case: full new derived candidate,
record+identity replay8783/146 PASS. Parent120 native images differ; original
attended case immutable. Full-size drive record99.7576%, replay100.0003%; p99
26.588/26.423ms, worst312/126ms, so not a stutter-free guarantee.

Proof: results/proof/2026-09-06-global-distance-trial. ZIPs retain raw CSVs,
invocations, probe sources and reports; provenance.json has every entry SHA256.
Overview video/PNG plus lossless fullsize frame6040; no ROMs/binaries/RAM dumps.
Original attended source remains world-germany-extended-20260906.

## Commands / next attended drive

python harness/run_world_distance_trials.py results/diagnostics/world-germany-extended-20260906 --candidate E:/Source/mame-src/vunit.exe --output results/diagnostics/my-global-matrix --motion 1500:8780 --gl-frames 1600:8000 --gl-every 20
Replay/derive_case/record_drive all accept --world-far/--world-lead/--world-cpu.
The matrix tool reports completion separately from visual/camera/native identity.

When the user is present and requests recording:
python harness/record_drive.py --game world --world-far 160000 --world-lead 8 --title "Germany global 2x" --with-ffb
With-ffb is attended-only; without it force
is OFF. No attended session was started while the user was away. The recording
keeps saved wheel/display preferences, disables selective scenery in its own
settings, and archives the temporary composed patch before its source disappears.
Normal Stream Deck launcher preferences stay unchanged. CLI recording support is
unit-tested; fresh physical drive still outstanding.

## Prior context to retain

docs/reviews/2026-09-06-global-distance-and-native-port.md: research/architecture.
Jeff Harris USA C/SDL2 project jeff-1amstudios/cruisin-usa, commit5eeeb65..., found
and inspected, NOT built/play-tested here; incomplete. Original USA source/ROM
walker useful; no equivalent World/OffRoad/Exotica source established. V-UnitC31,
ExoticaC32, not MIPS. OutRun2006 section union, OpenMW static paging, RT64 early
geometry capture inform next steps. Third-party clones are ignored diagnostics.
Archived docs/experiments/world-global-distance patches are historical drafts,
not instructions to reapply to current source.

Prior selective scenery baseline e8b8fc3be9c / d520c414 remains in the new build:
five mountains, four tree cards, forestCB2375, background early lead8, OFF default.
world_scenery.h canonical, per-model guards intentionally remain for compatibility
with old cases. Background-activation case8783/146 repeats; strict geometry order
failures remain documented, never relabel PASS. Original D binary archived in
results/diagnostics/germany-background-activation-native/case/binary/vunit.exe.
World transmission atlas retention/terrain wedge fixes: see world-assets-and-road
review. Black wedge around HUD1:36.78 mapped to real missing road; conservative
terrain-radius extension is separate from far distance. Exact GPU path unchanged.

Pending broader work: cross-game verified adapters, World weak impacts/physical
wheel acceptance (ImpactCues OFF), Cheats submenu. Toolkitv0.11.1 unchanged.
