# Fresh Germany recording: distance and weak impacts

The new attended recording is valid and repeatable. It was made with the World
edge-terrain option enabled, but that option does not extend draw distance.
The user still reports heavy scenery pop-in and weak impact feel at 80% FFB.
Neither observation is resolved by this batch. It adds clearer product controls,
reusable force/video alignment, and evidence for the next experiments.

## Recording baseline

`results/diagnostics/world-germany-extended-20260906` is the completed case titled
**Germany - Extended View**, ROM `crusnwld24`, native executable SHA256
`7eaf9ce8888190a5a6b8c30dd698fb57175c644779d4c65bf52cc083c74263fb`.
The archived patch includes the conservative World terrain helper. FFB was
explicitly attended, strength80, profile `cruisn-vunit@2`, on the MOZA R12.
The original case and older Germany recordings remain unchanged.

Full headless replay with the read-only lifecycle probe matches all **8783 input
and emulated-time rows plus 146 native screenshots**. Dense live GL controls
also pass the native comparison through frames2204 and2704. Screenshots alone
are not a route guarantee, but this is substantially stronger than merely seeing
playback start. The full case lasts about151.6 emulated seconds.

Committed evidence is in `results/proof/2026-09-06-world-distance-impacts/`.
Large traces and captures remain under `results/diagnostics/`.

## What the force evidence establishes

| Measurement | Observed result |
|---|---|
| Raw motor writes | 8317, spanning -126..126 |
| Raw versus driver-adapted byte | All identical; clamp/slew did not suppress these samples |
| Loaded profile | Crisp2, 20ms smoothing, archived/current profile hashes identical |
| Constant-force update receipts | 6621 accepted, zero rejected receipts |
| Generic rumble requests | 26 successful SDL return codes |
| Steering-axis impact enhancement | OFF during this recording |

Successful API receipts establish that the backend accepted commands. They do
not measure torque at the rim or establish that generic rumble feels useful on
this base. The trace gives no reason to solve this by raising overall strength.

Offline execution of the actual vendored algorithms at80%, using held samples
and4ms ticks, gives:

| Mode | Peak absolute output | RMS | Samples at configured maximum |
|---|---:|---:|---:|
| Current profile | 0.799796164 | 0.328623032 | 0% |
| Optional impact mixer | 0.707636356 | 0.246431708 | 0% |

These are normalized command units, not measured physical torque. The live worker
has variable wake intervals, so the offline waveform is not a bit-exact device
replay. Both offline runs find26 force-rise candidates. The mixer reserves25%
of the steering-force budget and replaces generic rumble with a short signed
pulse. Its lower peak/RMS contradict any claim that enabling it simply makes
all crashes stronger; it changes contrast and sustained steering weight.

The first candidate is45.076 emulated seconds, anchored to completed frame2612.
Dense GL inspection2520..2700 shows a hill crest/jump around the candidate,
without obvious car-to-car contact in the nearby frames. Hidden or off-camera
contact is not ruled out. No collision label or precision/recall score was
invented from this evidence. `first-force-candidate.png` shows representative
frames, cropped only to remove presentation letterboxing.

### Changes and next FFB experiment

**Settings → Force Feedback → Impact Cues** now offers independent game toggles.
All remain off by default. World writes the configured revision's setting,
normally `ffb_impact_crusnwld24`. Exact revision settings, includingOFF, override
family/global values. The runner and shell use the same resolver.

`analyze_ffb.py --frames CASE/record/frames.csv` adds candidate frame anchors.
Both `--frames` and `--labels` require the emulated-time force-source format;
host-time traces cannot silently be scored against emulated-time contacts.
This prevents a clock mismatch from producing plausible but incorrect labels.

Next: capture deliberately separated car hits, wall hits, road bumps and a clean
steering interval. Compare Impact Cues off/on on the same base at the same
strength/profile. Score candidates against observed contacts and measure command
peak, duration, contrast against pre-contact steering and clipping. Decode a
game collision/contact state before tuning a detector as if it were ground truth.
Do not infer that all26 candidates were crashes, or lower the threshold blindly.

## Actual distance investigation

