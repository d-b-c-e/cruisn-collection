# USA3× descriptor preparation

A current-build4K check completes5012 recorded inputs. The selected driving
window3500–4900 runs at97.367% emulation speed; its sole completed screenshot
is captured afterward at5000. All750 ordered scene fingerprints match the
accepted reserved-buffer candidate. The3201 camera and9603 ADC rows match its
corresponding prefix. This is a current performance baseline, not a new speed
improvement or broad visual acceptance.

Scene preparation remains the largest added phase. A saved-scene screen compared
the unchanged code, descriptor-vector reservation, and reservation plus hashed
duplicate membership. The hash set is used only to detect duplicate IDs; final
draw order remains the explicit depth/ID sort. Future counts are checked before
storage is reserved. All existing source bounds, cycle checks, model selection,
palette access and projection arithmetic remain in place.

Three alternating80-loop rounds on four actual saved scenes produced these
median preparation reductions relative to the same unchanged baseline:

| Saved frame | Reservation only | Reservation and hash set |
| --- | ---: | ---: |
|3501|6.56%|9.27%|
|4001|2.68%|4.06%|
|4501|11.46%|18.10%|
|4901|11.95%|18.60%|

Full ordered outputs match for all three variants at1×,2× and3× in every saved
scene. The canonical reservation/hash implementation also matches those twelve
outputs and passes the three focused native USA tests. Added checks exercise
duplicate future IDs, explicit equal-depth ordering, the future-size bound and
unchanged input memory.

The first local hash prototype failed to compile because the future-section
header inherited `<set>` indirectly. That failure is retained. The canonical
future header now explicitly includes its own dependency; the host header uses
`<unordered_set>`. Successful baseline/reservation benchmark executables were
reused rather than needlessly rebuilt for the corrected screen.

Local evidence under `results/diagnostics/usa-future-render-20260909`:
`current4k-qualified.json`, `descriptor-storage-screen` (compile failure),
`descriptor-storage-screen-v2/report.json`, and
`descriptor-storage-qualified/report.json`. Native8de985146b3 contains this
isolated CPU change. Live improvement remains to be measured; no full-speed or
release-parity claim follows from the microbenchmark alone.

The matching live4K pair now passes all5012 inputs,3201 camera and9603 ADC rows,
all750 non-timing scene records and the single completed5000 image exactly.
Preparation falls2.9428→2.6877 seconds (8.67%); total host callback time
falls3.3224→3.0672 seconds. Driving speed is effectively unchanged:
97.367→97.433% over3500–4900. This is a useful CPU reduction, not a demonstrated
end-to-end performance fix. No additional timing replay is justified merely to
obtain a better result.

The222-patch export reconstructs `acd5725bc96601388b41315262f1e456c84c67c6`.
Frozen candidate SHA256:
`34fef7a045e442ad3afba28426e89a859c3e9623d6b1e1cb8adc4b49b8322644`.
Evidence: `descriptor-storage-live-qualified.json` and
`descriptor-storage-native-export.json`. Personal87d/publicv0.5.0 are unchanged.

The next saved-work screen identifies substantial entirely offscreen output in
the expensive views:6226/9269 emitted quads at3501 and18446/19194 at4001 belong
to objects wholly outside a deliberately generous horizontal interval[-128,640].
The renderer's maximum margin is86, giving a visible interval[-86,598]. Later
4501/4901 samples have no such whole-object candidates. This is an opportunity
to investigate conservative horizontal rejection; it is not yet an implemented
or renderer-qualified optimization. Full projected vertices, original order,
validation behavior and actual output must be checked before promotion.
