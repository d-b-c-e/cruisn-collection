#include "../../native/motor_signal.h"
#include <cassert>
int main() {
    assert(cruisn::motor_level(-128) == 0);
    assert(cruisn::motor_level(128) == 0);
    assert(cruisn::motor_level(0) == 0);
    assert(cruisn::motor_level(126) == -32767);
    assert(cruisn::motor_level(127) == -32767);
    assert(cruisn::motor_level(-126) == 32767);
    assert(cruisn::motor_level(63) == -16384);
    assert(cruisn::motor_level(63, true) == 16384);
    // Exercise the actual driver helper: normal commands retain the prior
    // formula at all representative gain/limiter boundaries; neutral cannot
    // become a force regardless of previous state or optional conditioning.
    for (int raw = -128; raw <= 127; ++raw)
    for (int gain : {25, 100, 400, 800})
    for (int slew : {0, 1, 16, 127})
    for (int clamp : {0, 40, 127})
    for (int previous : {-127, -1, 0, 1, 127}) {
        int state = previous;
        int adapted = cruisn::adapt_motor_byte(raw, gain, slew, clamp, state);
        if (raw == -128) {
            assert(adapted == 0 && state == 0);
            assert(cruisn::motor_level(adapted) == 0);
        } else {
            int legacy = raw;
            if (gain != 100) legacy = std::max(-127, std::min(127, legacy * gain / 100));
            if (slew > 0) legacy = previous + std::max(-slew, std::min(slew, legacy - previous));
            if (clamp > 0) legacy = std::max(-clamp, std::min(clamp, legacy));
            assert(adapted == legacy && state == legacy);
        }
    }
    int state = 127;
    assert(cruisn::adapt_motor_byte(-128, 800, 1, 40, state) == 0);
    assert(cruisn::adapt_motor_byte(1, 100, 1, 40, state) == 1);
}
