# Off Road: late 3× rendering preserves original resources

A fresh matched El Paso pair on the current 3840×2160 monitor preserves all
8,762 recorded inputs and the sampled original game images. At native frame
8,760, with actual added scenery present, the complete original DMA journal,
framebuffer, texture RAM, palette RAM and capture metadata are byte-identical.
The frozen native candidate is `f2e08e49d9e`; physical FFB is disabled.

The scene emits 516 quads from 153 decoded objects, with 152 future sources.
Its counters and ordered 64-bit quad fingerprint match the earlier full 3×
drive. Recomputing that fingerprint from the current full quad log agrees.
This is a fingerprint comparison, not an independent full-byte reconstruction.
Earlier independent checks at four other late snapshots remain separate evidence.

The completed 3824×2073 CRT captures differ in 105,382 pixels within
`[1688,495 .. 3014,625)`. Inspection shows earlier canyon terrain near the
horizon, with the nearby road, truck and HUD preserved in this frame. Camera
words match on all 6,961 sampled frames, and all 27,844 actual ADC reads,
including their times, match. A single completed image does not establish
continuous handover, material ownership across time, other courses or speed.

## Retained failures and scope corrections

- An initial frame-9,240 pair contained no added quads. Resource equality there
  was insufficient to validate drawing; its failed nonempty-scene gate remains.
  Frame 8,760 was selected from prior actual scene and image evidence instead.
- A singleton GL capture request was incorrectly rejected by replay preflight.
  The interval check now permits `first == last`, consistent with the existing
  cadence validator. Seven focused GL tests passed.
- The old 3440×1440 monitor was absent. That preflight failure is retained; the
  successful pair explicitly requests the actual 3840×2160 display.
- The new auxiliary RAM probe retained its old frame constants because chained
  source substitution also rewrote replacement literals. No RAM snapshot was
  taken. A separate explicit resource/fingerprint check uses existing outputs;
  it does not claim the missing independent reconstruction. A subsequent checker
  also incorrectly assumed the older run had a full quad log; it has fingerprints.
  Both failed reports remain. No extra game run was used to repair analyzer errors.

`harness/compare_vunit_resources.py` now provides a reusable offline check for
original V-Unit resource preservation. It validates capture identity, resource
sizes, DMA format/order/frame span and full hashes. Four focused tests cover
single-byte changes, matching truncations, bad metadata and broken journals.
Added geometry and presentation require separate checks; this tool does not
declare drawing parity on its own.

Local evidence under `results/diagnostics/offroad-full-20260910/`:
`verified-late-resources-off`, `verified-late-resources-draw`,
`verified-resource-qualification-v2.json`, and `verified-resource-presentation.png`.
The resource dump contains the original DMA history, including the final drain,
and one captured resource state. Raw game data and screenshots remain local.
Personal Stream Deck/public v0.5.0 are unchanged.
