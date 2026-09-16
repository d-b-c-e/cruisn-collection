# Off-Road billboard transform foundation

A separate read-only probe now captures the original bit4 billboard path.
Across505draws and13models, independent Python and standalone C++ reproduce
all505prepared matrices and2020projected vertices, including original integer
depth slots. This closes an arithmetic gap for the four-vertex path; it does
not yet draw future billboards or qualify polygon commands/materials.

The source branch copies nine elements of the current billboard basis, preserving
the already prepared world-position translation. It deliberately ignores the
object Euler angles for this path. Basis translation slots are not copied.
The original four-vertex projection uses its own unclamped reciprocal lookup;
other billboard/local/clamped variants remain outside this helper.

The current basis is prepared at1BDD..1BF7 before the host's scene boundary at
1BF8. The capture reads it at the original1D62use, then checks the completed
matrix and projected buffer. Ten distinct basis snapshots occur; this is not a
constant identity-matrix trick. The source also has a second consumer at2779,
which is not covered by this first probe.

## Validation and retained instrumentation failures

The2524-input original replay preserves input/time/native images,723camera rows
and2892actual ADC reads. Its completed3824x2073 CRT image2520 is byte exact the
previous ordinary control. No host scenery is enabled in this capture.

The first probe omitted the mapped809800..80A000 scratch region, so it failed
when reading the projected buffer. A second bounded diagnostic identified the
actual809C00address atPC1DB7. Both failures are retained. The corrected third
capture includes that known scratch mapping and completes505/505records.
These were capture bugs, not emulator regressions.

Two focused Python tests and one native test pass. Tests cover branch selection,
ignored Euler/basis-translation fields and empty output on failed projection.
The current record verifier rejects partial/order/reciprocal aliases and compares
every matrix/XYZ word with both original and compiled independent output.
No broad suite or MAME build was necessary.

Canonical standalone files: offroad_billboard.py, verify_offroad_billboard.py,
offroad_billboard.h and analyze_offroad_billboard.cpp. The bounded Lua probe is
offroad_billboard_capture.lua; FIRST/LAST environment variables select at most121
frames. The local successful capture used fixed2500..2520before this equivalent
parameterization. Helpers are not MAME-linked/synced. Local evidence lives under
world25-roads-20260914/offroad-billboard-original-v3, original-qualified.json and
transparent.json. Existing failures remain in original and original-v2.

## Next source work

337observations have0x00800804flags and60have0x00000804; all observed hit-state
bits are clear.108observations belong to a dynamic0x04004004class and must not be
treated as static future descriptors. Bind the static records to actual ROM
section definitions and the current hit-state query. Reject damaged/custom/
alternate-material cases explicitly. Then qualify polygon emission and current
materials before live earlier drawing. The benefit remains unmeasured.

Native083ceb32407/personal87d/publicv0.5.0 unchanged. No deployment, release,
hosted CI, physical FFB or menu changes.
