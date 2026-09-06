// Cruis'n motor-byte adapter: positive game force uses negative SDL steering level.
#pragma once
#include <algorithm>
namespace cruisn {
inline int motor_level(int byte, bool invert = false) {
    if (byte == 0 || byte < -127 || byte > 127) return 0; // -128 is stop, not full force
    int magnitude = byte < 0 ? -byte : byte;
    int level = int(std::min(1.0, double(magnitude) / 126.0) * 32767.0 + .5);
    return ((byte > 0) != invert) ? -level : level;
}
}
