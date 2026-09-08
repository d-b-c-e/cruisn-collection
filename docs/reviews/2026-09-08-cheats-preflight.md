# Cheat-menu preflight for overnight work

The user's `C:/Users/antho/Downloads/cheat0279.zip` contains a nested `cheat.7z`.
That archive has arcade XML entries for every supported game; the similarly named
`n64/` and `gbcolor/` entries are unrelated console games. Five arcade files were
extracted only into ignored `build/overnight-cheat-inventory` for inspection.

| ROM | Entries in the downloaded arcade XML |
| --- | --- |
| crusnusa | Infinite Time, Finish this Race Now!, Always in 1st Place, Drive Anywhere, Drive Past Finish Line |
| crusnwld24 | Infinite Time, Finish this Race Now!, Always 1st Place |
| crusnwld (2.5) | Same three, plus Drive Anywhere and Drive Past Finish Line |
| offroadc | Infinite Time, Infinite Nitros, Always be in 1st Place, Drive Anywhere, Drive Past Finish Line |
| crusnexo | Infinite Time, Finish this Race Now!, Always in 1st Place, Drive Anywhere, Drive Past Finish Line |

These are an inventory, not working-cheat claims. World 2.4 timer/rank addresses
differ from 2.5. Several Drive Anywhere/Past Finish comments explicitly describe
out-of-bounds freezes. Off Road's two timer bytes explicitly require separate
writes. Preserve those distinctions and comments. No cheat was enabled or shipped
in v0.4.0 preparation.

The local MAME 0.286 frontend already has a C++ `cheat_manager` and `cheat_entry`
in `src/frontend/mame/cheat.h`. It exposes entries, descriptions/comments,
classification, next/previous/default state, activation and menu text. Parameter
changes, run/on/off scripts and one-shot actions are already supported. Reuse that
engine instead of translating its expressions into a second evaluator.

The local `luaengine*.cpp` search did not find a cheat-manager binding. Inspect a
small frontend bridge or the existing MAME cheat menu integration before assuming
Lua can enumerate/control these XML cheats. Keep commands on the emulation/UI
thread; the renderer thread must not mutate game state directly. Launch-time
preferences and live changes must enter diagnostic/replay identity.

Primary sources: the checked-out MAME source above,
[upstream cheat frontend](https://github.com/mamedev/mame/blob/mame0286/src/frontend/mame/cheat.h),
and [MAME's scripting documentation](https://docs.mamedev.org/luascript/index.html).
Use documentation for the checked-out version when interfaces differ.

Before bundling third-party data, inspect the archive's README/credits and terms.
An import flow for the user's archive avoids assuming redistribution permission.
Start runtime validation with reversible timer/rank cheats on exact ROM revisions,
in isolated no-force sessions, then inspect conflicts with installed game patches.
