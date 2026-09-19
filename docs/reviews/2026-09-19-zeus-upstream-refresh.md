# Zeus upstream check, September19

Two upstream changes merit separate consideration after the pending matched
Mars measurement. Neither is in the frozen4df rendering candidate or the newly
deployed707 controls build. No native edits, build or gameplay were performed
for this check.

[Display interrupt #16178](https://github.com/mamedev/mame/pull/16178) merged
September18 as `f42098cc1dcf96e087ea1159c699b4190eb3d03a`. It schedules vertical
sync at the programmed line and pulses IRQ0, replacing the driver's active-area
vblank interrupt. Exotica programs line402, two lines after its400-line active
area. The author reports missing-background repair for Mortal Kombat4 and no
measured Zeus2 gameplay change in their captures. This is not evidence that it
fixes our Exotica margins, pauses or pop-in.

Our current source still registers `set_vblank_int` and the old display IRQ
off timer. The change is therefore applicable in principle, but it changes
emulated scheduling. Backport it separately after the frozen timing run. Check
boot, interrupt pulse/line programming and recorded motion first; preserve
old input/capture failures if deterministic alignment changes. Compare actual
completed GL output, not the Zeus native black snapshots alone. Device mode
changes and resets need explicit consideration. No fresh recording should be
requested until the existing recording has been evaluated against that change.

[Zeus2 cleanup](https://github.com/mamedev/mame/commit/6941dc5ce66e3adc39d60ea1705e66a7467cf221)
landed September15 after the earlier review. It removes the static Wave RAM
base pointer, replaces macros with instance members, and simplifies swizzling
and types. It is a maintenance candidate, not a demonstrated visual fix. Our
large replacement renderer and retained-resource paths require a scoped port;
blindly importing the whole upstream file would lose local ownership rules.

The current-path history check covered `src/devices/video/zeus2.cpp`,
`src/mame/williams/midzeus.cpp` and `src/mame/williams/midvunit_v.cpp` since
September15. No new V-Unit video commit was returned. Open-PR keyword searches
for `Zeus` and `midvunit` returned none; this is a limited search, not proof that
no broader emulator change could affect these systems. Initial queries against
the local old `midway` paths were empty and were not used as upstream evidence.

Raw commit/PR responses and SHA receipts are retained locally under
`results/diagnostics/zeus-upstream-20260919`. Read-only GitHub API calls do not
run Actions or use hosted build minutes.
