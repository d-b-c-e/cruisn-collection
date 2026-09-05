**Speed telemetry: a fresh route beyond OCR — 5 September 2026**

OCR was a reasonable fallback after the memory hunt failed. I would keep it available while pursuing a more targeted source-level investigation. Failure to find a persistent “speed address” does not mean the value cannot be extracted: the game must produce a value before drawing its digits, and the emulator can observe that computation even if the value exists only briefly in registers.

This is a proposed investigation, not a claim that a new speed address or hook has been found. No gameplay was launched for this review. See the [main assessment](E:/Source/cruisn-collection/docs/reviews/2026-09-05-assessment.md) for scope and the [recording design](E:/Source/cruisn-collection/docs/reviews/2026-09-05-replay-and-testing.md) for reproducibility.

**What the earlier work actually establishes**

The chronology records several good falsifications. Attract-mode memory candidates turned out to track other cars rather than the human player. Additional RAM banks and representations were searched without finding the expected stop/start fingerprint. A proposed digit-quad decoder failed because these V-Unit HUD digits are CPU-blitted into videoram rather than submitted as digit-sized 3D quads.

Those results rule out particular candidates and an interception point. They do not prove that player speed “persists in no memory.” Sampling cadence, player-object identity, representation, derived values and an incomplete matching hypothesis can all defeat a broad scan. The strongest next step is to trace backward from the known HUD output.

The other session finished during this review. Its final MAME revision `58203bb13f7b4a5997b4f6dceed1e36a8fd631d8` changes comments to record that World's existing OCR box was checked through three-digit speeds, while Off Road's current box is wrong and has never produced working speed telemetry. This review inspected that source delta; it did not independently repeat those drives. USA's recently fixed hundreds-digit clipping is a separate issue.

The runtime absence-counter defect remains: failed OCR reads accumulate without resetting the counter on valid reads. That can cause an occasional false zero after intermittent failures, even with the box correctly positioned. It should be addressed independently of the longer-term source hunt.

**Start at the CPU HUD blit, then work backward.**

The local V-Unit memory map routes videoram through [`videoram_w`](E:/Source/mame-src/src/mame/midway/midvunit_v.cpp:2861). That gives a concrete observation point for the CPU-written speed digits. The earlier failed DMA-quad approach should not be retried unchanged.

Proposed sequence:

1. Replay a short drive with known displayed speeds, including 0, 9→10, 99→100, acceleration and braking. Preserve native HUD frames and page identity.
2. Instrument writes only to the speed-digit region on both framebuffer pages. Capture a bounded sample of writer PCs, destination addresses and relevant CPU/register context. Aggregate recurring PCs rather than logging every pixel indefinitely.
3. Identify the glyph blit loop and its callers. Trace the glyph selection back to decimal conversion or numeric formatting. The value before formatting may be a directly useful display-speed signal, even if it is never stored at a stable address.
4. Trace that value further upstream when useful: player structure, velocity components, fixed-point conversion or scaling. Establish which object supplies it during real player control.
5. Add a narrowly versioned observation hook at the verified producer or read the verified player field. Keep OCR as an independent comparison during validation.

This is more constrained than correlating every RAM word with a guessed speed curve. It also has a useful intermediate outcome: a trustworthy numeric HUD value is an improvement over OCR even if a physical velocity representation remains unresolved.

**Distinguish displayed speed from physical speed.**

| Candidate signal | Meaning | Appropriate use |
|---|---|---|
| Numeric value passed to HUD formatting | What the player is shown, possibly rounded/scaled | Dashboard agreement and display regression checks |
| Verified player velocity magnitude | Motion in game-world units per game time | Physics/telemetry after units and axes are established |
| Signed forward velocity | Movement along the car's forward direction | Reverse/slip interpretation when that is the desired quantity |
| Wheel/engine-derived estimate | Depends on gearing, wheelspin and game conventions | Labelled estimate; not automatically vehicle speed |
| OCR result | Recognized displayed value with uncertainty | Fallback/independent cross-check |

An arcade speedometer may intentionally scale or smooth its value. A field that does not equal displayed MPH can still be a valid velocity signal, and a field that tracks MPH may still belong to a drone. Record source and semantics instead of forcing every candidate into one number.

For V-Unit, preserve the distinction between TMS320C3x floating-point, integer/fixed-point and packed values. For Exotica, investigate its own CPU/HUD/physics path rather than assuming the same representation or hook addresses.

**Validation that earns “found”**

Use multiple player-controlled drives and a held-out track. Compare candidate values with recorded HUD readings through acceleration, coasting, braking to a true stop, collisions, jumps, gear changes, reverse if available, restart and menus. Identify the player instance explicitly; test a case where nearby traffic behaves differently.

Record units, conversion, update cadence, producer PC or field offset, object identity and ROM revision. Verify whether a pause holds the last valid sample and whether menus mark it invalid instead of retaining a drone's motion. A strong correlation coefficient is supporting evidence, not proof of identity or units.

The accepted hook should produce stable values under deterministic replay and stop reporting valid player speed when no player race exists. If a numeric HUD hook is the first success, label it “display speed” and continue to keep physics-derived fields separate.

**Improve OCR while the hunt proceeds.**

Calibrate Off Road from an actual driving HUD frame and verify the box across views and overlays. Do not infer its coordinates solely from another game's layout or an upscaled photograph. Preserve example glyph crops at single-, double- and triple-digit values. Validate both World ROM revisions actually supported by the launcher.

Test temporal behavior as well as recognition: an isolated bad read, many scattered bad reads, a sustained missing HUD, a real rapid speed change and a menu transition. Reset consecutive-absence state when valid evidence returns, and avoid accepting “two matching candidates” separated by unrelated absent periods unless that behavior is explicitly intended.

Report raw candidate, recognition score, accepted value, age and validity. Avoid presenting a stale or unsupported value as a valid zero. Keep dashboard packet adaptation separate from the recognition algorithm, and use actual emulated timestamps and race-state evidence rather than a fixed 17 ms increment and unconditional race-on flag.

**Recommended endpoint**

Provide a per-game telemetry adapter with a versioned source definition: preferably a verified player field or numeric producer hook; otherwise explicitly identified OCR. Expose validity and freshness internally, then translate to SimHub/Forza-compatible output. The dashboard can remain useful throughout the transition, while the source quality becomes measurable and progressively less dependent on screen layout.
