// license:BSD-3-Clause
#pragma once
#include <array>

namespace cruisn {
// Rows referenced by CPU-side vertex batches must survive until GL draw
// commands have been issued. Uploading over a live row requires a draw first.
struct zeus_palette_lifetime {
    std::array<bool,256> pending{};
    void use(unsigned slot) { pending[slot & 255] = true; }
    bool conflicts(unsigned slot) const { return pending[slot & 255]; }
    void clear() { pending.fill(false); }
};
}
