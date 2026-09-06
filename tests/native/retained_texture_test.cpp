#include "retained_texture.h"
#include <cassert>
#include <limits>

int main() {
    cruisn::retained_texture held;
    uint8_t actual[] = {1, 2, 3, 4, 5, 6};
    assert(!held.capture(actual, 6, 5, 2));
    assert(!held.capture(actual, 6, std::numeric_limits<std::size_t>::max(), 2));
    assert(!held.capture(nullptr, 6, 1, 2));
    assert(held.capture(actual, 6, 2, 2));
    actual[0] = 9; actual[2] = 7; actual[3] = 8;
    assert(!held.capture(actual, 6, 2, 2)); // don't recapture overwritten memory
    uint8_t upload[6];
    std::copy(actual, actual + 6, upload);
    assert(!held.apply(upload, 3));
    assert(held.apply(upload, 6));
    assert(upload[0] == 9 && upload[2] == 3 && upload[3] == 4 && upload[5] == 6);
    assert(actual[2] == 7 && actual[3] == 8); // emulation stays current
    held.release();
    assert(!held.apply(upload, 6));
    assert(held.capture(actual, 6, 2, 2)); // next visit captures fresh assets
    assert(held.apply(upload, 6) && upload[2] == 7 && upload[3] == 8);

    std::vector<uint32_t> ram(0x20000);
    ram[0x6f] = 0x082861ed; ram[0x70] = 0x6200034c;
    ram[0x61ed] = 0x1234; ram[0x1234] = 0x1081c;
    ram[0x1081c + 13] = 0xfd70c1;
    assert(cruisn::world24_transmission_visible(ram.data(), ram.size()));
    ram[0x1081c + 13] = 0; ram[0x1081c] = 0x10870;
    ram[0x10870 + 13] = 0xfd76b3; // header outlives the D/A panels
    assert(cruisn::world24_transmission_visible(ram.data(), ram.size()));
    ram[0x1081c] = 0;
    assert(!cruisn::world24_transmission_visible(ram.data(), ram.size()));
    ram[0x1081c] = 0x1081c; // corrupt cycle is bounded
    assert(!cruisn::world24_transmission_visible(ram.data(), ram.size()));
    ram[0x1081c] = 0xffffffff;
    assert(!cruisn::world24_transmission_visible(ram.data(), ram.size()));
    ram[0x1081c] = 0x10870; ram[0x6f] ^= 1; // wrong revision fails closed
    assert(!cruisn::world24_transmission_visible(ram.data(), ram.size()));
}
