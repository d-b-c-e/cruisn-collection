# Upstream check before v0.4.0

Read-only GitHub commit queries were made for the old Midway and current Williams
driver paths, the Zeus2 device and the shared DCS path on September 8.

- [Exotica speed/depth-clear fix #16046](https://github.com/mamedev/mame/pull/16046)
  is already backported in our exported patch 80/123. It is part of this release.
- [Zeus2 dot clock, XOffset and VCOUNT #16058](https://github.com/mamedev/mame/pull/16058)
  is a newer September 5 change, described upstream as fixing Skins Game. It derives
  dot clock from a register, corrects interlaced scanline reporting and latches the
  render window for deferred drawing. It is not in our current patch series.
  Its possible Exotica implications need an isolated compatibility study; no claim
  is made that it fixes our text or pop-in. Do not insert an untested backport into
  the approved release. Consider it alongside post-release Zeus diagnostics.
- The recent V-Unit driver history includes structural/API changes. No new V-Unit
  draw-distance fix was identified in this bounded inspection. This is not a full
  audit of every open upstream pull request or hardware-device change.

Exact API responses and the #16058 diff are retained as ignored
`build/release-v040-upstream-*.json` and copied into the release proof archive.
The frozen native binary remains commit 97600e9597e.
