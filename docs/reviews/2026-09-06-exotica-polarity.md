# Exotica cabinet settings and the older Fanatec oscillation report

2026-09-06. Analysis of the tester's historical report, current source and
Endprodukt's public repositories. No FFB behavior or saved rig settings changed.
Local emulator reference: `377ddc06db1`; collection baseline: `0183bf3`.

## What the tester was referring to

The matching project is [Endprodukt/FFBPluginRacerMAME](https://github.com/Endprodukt/FFBPluginRacerMAME),
his version of FFB Arcade Plugin. Its companion configuration application is
[FFBPluginGUIMAMERacer](https://github.com/Endprodukt/FFBPluginGUIMAMERacer).
The plugin README explicitly prescribes three Exotica settings:
**Wheel Invert On, Game Type Dedicated, Cabinet Sit Down**. The third-party
report omitted Game Type. Exotica is marked as requiring his custom MAME fork.

The corresponding emulator work is in
[Endprodukt/mame, MameRacer289.2](https://github.com/Endprodukt/mame/tree/MameRacer289.2).
Its Exotica motor-output addition exposes the low byte written to LED-board
offset zero as `wheel_motor`, the same hardware register our local driver uses.
See [commit 67e1d23](https://github.com/Endprodukt/mame/commit/67e1d2311f150e6b496001ab5366d6a603b5daca).
Our direct SDL integration already receives that register; changing plugins is
not necessary to obtain the signal.

The reference to fixes planned for MAME 0.290 is plausible, but is not a precise
version guarantee. The upstream [speed/depth-clear fix](https://github.com/mamedev/mame/pull/16046)
is merged. The [motor-output PR](https://github.com/mamedev/mame/pull/16055) and
[DIP-label PR](https://github.com/mamedev/mame/pull/16057) were still open when
checked. The exact binary used by the tester has not been identified or compared.
No external plugin or executable was installed during this review.

## The misleading switch name matters

In [PR16057](https://github.com/mamedev/mame/pull/16057), Endprodukt says the
old Wheel Invert label describes **force-feedback and shifter polarity**, not
steering direction. The shifter distinction is normally open versus normally
closed contacts. This offers a credible explanation for why the switch also
changes transmission selection. The PR proposes a label correction; it does not
implement a new force algorithm, and its open status is recorded here.

His plugin also contains a specific [Exotica force-direction correction](https://github.com/Endprodukt/FFBPluginRacerMAME/commit/c3f2ea699d8cd097a0fb1b414ba9486fac863eb6):
after gain and clamping it negates the force for the recommended DIP setup.
That independently supports investigating force polarity. It does not establish
equivalence between the plugin's direction constants and SDL's steering axis.

Our September 4 engineering log correctly measured that toggling the DIP reversed
the motor response to a parked wheel. It then called this proof of reversed
**driving input** and introduced `MIDZ_WHEEL_INVERT`, which changes ANALOG3 to
`255 - value`. Motor-force direction alone cannot prove vehicle steering direction.
The observed transmission-menu behavior remains useful evidence; the explanation
and input compensation need reassessment with actual left/right driving.

Current source keeps three different operations coupled in the launch path:

| Operation | Current behavior |
|---|---|
| Exotica DIP 0x0800 | Launcher forces On unless `exotica_manual=0`. |
| Driver input mirror | The same launcher decision enables `MIDZ_WHEEL_INVERT=1`. |
| Physical force direction | `native/motor_signal.h` maps positive game force to negative SDL level; global `ffb_invert` can reverse it. |

Inverting the input can make a motor-versus-input trace look restoring while also
reversing the car's response. Conversely, copying the plugin's force negation
without removing or testing the input mirror could reverse a working loop twice.
Do not fix this by changing the global direction for every game.

## What Sit Down means and what the launcher does

Sit Down selects Exotica's emulated cabinet variant; it is not the motion-seat
option or a generic FFB damping setting. These are distinct DIP fields in
`midzeus.cpp`: Game Type 0x0100, Seat Motion 0x0200, Cabinet 0x0400,
Wheel Invert 0x0800. Dedicated and Seat Motion Off are upstream defaults.
Cabinet defaults to Stand Up, and Wheel Invert defaults Off in our base.

The launcher selects Sit Down through `apply_shifter_config`, but only when the
active transmission mode has all four H-pattern gears or both paddles bound.
`apply_exotica_dips` sets Wheel Invert independently. Tests invoking those actual
functions against temporary config files produced:

| Configuration | Cabinet | Wheel Invert | Game Type |
|---|---|---|---|
| Fresh keyboard or unbound sequential setup | Stand Up | On | Dedicated |
| Complete paddles or H-pattern bindings | Sit Down | On | Dedicated |
| Complete bindings with an existing Kit setting | Sit Down | On | Kit |
| Fresh config with `exotica_manual=0` | Stand Up | Off | Dedicated |

The driver mirror follows Wheel Invert in these cases. Evidence:
[launcher-dips.json](../../results/proof/2026-09-06-fanatec-review/launcher-dips.json).
No emulator or wheel was launched by this check. The current local rig has
Sit Down and Wheel Invert On; no Game Type override means Dedicated. That cannot
be assumed for a tester's older install or imported config.

## Why Tab and direct execution differ

The custom GL renderer presents an owned popup above MAME. Source inspection of
both overlays finds custom Esc menus and minimize handling, but no mechanism to
surface MAME's native configuration menu. No explicit Tab unbinding was found in
the current launcher/generated controller mapping. The likely failure is a MAME
menu hidden behind the overlay. This is a source-based explanation, not a fresh
physical-Tab reproduction of the tester's older build.

Exotica's existing `MIDZ_GL=0` fallback uses MAME's normal display, which provides
a route for an attended configuration session. A proper launcher service mode
should expose that route and explain which settings are reapplied on launch.
Simply hiding the Zeus overlay during gameplay is insufficient because the live
path normally skips native CPU polygons. Native drawing must resume too.

Starting `vunit.exe` directly does not enable `MIDV_FFB=1` or reproduce the
launcher's device/profile/environment selection. FFB is implemented inside the
emulator; the Python launcher configures it. His observation therefore makes
sense and is not evidence that FFB requires a separate Python process.

## Recommendations and acceptance evidence

1. **Test Exotica's input and force polarity independently.** With physical FFB
   disabled, run an eight-case matrix: Stand Up/Sit Down × DIP Off/On × driver
   input mirror Off/On, holding Dedicated and Seat Motion Off fixed. Start each
   case from identical retained NVRAM. Record an actual left/right race segment,
   analog reads, raw motor byte, conditioned level and shifter/menu state.
   Check vehicle direction from gameplay or a validated heading signal, never
   infer it from spring force. Keep the current setup as a retained control.
2. **Make cabinet setup explicit and observable.** After that matrix, define a
   consistent Exotica cabinet profile independent of whether paddles were bound.
   Record effective DIP values alongside the launch environment. Imported Kit
   settings need a deliberate migration/override policy, not silent assumptions.
3. **Separate game polarity from wheel polarity.** A game-specific correction
   belongs in its adapter. Device direction belongs in a per-device profile.
   Retest USA, World and Off Road whenever changing the shared motor adapter.
4. **Establish a low-gain attended Fanatec baseline.** Confirm restoring force
   before tuning damping or impacts. Compare the same recorded drive and driver
   settings. Our launcher currently requests Exotica gain 800%; Endprodukt's
   plugin defaults to 400%. Our gain is clamped before final strength/shaping, so
   turning down global strength cannot recover information already clipped.
   Log saturation fraction, sign reversals and decay, rather than treating one
   rig's global strength as portable tuning. Gain difference alone does not prove
   the historical oscillation cause.
5. **Expose a maintenance launch and test stop semantics.** Preserve wheel and
   DIP configuration when using MAME's menu. Add an Exotica driver-stage vector
   for raw 0x80: our motor adapter treats -128 as stop, but Exotica scales/clamps
   before that adapter and can turn it into -127. Endprodukt normalizes the stop
   code before gain. This source-level inconsistency needs correction/testing;
   no occurrence in the tester's old trace has been established. Compare the
   [pinned Exotica handler](https://github.com/Endprodukt/FFBPluginRacerMAME/blob/7e95f65cab18109cda6b6d0da8ab4c210f3c9c12/Game%20Files/MAMESupermodel.cpp#L1383-L1410).

Wrong loop polarity can cause a wheel to drive away from center; excessive gain
and delay can also cause oscillation. The anecdote makes polarity/cabinet setup
a strong lead, not a diagnosis of this Fanatec or evidence of a mechanical fault.
No physical Fanatec validation, FFB sign change, gain change or DIP migration is
claimed by this review.

Source snapshot: plugin master `7e95f65cab18109cda6b6d0da8ab4c210f3c9c12`,
read-only API/raw-source evidence under `results/diagnostics/endprodukt-review`.
