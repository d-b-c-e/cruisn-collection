# Conservative horizontal rejection for USA host scenery

The expensive saved USA views contain thousands of host polygons belonging to
models wholly outside the horizontal viewport. The standard renderer's maximum
margin is86 pixels, giving visible source x coordinates[-86,598]. The new host
check retains a deliberately larger interval[-128,640]. It only rejects a model
if **every projected vertex** lies strictly beyond the same side of that interval.
It never uses only the center, an assumed model radius or vertical screen bounds.

All original projection/range, source/model and palette-address validation runs
first. Rejected models retain their object identity, depth order and decoded
counter, but need no polygon/backface/material packing. The check returns early
as soon as the model could intersect the retained interval. No guest distance,
physics, original DMA or camera input is changed.

Four saved scenes at1×,2× and3× preserve the exact ordered retained quad bytes.
Every removed quad independently lies outside the generous horizontal interval.
At3×,3501 removes6226 of9269 quads and4001 removes18446 of19194. The later4501
and4901 scenes retain every quad. The initial full-scan prototype reduces median
preparation by15.0% and30.0% in the two expensive scenes, but adds2.3%/3.3% in the
unculled scenes. The canonical check exits early for potentially visible objects;
no additional timing claim has yet been made for that refinement.

The actual removed3× payloads were sent through the shared V-Unit vertex and
material shader at maximum86-pixel margins,401-pixel height, and scales1 and4.
Every generated triangle remains outside the viewport. All four real OpenGL
checks produce zero index pixels and zero coverage pixels; an onscreen positive
control produces7056 covered pixels. This uses a synthetic texture atlas and
proves no-fragment coverage for these payloads, not a live stream-order comparison.

Three focused native checks pass, including strict boundaries, straddling models,
empty input, duplicate rejection and ordering. Twelve canonical saved-scene
outputs exactly match the independently checked retained subsets. The first
test compilation used an unqualified namespace; its failure is retained and the
corrected qualification is separate. No emulator replay was used to fix that test.

Nativeebe10e87c33 contains the isolated optimization. Live 4K image and performance
acceptance remains pending. Local evidence under the USA diagnostics directory:
`horizontal-cull-prototype`, `horizontal-cull-gpu`, `horizontal-cull-qualified`
(test compile failure), and `horizontal-cull-qualified-v2`.

The matching live pair now passes5012 inputs,3201 camera and9603 ADC samples,
and all seven completed4K-monitor images exactly. All750 source/selection records
remain equal apart from emitted quad count and hash. Host quads fall from6445085
to1637123; preparation time falls2.6815→2.1742 seconds, packing0.2146→0.0524 and
submission0.1707→0.0377. Total callback time falls3.0678→2.2654 seconds.

Six predefined timing windows are separated from screenshot frames by50 frames.
Their combined speed improves98.18→99.68%. The slowest window3800–3950 improves
90.96→97.99%; the other five candidate windows are approximately100%. This is
a measured end-to-end benefit, but the remaining busy-scene gap is not hidden.
It is not an uninstrumented release soak, a per-frame geometry proof across the
whole drive, or acceptance of all tracks. No further timing repetition is needed
to seek a more favorable result.

The223-patch export reconstructs `1eee62d5a610c40f42411f55d714830936d1232a`.
Frozen SHA256:
`6f65d28f6936c85f20d32a6cf2d251603f58ba38df7ad4c5d2c1bf8d9d3bafc2`.
Evidence: `horizontal-cull-live-qualified.json` and
`horizontal-cull-native-export.json`. Personal87d/publicv0.5.0 remain unchanged.
The same conservative idea can be assessed against saved World/Off-Road scenes
before introducing another game-specific implementation or another live trial.
