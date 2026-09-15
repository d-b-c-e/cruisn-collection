# USA coverage clipping and Off-Road admission screening

The shared far-coverage renderer now supports a separately gated USA adapter.
Its complete recorded scene and transport checks pass. The visible live benefit
in this short window is very small: only 26 pixels in two of 21 frames change.
This is useful boundary handling, not a solution to most remaining pop-in.

## USA

Four saved scenes contained 158 first-vertex far rejections and 23 screen-range
rejections. Extending private projection to a bounded 480,000 units and clipping
coverage at 240,000 adds 294, 138, 28 and 49 quads respectively. Every old ordered
quad remains exact in these samples. Added geometry is from future sources.
Independent Python reconstruction matches full scene counts, ownership,
geometry, materials and all depth sidecars, including existing pending objects.

The native adapter retains the ordinary projection and quad paths by default.
Only `--usa-host-far-coverage on` enables it, requiring an explicit candidate,
3× future drawing and physical FFB0. Near and signed16 screen guards remain.
The shared transport and shader preserve original UV interpolation. There is
no product-menu change or personal deployment.

Isolated host-scene GPU comparisons, using each snapshot's actual textures and
palettes, change 1,128 / 0 / 8 / 0 RGB pixels. They exclude original foreground
geometry. The first local resource check assumed a u16 palette file; the actual
snapshot contains u32 words. That failed assertion is retained separately;
the corrected resource check passed before the live comparison.

The matched live pair used frozen native `fe1a862c784`, 3,522 inputs, CRT on,
4× internal rendering and 21 completed 3824×2073 captures on the 4K monitor:

- Original native-image checks, 1,721 camera samples and 5,163 actual ADC reads
  match, including ADC times. Original DMA, framebuffer, textures, palette and
  metadata match at frame 3520.
- All 5,289 crossing packets match GPU preparation records and independently
  calculated masks. These records precede rasterization; completed GL captures
  provide separate presentation evidence.
- Actual scene 3501 matches the independently checked saved scene: 9,269 old
  quads retained plus 294 new quads, with 136 crossing depth packets exact.
- Frames 3500–3518 are pixel-identical. Frames 3519 and 3520 each change 26
  pixels in a 10×4 horizon region. No new near-black pixels were measured; the
  full area below y1200 is exact. Inspected images preserve road, cars and HUD.

Do not confuse the larger isolated-scene change with visible gameplay benefit:
ordinary nearer scenery hides most of it. This pair is not a speed benchmark,
full-drive handover test or all-track acceptance. Three native tests and 16
focused Python tests pass; defaults and coverage outputs match the frozen
baseline/prototype across all four saved scenes.

Candidate SHA-256:
`ebed961ddfb838e75f3f79d9a85a4d3dc88dae0c18c8e9bbb0e960560ba48c5f`.
The 217-patch export reconstructs tree
`d31f63cf92dd9d60c616570490cb1d93f3415adb`.

## Off-Road: a different admission boundary

The full El Paso log has 1,039 aggregate projection rejections in 264 scenes.
That counter alone does not mean far-plane failure. Separate saved snapshots
show 94 first screen-coordinate failures and no first far-plane failures across
16 scenes. This does not classify every rejection in the full drive.

Off-Road's 3× sphere admission ends at 141,888 units while its existing vertex
projection supports 191,040. A local copied-header prototype uses that existing
projection limit for sphere admission, retaining the same projection, LOD,
ordering and material bounds. Independent reconstruction passes all 16 scenes;
every old ordered quad remains exact. Ten scenes gain geometry, ranging from
161 to 2,115 added quads. Six, including the late finish snapshots, are unchanged.

This is not yet linked, built or accepted visually. It changes the selection
distance rather than copying World's far-plane mask or its units. Next inspect
actual material-backed rendered output before making a runtime candidate.
The initial local parser failed to normalize Windows CRLF before splitting
cold/warm outputs; its failure is retained, and the corrected verifier passes.

Local evidence is under `results/diagnostics/world25-roads-20260914/`:
`shared-projection-screen`, `usa-far-prototype`, `usa-far-qualified-v2`,
`usa-far-canonical`, `usa-far-live-off`, `usa-far-live-on`,
`usa-far-live-qualified.json`, `usa-far-native-export.json`, and
`offroad-admission-screen-v2`. Personal native87d and public v0.5.0 are unchanged.
