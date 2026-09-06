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
}
