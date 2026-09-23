# V-Unit sky-gap screen on saved gameplay frames

The source-joined Off-Road El Paso opening is detectable without altering a
game or rendering a new image. `harness/screen_vunit_sky_gaps.py` reads a passing
replay's completed indexed mirror and same-run original DMA capture. It derives
the game's backdrop palette from its wide original sky commands, then finds
short runs of backdrop pixels in the 16:9 margin that have host-owned scenery
immediately above and non-sky original content immediately below. It validates
the mirror, original command receipt, native scale and margin before reporting
candidate connected regions. The default maximum run is now 32 coarse pixels:
the earlier 16-pixel threshold missed the longer opening later in the same turn.

The source-hashed local `vunit-sky-gap-screen-v5.json` screens ten saved
completed views without launching MAME:

| Game / saved view | Host-bounded pixels | Connected sky envelope |
| --- | ---: | ---: |
| Off-Road El Paso, completed 3120 | 5,841 | 6,756 pixels; fine bbox `(0,941)..(228,982)` |
| Off-Road El Paso, completed 3136 | 7,438 | 11,649 pixels; fine bbox `(0,910)..(172,1016)` |
| Off-Road, completed 2520/2524/3360/3360 | 0 each | 0 |
| World 2.4 Germany, completed 7280/7340 | 0 each | 0 |
| USA, completed 3501 in two controls | 0 each | 0 |

At 3120, the extra 915 pixels are adjacent ordinary-only sky runs that connect
directly to the verified host-bounded region. This includes the right tip left visible
by the four [offline fill trials](2026-09-23-offroad-gap-fill-screen.md).
At 3136, the same rule adds 4,211 adjoining pixels. The source-joined center
sample is original sky with no intersecting projected host bounds; the
completed image is byte-exact to the independent temporal replay.
Ordinary-only pockets elsewhere in the captured views are deliberately excluded;
without a host-bounded seed they are too ambiguous to label as this gap.
The v2/v3 reports retain the earlier narrow screen. The v4 report uses 32
coarse pixels explicitly; v5 makes it the default. The original nine views
retain their strict-region counts at the wider threshold, with zero new
regions in the eight controls.

The two positive regions cover the moving blue opening investigated in
[the source review](2026-09-23-offroad-left-margin-source.md). Four Off-Road
controls and four USA/World controls did not trip this particular predicate.
Some controls are duplicate views under different diagnostics, so this is
**ten captured images, not ten independent routes**. World Hawaii and the
reported New York defects are not in this screen because these saved cases
lack the required same-run original-command capture or representative drive.

This is a triage result, not a safe fill algorithm. The predicate can miss
holes where the upper object has transparent texels, the lower content is
CPU-written or the gap is wider. It can also mark an intentionally open vista
between two surfaces. A proposed renderer treatment still needs material and
depth ownership, temporal continuity around the turn, and completed-image
checks. The old Margin Fill would copy a ground boundary column into the
sampled sky band, explaining why simply enabling it is not the next step.

The saved local one-scene scripts `left-gap-marginfill-screen.py` and
`left-gap-gap-policy-screen.py` remain exploratory evidence. The reusable
`harness/screen_vunit_sky_gaps.py` has four focused candidate/component tests;
the adjacent ten-test analyzer/original-scene selection run passes. No MAME
binary, default setting, installed build or public release changed.
