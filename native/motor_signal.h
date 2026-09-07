// Cruis'n motor-byte adapter: positive game force uses negative SDL steering level.
#pragma once
#include <algorithm>
namespace cruisn {
// Driver conditioning for signed game bytes. The reserved neutral command
// must not become ordinary force through gain, slew limiting or clamping.
inline int adapt_motor_byte(int raw, int gain, int slew, int clamp, int &previous) {
    if (raw == -128) { previous = 0; return 0; }
    int value = raw;
    if (gain != 100) value = std::max(-127, std::min(127, (value * gain) / 100));
    if (slew > 0) value = previous + std::max(-slew, std::min(slew, value - previous));
    if (clamp > 0) value = std::max(-clamp, std::min(clamp, value));
    previous = value;
    return value;
}

inline int motor_level(int byte, bool invert = false) {
    if (byte == 0 || byte < -127 || byte > 127) return 0; // -128 is stop, not full force
    int magnitude = byte < 0 ? -byte : byte;
    int level = int(std::min(1.0, double(magnitude) / 126.0) * 32767.0 + .5);
    return ((byte > 0) != invert) ? -level : level;
}
}
