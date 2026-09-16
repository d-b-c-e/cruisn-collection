# Extended scenery: remaining release work

All four games have host scenery implementations, but the current candidate is
not yet accepted for release. The newer adapters are still diagnostic CLI
features; the personal installation and public v0.5.0 package are unchanged.

September16 update: [verified V-Unit scene startup](2026-09-16-vunit-scene-bootstrap.md)
and [continuous operation with owned graphics shutdown](2026-09-16-vunit-continuous-runtime.md)
now have focused recorded qualification across USA, both World revisions and
Off-Road. This closes the fixed-start/fixed-end implementation gap for explicitly
selected candidates. Routine logging, multiple-race transitions and product
acceptance remain open; it does not establish elimination of pop-in.
The subsequent [quiet runtime change](2026-09-16-vunit-quiet-runtime.md) removes
persistent V-Unit scene journals and bootstrap dumps under explicit continuous
selection, with matching geometry fingerprints and recorded presentation.
Routine capture separation is now implemented; multi-race and product gates
remain open.
Exotica now also passes a [3x scripted race transition](2026-09-16-exotica-race-transition.md)
after the full Amazon recording: identical menu images and camera/ADC, ten native
pool epochs, clean shutdown and a new-race start. This is not a complete second
race or proof of useful outer-band visibility.

World now passes a [3x race-selection continuation](2026-09-16-world-race-transition.md)
through a new coastal race:12,669 inputs, exact motion, clean continuous shutdown
and visible distant terrain in changed completed images. This is sparse visual
coverage, not complete second-race acceptance. Off-Road also passes a [3x El Paso restart](2026-09-16-offroad-race-transition.md)
through car selection and early second-race driving. The initial401/400-line
image mismatch is retained; a matching400-line control verifies distant-cliff
additions. This is same-course restart coverage, not a new-track acceptance.

USA now passes [Continue and a Golden Gate restart](2026-09-16-usa-race-transition.md)
with12,212 exact inputs/motion and clean continuous shutdown. Each game family
now has a recorded race/menu/new-race continuation, with explicitly scripted tails
and limited second-race scope. A [shared diagnostic preset](2026-09-16-scenery-presets.md)
centralizes the qualified continuous3x configuration; it is not yet a product
control or full-course release acceptance.

[Normal mid-race close](2026-09-16-normal-close.md) now qualifies on Exotica
and USA as representatives of both renderer workers. Both drain and join cleanly;
full playback failures are retained separately from the passing close/prefix
scope. Machine reset and product integration remain separate requirements.

[Continuous Exotica recovery](2026-09-16-exotica-continuous-retirement.md)
now returns to the exact ordinary view after a rejected future assembly beyond
the old capture cutoff. The preset selects this narrow fallback; degraded output
still fails parity. Startup recovery and machine reset remain separate.

## Current position

The [animated-source census and sequencer](2026-09-16-exotica-animation-sequencing.md)
identify a separate Exotica coverage gap.246original animation updates now match
independent scalar/native helpers, but initial phase, lifetime ownership and earlier
animated drawing remain unqualified. The helper is standalone, not a live fix.

| Game | Latest useful evidence | Remaining requirement |
| --- | --- | --- |
| USA | Conservative horizontal rejection preserves seven 4K captures, cuts submitted future quads by 74.6%, and improves six measured windows from 98.18% to 99.68% speed overall. | The busiest window still measures 97.99%. Broader track and activation coverage remain; small far-coverage gains are not elimination of pop-in. |
| World 2.4 / 2.5 | Both future adapters and both road codecs are implemented. The 2.5 far-coverage candidate adds distant coverage in 18 of 21 completed 4K frames. Active-road polygon recovery now repairs the sampled Germany black/pale road gaps, passes the full drive and a 2.5 compatibility segment, with exact original buffers and recorded inputs. | Hawaii's exposed authored terrain edge remains. New York artifacts/crash need their own reproduction. Coverage, handover and occlusion must be evaluated beyond the current routes. |
| Off Road | Complete El Paso 2×/3×/repeat preserves the drive; 3× changes 22 of 66 images over 2× and repeats all 66 exactly. Late original resources and a nonempty future scene pass. | Other courses and broader foreground/handover coverage remain. The wider-admission trial adds geometry but changes none of its 21 completed frames; it is not a product improvement. |
| Exotica | Combined future/waiting/active margins and original replacements pass the Amazon route. Current 4K temporal checks retain earlier foliage through handover, preserve the car region and repair sampled black wedges. Correcting the harness's covered-window size restores approximately 100% in measured windows. Hong Kong also passes a second-track segment. | The outer visibility boundary still needs a useful, continuous transition. Hong Kong is not a complete attended race, and its saved frame5000 contains no third-band objects. Other courses and final combined defaults remain separate gates. |

