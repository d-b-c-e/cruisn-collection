# Reusable indexed-pixel provenance probe

`harness/probe_vunit_pixel.py` now answers a narrow but recurring question:
at a saved V-Unit indexed pixel, was the final value auxiliary, original game
output or unowned, and does the captured current original DMA reproduce the
original-only value? It reads the same invocation's four original-mirror
planes, selects the current original DMA by the mirror's consumed-command
receipt, independently rasterizes it with captured texture RAM, and reports a
quad ordinal only when its index and material tag match the original-only
pixel. It includes source hashes and the raw replay status; a raw FAIL remains
visible even if a separate posthoc qualification exists.

Direct `--point` coordinates use bottom-up fine indexed pixels. The optional
`--screen-point` accepts top-down pixels from the **2544×1353** completed CRT
screenshot in the same run. It maps the center sample through the calibrated
viewport/curvature only after the saved indexed page and palette reproduce the
whole screenshot within a strict tolerance. For example:

```text
python harness/probe_vunit_pixel.py RUN --point 2308,891 --point 115,924 --report RESULT.json
python harness/probe_vunit_pixel.py RUN --screen-point 2100,600 --screen-point 170,575 --report RESULT.json
```

The frozen USA Golden Gate source at completed 10500 yields original DMA
ordinal 2233 for the dark right panel at `(2308,891)` (combined/original-only
index 8, tag 3), while the left red bridge sample `(115,924)` is auxiliary
index 24165/tag 5 over original sky index 7750/tag 1, reproduced by original
DMA ordinal 3 underneath. That USA raw replay remains **FAIL** from the
formerly overstrict same-frame host-scene analyzer; the separate posthoc
input/native/host/mirror qualification is in the Golden Gate review. The
probe's local `indexed-point-probe-v2.json` preserves the raw FAIL status.
The screenshot-point variant maps those two visible positions to indexed
`(2309,892)` and `(116,924)`, with the same panel/auxiliary ownership. Its
whole-image color reconstruction differs by more than one channel unit at
128 of 3,442,032 pixels; the local `screen-point-probe-v1.json` binds the
screenshot, palette, mirror and source hashes. The mapping identifies a center
indexed sample, **not** every CRT blur/dither contributor to that display pixel.

On a different game's passing Off-Road El Paso source, `(60,960)` in the
known left opening is original game output from DMA ordinal 1. The local
`left-gap-original-run/indexed-point-probe-v1.json` ties this point to its
mirror, DMA and texture hashes. These two runs exercise both auxiliary-over-
original and original-only classifications. The helper compiled and both
actual-source probes completed; no native or gameplay replay was performed.
An Off-Road screenshot point `(120,545)` maps to indexed `(58,962)`, also
original DMA ordinal 1. That screenshot's independent palette reconstruction
differs by more than one channel unit at 121 of 3,442,032 pixels.

The same screenshot path also checks the positive World 2.4 New York repair at
completed frame 6000. Visually chosen black-margin points `(95,940)` and
`(2450,935)` map to indexed `(24,472)` and `(2713,478)` after a near-exact
whole-image reconstruction (163 of 3,442,032 pixels differ by more than one
channel unit). Both control pixels are index/tag `(0,0)` with no current
original DMA coverage. In the separately qualified active non-road candidate,
they become `(17634,5)` and `(17491,5)` while its original-only plane stays
`(0,0)`. The candidate raw replay is still **FAIL** from the older policy-2
reader; `active-nonroads-fade-qualified-v1.json` passes its posthoc input/native,
mirror, completed-image and owned-stop checks. Local
`ny6000-screen-points-qualified-v1.json` hashes both sources and limits the
new claim to two screenshot-selected points, rather than relabeling the full
8,117/11,651-pixel components as new evidence.

This tool does not infer source ownership for auxiliary packets, support other
CRT screenshot sizes without calibration, prove a whole region or establish
temporal safety.
An original DMA ordinal means this current isolated raster matches the saved
original-only value at that point. Read the replay, input/native, resource,
completed-image and shutdown receipts before using such a point to justify a
renderer change. The probe's GPU work should be serialized with other shared
GPU diagnostics.
