# Exotica 4K performance: keep the covered owner window small

Correcting the replay harness restores approximately full speed in all three
measured Amazon driving windows, with the same native executable and genuine
3840×2160 CRT output. `--display-size` previously maximized MAME's covered GDI
window to the monitor size. Zeus already presents through a separate full-monitor
window; scaling the hidden software renderer added substantial unnecessary work.

The launcher and normal rig already keep this owner small. The regression was in
explicit replay monitor selection, which overrode that policy. The correction
selects the requested monitor but uses `-resolution auto -window -nomaximize`
only for the Zeus GL overlay. V-Unit and native-renderer controls retain their
requested presentation size. Six focused display-target tests pass, including
preservation of the recorded command and all four native-control selections.

## Attribution and limits

One shortened 6,402-input replay used MAME's built-in Windows CPU sampler.
About 41.3% of samples passed through `renderer_gdi::draw`; another 13.1% were
in `NtGdiStretchDIBitsInternal`. The first group's leaf was misleadingly labeled
`luaopen_lfs` by nearest-symbol lookup: its caller chain identifies GDI, not Lua.
MAME's profile mode also disables throttling and limits processors, so these
samples locate work; they are not normal-mode performance measurements.

`drawgdi.cpp` software-renders at owner-window dimensions and then stretches the
result. Zeus's monitor-sized popup and existing source comments confirm that
the owner need not be maximized. No native rendering or simulation change was
needed for this correction.

## Matched normal-mode acceptance

Both full Amazon runs use native `f0cfbd005c87f4f40b81381227785acfbfb6485c`,
SHA256 `30d3472d471f77b5cd1ff6cb1a30cf0cc91e58e32d64d1e491816644960a5fa4`.
The corrected run preserves all 8,860 inputs and original native images, all
camera/ADC, lifetimes, admissions, ordered endpoint records, deterministic
scene/material fields and 22 saved original/replacement model binaries.
All 30,308 marked preparations succeed with zero rejections; 282,036 GPU pairs
match. Both completed CRT frames (6538 and 6545) remain pixel-identical at
3840×2160. The first was visually inspected after the comparison.

| Native frames | Maximized covered owner | Small covered owner | Host-time reduction |
| --- | ---: | ---: | ---: |
| 3501–5000 | 81.56% speed | 99.94% | 18.39% |
| 5701–6400 | 72.89% | 100.10% | 27.19% |
| 7001–8848 | 79.14% | 100.01% | 20.87% |

The small deviations around 100% reflect window timing. This is one matched
pair with correctness journals still active, not a log-free or physical-FFB
release verdict. It supersedes the low absolute 4K speeds in the preceding
[projection-reuse comparison](2026-09-15-exotica-projection-reuse.md); the CPU
assembly saving measured there remains valid. Do not extrapolate this result
to older runs without checking their actual window options.

Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`projection-native-profile`, `projection-native-profile-plan.json`,
`projection-reuse-live-candidate`, `projection-small-owner-candidate`,
`projection-small-owner-qualified.json`, `projection-small-owner-cost.json`,
and `projection-small-owner-invocation-presentation.json`.
The copied local run-plan description still names three relative-cadence frames;
the invocation and completion receipts establish the actual two global-cadence
frames above. No third frame or full-drive visual inspection is claimed.

Personal Stream Deck/native87d and public v0.5.0 remain unchanged. The next
acceptance work is temporal 4K visibility and margin coverage, another track,
and default regressions on the combined candidate. This performance result
does not clear remaining geometry defects or four-game release parity.
