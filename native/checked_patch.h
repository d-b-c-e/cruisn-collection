// SPDX-License-Identifier: BSD-3-Clause
// Collection-owned helper; synchronize to MAME with harness/sync_native.py.
#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>

namespace cruisn {
struct patch_word {
    uint32_t addr, oldval, newval;
    bool guarded;
};

// Validate the entire group before its first write. A bad later word must
// never leave a branch pointing into an incompletely installed trampoline.
inline bool apply_checked_patch(uint32_t *ram, size_t words,
                               const std::vector<patch_word> &patch,
                               size_t &bad_entry)
{
    for (size_t i = 0; i < patch.size(); ++i) {
        const auto &p = patch[i];
        if (p.addr >= words || (p.guarded && ram[p.addr] != p.oldval)) {
            bad_entry = i;
            return false;
        }
        for (size_t j = 0; j < i; ++j)
            if (patch[j].addr == p.addr) {
                bad_entry = i;
                return false;
            }
    }
    for (const auto &p : patch) ram[p.addr] = p.newval;
    return true;
}
}
