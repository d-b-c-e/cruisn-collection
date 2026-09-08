# Distance capability baseline — 2026-09-08

This is a measured starting point for extending distance across the four games,
not a new rendering fix. The default renderer, released package and personal
settings are unchanged. Native build is `44c3494d6af`, SHA256
`eb2db42a90288bf37ac0dcce9b9ce2106c136fad198c52320ee2b3af3c435a97`.

## What the driving probes establish

`lua/distance_capability.lua` checks each revision's actual instructions before
installing read-only taps. It observes the object far test and that culler's
reciprocal read from frames 2500–4300. The taps return no replacement data, have a
bounded lifetime, buffer their CSV and propagate exceptions to the replay frame
callback. No guest instructions or RAM are changed. CPU float registers are
decoded through MAME's exported IEEE representation; backing RAM uses C31 format.

| Game / revision | Far limit (game units) | Far rejects / tests | Reciprocal at its upper clamp / reads | Consequence for the next experiment |
|---|---:|---:|---:|---|
| USA 4.5 | 80,000 | 903 / 236,969 | 5 / 227,795 | Only three rejected visits lie within 3×. Trace the earlier admission window before expecting gains from the far limit. |
| World 2.4 | 80,000 | 41,519 / 182,144 | 3,142 / 129,482 | All rejected visits are within 2× in this sample. Existing far + virtual reciprocal architecture addresses a real gate. |
| World 2.5 | 80,000 | 44,807 / 223,727 | 3,572 / 166,048 | Same kind of bottleneck, with separately identified table and pending-list addresses. Suitable for a guarded port of the 2.4 trial. |
| Off Road 1.63 | 47,296 (float) | 1,371 / 78,907 | 0 / 75,992 | 1,173 rejects are within 1.25×; try a bounded float-limit experiment, keeping its distinct projection path intact. |
| Exotica 2.4 | 204,800 | 0 / 339,018 | 85,388 / 339,018 | Raising this far limit cannot admit more objects in this sample. Investigate earlier activation and the CPU visibility test before changing Zeus projection. |

These are repeated object visits, not distinct mountains, trees or visible pixels.
The visits exclude objects that the game has not activated or loaded. USA's other
900 rejected visits concern one object at approximately `INT_MAX` depth; Off Road's
other 198 are millions of units away. Neither should be counted as evidence that
a normal 2×/3× extension will reveal scenery. Exotica compares **depth + radius**;
the other families use **depth − radius**, and Off Road's rejection is inclusive.
The analyzer preserves those distinctions.

## Capability and uncertainty matrix

| Layer | USA | World 2.4 / 2.5 | Off Road | Exotica |
|---|---|---|---|---|
| Object far test | Verified word `55`, consumer `CB` | Verified word `40`, consumer `A0` | Verified DP=1 word `1B724`, float consumer `1C35` | Verified word `67DA`, consumer `6887`; no sample rejects |
| Reciprocal projection | Base `B2B3`, index clamp 4,999; full vertex consumers still need enumeration | Bases `B66F` / `B665`, index clamp 4,999; current 2.4 host extension avoids adjacent RAM | ROM base `CB0FC8`, signed unit-depth index, upper index 63,679; different algorithm | Base `EAAB`, clamp 4,999 in CPU sphere culler; Zeus performs its own downstream drawing |
| Activation / residency | Static trace identifies 75,000 admission (`727D`) and 80,000 removal (`727E`); runtime intervention not yet validated | Section lookahead 11 at `D58C` / `D586`; separate pending code at `7B50` / `7B42` | Object lists and LOD path identified; streaming window unverified | Active objects reach beyond 80,000; pending/loader limit still unverified |
| LOD | Existing 8,000/15,000 thresholds; detail experiment is separate | Existing 10,000/15,000 thresholds | Flag-dependent model selection around `1C64..1C97`; not the World LOD path | Separate model/packet path; not yet mapped sufficiently |
| Texture residency / draw budget | Not certified beyond current window | Extra World drawing can change later simulation; New York 3×/+12 crash remains unresolved | Not certified beyond current window | Not certified beyond current window |

All addresses above are hexadecimal **word addresses**, except explicitly decimal
limits. They are evidence for the named revisions only. The first 5,000 reciprocal
words are identical across USA, both World revisions and Exotica in the retained
program captures: SHA256
`0dcebbd3ebfc924c96da5c12da3773b26d04fc6c6eba727fc0a285383b3e551e`.
This supports sharing the measured far-tail generator, but does **not** mean
sharing instruction addresses or treating the Exotica culler as a V-Unit renderer.
Off Road's table is in ROM and does not share this layout.

## Controls and limitations

- USA, World 2.4, World 2.5 and Off Road prefix replays pass all 4,305 input frames
  and their native reference images with the probe installed.
- Exotica's first headless run completes with identical inputs but fails 48 native
  image comparisons, starting before the probe interval. As already documented,
  its headless CPU rasterizer is not the live GL oracle. That FAIL is retained.
- A separate full Exotica live replay passes 6,000 input frames and all 21 completed
  4K GL comparisons. Its distance CSV is byte-identical to the headless trace.
- 131 Python tests pass, including malformed/partial trace rejection and distinct
  Exotica/Off Road comparison boundaries. These diagnostics do not establish host
  performance under an extended-distance candidate or unattended handling quality.
- All runs have physical force disabled. World force tuning remains deferred.

Evidence is under `results/diagnostics/distance-capability-20260908`. Derived traces,
reports, invocations, scripts and a ROM-free verifier are archived under
`results/proof/2026-09-08-distance-capabilities`. Guest program dumps/disassembly,
ROMs and screenshots are not redistributed in this archive. It recomputes the
distance conclusions; completed-image receipts retain their original run binding.

## Next implementation order

1. Extend the existing global World adapter to verified 2.5 addresses, preserving
   the 2.4 zero-extension control and independent lookahead. Test repeatability,
   completed GL, resources/order and timing before exposing it as a supported trial.
2. USA: measure/extend the common admission and removal limits together with a
   correctly bounded virtual reciprocal tail. Stop treating the far word alone
   as a useful global fix.
3. Off Road: begin with its own bounded float-limit control and trace resource
   lifetime; extend its ROM reciprocal range only if observed vertices need it.
4. Exotica: follow the pending/activation path and distinguish CPU sphere rejection
   from Zeus clipping. A larger advertised far multiplier with zero newly admitted
   objects would be misleading. Host future/static scenery remains a longer-term
   direction for all games when guest activation is the limiting factor.

None of these probe counts proves reduced visible pop-in. New candidate drives
must preserve the originals, repeat against themselves, retain failed controls
and eventually receive attended acceptance on more levels.
