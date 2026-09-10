// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

namespace cruisn {
// OpenGL supplies bottom-up, tightly packed BGR. Preserve that ordering and
// the existing 54-byte BMP header, adding only the required zero row padding.
// Reuse scratch between captures; encode before opening/truncating any file.
inline bool encode_capture_bitmap(int width, int height, const uint8_t *pixels,
    size_t bytes, std::vector<uint8_t> &scratch)
{
    if (width <= 0 || height <= 0 || !pixels) return false;
    const uint64_t tight = uint64_t(width) * 3;
    const uint64_t stride = (tight + 3) & ~uint64_t(3);
    const uint64_t image = stride * uint64_t(height);
    // Diagnostic captures have a bounded allocation, including header/padding.
    if (image + 54 > 512u * 1024u * 1024u || tight * uint64_t(height) != bytes)
        return false;
    scratch.resize(size_t(image + 54));
    std::memset(scratch.data(), 0, 54);
    scratch[0] = 'B'; scratch[1] = 'M';
    auto put32 = [&](size_t at, uint32_t value) {
        for (unsigned i = 0; i < 4; ++i) scratch[at + i] = uint8_t(value >> (8 * i));
    };
    put32(2, uint32_t(image + 54)); put32(10, 54); put32(14, 40);
    put32(18, uint32_t(width)); put32(22, uint32_t(height));
    scratch[26] = 1; scratch[28] = 24; put32(34, uint32_t(image));
    if (tight == stride) std::memcpy(scratch.data() + 54, pixels, bytes);
    else for (int y = 0; y < height; ++y) {
        uint8_t *row = scratch.data() + 54 + size_t(y) * size_t(stride);
        std::memcpy(row, pixels + size_t(y) * size_t(tight), size_t(tight));
        std::memset(row + tight, 0, size_t(stride - tight));
    }
    return true;
}

inline bool write_capture_bitmap(const char *path, int width, int height,
    const uint8_t *pixels, size_t bytes, std::vector<uint8_t> &scratch)
{
    if (!encode_capture_bitmap(width, height, pixels, bytes, scratch)) return false;
    FILE *file = std::fopen(path, "wb");
    if (!file) return false;
    // One bulk stdio write replaces a header plus one write per screen row.
    const bool written = std::fwrite(scratch.data(), 1, scratch.size(), file) == scratch.size();
    const bool closed = std::fclose(file) == 0;
    return written && closed;
}
} // namespace cruisn
