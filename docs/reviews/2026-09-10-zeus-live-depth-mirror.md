# Original-only live Zeus depth mirror — September 10, 2026

The standalone [depth diagnostics](2026-09-10-zeus-depth-domain.md) are now
connected to a separately built native candidate. The live prototype mirrors
original rendering into a private color/D32F target. It continues displaying
the original target and inserts no future scenery.

Native `25228b19d59bf434817b998134a042637b16075b` is built separately, frozen at
`build/candidates/25228b19d59/vunit.exe`, and pushed to the fork. SHA256:
`2267c6502d17e6c8efe73d7a2daecda4e752267f26bcbf25af088bb3488f321f`.
The 177-patch export reconstructs tree
`2ec2d719b45267c9fece2bfeacd1f68420cd780c`.
Personal v0.5.0 / SHA87d04de4 remains unchanged.

## First live result — retained coverage failure

The first 6,000-input Amazon trial requested frame markers 1 through5990.
Actual completed markers begin at2. The harness rejects that one-frame coverage
gap even though the native consumer completes its processing and all snapshots.
This original request remains a **FAIL**. A fresh run with the observed2..5990
interval now passes all5,989 markers, six independent color/depth pairs, original
camera/input-read timing, ten original resources and25 completed4K images.

Independent postchecks on the completed first run pass all six full private
color/depth comparisons at300,1800,3500,5072,5604 and5990. The framebuffer is
2736x4096 at internal4x. Each original depth code maps exactly into the private
depth representation, and every color byte matches. Original camera/input-read
timing and25 completed3840x2160 images also match the control. This completed
prefix evidence does not retroactively make the requested interval pass.

## Implementation and completed checks

`--zeus-depth-mirror observe` requires an explicit candidate, Exotica/liveGL,
physical FFB0, bounded first/last frames and no late host-margin pass. Optional
snapshot frames are bounded to16. Absent settings preserve old recordings;
`off` removes the mirror settings. Controls round-trip in recording metadata.

The mirror starts at renderer initialization, regardless of the diagnostic
logging interval. Every original batch uses the same vertex buffers, textures,
palettes, blending, depth-test/write state, scissor and order in both targets.
Startup and explicit margin-page clears also affect both targets. Only the
private shader's depth normalization changes. Attribute locations and actual
32-bit floating depth storage are checked before use.

Snapshot requests read four owned buffers through the bounded asynchronous writer.
Native comparisons are checked again independently in Python. The harness rejects
missing frame markers, missing/short raw files, color/depth differences, nonfinite
values and incomplete writer counts. Four focused configuration/completion/
corruption tests pass. The final local suite passes336Python tests with no skips,
46native helpers and129commands, including76actual-shader cases/380steps. Its
492-file source identity is
`6df14d2faa33e0c3e9172e396d6b18e9b73f776f37deb5b9f6433a13e2e86d35`.

The first disabled-control run captured3440x1440 despite selecting3840x2160
at preflight; the serial queue stopped and that failure is retained. With the4K
display available, a fresh disabled control passes25GL/route/resources. Full
Amazon now passes8860inputs,8849requested markers, nine independent raw
color/depth pairs,117completed4K images and original camera/ADC/resources.
Repeat playback and Hong Kong also pass. Across aligned short, disabled control,
full, repeat and Hong Kong there are305completed4K comparisons and29independent
raw color/depth pairs. Full/repeat have8,849ordered markers and36identical raw
files. Original full-route camera7,060/input-read times21,180 and ten captured
resources remain exact. Batch boundaries vary; vertex/clear counters and raw
pixels/depth repeat exactly.

The seven-case default suite **retains a failure**: USA widescreen has one6.1315s
interval at frames1857..1858, failing its menu timing window. Its native/input
comparison, telemetry and later driving window pass. The other six cases and all
four software force-policy checks pass. A separate USA retry passes both timing
windows at approximately100%, with worst intervals29.59/28.68ms. The pause's
cause is unresolved. No threshold was relaxed and the first suite is not relabeled
as passing. The last clean seven-case suite remains on native50a.

[Public proof](../../results/proof/2026-09-10-zeus-live-depth-mirror/README.md)
recomputes source identity, marker/writer coverage, repeat counters and the failed
clock interval. Actual GPU execution, raw buffer comparisons, original resources,
route/pixels, native build and default outcomes remain hash-bound receipts.
No raw game resources are published. The source/binary checkpoint is separate
from personal v0.5.0; no deployment or release.

Next: actual wider-depth semantics and early future insertion. The compatibility
sentinel policy is not a finished extended-distance policy. Harden the harness
so requested Zeus display size is checked against completed captures directly,
in addition to the outer trial comparison that caught the first wrong-size run.

## Next depth-policy finding (not integrated)

Six existing host snapshots include vertices above the original24-bit limit;
Amazon frame7187 reaches50,310,035 after bias, with28,760 of33,132vertices above
16,777,215. All sampled vertices remain below2^26. This is an endpoint envelope,
not a game-wide or per-fragment bound. Three original command captures contain
four fast clears at depth0xffff00, below the nominal maximum. Consequently a
wider shader that treats only0xffffff as an empty-depth sentinel would still
block future scenery. Source command type must distinguish range initialization
from ordinary direct depth writes; a LOCAL synthetic draft explores that policy.
The first synthetic GPU run finds exact RGB but alpha254 against a scalar
prediction255 in a blended case. That failure is retained; comparison against the
actual original material shader is next. No wider policy is linked into MAME.

## Completed display validation follow-up

The replay harness now checks requested Zeus monitor dimensions against completed
captures. It directly rejects the retained25-frame3440x1440 set and accepts the
25/117-frame4K controls. All337Python tests pass. This changes only
harness/display_target.py, harness/replay.py and tests/test_display_target.py;
the prior native/GPU/default evidence is not relabeled as a fresh run.
[Proof](../../results/proof/2026-09-10-completed-display/README.md) includes the
archived validator and captured dimensions. V-Unit client-border sizing is unchanged.
