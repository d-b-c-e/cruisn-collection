// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>
#include <algorithm>

namespace cruisn {
// Producer-thread display resource. Never writes into emulated texture memory.
class retained_texture {
    std::size_t start_ = 0;
    std::vector<uint8_t> bytes_;
public:
    bool active() const { return !bytes_.empty(); }
    bool capture(const uint8_t *source, std::size_t size, std::size_t start, std::size_t length) {
        if (active() || !source || !length || start > size || length > size - start)
            return false;
        start_ = start;
        bytes_.assign(source + start, source + start + length);
        return true;
    }
    bool apply(uint8_t *destination, std::size_t size) const {
        if (!active() || !destination || start_ > size || bytes_.size() > size - start_)
            return false;
        std::copy(bytes_.begin(), bytes_.end(), destination + start_);
        return true;
    }
    void release() { bytes_.clear(); }
};

// World 2.4's actual UI render-list root, guarded by its instruction words.
// A list header precedes the first object; model pointers are object word 13.
inline bool world24_transmission_visible(const uint32_t *ram, std::size_t words) {
    if (!ram || words < 0x20000 || ram[0x6f] != 0x082861ed || ram[0x70] != 0x6200034c)
        return false;
    const uint32_t head = ram[0x61ed];
    if (!head || head >= 0x20000) return false;
    uint32_t object = ram[head];
    for (unsigned count = 0; object && count < 256; ++count) {
        if (object >= 0x1ffe0) return false;
        const uint32_t model = ram[object + 13];
        if (model == 0xfd70c1 || model == 0xfd763c || model == 0xfd76b3 || model == 0xfd778c)
            return true;
        object = ram[object];
    }
    return false;
}
}
