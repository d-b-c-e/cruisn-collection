# Zeus palette lifetime — September 9, 2026

The enhanced Zeus renderer cycles through256 GPU palette rows. A vertex batch
retains the selected row number until its draw is submitted. Replacing a row
while a pending batch still references it can change that batch's colors. The
consumer's timing determines its batch boundaries, making this a candidate
explanation for intermittent material errors. It is separate from the upstream
depth/blend trial described in [the upstream review](2026-09-09-zeus-upstream.md).

## Reproduction and limits

A synthetic GPU fixture renders the same pending geometry with different palette
upload/draw timing. Late reuse produces green where an earlier draw produces red.
Drawing before row reuse preserves red. These are actual shader results, with
controlled expected colors, rather than a screenshot similarity threshold.

Amazon's frame3600 native capture has288 palette loads between its clear and
final draw. An independent CPU replay of the actual commands/resources matches
all1,048,576 native RGB24 and depth entries. Delaying its draws with the256-row
policy corrupts29,968 full-buffer pixels. An early draw or one guarded flush
restores exact native colors. Those corrupted pixels are outside the page being
displayed in that capture, so this CPU experiment alone did not explain the
earlier black sky. The subsequent native GL reproduction below supplies that
missing visible evidence. The original failing pair is retained.

The first full native legacy trace now observes29 pending-row conflicts before
completed-frame3601, eight before4201 and nine before4202. This confirms that
unsafe overwrites occur in the actual consumer. Dense pixel correlation and
guarded repeated drives were then used to connect them to visible defects.

The first dense legacy run reproduced the black sky/wrong mountain colors at3600,
but completed only47/49 requested images before teardown. That run is retained
as FAIL. A longer3800-frame prefix completes all49 images at3576..3624. Its legacy
trace has532 unsafe overwrites; guard and repeated guard each draw safely at25
conflicts. Guard changes25/49 images and both guarded runs match all49 exactly.
At3600 the guarded image matches the original good4K reference **pixel-for-pixel**.
The reproduced bad image matches the older failure outside a small waterfall
region (5632 differing pixels). This establishes a visible fix for the reproduced
palette corruption, rather than a speculative explanation based on counters.
All three runs preserve2000camera/6000actual ADC samples,414models/3488ordered
quads and all ten captured original resource/submission files at3600. The
second window covers4190..4210, with21 completed4K images per4400-frame run.
Legacy has133 unsafe overwrites and incorrect distant mountain/foliage colors;
guard and repeat handle28/29 conflicts. Guard changes16/21 images; both guarded
runs match all21 exactly. Each preserves2600camera/7800actual ADC samples,
412models/3563ordered quads and the same ten original resource/submission files.
These corrections concern palette corruption at about game0:09 and0:19. They
do not establish fixes for the user's later0:35/0:45/0:57 margins or1:12 rectangle.

## Isolated native candidate

Native commit `f537f74ddbf5f93cfb0daa23c7a26c30b482cbbb` is built separately and
pushed to the fork. Frozen executable: `build/candidates/f537f74ddbf/vunit.exe`,
SHA256 `37515ca7b6fe507a92be97cb56a64f31197e99f8ac1670bb43a60db7a97c122c`.
The150 exported patches reconstruct tree `3dc2a349833e9ede18e21ca85fb82ad3a7fd53bf`.
The personal v0.5.0 executable remains SHA87d04de4.

`replay.py --zeus-palette legacy|guard` is diagnostic-only. Both explicit modes
require a candidate and live Exotica GL. Native checks require physical FFB0.
Absent settings preserve existing recordings and rendering behavior. There is
no launcher option or deployment at this checkpoint.

The shared native helper tracks which palette rows pending vertices reference.
Guard mode submits the pending batches before an upload would overwrite a used
row. It does not wait for the GPU to become idle or flush on every palette load.
Existing draw/clear/upload boundaries reset those references. Legacy mode only
tracks conflicts. Native startup and completion receipts must agree with the
requested mode; guarded conflict and flush counters must match. Per-frame
conflict logging is bounded to64 messages, with complete totals retained.

