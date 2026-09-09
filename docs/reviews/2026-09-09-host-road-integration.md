# Host road integration and resumed parity work — September 9, 2026

The maintainer explicitly resumed work after the scheduled morning stop. The
existing heartbeat is active as **Cruisn extended scenery parity**, without the
expired 08:00 cutoff. Cross-game parity remains the objective; it is not complete.

World 2.4 now has a separately guarded host road decoder. At frame 6720 of the
Germany drive it fills the long missing stretch of uphill road that previously
showed sky. It preserves the original drive and repeats the added geometry and
completed images. Some sky gaps beside trees remain. This is a CLI diagnostic,
not a deployed or released replacement for the existing experiments.

## Implementation and the timing defect caught by replay

`--world-host-roads on|off` requires an explicit bounded host-scenery mode.
Absence preserves older recordings; recording the option freezes its choice.
The original guest still owns simulation, allocation, activation and hardware DMA.

Roads use original ROM vertices but select their distant polygon/UV template from
checked main RAM. The decoder follows the game's metadata selector and LOD
threshold, rather than a model or track allowlist. Class B future descriptors add
only the independently checked render fields; no physics links are initialized.
Near clipping, custom class A and broad resource lifetime remain incomplete.

The first native candidate exposed a critical distinction between a memory read
and an observation without side effects. MAME's `generic_speedup_r` consumes 100
CPU cycles when the CPU reads D4C0/D4C1. D4C0 is also the road-detail threshold.
Host reads through the regular address space therefore changed emulated timing.
ADC timestamps first diverged at1802 and the camera at3108. Both the headless
failure at8562 and the on-screen route failure are retained.

The final candidate reads main RAM directly, restricts other reads to known ROM
and internal RAM spans with side effects disabled, and fails if a host callback
changes the emulated CPU cycle count. Full camera and actual ADC timestamps then
match again. These protections belong in the other adapters too; a decoder that
writes no memory can still alter emulation through read handlers.

## Evidence

| Check | Result and limits |
|---|---|
| Captured road oracle | Native template selection matches all23,589 road calls. Independent Python also verifies23,589 projected buffers and21,123 unclipped ordered DMA calls. The2,466 clipped calls remain excluded from the polygon oracle. |
| Future snapshot oracle | Four snapshots pass descriptor and projection comparisons with and without roads, at1x/2x/3x. The native and independent Python implementations use captured resources; this does not certify future texture residency everywhere. |
| Full Germany | Three9,269-input runs: roads off, roads on and repeat. All preserve native reference images,7,461 camera samples and22,383 actual ADC reads/timestamps over1800..9260. |
| Added road visibility | Roads on changes18/21 completed3824×2073 images at6400..6800. The uphill-road frame6720 changes41,705 pixels;6560 changes19,903. This measures filling omitted geometry, not a new measurement of3x versus2x distance. |
| Repeatability | All21 completed images and10,094,461 ordered host quads across3,731 scene fingerprints repeat. Roads off submits8,774,663 host quads. |
| Tunnel integrity | All51 completed4K tunnel images equal the earlier coverage control. Original82,601,136-byte DMA stream, VRAM, textures, palette and metadata match. The initial “expect changed” comparison remains a failed benefit expectation, not an integrity failure. |
| Cost | Roads on callback p99/max7.98/9.43ms; off5.80/6.73ms. First complete on run reports99.72% average emulation speed. This is not an uncontended GPU-latency or whole-game smoothness measurement. |
| Local checks |204Python/no skips,16native helpers,10,081C31 vectors/137yaw,32GPU checks and44local commands pass. Source identity`f93ad7f9e32fe0da96aced4ed4b439d7df036d76c6528662de285b1251d392c5`. |
| Seven default drives | All seven pass on the final8bc candidate, including actual UDP/independent memory and four force policy/polarity checks, plus Exotica's21 completed4K images. Physical force remains0; these are not new attended whole-track or wheel-feel observations. |

The PC initially exposed only3440×1440. The explicitly requested3440 retry failed
when the display changed back to3840×2160; the completed4K tests were then run at
the correct size. A manually interrupted early trial remains a failure. No failed
drive or mismatched-resolution result was silently substituted for acceptance.

Native`8bc9de136e6c24121d61bc1a991805c5c3438a2a` is built separately and pushed,
SHA256`a2fbecfb4179a4a00f4fa90795b10729f7f178b62a7c07166be1834c76877148`.
Its139-patch export reconstructs tree`dcb854a8574e3e48758acefc0c163329eef4d91d`.
Source implementation is collection`c74c152`. Stream Deck remains v0.5.0 native
SHA`87d04de4…`; personal settings and released packages are unchanged. Physical
force stayed0. No menu removal, hosted workflow or new release occurred.

Raw evidence stays local under`results/diagnostics/world-host-roads-20260909`.
The [publishable proof](../../results/proof/2026-09-09-host-roads/README.md) distinguishes
recomputed selected pixels, driving traces and telemetry from receipts for full
resources, geometry and builds.

## Next adapters

World2.5 has a compiled **offline prototype**, not an integrated emulator option.
Its separate layout passes all4,390 future descriptors at the captured4500 scene;
1,251 later allocations agree after applying the independently observed active/
pending membership rule. Independent projections agree on0/1,048/2,165 future
quads at1x/2x/3x. Raw snapshots and draft code remain local in`world25-draft`.
Next integrate its explicit layout/guards, broaden snapshots/frontiers and run
on-screen stock/2x/3x/repeat controls. Roads in this prototype remain24-only. Its revision abstraction also passes
the four earlier World2.4 road snapshot oracles without changing their outputs.

USA shares C31 math but requires a different model decoder: the inspected main
path reads a two-word header, count-minus-one vertices and interleaved polygon/
UV/texture words, unlike World's three-word header and separate material table.
These are static leads to verify against actual vertex buffers/DMA before host
drawing. Identify the correct scene insertion point relative to sky drawing.
Carry the zero-cycle observation check, then map future storage and bindings.

Off Road and Zeus still need their own codecs and admission/resource contracts.
Do not copy World addresses, call additional admissions visible success, or remove
old controls until a tested replacement provides comparable behavior across games.
