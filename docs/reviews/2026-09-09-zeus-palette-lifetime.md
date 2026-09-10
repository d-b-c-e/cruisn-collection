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
displayed in that capture: this has **not yet reproduced the specific black sky**
in the earlier full-drive repeat. That failing pair remains unresolved.

The first full native legacy trace now observes29 pending-row conflicts before
completed-frame3601, eight before4201 and nine before4202. This confirms that
unsafe overwrites occur in the actual consumer. Dense pixel correlation and
guarded repeated drives are still required to connect them to visible defects.

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
all256 starting slots. These checks do not prove the original Amazon failure's
cause or establish whole-game visual acceptance.

## Active acceptance

Full8860-frame Amazon legacy, guard, repeated guard and combined upstream/guard
trials are running serially with physical FFB0. Each keeps camera/actual ADC
timing,59 completed4K frames and original model/resource capture at3600.
Compare native conflict events with changed pixels; preserve all original
commands/resources and the old failing pair. Renew seven defaults on this
candidate: their last complete acceptance still belongs to edb517/cb65a787.
No release, deployment, default change or extra-scenery claim follows from the
standalone fixture results.

Evidence and drafts stay under `results/diagnostics/exotica-amazon-20260909`.
Raw model, palette, framebuffer and WaveRAM operands remain local.
