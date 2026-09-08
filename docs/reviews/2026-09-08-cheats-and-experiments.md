# Overnight: Cheats, Experiments and capture targeting

The source launcher now has a per-game Cheats menu, and **Settings → Experiments**
sits beside Display. These changes are post-release development. The published
v0.4.0 tag, download and defaults remain the rollback baseline.

## Product changes

- Import exact arcade XML entries from XML, ZIP or nested `cheat.7z` archives.
  Console entries and parent-ROM fallback are excluded. The user's downloaded
  archive contains 23 entries across USA, World 2.4/2.5, Off Road and Exotica.
- Each game/revision saves its own choices, bound to the imported file's hash.
  Importing/replacing an XML never silently enables old selections. Files are
  user data in `rig/cheats`; the package contains no third-party cheat database.
- Continuous toggles and bounded parameter choices use MAME's existing engine.
  Turn All Off resets the current revision. Wheel navigation follows the other
  launcher pages. Imports and write errors remain visible in the menu.
- One-shots and cheats with restoration scripts remain visibly unavailable.
  Boot-time activation can save uninitialised instruction words for later
  restoration. Live activation is required before offering those actions; the
  native bridge already supports future live commands.
- Experiments keeps its Shared/game contexts, revision restrictions, preference
  keys and option exclusions. Its generic title allows future gameplay trials.
  Back/Esc returns to Settings with Experiments selected. No force or graphics
  tuning accompanies this move.

The user's archive was imported into the source rig, with every cheat still off.
Existing collection preferences, calibration, NVRAM and recordings were preserved.
World force normalization and race-end oscillation remain deferred.

## Native and recording design

Native commit `44c3494d6af372d27612f330b86c8001b8c2535f` adds copied metadata and
guarded commands to the Lua manager. Commands reject disabled engines, invalid
indices, stale descriptions and unknown actions. They call the original MAME
cheat implementation on the emulation thread. The renderer and force code are
unchanged. The 124-patch export reconstructs native tree
`f7af3475d0ce0b6347e2be669338283437a81447` exactly.

The source `E:/Source/mame-src/vunit.exe` is built from that commit, SHA256
`eb2db42a90288bf37ac0dcce9b9ce2106c136fad198c52320ee2b3af3c435a97`.
Stream Deck continues to use the source collection and this executable.

With no selections, launches explicitly use `-nocheat`. Otherwise they stage only
the exact revision's XML, current loader and saved selections. Recordings freeze
those files and rebind their paths inside each replay. Native state changes are
logged separately and included in replay equality. Support bundles include
selections/state logs, without XML scripts or ROMs.

## Verification and a harness defect found

- The bridge enumerated and toggled cheats in all five ROM variants, rejecting
  invalid/stale commands. Five separate cheat-enabled 4,000-frame recordings
  replayed against themselves with equal input/state traces and native snapshots.
  Exotica's headless snapshots are not a visual oracle; its live GL control is
  listed separately below.
- The timer probe uses real MAME on/off commands and independent program-space
  reads. USA and both World revisions hold 99 with occasional single-frame 98
  ticks, corrected on the next callback. Exotica also passes on/off observation.
  Off Road's separate seconds/hundredths values stay within 0.00–0.02 while on
  and resume increasing when off. The archive's separate byte writes are kept.
- Early timer assertions incorrectly required zero callback-phase differences;
  their FAIL receipts are retained. The corrected analyzer requires bounded
  correction, and rejects a continuing countdown while On or no progression
  after Off. These are timer-memory tests, not blanket acceptance of every cheat.
- Six default driving cases passed on the new binary. Exotica's first GL check
  failed with **1920×1080 captures against 3840×2160 references**. The game had
  selected the secondary monitor. No frame mismatch was waived or resized away.
- Zeus `--compare-gl` now selects an available monitor matching the reference
  size before launch, logs its choice, and fails early when none matches.
  The rerun passed all 6,000 inputs, 21 completed GL frames, actual telemetry,
  independent memory checks, force polarity/gate checks and timing. Normal
  product display selection is unchanged. This completes the seven binary-bound
  default controls; the original aggregate FAIL report remains intact.
- 128 Python tests pass, including archive filtering, saved-selection identity,
  recording isolation, mismatched-state rejection, timer negative controls,
  menu Back behavior and mixed-resolution monitor selection. Existing graphics
  context/persistence tests were updated for the new menu location.

The default regression receipts bind the native binary and case dependencies.
Some launcher/diagnostic source edits continued during that run, so they are not
represented as a new source-bound release gate. No new release is authorized or
published. All five cheat-enabled cases also pass against the final native binary.
The isolated frozen dev ZIP passes nine menu pages, four default boots (12
completed GL images), one additional cheat-enabled World boot (three images),
import, setup health and support-bundle checks. It contains 1,649 hashed files,
with CRT/widescreen/scale4 defaults verified. Shared Crack Fill keeps its existing
On default; per-game distance trials and cheats start off.

Local package: `build/CruisnCollection-dev-20260908-012408.zip`, built at `f8a804f`,
SHA256 `f7a5a641affe81d7e44102d86cc9a6fa19411820a8b9d76607a99e7d08ecfdf5`.
The later diagnostic display-target fix is `1baa99a`; all four CI jobs pass at
34195061384. The [75-file proof archive](../../results/proof/2026-09-08-cheats-and-experiments/README.md)
includes a ROM-free verifier that checks bytes/bindings and recomputes the five
timer-effect conclusions. Archive SHA256:
`ad9ff1881ca4e3e8003794c98a911369e9b6c7fce05451015ebf3da78988c951`.

## Remaining work

1. Add live in-game cheat activation before exposing one-shot/code-restoring
   actions. Validate individual rank/nitro/custom parameter effects and more
   levels; current runtime effect acceptance covers Infinite Time.
2. Continue the overnight global distance capability matrix and guarded trials
   across all four games. Existing World 2.4 experiments remain optional; this
   menu change adds no new distance behavior to another game.
3. Preserve the distinction between native/input agreement, actual completed GL
   agreement, runtime telemetry, and attended driving/physical force acceptance.