These are route-specific findings. A nominal multiplier does not establish equal
visible distances, performance or visual quality across four different engines
and authored courses. Changed-pixel counts alone are not visual acceptance.

## Avoiding low-value work

A saved-quad screen finds substantial wholly offscreen output in World and Off
Road too: 4,617 of 8,403 quads in World25 frame5900, and between zero and all
quads in five Off Road samples. This is not yet a proof that their complete
projected models can be rejected. In particular, Off Road validates material
bounds after generating quads; moving rejection ahead of that check would change
its guard behavior. Both paths already measure close to full speed in their
accepted windows. No horizontal-culling change is being carried to them merely
to reproduce USA's optimization.

The outer Exotica appearance check now includes Amazon5644 using the current
saved early-visibility packet. A separate immediate-insertion renderer exactly
reproduces its recorded color and depth before testing removals. Removing the
82 screen-intersecting objects in the outer tenth removes 1,504 quads and changes
26,535 intermediate color/depth pixels. Removing the whole third distance band
removes 3,746 quads and changes 32,942 pixels. None of the outer group's affected
pixels has both the same color and depth in the completed5645 private target.

That last comparison is correspondence, not a command-ownership proof or a
completed render with those objects removed. It does not establish that the
current combined path has no distant benefit. It does mean that fading this
intermediate contribution cannot yet be claimed to soften a visible boundary.
The existing7188 completed future-only removal likewise finds no visible gain.
Do not run another whole drive merely to inflate submission counts.

The [subsequent sample-selection investigation](2026-09-15-exotica-distance-sample-selection.md)
finds no uncovered active object in nine saved Exotica views. A completed2x/3x
comparison is exact at three snapshots, but those scenes have no third-band
polygons and do not establish outer-boundary quality. The two sampled scenes
with substantial third-band geometry produce no colored fragments when screened
against their completed depth. Use the new saved-band preflight and seek a more
open sightline before another distance replay; retain the existing Amazon case
for its useful margin and handover coverage.

The [Mars scout and matched pair](2026-09-16-exotica-mars-distance.md) now find
a small actual3x benefit:509 completed4K pixels at5200, zero new near-black,
with the other12 sampled images exact. The source-fragment diagnostic qualifies
its unchanged full insertion before attributing the conservative completed-depth
screen. This supplies a useful positive sample; continuous appearance, broader
course coverage and physical-wheel acceptance remain open.

## Next decisions

The [active-road margin recovery](2026-09-15-world-active-road-margins.md) now
repairs the sampled Germany1:37 black wedge in all five compared current4K
frames. Original route/resources/draw commands remain exact. This nearby-road
repair is separate from far-distance parity. The subsequent
[polygon coverage repair](2026-09-15-world-road-polygon-coverage.md) also fills the
two residual Germany1:35.69 holes and passes the full recording plus World2.5
compatibility. Its entire displayed indexed page matches the independently
reconstructed proposal. Broader track/handover acceptance remains open. The
diagnostic stays off by default.

The subsequent [World fade comparison](2026-09-15-world-germany-distance-fade.md)
preserves the Germany drive and all 31 completed current-4K images, but changes
none of them. The earlier World2.5 positive effect is small. Neither result
establishes a useful general solution to pop-in or repairs the left road wedge.
Off Road now has [verified optional camera depths](2026-09-15-offroad-camera-depth.md)
and a [gated partial-frontier recovery](2026-09-15-offroad-partial-frontier.md).
The latter restores 235 polygons in a captured town scene but changes none of
its 11 completed images. Keep these experimental controls out of product
promotion until there is a demonstrated completed-image benefit. Do not repeat
those same windows merely to obtain a positive result.

1. The [seven-case default suite now passes](2026-09-15-combined-default-regressions.md)
   on the combined native candidate. Retain that result; do not repeat it without
   a new change or unresolved concern. Package/fresh-install/attended gates remain.
2. For visible distance transitions, select an actual completed-image boundary
   and follow its source through admission and original handover. Reuse saved
   command/resource captures; capture a missing bounded interval only when it
   answers that specific question. A fade must preserve intrinsic transparency,
   foreground depth and lifetime continuity.
3. Keep World's authored terrain gap separate from far-plane clipping. Find the
   adjacent coverage or backdrop relationship before considering generated
   geometry; increasing an already sufficient far plane cannot extend a mesh.
