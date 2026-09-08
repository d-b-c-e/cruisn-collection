# Off Road native distance evidence

Run `python verify_archive.py` with Python's standard library. No ROMs, wheel or
graphics libraries are required. The 190-entry ZIP is SHA256
`077b1aee432ddc754c7b7897cceef876732ba0ad48baae4ae0f27318d04638c6`.

The verifier checks every archived hash, then recomputes the four native distance
trials, their original frame inputs, camera/actual ADC comparisons and repeat
counters. It also checks the separate6000-frame/13-image3824×2073 candidate,
paired scene receipts, both rejected duplicate-row logs and all seven regression
telemetry/independent-memory results with the four applicable force policies.
All physical-force invocations are disabled.

Ordered quad hashes retain the strict failure: one original quad changes, despite
715 common quads retaining order and texture/palette memory matching. The archive
contains capture dimensions, image/resource hashes and the comparison reports;
the raw completed images and resource RAM remain local. Hash-bound GL/resource
receipts are not a ROM-free rerender or an attended quality acceptance.

Native12e9ea6a374 / executable SHA256
`9936c7160ddb708949d9e776c9197d833e868ffc921fd679153a72ab99735275`.
Collection core2669afe, menu ba3364c; all262 source hashes agree between local and
both CI platforms. The published v0.4.0 tag/ZIP and personal settings are preserved.
See [the review](../../../docs/reviews/2026-09-08-offroad-native-distance.md) for
limits, measurements and the optional menu control.
