// USA's decimal HUD formatter packs up to three ASCII digits into one C31 word.
// This is numeric display telemetry, not a physics velocity estimate.
#pragma once
#include <cstdint>
namespace cruisn {
inline int packed_hud_speed(uint32_t word) {
    int value = 0, digits = 0;
    while (word && digits < 3) {
        unsigned ch = word & 255;
        if (ch < '0' || ch > '9') return -1;
        value = value * 10 + int(ch - '0');
        word >>= 8;
        ++digits;
    }
    return digits && !word && value <= 400 ? value : -1;
}
}
