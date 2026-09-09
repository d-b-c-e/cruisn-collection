# Imported cheats

Available in the current source; **not included in the published v0.4.0 ZIP**.
Reopen a source launcher after updating: the September8 `env` launch regression
is corrected in [the launch fix](reviews/2026-09-08-launch-environment.md).

Open a game card, then **Cheats → Import Cheat File**. Select MAME cheat XML, ZIP,
or 7z. The downloaded MAME archive's nested `cheat.7z` is supported. Only exact
arcade ROM entries are imported: USA, World 2.4, World 2.5, Off Road and Exotica.
Console entries and another revision's addresses are never substituted.

Use Left/Right or Enter to select a continuous cheat, then launch the game.
**Turn All Off** clears selections for the current revision. Everything starts
off; importing a file does not enable it. World selections follow the Game
Revision selected on its card. Wheel buttons and the directional pad work as on
the other launcher pages. The import file picker also accepts mouse/keyboard.

This first implementation supports continuous toggles and bounded parameter
choices. One-shot actions such as Finish Race Now, and cheats with instruction
restoration scripts such as Drive Anywhere, are shown as unavailable. They need
activation after the running game has loaded its code; they are not safely
equivalent to a preference applied at boot. An in-game activation menu is follow-up
work. Original cheat comments remain visible when selecting an entry.

Files live in `rig/cheats`. Settings are bound to both the ROM revision and the
exact imported XML hash; replacing the XML clears its effective selections.
Previous XML versions are backed up. No third-party cheat database is bundled.
Cheats use MAME's original expression interpreter through a small native Lua
bridge. The collection does not translate or rewrite cheat expressions. Imported
data can still contain faulty game addresses, so imported does not mean validated.

The current source build can also import without opening the launcher:

```powershell
python harness/collection.py --import-cheats C:/Downloads/cheat.zip
```

A newly frozen source launcher accepts the same option. Automated recordings retain the exact
XML, selection, loader and native state changes; replay rejects a mismatch. Support
bundles include selections and state logs, without including the cheat XML or ROMs.
Normal launches explicitly disable MAME cheats when no selections are active.

For repeatable timer verification, use an existing driving case and the user's
exact-revision XML/archive. The command runs isolated with physical force off:

```powershell
python harness/check_cheats.py results/diagnostics/my-drive C:/Downloads/cheat.zip --candidate E:/Source/mame-src/vunit.exe
```

This checks real engine commands, timer memory while on, and resumed progression
after turning off. It does not certify every imported cheat or attended gameplay.
