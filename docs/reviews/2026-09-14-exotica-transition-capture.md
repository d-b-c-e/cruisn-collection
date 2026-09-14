# Amazon handover evidence and dense diagnostic capture

One selected waiting-scenery object now has an observed transition into the
original renderer, including its actual primitive blend values. The investigation
also exposed and fixed a pacing gap in dense diagnostic captures. No scenery
opacity, distance setting, game memory, FFB policy or deployed executable changed.

## Transition finding

Existing accepted snapshots identify an allocation-owned, 18-quad object near the
Amazon checkpoint at game elapsed time approximately 1:12. At proposal7187 its
private draw changes8,188 internal pixels. It remains in the completed waiting
cohort at7187,7188 and7189, then leaves at7190 when the original game first submits
it. Exact slot/epoch/generation, immutable object fields, model base/count and
CPU/device times join the original submission to the captured object.

All18 original polygons start with source/destination blend values8/240, matching
the waiting copy. Subsequent observed object states advance to16/240,24/232 and
onward in steps of8. The capture covers28 fading submissions. This supports
retaining the current handover for this object: forcing its waiting copy opaque
would introduce a new mismatch at original admission. It does **not** establish
that every material behaves this way, or advance the game's fade earlier.

The saved40-frame completed presentation window7180..7219 was inspected using
selected adjacent-frame crops around admission. No obvious disappearance was
seen in those inspected crops. This is one object's transition, not general
temporal acceptance or proof that pop-in is eliminated. Initial screening of the
five older snapshots found719 instance observations with later first submissions,
247 marked fading; these include zero-quad instances and repeated lifetimes, so
they are not counts of visible objects or independent validated transitions.

## Capture failure and fix

The first live window on native1d5 combined five adjacent private material/geometry
snapshots, six completed depth snapshots and presentation captures. The renderer
consumer timed out at presented7190; the final old capture row reports one dropped
message. That run remains failed. Its CPU-side model/lifetime evidence is useful
separately, but its GPU stream cannot be accepted.

Previously, explicitly paced captures signaled only writer-queue admission waits.
Large readbacks, copying and per-pixel validation could consume the normal render
wait budget without that signal. Native03e43 adds a scoped signal around private
future/waiting snapshot work and depth snapshot readback/validation. Nested writer
waits now restore the outer signal instead of clearing it. The signal has one
capture-producing thread; it is not a cross-thread reference counter.

This only applies with explicit capture pacing and literal physicalFFB0. Ordinary
rendering remains on the existing wait policy, and the independent10-second hard
limit remains. The shared writer's ordinary admission, byte/job limits, FIFO order
and default behavior are unchanged. A focused native test checks nested writer
timeouts, exception unwinding, signal restoration and existing writer behavior.

One retry on03e43 delivers all5,323 early and5,323 waiting GPU batches, all10,646
material generations, five private insertion samples and six completed depth
snapshots without a consumer timeout. Both original source/cohort traces and
original fade-submission bytes match the failed run. The eight internal before/
after color/depth buffers at7187 match the earlier accepted4K-run artifacts exactly.
The11 saved presentation images before the old stream's first reported drop also
match byte-for-byte. This does not turn the old failed stream into a passing run.

## Explicitly narrowed acceptance

The retry's original request still fails: it asked for image7220 while stopping
the replay at input7220. Only40 of41 requested images completed, through7219;
the final presentation drain timed out. The raw report remains unchanged and
failed. A separate receipt accepts **only7180..7219**, verifying all40 completed
images at3440x1440,7,220 input records,5,420 camera samples and16,260 ADC records
against the original route. The replay's independent input/native comparison
passes; no new run was needed to assess this complete interior window.

The harness now rejects explicit Zeus capture cadences that request the stop
frame or later before launching the game. It checks the last actual scheduled
capture, so an interval ending at the stop frame is allowed when its cadence
finishes earlier. Other renderers retain their existing behavior. Seven focused
Python capture tests pass. The initial command-journal combination was also
rejected before launch because that journal cannot capture private future draws;
the incompatible option was removed, not bypassed.

The monitor is3440x1440. This is not renewed4K presentation acceptance. Internal
render targets remain2736x4096; matching old internal buffers demonstrates that
this particular diagnostic could continue without switching monitors. No speed
claim is made from this dense capture or comparison to the earlier full-drive run.

## Reproduction and next work

Native commit`03e43ffc3f5c1c9672247c3f971be7e93cb73b6e`, frozen at
`build/candidates/03e43ffc3f5/vunit.exe`, SHA256
`8ac2166812d63c253f602fe101250d5c553f876f8de541b96d358efc1ce0a625`.
The191-patch export preserves the verified prior190-patch bytes and reconstructs
tree`9d743f9ed71969d53bc49189e1dfcdb842650f65`.

Local evidence under`results/diagnostics/exotica-amazon-20260909/`:

- `transition-screening.py/.json`, `transition-pixels/` and `transition-object.py`.
- `transition-7187-baseline/`: rejected command-journal request, no game run.
- `transition-7187-live/`: original consumer-timeout failure, retained unchanged.
- `transition-7187-paced/`: fixed consumer, retained failed41-image request.
- `transition-7187-window-acceptance.json`: explicitly narrowed40-frame result;
  `transition-7187-paced-object.json`: original model/material join.
- `transition-7187-visual/transition.png`: selected completed-frame crops.
- `transition-trial.py`, `transition-paced-trial.py`, plans and process logs retain
  exact historical requests, including the stop-frame mistake. Future runs must
  end capture before stopping. The initial full-reader rejection of the old
  dropped-stream capture led to comparing only its pre-drop raw images, separately
  from the accepted new window; no dropped-stream acceptance rule was relaxed.
- `transition-pacing-native-export.json`; build/test outputs under
  `build/scenery-perf-20260914/`.

Next compose the existing ground-margin repair with extended scenery, and broaden
handover checks to opaque, additive and other intrinsic transparency cases when
the proposed change needs them. An earlier host fade will require continuity with
the corresponding original object's fade; this window is a reference for that
work, not a new fade policy. No blind repeat of this accepted interior window or
full four-game matrix is needed. Final combined regressions and4K acceptance
remain required before deployment. Personal87d and publicv0.5.0 are unchanged.
