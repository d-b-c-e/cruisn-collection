#include "pause_cheats.h"
#include <cassert>

int main() {
    using namespace cruisn;
    cheat_row toggle; toggle.index = 1; toggle.description = "Instruction patch";
    toggle.kind = "toggle"; toggle.choices = {"OFF", "ON"};
    cheat_row shot; shot.index = 2; shot.description = "Finish";
    shot.kind = "oneshot"; shot.choices = {"OFF"};
    cheat_row param; param.index = 3; param.description = "Choose";
    param.kind = "oneshot_parameter"; param.choices = {"OFF", "First", "Second"};
    cheat_bus().publish({toggle, shot, param}, false);
    pause_cheats menu; menu.begin_pause(); menu.open = true;
    menu.change(1, false);
    assert(menu.rows[0].steps == 1 && menu.pending.size() == 1);
    assert(cheat_bus().take().empty()); // No writes while paused.
    menu.move(1); menu.change(1, false);
    assert(menu.pending.size() == 1); // Arrow cannot activate a one-shot.
    menu.change(0, true); menu.change(0, true);
    assert(menu.pending.size() == 3); // Two deliberate presses are two actions.
    menu.move(1); menu.change(1, false); menu.change(1, false);
    menu.change(0, true);
    assert(menu.rows[2].steps == 2 && menu.pending.back().activate);
    menu.move(1); menu.change(0, true);
    assert(!menu.open && cheat_bus().take().empty()); // Back is not Resume.
    menu.resume(); auto requests = cheat_bus().take();
    assert(requests.size() == 6 && requests[0].index == 1 && requests[5].steps == 2);
    menu.resume(); assert(cheat_bus().take().empty()); // Never re-apply a queue.
    menu.begin_pause(); menu.change(1, false); menu.cancel(); menu.resume();
    assert(cheat_bus().take().empty()); // Exit discards unapplied one-shots.
    cheat_bus().publish({toggle}, true);
    menu.begin_pause(); menu.change(1, false); menu.resume();
    assert(menu.pending.empty() && cheat_bus().take().empty()); // Replay cannot be edited.
    cheat_bus().publish({}, false); menu.begin_pause(); menu.open = true;
    menu.move(-1); menu.change(0, true); assert(!menu.open);
    cheat_bus().publish({toggle}, false); menu.begin_pause();
    for (int i = 0; i < 300; ++i) menu.change(0, true);
    assert(menu.pending.size() == 256); // Bounded even during a long pause.
}
