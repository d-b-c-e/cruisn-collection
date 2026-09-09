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

The launcher supports continuous toggles and bounded parameter choices. One-shot
and instruction-restoring actions remain unavailable **before launch**: activate
them during the race after the game has loaded its code. Original comments remain
visible when selecting an entry.

## During gameplay

The new native candidate adds **Esc → Cheats** to the enhanced renderer in all
four games. This needs the matching rebuilt emulator, not just updated Python
files. As of September 8 evening, the candidate is built separately; visual menu
acceptance and deployment to the Stream Deck copy are pending a free testing window.
The published v0.4.0 ZIP and previous personal emulator have no live Cheats page.

Use Up/Down to select, Left/Right to change a toggle or value, and Enter to activate
one-shot actions such as Finish Race Now. A parameter action uses the selected
value. Changes are queued while paused and apply when you **Resume**. Esc inside
Cheats goes back to the pause menu; another Esc resumes. Exiting the game discards
pending actions. Repeated Enter presses queue repeated one-shot activations.
Session changes do not overwrite the launcher's saved selections.

Drive Anywhere and similar cheats can now be switched on and off after boot;
MAME executes their original save/restore scripts. Read the imported comments:
some cheats have game-specific limitations. Import a file from the launcher card
before starting the game. Importing alone leaves every cheat off.

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

A newly frozen source launcher accepts the same option. Automated recordings retain
the exact XML, selection, loader, state changes and a frame-stamped action journal.
Playback repeats the actual actions, including one-shots; its menu is read-only.
Replay rejects missing or altered evidence. Support bundles include selections,
actions and state logs, without including the cheat XML or ROMs. With no imported
catalog, launches disable MAME cheats. An imported catalog enables the engine with
all unselected entries off so they remain available in the live menu.

For repeatable timer verification, use an existing driving case and the user's
exact-revision XML/archive. The command runs isolated with physical force off:

```powershell
python harness/check_cheats.py results/diagnostics/my-drive C:/Downloads/cheat.zip --candidate E:/Source/mame-src/vunit.exe

# Current live loader, exact action frames, available finish and restoration checks:
python harness/check_cheats.py results/diagnostics/my-drive C:/Downloads/cheat.zip --candidate E:/Source/mame-src/build/mingw-gcc/bin/x64/Release/vunit.exe --live-actions --restore-and-finish

# Opens a game window: exercise Esc/Cheats/Resume, record actions, replay completed images.
python harness/check_live_cheat_menu.py results/diagnostics/my-drive --candidate E:/Source/mame-src/build/mingw-gcc/bin/x64/Release/vunit.exe
```

The headless checks inspect actual timer and instruction memory while MAME executes
the original scripts. They do not certify rank/nitro, every imported parameter or
attended gameplay. The windowed check separately verifies navigation, pause/resume,
staging and recording fidelity; it always disables physical force.
