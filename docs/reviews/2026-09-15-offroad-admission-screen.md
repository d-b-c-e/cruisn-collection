# Off-Road: extra admission has no demonstrated visible benefit

Do not promote the proposed 141,888-to-191,040 host admission change. It adds
geometry, but none of the seven material-backed views examined changes a pixel.
This saved-scene experiment therefore does not justify another MAME build,
launcher option or live distance trial.

The first five material captures belong to `six-final-offroad/case`, an older
test case. They are not the user's later El Paso drive. Each full native scene
matches independent Python reconstruction with unchanged old ordered quads and
current palette/texture bounds. Isolated host rendering remains identical at
frames 4000, 4500, 5000, 5500 and 5900 despite 161–266 additional quads.

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
6,244 actual ADC events match the original drive over 1800–3360. All four
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
3× setting and eleven material rejections. Those require classification before
being treated as repair targets. Do not bypass the screen or material guards
merely to increase quad counts. Next use these new operands to identify what
was rejected and whether any rejected geometry intersects the viewport.

Local evidence under `results/diagnostics/world25-roads-20260914/`:
`offroad-admission-materials`, `offroad-drive-resources` (failed),
`offroad-drive-resources-v2` (incomplete),
`offroad-drive-resources-partial-qualified.json`, and
`offroad-drive-admission-materials`. Nativefe1, personal native87d and public
v0.5.0 are unchanged. No Off-Road rendering change was promoted.
