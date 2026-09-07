// SPDX-License-Identifier: BSD-3-Clause
// Collection-owned World 2.4 scenery policy. No guest memory writes.
#pragma once
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace cruisn { namespace world_scenery {
constexpr uint32_t original_far = 80000, extended_far = 160000;
constexpr uint32_t reciprocal_base = 0xb66f, first_extra = 5000, last_extra = 10000;
enum kind { other, mountain, tree, forest };

inline kind classify(uint32_t model, uint32_t flags, uint32_t radius)
{
    flags &= 0x7fffffff; // verified per-instance state bit, not a model class
    if (flags == 0x1000 && ((model == 0xcb15f8 && radius == 33292)
        || (model == 0xcb171e && radius == 31514)
        || (model == 0xcb1a8b && radius == 26031)
        || (model == 0xcb2314 && radius == 19772)
        || (model == 0xcb21a2 && radius == 12790))) return mountain;
    // Grouped forest strip uses the original clamped projection, like mountains.
    // It is not a small tree card and must never enter the virtual fast path.
    if (flags == 0x1000 && model == 0xcb2375 && radius == 10935) return forest;
    if (flags == 0x1008 && (((model == 0xca57f3 || model == 0xca5833) && radius == 1950)
        || (model == 0xca5863 && radius == 818)
        || (model == 0xca5896 && radius == 1252))) return tree;
    return other;
}

inline bool enabled(kind type, unsigned mode)
{
    return (type == mountain && (mode & 1))
        || ((type == tree || type == forest) && (mode & 2));
}

inline bool code_matches(const uint32_t *ram, size_t words)
{
    return words >= 0x20000 && ram[0x40] == original_far && ram[0x4d] == reciprocal_base
        && (ram[0x9c] >> 16) == 0x1529 && ram[0xa0] == 0x04a30040 && ram[0xa8] == 0x04a30040
        && ram[0xae] == 0x04e31387 && ram[0xaf] == 0x54e31387
        && ram[0x13a] == 0x04f21387 && ram[0x13b] == 0x55721387
        && ram[0x14d] == 0x04f21387 && ram[0x14e] == 0x55721387
        && ram[0x199] == 0x04f21387 && ram[0x19a] == 0x55721387
        && ram[0x677] == 0x04f21387 && ram[0x678] == 0x55721387
        && ram[0x21b] == 0x24c00182 && ram[0x21d] == 0xde180b82;
}

// Keep every originally admitted object on its original path. For new trees,
// depth-radius <= far-2*radius-16 guarantees depth+radius <= far-16.
inline uint32_t admission(kind type, int32_t depth_minus_radius, uint32_t radius)
{
    if (depth_minus_radius <= int32_t(original_far)) return original_far;
    if (type == mountain || type == forest) return extended_far; // original clamped perspective
    if (type == tree && radius > 0 && radius <= 2000) return extended_far - 2 * radius - 16;
    return original_far;
}

inline bool projection_pc(uint32_t pc)
{
    return pc == 0x1df || pc == 0x1e3 || pc == 0x1ea || pc == 0x1ec || pc == 0x21c || pc == 0x21e;
}

inline uint32_t reciprocal(uint32_t index)
{
    // Match the measured far-table generation, leaving existing entries exact.
    // The caller bounds the virtual extension; unsupported indices return zero.
    if (index < first_extra || index > last_extra) return 0;
    float value = float(std::floor(512.0 / (16 * index + 1) * 1000000 + 0.5) / 1000000);
    uint32_t ieee;
    std::memcpy(&ieee, &value, sizeof(ieee));
    return ((((ieee >> 23) - 127) & 255) << 24) | (ieee & 0x7fffff);
}
} }
