#include "../../native/hud_numeric_speed.h"
#include <cassert>
int main() {
    using cruisn::packed_hud_speed;
    assert(packed_hud_speed(0x393031) == 109);
    assert(packed_hud_speed(0x303131) == 110);
    assert(packed_hud_speed(0x30) == 0);
    assert(packed_hud_speed(0x303034) == 400);
    assert(packed_hud_speed(0x303035) == -1);
    assert(packed_hud_speed(0) == -1);
    assert(packed_hud_speed(0x00300031) == -1);
    assert(packed_hud_speed(0x30303031) == -1);
    assert(packed_hud_speed(0x2d) == -1);
}