The full identity replay's lifecycle probe sampled1750 draw frames during
1800..5300:525032 object visits,697 objects. The far gate is80000.
There are13601 visits from94 objects beyond80000 but within160000, with maximum
depth-minus-radius117424 in that interval. No sampled visits exceed160000.
This proves some additional scenery is already resident; it says nothing about
objects the game has not instantiated. There are also44 model transitions.

Large-object crossings include object13E40/modelCB1A8B, radius26031, crossing the
far gate at frame2027; object142A0/modelCB23C3, radius20313, crosses2131.
Object/model attribution to individual visible mountains remains open.

The existing bounded World2.4 projection probe now accepts
`CRUISN_DISTANCE_FAR` in80016..160000, multiples of16. It expands verified
projection clamps and intercepts reciprocal reads only at known projection PCs,
without replacing adjacent guest RAM. Original table entries remain untouched;
extended values use the previously measured six-decimal reciprocal approximation.
Original words restore after the specified interval. This is diagnostic Lua,
not a shipped distance implementation or a portable per-game patch.

Three runs used the same attended baseline and completedGL frames2000..2200
every2frames, scale4 with an unmaximized512x451 presentation. The mutations were
active1950..2202; all runs stopped at2204 with101 completed GL captures.

| Limit | Extended reciprocal reads | Emulation speed1952..2200 | Callback p99 |
|---|---:|---:|---:|
| Original80000 | 0 | 100.01% | 26.12ms |
| 100000 | 143145 | 100.09% | 29.87ms |
| 160000 | 182338 | 79.95% | 48.21ms |

Both candidates have zero input/time mismatches and four changed native sampled
images, which correctly makes their strict identity reports FAIL. They exited
cleanly and produced all requested completed GL images. This is expected changed
rendering evidence, not evidence of a failed launch or a passing regression.

`distance-three-way.png` shows changed terrain under the bridge and changed
mountain silhouettes. Larger limits do not yield a clean, verified elimination
of the visible mountain appearance changes. Some changes can be projection/LOD
effects rather than earlier visibility. The160k slowdown includes Lua tap cost
and extra game drawing; it is not an isolated estimate of a native implementation.
No new distance patch was deployed.

Next: capture the model/vertex submission responsible for a specific mountain's
first visible frame, then distinguish the object far gate, projection clamps,
per-face decisions, LOD selection and residency. Test those changes from a
matched state before committing to native projection support. A larger far value
alone is insufficient. Full new recording baselines remain acceptable when useful
extra drawing changes the route; preserve the parent and verify repeatability.

The launcher label is now **Widescreen Terrain: On/Off**, with an explicit note
that it does not increase draw distance. Existing `terrain_visibility_crusnwld`
settings are preserved. This resolves the misleading implication of Extended.

## Cheats stretch goal

The downloaded archive does contain arcade cheats. The extracted files are in
`C:/Users/antho/Downloads/cheat0279/cheat/`, including `crusnusa.xml`,
`crusnwld24.xml`, `crusnwld.xml`, `offroadc.xml`, `crusnexo.xml` and many revisions.
Nested console-platform files are separate. The files identify their source as
[Pugsy's MAME Cheats](https://www.mamecheat.co.uk/).

Revision matching matters: World2.4 Infinite Time targetsEBE4 and first place
EBC0; World2.5 usesEBDE andEBBA. Off Road's timer cheat deliberately writes two
separate locations. Do not translate word-addressed CPU expressions into naive
host byte offsets or combine the writes. Some Drive Anywhere/Past Finish cheats
explicitly mention freezing beyond valid level boundaries.

Our changes have not globally relocated game RAM, so modification alone does
not make these cheats incompatible. Compatibility still needs revision-specific
checks, including overlap with guarded instruction patches. The practical path
is MAME's existing XML cheat engine, exposed through a convenient submenu, with
cheat selection/files captured in recording metadata and cheats off for normal
regressions. This batch does not install, enable or redistribute the cheat files.

## Verification and deployment

65 Python tests pass, including revision precedence, per-game persistence and
clock mismatch rejection. Offscreen renders of the actual FFB and Impact Cues
pages were inspected. Full recording identity and both dense control prefixes
pass. Experimental image differences are retained, not recategorized as passes.
The native binary, shaders, toolkit and force profiles are unchanged. Python
launcher changes are active in the checkout used by Stream Deck after reopening
the launcher; the distance probe is invoked only by explicit diagnostic playback.