4. Separate production operation from diagnostic capture. The current adapters
   have bounded observation intervals and deliberate fatal guards. A normal
   gameplay mode needs continuous operation, bounded resource use and an explicit
   fallback/reporting contract for an unsupported scene before these controls
   are suitable for player use. Keep diagnostic failures strict and visible;
   do not silently count degraded output as passing parity.
   The [preparation fallback candidate](2026-09-15-vunit-preparation-fallback.md)
   now completes injected World, USA and Off Road failures with exact
   original-only output and explicit degraded reports. Continuous product
   operation remains to be qualified.
   An [Exotica bounded stop](2026-09-15-exotica-stop-boundary.md) now drains all
   pending work and returns its private color target to the original image in
   the retained Amazon segment. Actual fault recovery still needs an ordered
   retirement protocol; a blanket early return would strand scene ownership.
   The subsequent [ordered retirement candidate](2026-09-15-exotica-retirement.md)
   now recovers a future-assembly-only fault and matches the original-view control
   from its first retired frame. Other failure phases remain strict.
   The [saved runtime-budget audit](2026-09-15-continuous-runtime-budget.md)
   finds modest live ledger occupancy but a handover journal already73.5% of
   its64MiB cap in one Amazon drive. Separate runtime enablement from capture
   policy before removing diagnostic windows; do not simply raise every limit.
   [Quiet journals and checked counters](2026-09-15-exotica-runtime-counters.md)
   now qualify on a primary4K sample with exact captured-control output.
   Routine journal budgets no longer stop quiet execution; live bounds and
   snapshot/failure evidence remain. [Guest-based startup](2026-09-15-exotica-bootstrap-scenes.md)
   now passes a targeted4K replay: pool and scene activation use verified game
   transactions, including the previously excluded boot/menu period. The
   [continuous runtime policy](2026-09-15-exotica-continuous-runtime.md) now
   carries CPU/GPU work past shortened capture ends in one quiet5,300-input
   replay, preserving193 saved files and four4K images with joined quiescent
   shutdown. Multi-race operation, interrupted exit and machine reset remain
   separate acceptance work; this is still a candidate-only mode with FFB0.
   The [V-Unit runtime audit](2026-09-15-vunit-runtime-readiness.md) identifies
   the corresponding per-game startup/end work and fixes ignored buffered
   diagnostic write/close failures. Existing summary sizes do not justify
   treating V-Unit logging as the same measured cost problem as Exotica.
5. After the rendering policy is stable, expose coherent per-game controls and
   renew final package/default/4K gates. Obtain attended cross-track and wheel
   acceptance; do not treat prior-release waivers as acceptance of these changes.

The [September15 upstream refresh](2026-09-15-zeus-upstream-refresh.md) also
backports the Zeus2 solid-color register correction separately. The frozen
successor preserves the sampled Exotica original/private output; it is not a
new distance or black-margin improvement.

Local evidence: `world25-roads-20260914/horizontal-cull-cross-game-screen.json`
and `exotica-amazon-20260909/far-appearance-immediate5644/` under
`results/diagnostics`. The latter contains the exact control, two removal
variants, completion correspondence and inspected image. These checks needed no
new game execution or native build. Raw game resources remain local.

The [quiescent Exotica reset candidate](2026-09-16-exotica-quiescent-reset.md) now reboots with exact original inputs and completed images in an early case. The subsequent7500-input Mars reset also passes nonempty scenery, camera/ADC and all ten sampled post-reset images. Interrupted-work and pre-startup reset boundaries remain open; no reset workload waiver was introduced.

The [USA](2026-09-16-usa-opacity-observer.md) and
[Off-Road](2026-09-16-offroad-opacity-observer.md) completed-opacity observers now
separate final-distance envelopes from foreground occlusion without changing
displayed colors. USA's sampled visible page has41 potentially affected fine
pixels; Off-Road's has none. These windows do not justify another fade replay.
Existing positive2x/3x comparisons remain valid; broader visible transitions need
their own source/ownership evidence.

The [pristine Exotica startup reset](2026-09-16-exotica-startup-reset.md) now
passes a full5460-input case with nonempty scenery and unchanged original motion.
Its separate receipt/proof path complements active quiescent reset support;
interrupted work and degraded-reset handling remain open.

[Pre-device Exotica reset](2026-09-16-exotica-pre-device-reset.md) now checks FIFO ownership before MAME clears child-device state. The existing active reset and all twelve completed4K images remain exact; interrupted-work reset remains separate.

[Off-Road's visible boundary screen](2026-09-16-offroad-visible-boundary.md) preserves the early3x view but finds no completed opacity contribution. The next investigation is the excluded billboard object class, including its persistent hit-state hook, rather than another replay of these fade windows.
