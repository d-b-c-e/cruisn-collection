# One explicit continuous3x diagnostic preset

`replay.py --scenery-preset continuous-3x` selects the appropriate existing host
renderer configuration from the exact recorded ROM: USA, World2.4/2.5, Off-Road
or Exotica. An explicit live candidate is required. Physical FFB remains off.

The new `harness/scenery_presets.py` centralizes the previously long lists of
accepted controls. They include verified startup, continuous operation, quiet
journals, checked shutdown, CRT on and4x; V-Unit also explicitly selects400-line
height. Exotica uses combined future/waiting/active scenery and marked endpoints,
with scheduled endpoint operands disabled. Its first-failure capture remains.
World keeps its road/coverage fixes, and Off-Road retains the already qualified
partial-frontier configuration. No renderer algorithm or native guard changes.

The replay report records every expanded control. Mixing a preset with a manual
control it owns is rejected, including equals-form arguments. Other capture,
probe, output and display options remain caller-owned. Existing recorded patch,
ROM, guest-distance conflict and resource validation still run. This does not
silently alter an incompatible recording to make it pass.

Three focused tests cover all five layouts, real replay argument parsing before
any run, duplicate selection, unknown ROMs and every managed-control conflict.
A separate saved-plan check matches13/17/17/15 controls for USA/World24/World25/
Off-Road and38 Exotica controls. Exotica's sole delta is snapshot5219 to0, already
live-qualified separately with unchanged geometry/pixels. No game is repeated
merely to retest equivalent argument spelling.

The preset is diagnostic CLI convenience, not a launcher setting or deployed
release. The finite numbers retained in its configuration are reference bounds;
continuous operation does not stop there. Neither a multiplier nor successful
setup proves equal visible distances, complete temporal quality or full release
parity. Candidate must include nativef0b4db1f25d's snapshot0 support or a compatible
successor. Local equivalence evidence is `world25-roads-20260914/scenery-preset-plan-equivalence.json`
under `results/diagnostics`; detailed usage is in DIAGNOSTIC-REPLAY.
