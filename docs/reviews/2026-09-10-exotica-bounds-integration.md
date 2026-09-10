# Exotica scene bounds integration

The private Exotica scene assembler now caches conservative bounds with its
owned model data. `--exotica-host-bounds on|off` is explicit and recorded;
the default remains off. This still observes generated geometry without
drawing it into the game.

An enabled capture uses XCS2 with an explicit bounds field. Off captures retain
the original XCS1 byte layout. Old recordings do not gain a bounds setting.
Missing native acknowledgments, mismatched modes or incomplete snapshots fail
verification. Unknown model commands, invalid texture formats and unsafe depth
values still fail rather than being hidden by offscreen rejection.

Native `86deac56192a7692110d44d264b5d30b02c5f208` is built separately and
pushed. Frozen `build/candidates/86deac56192/vunit.exe` has SHA256
`f25ecd8ea7cd9d2a0c13becb94c96d59aebffc8f1aabe92cd6431c2cfe18e471`.
All162 exported patches reconstruct tree
`55f86667417c7895dd98aff50926c54a050238dd`.
The final local suite passes307 Python tests without skips,36 native helpers
and103 commands at454-file identity
`89674403e4130d759d235e6c259dbe8cf8f334a4325665afc7ec5fe56d905585`.

## Geometry and initial live results

All three earlier standalone snapshots pass with bounds off and on at1/2/3x,
each with a3x repeat and original/completed fade. The48 cases compare every
remaining native instance and quad against full independent Python projection;
no visible polygon is rejected. Off preserves the original unfiltered result.

Five6000-input Amazon replays now pass: unfiltered3x, filtered1/2/3x and a
filtered3x repeat. Each preserves4,191 camera/12,573 actual ADC observations,
all17 completed4K images, ten original resource files, exact original device
context and the independently journaled game-scene boundary. All2,457 scene
identities and clocks match; filtered3x retains the viewport polygon count
in every scene. Its4,848,660 ordered generated-quad fingerprints repeat.
The5072 snapshot retains all401 visible quad records byte-for-byte.

The unfiltered observer generates20,343,986 quads across those scenes. Filtering
reduces that to4,848,660, rejecting1,720,489 offscreen object instances. Average
source assembly, projection and diagnostic hashing falls6.33 to3.53ms; p99 falls
13.04 to6.13ms. These are observation costs, not extra-GPU rendering timings.
The one raw snapshot separately pauses292.9ms in the control and651.2ms in the
filtered run. Snapshot disk I/O must not be part of normal gameplay.

## New third-band test windows

The broader Amazon comparison finds578 scenes where3x puts additional polygons
inside the viewport compared with2x. Earlier sparse snapshots did not show this.
The candidate windows are native3501–3534,5112–5137 and5463–5990; frame5978 has
5,142 additional viewport polygons. This is a geometric intersection count,
not demonstrated final pixel benefit or relief from pop-in. Capture5978 for
material, depth and foreground-composition testing next.

All three Hong Kong runs now pass:5000 unfiltered/filtered and5990 filtered.
Each preserves the original route, resources and independently checked scene;
the5000 pair has21 completed4K images each and5990 has17. All2,457 viewport
counts and clocks match, and2,776,927 filtered ordered-quad fingerprints repeat
between the two windows. Average diagnostic source/assembly/hash cost falls
10.65 to5.12ms and p99 falls20.06 to7.43ms at5000.

The new5978 Amazon pair also passes original route/resources,17 paired4K images
and independent scene/context/geometry. Its unfiltered control uses the prior
accepted f49 binary; the filtered run uses86deac. All7,941 visible quad records
are retained exactly. Eight additional offline variants compare native/Python
at1/2/3/repeat with original/completed fade, bringing the total to56 variants.

A local1368x800 composition uses separate current host/original WaveRAM textures,
private D32F depth and completed fade. It draws the extra layer after the42
initial sky quads, then the2,664 remaining original quads. The original depth
and both GPU WaveRAM textures remain unchanged; control and2x repeat exactly.
3x changes1,110 pixels beyond2x, mostly a small pale ground area through the
left-side trees. This is a modest visible difference: most extra polygons are
occluded. It excludes CRT and the live sky-repeat feature and is not native4K,
general occlusion, handover, correct-material or pop-in acceptance.

The complete seven-default suite now passes on86deac/SHAf25ecd8e, including
actual UDP/memory telemetry, four software force-policy checks, full Germany
and Exotica's21 completed4K images. Automated physical force remainszero.
The [public proof](../../results/proof/2026-09-10-exotica-bounds-integration/README.md)
checks84 evidence hashes, recomputes sanitized scene clock/counter/timing
comparisons and compares ordered-geometry fingerprints. Raw geometry,
resources, driving routes and GPU pixels remain hash-bound local receipts.

## Material follow-up

The original palette rows for655 models/7,569 quads match RGB555 conversion from
the corresponding live scene WaveRAM snapshots. Between Hong Kong5000 and5990,
the full16MB WaveRAM differs in only1,910 bytes across four4KB pages; the
captured future-instance palette spans are unchanged. This does not establish
continuous residency or upload ordering.

A local owned-page prototype reproduces all16MB after delayed ordered
consumption across five snapshots, including repeated and switched tracks.
It begins with a full image, then copies only changed pages. This avoids relying
on an unproven UV-footprint estimate. Promote with strict generation, ordering,
size and ownership checks, then connect separate host textures, palettes and
D32F depth. Original resources must remain untouched.

The observer's first supported model remains an observation point, not a
general GPU insertion guarantee. Earlier unsupported foreground, scene handover
and earlier-source eligibility still need explicit treatment. Future-only
geometry does not fix the known5072 black-ground region.

Raw evidence and local drafts remain under
`results/diagnostics/exotica-amazon-20260909`. Personal Stream Deck remains
v0.5.0/SHA87d04de4. No deployment, release, hosted workflow, menu removal,
World force tuning or physical-force test occurred.
