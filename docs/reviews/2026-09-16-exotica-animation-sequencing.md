# Exotica animated scenery: sequencing investigation

The distant-source decoder already enumerates the complete authored track.
Some remaining exclusions are animated model descriptors and custom handlers,
rather than geometry beyond a short section lookahead. They must not be silently
reclassified as static ordinary scenery.

## Saved-source census

In the Mars5200 snapshot, the60sections contain3824sources:3561ordinary and263
excluded,251of those still future.125excluded sources have a high-byte animation
tag. The remaining138use classA/F;135match the game's handler table and three
unmatchedF1E descriptors are already behind the loader frontier. There is no
useful future no-op handler omission in this sample.

Amazon5644 contains47sections and4286sources:4200ordinary and86excluded,
51stillfuture.21sources have animation tags;65use matched classF handlers.
The commonFB1..FB8/FBA handlers schedule coroutines and replace models. A
static-template interpretation would discard real behavior.

The high-byte model path is more bounded. E88C allocates an animation node,
associates it with an object, selects a per-track sequence, and optionally chooses
a random cursor offset. E8CB subsequently decrements the countdown. At zero it
resets the period, reads the next model descriptor, wraps on a negative sentinel,
and writes the object's current model pointer. This is separate from draw distance.

Mars uses11sequence tags with periods1..5 and lengths5..15; three have nonzero
random-offset extents. Amazon uses tags15/16, with periods1/3 and lengths40/7.
The observed tables encode length in both the header and negative terminator.
The new standalone C++/Python helpers reject tables outside that observed shape.

## Qualification scope

The helpers do not allocate guest objects, call the RNG, select an initial phase,
establish allocation generations, schedule updates, upload materials or draw.
They are not linked into MAME. A read-only Lua probe captures original countdown,
cursor and model writes for independent comparison; no new live rendering policy
is enabled by this work.

The first probe failed with overlapping updates. A bounded raw-tap trace in the
second run showed program-space instruction fetches interleaved with operand
reads. At E8CC the fetch of the SUBI instruction was being mistaken for another
node read. The corrected probe excludes that exact instruction-fetch address
while retaining the node/owner assertions. Both failed runs remain local evidence.

The corrected7220-input original replay passes. The41-frame observation captures
246updates across six node/owner/table tuples, with78model changes and six wraps.
Every countdown, cursor and model result matches both the independent Python
sequencer and compiled C++ helper. Three focused Python tests and the standalone
native boundary test pass. `animation-qualified/actual-updates.json` retains the
event and executable hashes. This proves individual steps, not a lifecycle join
or the initial randomized phase; no game rerun was needed for the checker.

Next compare animated source initialization against already saved original object
fields, then establish phase and allocation ownership before any live admission.
The personal installation, public release and frozen MAME candidate are unchanged.

## Initial fields from existing allocation captures

The standalone `exotica_animation_source.h` now reproduces28initial render fields
for35captured allocations covering tags7..12 at frames3485,5020 and5970. The
independent Python result matches the original fields, and the compiled helper
matches all32reconstructed words. The actual animation-node pointer is supplied
as an input and is explicitly excluded from the independent allocation claim.
The result remains `supported=false` for future-source admission.

ClassA/F callbacks and classB/C word24 overrides remain rejected. The separate
Amazon allocation capture contains only one tagged source, which also invokes a
custom handler; its initial-field report correctly fails for empty supported
coverage. It is retained, not counted as a passing Amazon initialization test.
An earlier local prototype also stopped on that unsupported combination. Four
focused Python tests and the expanded native boundary test pass; the combined
analyzer still reproduces all246previously captured animation updates.

Six later Amazon objects in the7187 snapshot match the ordinary placement and
binding hypothesis, but their current model, rendering coefficients and linkage
have already changed. That saved-state screen is not an initial-allocation proof.
The first screen named a run without the requested snapshot; the corrected screen
uses the existing `composition-live-full` snapshot and its own lifetime journal.

Evidence: `animation-qualified/initial-fields5990.json` (35objects),
`initial-fields5072.json` (unsupported-only failure), `updates-combined-analyzer.json`,
`animation-initialization-fields.json`, and `animation-allocations-prototype.json`.
Next assess the excluded animated sources' potential visible coverage from saved
scenes before investing in live phase, residency and ownership integration.

The saved-geometry screen finds one of125future tagged Mars sources within3x
range (149viewport polygons) and ten of20Amazon sources (27viewport polygons).
Both initial-model hypotheses decode without geometry errors. Their new palette
rows come from the same captured WaveRAM, which exactly matches the GPU image.
The unmodified full insertion first reproduces saved color/depth exactly.
Against the completed depth buffer, neither group produces any colored pixels.
`animation-completed-depth.json` records this negative result. It does not test
every animation phase, but supplies no positive visual reason to prioritize live
integration in these samples. No game run or MAME build was needed.

Keep the standalone groundwork and return to the independent machine-reset
release gap; seek useful animated visibility before further runtime integration.

Local evidence is under `results/diagnostics/exotica-open-course-20260916`:
`custom-descriptor-census.json`, `animation-table-screen-v2.json`,
`amazon-animation-live-snapshots.json`, `amazon-animation-updates`,
`amazon-animation-trace-v2`, and `amazon-animation-updates-v3`.
The initial live-snapshot draft incorrectly included the linked-list anchor as
a node; it is not used as animation evidence. The corrected walk starts at its
next pointer. Another initial table screen wrongly reused a Mars table for an
Amazon tag; per-track table identity is retained in the corrected screen.