Local checks pass275 Python tests without skips,30 native helpers,
10,081 C31/137yaw vectors,32 existing GPU checks,25 upstream pixel cases and
three palette timing cases across84 commands. The414-file source identity is
`a7803d6530e5b20e40b1232e412ce1b14d9658e0d0562336c0baf35b024971b9`.
The native lifetime test covers sparse references and repeated rollover from
all256 starting slots. Whole-game visual acceptance remains open; the dense
native image evidence above is distinct from these standalone helper tests.

## Active acceptance

Full8860-frame Amazon legacy, guard, repeated guard and combined upstream/guard
trials complete serially with physical FFB0. Each preserves7051camera/21153actual
ADC samples and59 completed4K frames. Legacy observes46 unsafe overwrites;
guard/repeat/combined handle4/3/3 conflicts respectively. All59 guard/repeat
images equal legacy, and combined equals the earlier upstream trial. The three
same-policy captures preserve all ten original files exactly; every mode's
independent geometry oracle passes. Sparse images miss the transient defect,
which is why the dense comparisons above are necessary. Seven defaults were
subsequently renewed on the final shutdown candidate below. The earlier f537
binary did not receive a separate seven-default run.
No release, deployment, default change or extra-scenery claim follows from the
standalone fixture results.

Evidence and drafts stay under `results/diagnostics/exotica-amazon-20260909`.
Raw model, palette, framebuffer and WaveRAM operands remain local.

## Harness follow-through

The CPU oracle previously printed color/depth mismatches but always exited zero.
It now returns failure for any full RGB24 or depth-buffer difference, emits an
optional hash-bound JSON verdict, and continues ignoring the unused alpha byte.
A ROM-free clear fixture independently changes a hidden color or depth entry;
both must fail even though the displayed page remains identical. Exact and
alpha-only controls pass. Historical CPU acceptance used an independent strict
wrapper and is not being inferred from the former CLI exit status.

The incomplete47/49 dense run also exposes a capture teardown race. A separate
native candidate now waits for its already-queued requested frame, with a10-second
bound and physical FFB0 requirement. This does not advance the emulated machine.
Strict completed-image validation still decides success, including with older
binaries that ignore the request. The300-frame boundary completes all49 images
at250..298 and waits1078ms for the consumer. An intentionally stopped consumer
correctly fails with a zero-millisecond drain, retaining its incomplete captures.
Two3650-frame Amazon trials both complete49 images and match each other and the
prior corrected window exactly. They preserve the same ten original resource
files,414models/3488ordered quads and original input/motion timing. The old47/49
failure remains archived. Normal launches retain their existing exit path.

The separate native shutdown commit is `5a80a77e589bfac396208bfb153e741c766cfac4`,
candidate SHA256 `66b0132ea2b312e2284f76be6cfed7ac8061b6752ba9517b6a84f896e501b39c`.
Its151-patch export reconstructs tree `8285f1816927eb9fd7986f3d42884d711c620a9e`.
Final local checks pass276 Python tests without skips,30 native helpers and all84
commands at415-file identity
`8de7361df4a0e0040f519a3d3a8bd1058bf3c644eb6d72e0752b6d21ad263359`.
All seven default cases now pass on this final candidate, including full Germany,
actual UDP versus independent memory, four software force-policy/polarity checks
and Exotica's21 original completed4K images. This renews baseline compatibility;
it does not certify physical force, every course or added scenery.

The [245-file public proof](../../results/proof/2026-09-09-zeus-palette-lifetime/README.md)
recomputes twelve original input/camera/actual-ADC prefixes and selected4K palette
corrections, including retained failures. Complete image sequences, native
geometry/resources/CPU/GPU/build and seven-default checks remain hash-bound
receipts. Raw game resources are excluded. Next marked-window runs enable real
CPU rasterization alongside GL; their legacy blank-CPU-image comparisons are
expected to fail and are kept separate from strict native CPU pixel acceptance.
