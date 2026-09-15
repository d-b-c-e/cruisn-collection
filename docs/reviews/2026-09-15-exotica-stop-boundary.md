# Exotica: stopping extra scenery cleanly

The existing bounded scene and endpoint controls can stop extra Exotica work
without disturbing the recorded game. This supplies a useful prerequisite for
failure recovery; it is not an implemented fault fallback or release acceptance.

## Bounded Amazon result

On frozen native `e1f9ce0f17f`, retain the earlier combined2x configuration but
end new host scene and endpoint selection at5220. Continue the same5300 recorded
inputs, lifetime observation and ordinary rendering. Capture the prior internal
targets and a later completed5280 target. Physical FFB stays0; display3440x1440.

The ordinary input/native-image comparison passes. All3500 camera,10500 ADC and
50690 lifetime-event rows equal the retained complete-window control. The
3363 host/active scenes and their10089 material stages equal the control prefix
after excluding named timing fields. Waiting, handover, composition, endpoint
models and65576 GPU endpoint rows also equal their respective prefixes.

All requested scene/fence/handover/endpoint completion checks pass, with no
pending ownership left at exit. Last host submission frame is5220. The twelve
original/private color/depth files at5073,5081,5220 are byte-identical to the
retained control. This is a stop/drain check, not a more distant visibility test;
repeating at3x is not needed merely to restate the same boundary contract.

At completed5280 the entire2736x4096 private color image exactly equals the
original color image, including both physical pages. Ten depth samples differ
from the simple D24-to-wide correspondence; full depth equality is **not** claimed.
All ten have original code16776961 and private value0.9999848008155823. The
correspondence divides ordinary polygon depths by2^26, whereas the wide shader
has a separate2^24 path for explicit raw-depth writes. The observed numbers fit
that separate path, but no command journal was captured at5280 to prove their
writers. They are not small rounding errors. Do not overwrite the depth buffer
or change the shader on this evidence.

## Recovery design implications

The normal original color target stays independently maintained. A production
fallback should present that target explicitly, rather than assume that a
private target with different depth semantics is interchangeable forever.

The CPU source observer is not a single isolated draw call. By the time future
geometry is assembled, the current scene may already own a waiting proposal,
active capture and original-command endpoint tickets. Returning early on every
error would strand this state and break the existing fence checks.

A narrow next implementation can recover a **future-assembly-only** rejection:

1. Preserve strict revision, source ownership, read-span and original-model
   checks. Treat transport, resources, active/waiting ownership and endpoint
   failures as fatal; their recovery has not been established.
2. Record the failed scene explicitly. Discard its partially assembled future
   result, prevent new source/endpoint admissions, and latch later scenes off.
3. Finish already validated current waiting/active work and drain previously
   committed original endpoint tickets. Never erase queued ticket ownership or
   retroactively alter guest state.
4. At the proved scene-ready fence, enqueue an ordered retirement message after
   the current private work. The GPU must reject it inside an endpoint pair,
   acknowledge it once, select the original presentation target, and reject any
   subsequent auxiliary submissions.
5. Exercise that path with one deliberate fault in the retained Amazon segment.
   Keep the original route and prior resources exact; require CPU and GPU
   retirement receipts, continued original presentation, and a degraded parity
   result. Missing late diagnostic snapshots must be accounted for explicitly,
   not silently ignored.

This is deliberately narrower than turning every fatal guard into fallback.
Continuous production use also needs separation of bounded diagnostic journals
from runtime state: endpoint commit IDs, admission journals and observation
windows currently have deliberate finite diagnostic limits. A recovery toggle
alone does not remove those limits or make the adapters release-ready.

Local evidence under `results/diagnostics/exotica-amazon-20260909/`:
`scene-scope-stop/`, `scene-scope-stop-plan.json`,
`scene-scope-stop-qualified.json`, `scene-scope-stop-depth.json`, and their saved
runner/checker scripts. No additional native changes, build, deployment, release,
physical force or broad default suite were needed for this check.
