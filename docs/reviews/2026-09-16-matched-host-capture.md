# Capture host operands and their later completed presentation

The diagnostic pipeline can now capture host depth operands at preparation S
and the framebuffer at a later presentation P. The new explicit
--vunit-host-metadata-frame option requires existing V-Unit metadata capture,
physical FFB0, and S within the host interval and no later than P. Verification
rejects a pair unless the entire S scene reached the completed visible page.

The native change affects only which already-observed packets are written to the
diagnostic files. It does not change packet delivery, projection, materials,
rendering order or display policy. Omitting the option preserves the old capture
selection. The completed-prefix binding still reports whether that old selection
matches presentation; it does not silently certify mismatched evidence.

## Actual Off-Road qualification

One2528-input El Paso replay captured source2520 and presentation2524 at4K,
CRT on, scale4 and401-line projection. All1482 source quads are accounted for on
visible physical page1; page0 contains source2522. The original-command completion
fence independently selects931 original quads from2520..2521 on the visible page.

All2528 recorded inputs and native images match;727camera rows and2908actual ADC
reads match the original full drive. ROM, RAM2520, texture2520, palette2520 and
the complete ordered depth-metadata file are byte exact the prior083capture.
The shared completed2520CRT image is also byte exact. The new2524image was viewed:
early El Paso,0:02.96,49MPH,2AUTO with the car and HUD intact.

Both completed pages still have zero partial/zero opacity. This time the visible
page is explicitly aligned to the reconstructed source, resolving the earlier
timing ambiguity. No displayed fade or new billboard geometry was applied.
No performance or temporal transition claim follows from this one view.

Eleven focused original-mirror tests pass, including source-frame bounds and
explicit selection; the preceding four completion-selector tests also pass.
The standalone billboard helpers remain outside MAME pending visibility and
handover qualification. No broad suite was repeated.

Native07e9eb25de5 is built/frozen/attested:
SHA1adac2fd14f4443b0c41366bfd8be144abfe42320c2ae539d50ec963488e830e.
263patches reconstruct4164af8ba5471e313fe4948308463718d669e2a1.
LOCAL world25-roads-20260914/metadata-presentation-native-export.json,
offroad-matched2520/report.json and offroad-matched2520-qualified.json.
Personal87d and publicv0.5.0 remain unchanged; no deployment/release/physicalFFB.
