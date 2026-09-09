# USA host scenery integration — September 9, 2026

USA now draws additional pending scenery through an optional host adapter, using
its verified model codec. This candidate preserves the recorded drive and original
rendering resources. It establishes visible additional distance in USA, but **3x
does not yet improve on 2x** in the measured interval. Future section loading is
the next limit. Four-game parity and visual acceptance remain open.

The maintainer clarified that the 30-minute heartbeat is a recovery wakeup, not a
work cadence. Work continues directly between implementation and verification
steps during active turns. There is no scheduled morning cutoff.

## Implementation and isolation

Collection `492bf48` adds `native/usa_host_scenery.h`, an independent scene analyzer,
bounded scene capture and replay-only controls. Native
`4e565971954171798caf7bc633c9a57cb3f23b04` links the USA codec and adapter into MAME.
It was built separately and pushed to the fork. The frozen candidate is
`build/candidates/4e565971954/vunit.exe`, SHA256
`248aef7c5c56402ed117d52ef228cc3864d9f14dadbfaf654a025d4cb834f20b`.
The 142-patch export reconstructs native tree
`2ea79b989c1869495cd419aa123a3075be9d680a` from the declared base.

The adapter reads USA's pending list at the checked ordinary scene boundary
(PC0x81/list0x40), prepares full/compact transforms and billboards, selects LOD,
decodes USA's interleaved model format and submits auxiliary polygons through the
existing GPU transport. It uses direct main RAM, bounded ROM/internal RAM reads
and a zero-guest-cycle assertion. It does not activate guest objects or append
hardware DMA. Absent controls install no hook; stock guest distance/residency is
required. Alternate/deformed codecs are counted as unsupported, without model
allowlists. Near-plane crossings and signed16 projection overflow are rejected.

Controls are deliberately diagnostic and require explicit frame bounds:

```text
--usa-host-scenery observe|draw
--usa-host-first 3500 --usa-host-last 5010
--usa-host-far 80000|160000|240000
--usa-host-log summary|quads
--usa-host-layer legacy|coverage|split|both
```

Summary logging and the existing combined coverage/split layer are defaults for
this opt-in adapter. `off` clears its recorded controls. Old recordings and all
other game configurations retain their prior behavior. No launcher menu, default,
personal preference or World FFB setting changed. Stream Deck still uses v0.5.0,
native SHA256 `87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`.
No deployment, release or hosted workflow ran; physical force remained0.

## Evidence

The control, draw1/draw2/draw3, repeat3 and final observe3 runs complete the original
5,012 inputs. They preserve3,211 camera samples and9,633 actual ADC values **and
timestamps** over1800..5010. Each completes16 current4K captures at3500..5000,
every100, with client dimensions3824x2073.

| Comparison | Completed images changed | Ordered host quads across755 scenes |
|---|---:|---:|
| Stock control to host1x | 10/16 | 10,751 at1x |
| Host1x to host2x | 12/16 | 168,874 at2x |
| Host2x to host3x | 0/16 | 168,874 at3x, same fingerprints |
| Host3x repeat | 0/16 | All fingerprints identical |
| Stock to final observe3 | 0/16 | Observe and draw3 geometry identical |

Image inspection confirms additional distant trees and structures. Original nearby
cars/road/HUD remain in the inspected views. This is **not** full material,
foreground occlusion, temporal handover or whole-track visual approval. Sparse
images cannot rule out flashes between captures or certify each added surface.
The earlier list0x43 is empty in all750 observed scenes; this does not prove where
every USA sky/background path is drawn.

Three pending-list snapshots compare all decision counts and ordered quads against
independent Python and the compiled native helper at all three far settings. The
final probe also matches the live MAME output at exact native frame/time/page.
The snapshots have222/109/204 pending descriptors. Their1x outputs are2/9/36 quads;
2x and3x are311/11/502. Everything eligible and currently loaded is already inside
2x in these samples. Across the entire measured host interval,2x and3x match.

Two separate4,502-input runs capture the original hardware polygon stream, video
memory, textures, palette and metadata. **All153,833,626 bytes match**, alongside
2,701 camera samples and8,103 actual ADC timestamps. This protects original
resources; it does not independently certify the material lifetime of added
pending objects or their visibility against foreground surfaces.

Summary draw3 callback p99/max is0.439/0.605ms; repeat0.412/0.563ms. Measured
3500..5000 emulation speed is approximately100% in each control/draw/observe run.
Detailed observe logging raises callback p99/max to2.167/2.525ms. These are host
callback and emulation interval measurements, not GPU latency or a full smoothness
assessment. Resource captures have separate heavier instrumentation.

## Retained diagnostic failures

The first snapshot probe used address-space reads and retriggered the native hook
while inspecting list0x40. The strict verifier rejects its duplicate scenes. The
capture now reads the main RAM share directly, including palette words, and
collects lookup bindings even if a model was previously seen with direct colors.
Normal draw runs used a different motion-only probe and contain no duplicates.

The next probe exposed a clock mismatch: Lua's latched replay frame can be one
ahead of the native screen frame at the same emulated instant. Its runtime match
fails at the third snapshot. The final probe explicitly captures the native screen
frame together with exact emulated time and page; no approximate alignment is
used. Both failed reports and their source runs remain local.

An initial allocator provenance draft rejected the internal-RAM stack address and
stopped at1804. That failure is retained. This draft is separate from the successful
scene adapter and its tests; bounded stack support is being added for future
section mapping.

## Validation and continuing work

Local checks pass217 Python tests with no skips,18 native helpers,10,081 C31/137 yaw
vectors and32 GPU checks across50 commands. All329 source hashes have identity
`90c5978628d5091cd57b4330e5ad5333761a96565a0e2dbf012770c4a2c0c1b8`.
The final independent scene oracle uses the analyzer compiled in this check run.
All seven default regressions pass on this exact native candidate and source
identity, including the full Germany replay, actual UDP/memory telemetry, four
software force policy/polarity checks and21 completed Exotica4K images.

Raw evidence and unfinished mapping scripts remain LOCAL under
`results/diagnostics/usa-host-scenes-20260909`. [Publishable proof](../../results/proof/2026-09-09-usa-host-scenery/README.md) distinguishes
recomputed route/pixel/scalar checks from hash-bound geometry/resource/build
receipts. Raw ROM/model/material operands must not enter the public repository.

Continue into USA's section loader:3F80..4214 builds variable-length section
records, with generic model allocation at40B9/7035. Sections use six base words,
optional lists/placement offsets, and runtime palette binding through9EF8.
Map placement, final flags, pending/future membership and material residency before
adding host-owned future descriptors. Keep the World2.5 road/ground work and
Off Road/Zeus adapters active alongside this effort. Preserve existing experiments
until useful replacements pass comparable visual and original-route acceptance.

A LOCAL preliminary decoder reconstructs383/383 matching scenery objects in the
older frame3000 mapping snapshot from26 sections/1,227 definitions. This checks
model/position/heading matching only, not future material residency, all final
flags or live allocation timing. The subsequent LOCAL `section-probe.lua` and
`section-oracle.py` now match1,700 ordinary allocations across20 sections,
10 headings and413 offset placements, including1,504 direct palette bindings.
Twenty-four custom handlers remain excluded. Fields are captured before the
final class-specific link/flag processing, so this is not a final descriptor
oracle. Its5,012-input replay preserves camera/ADC timing and all three late4K
images. These additional local prototype results are separate from the archived
host-pending proof above. Promote the probe and verify final fields/frontiers
before adding future scenes to MAME.
