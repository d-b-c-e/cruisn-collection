# Off Road host scene and material foundation — September 9, 2026

The standalone Off Road host renderer now combines checked pending/future
descriptors, original transforms and LOD, extended projection, material bounds and
the game's radial sorting rule. Independent Python and native implementations
agree on 72 scenes and 50,736 ordered quads: twelve snapshots, pending/future
sources and 1x/2x/3x. Cold and warm caches match exactly. MAME integration and
visible-distance acceptance are the next step.

## Host implementation

`native/offroad_host_scenery.h` uses the original C31 arithmetic and a host-only
reciprocal tail. Stock model projection retains its previous default behavior;
extended projection is explicit and rejects near crossings, excessive depth and
coordinates outside signed16 screen bounds. This conservative policy is not a
complete clipping implementation and can omit crossing terrain.

The game sorts by signed radial distance, with specific store/reload points for
the X/Y components and an extended Z component. A local Python check matches
all 1,399 captured original object scores. Native/Python host scene comparisons
then agree on that ordering. This does not reproduce every special linked-layer
ordering rule or establish foreground occlusion.

Immutable models and section descriptors are cached with bounded storage. Track
and partial-frontier changes invalidate the relevant state. Material addresses
are refreshed even when the section cache is warm; colors are never frozen.
The palette queue, texture-loader busy flag, allocation limits and per-quad
material bounds are checked. Pending uploads defer the host scene. Queue/busy
deferral has synthetic coverage; none was active at the sampled scene boundaries.

The original prepared-model oracle is renewed on the updated helper: all 1,399
transforms/LOD/projections and 9,602 DMA quads still match. The twelve-snapshot
future-descriptor oracle also remains exact. The added host projection mode does
not change those captured stock paths.

## Live material and background evidence

A local bounded material probe completes the original 6,000-input Off Road drive.
It preserves 4,191 camera samples, 16,764 actual ADC reads/timestamps, and the
three completed 3824x2073 captures at5500/5550/5600. No physical force is enabled.

At scene-entry snapshots4000/4500/5000/5500/5900, the entire 8,388,608-byte texture
share and 131,072-byte palette share are identical. The texture/palette write
counters are also unchanged across those snapshots. All1,978 scene-entry queue
samples report no queued palette upload and no active texture loader. The probe
observes5,305,732 texture writes and62,406 palette writes earlier in its bounded
window; it does not establish whole-session or other-track material lifetime.

The eight contiguous textured background tiles are already submitted immediately
before the proposed scene hook. Captures record both the Lua frame and actual
native frame/time/page; the native frame is one lower in these samples. That
difference must be preserved when matching a future runtime adapter's logs.

Two diagnostic mistakes are retained: the first probe required16 DMA words,
while these generic2D calls write15; the first background oracle also included a
preceding flat clear from the same generic submission PC. The corrected probe
records actual word counts and the oracle checks only the current-frame textured
suffix. Neither failure required changing game rendering.

Local evidence is under `results/diagnostics/offroad-material-20260909`.
`host-oracle-cached.json` is the final72-scene comparison; its ordered output equals
the earlier uncached result. `materials-v2` owns the new visible/resource evidence.
Raw material, ROM, model and DMA operands remain local.

## Checkpoint and next step

Local checks pass241 Python tests with no skips,23 native test executables,
10,081 C31 vectors/137 yaw vectors and32 GPU checks,63 commands total. All363
source files match identity
`3fa8026171f79424ece7fe66f4951adb0db2079070d3f94a688687a3ae14b590`.

Connect this helper to a separately built, explicitly selected MAME candidate.
Keep guest RAM, allocations and hardware DMA untouched and assert zero guest CPU
cycle delta. Preserve absent options and old recording behavior. Then measure
1x/2x/3x and repeat gameplay, exact original resources/route, foreground occlusion,
handover and 4K performance before any menu or deployment decision.

No new MAME build/export/default renewal belongs to this standalone milestone.
Native cf58/SHA37c0a4ce retains its prior seven-default acceptance. Personal
Stream Deck remains v0.5.0/SHA87d04de4, verified again. No release, deployment,
hosted workflow, physical FFB, World tuning or menu removal occurred. Work
continues directly; the one-minute heartbeat is recovery only.
