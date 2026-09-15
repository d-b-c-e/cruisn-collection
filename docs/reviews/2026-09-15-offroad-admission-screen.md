# Off-Road: extra admission has no demonstrated visible benefit

Do not promote the proposed 141,888-to-191,040 host admission change. Later
saved-scene evidence justified a gated native trial, but its 21 completed 4K
frames are identical to the stock-admission control. The original seven-view
screen below is retained; the follow-up at the end records the larger sample
and actual live outcome. There is no demonstrated benefit for a launcher option.

The first five material captures belong to `six-final-offroad/case`, an older
test case. They are not the user's later El Paso drive. Each full native scene
matches independent Python reconstruction with unchanged old ordered quads and
current palette/texture bounds. Isolated host rendering remains identical at
frames 4000, 4500, 5000, 5500 and 5900 despite 161â€“266 additional quads.

To avoid extrapolating from those views, a short replay targeted three views
from the recorded El Paso drive: open horizon 2640, canyon turn 2880 and hill
crest 3360. A new `lua/offroad_scene_resources.lua` probe captures RAM, ROM,
textures and palettes at the actual scene callback, rather than continuously
tracing every texture write or allocation. Raw snapshots stay local.

## Capture failures and usable scope

The first attempt selected the Lua replay tick; this drive's scene callback uses
a different native-frame label, so no requested snapshots were taken. The
completion assertion failed as intended. The second attempt selected native
frames and saved 2640 and 2880, but the replay stopped before native scene3360
executed. That run also remains failed. It is not relabeled a successful run.

The two complete snapshots are separately qualified. Their recorded replay
ticks are 2641 and 2881; both native timestamps, callback PCs, exact resource
sizes and ROM identity are retained. The observer's 1,561 camera samples and
6,244 actual ADC events match the original drive over 1800â€“3360. All four
completed 4K images at 2640/2880/3120/3360 match the original recording control.
No full-run input/native-image acceptance is claimed for this failed run.

The probe now preserves both clocks and rejects requested frames without two
replay ticks of headroom before its end. A full successful capture with that
final scheduling guard is still unverified. There was no third game replay
just to obtain the missing hill-crest snapshot.

## Actual drive result

| Native frame | Old quads | Expanded admission | Added | Changed RGB pixels |
| --- | ---: | ---: | ---: | ---: |
| 2640 | 1,548 | 1,764 | 216 | 0 |
| 2880 | 1,427 | 2,145 | 718 | 0 |

Both complete scenes match the independent decoder, including order and
material selection. All old quads remain exact. Every added quad's screen
bounding box lies outside the current widescreen viewport in these two views.
More submitted geometry is not more visible scenery here. This says nothing
about unexamined track views, but removes the current justification for this
particular admission change.

The actual canyon snapshot still has seven projection failures at the accepted
3Ã— setting and eleven material rejections. Those require classification before
being treated as repair targets. Do not bypass the screen or material guards
merely to increase quad counts. Next use these new operands to identify what
was rejected and whether any rejected geometry intersects the viewport.

Local evidence under `results/diagnostics/world25-roads-20260914/`:
`offroad-admission-materials`, `offroad-drive-resources` (failed),
`offroad-drive-resources-v2` (incomplete),
`offroad-drive-resources-partial-qualified.json`, and
`offroad-drive-admission-materials`. Nativefe1, personal native87d and public
v0.5.0 are unchanged. No Off-Road rendering change was promoted.

## Follow-up: completed capture and live trial

The canyon classification is complete: all seven rejected projected models and
all eleven rejected material quads lie outside the widescreen viewport. Relaxing
those guards would not repair a visible canyon defect in that snapshot.

A subsequent replay captured the missing hill crest3360 and later views6240/8760
in one run. Its completion receipt confirms all three atomic snapshots, with
8,802 recorded inputs/native images exact, 7,001 camera samples and28,004 ADC
reads/times exact over1800–8800. Completed original4K frame8760 is exact against
the prior control. The two earlier capture failures remain failed.

Isolated host rendering at3360 changes14,125 RGB pixels, adding13,649 covered
pixels on the right horizon. The other two new views remain identical, making
nine unchanged views out of ten material-backed samples. This positive isolated
result justified one bounded live pair; it did not establish gameplay benefit.

The canonical optional adapter and independent Python decoder reproduce all21
saved scenes in both modes exactly, including every old ordered quad. Two native
unit tests and six focused options/scene tests pass. `--offroad-host-admission
clip` requires an explicit candidate, future drawing at3× and physicalFFB0.
Stock defaults and all projection, material, near and ordering guards remain.
The only change is sphere admission to the existing191,040 projection limit.

Native `6ec8b0fbfc540da7c3f6aee35e67564695612c58` is frozen separately, SHA256
`005041d61c33cf6ab4fb26d4a8739f4ab186e85e9cfea64da1b5b2b819d6ec71`.
The218-patch export reconstructs `547d2c754dec2e7f76f60be025836aa07b6a5aa8`.
No personal binary or public package changed.

Both bounded live runs pass3,382 original inputs/native images. Original DMA,
framebuffer, textures and palettes at3380 are byte-exact, as are1,581 camera
samples and6,324 actual ADC reads/times. At3360 the full live ordered scene equals
the independent saved scene:856 stock quads versus4,467 with expanded admission.
All21 completed3824×2073 CRT images at3350–3370 are nevertheless identical.
The isolated added geometry does not produce a visible gain in this live window.
No speed, full-drive handover or other-track acceptance is claimed.

The first candidate attempt failed before launch because the new options gate
saw attended FFB from the recording, before playback disabled it. Replay now
applies its existing physicalFFB0 policy before experimental option validation;
all ten session-case tests pass. The failed preflight report is retained.
The initial local live checker copied USA's T-junctions-off assumption; both
actual OffRoad runs retained this recording's T-junctions1/crackfill1. The
corrected checker passes without repeating a game. Both checker reports remain.

Additional local evidence: `offroad-drive-resources-v3`,
`offroad-drive-resources-complete-qualified.json`, `offroad-drive-rejections`,
`offroad-drive-late-admission-materials`, `offroad-admission-canonical`,
`offroad-admission-native-export.json`, `offroad-admission-live-stock`,
`offroad-admission-live-clip` (preflight failure), `offroad-admission-live-clip-v2`
and `offroad-admission-live-qualified-v2.json` under the same W directory.
No further live trial of this admission policy is justified without new visible
saved-scene evidence. Keep the gated diagnostic out of the product menu.
