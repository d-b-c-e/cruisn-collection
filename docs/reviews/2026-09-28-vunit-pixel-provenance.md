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

Points use bottom-up fine indexed coordinates, **not** CRT screenshot pixels.
For example:

```text
python harness/probe_vunit_pixel.py RUN --point 2308,891 --point 115,924 --report RESULT.json
```

The frozen USA Golden Gate source at completed 10500 yields original DMA
ordinal 2233 for the dark right panel at `(2308,891)` (combined/original-only
index 8, tag 3), while the left red bridge sample `(115,924)` is auxiliary
index 24165/tag 5 over original sky index 7750/tag 1, reproduced by original
DMA ordinal 3 underneath. That USA raw replay remains **FAIL** from the
formerly overstrict same-frame host-scene analyzer; the separate posthoc
input/native/host/mirror qualification is in the Golden Gate review. The
probe's local `indexed-point-probe-v2.json` preserves the raw FAIL status.

On a different game's passing Off-Road El Paso source, `(60,960)` in the
known left opening is original game output from DMA ordinal 1. The local
`left-gap-original-run/indexed-point-probe-v1.json` ties this point to its
mirror, DMA and texture hashes. These two runs exercise both auxiliary-over-
original and original-only classifications. The helper compiled and both
actual-source probes completed; no native or gameplay replay was performed.

This tool does not infer source ownership for auxiliary packets, map completed
CRT pixels automatically, prove a whole region or establish temporal safety.
An original DMA ordinal means this current isolated raster matches the saved
original-only value at that point. Read the replay, input/native, resource,
completed-image and shutdown receipts before using such a point to justify a
renderer change. The probe's GPU work should be serialized with other shared
GPU diagnostics.
