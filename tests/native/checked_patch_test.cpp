#include "checked_patch.h"
#include <cassert>
#include <array>

int main()
{
    std::array<uint32_t, 4> ram = {10, 20, 30, 40};
    const auto original = ram;
    size_t bad = 0;
    std::vector<cruisn::patch_word> p = {{0, 10, 99, true}, {2, 31, 88, true}};
    assert(!cruisn::apply_checked_patch(ram.data(), ram.size(), p, bad));
    assert(bad == 1 && ram == original); // first branch remains original
    p[1].oldval = 30;
    p[1].addr = 4;
    assert(!cruisn::apply_checked_patch(ram.data(), ram.size(), p, bad));
    assert(ram == original);
    p[1].addr = 0;
    p[1].oldval = 10;
    assert(!cruisn::apply_checked_patch(ram.data(), ram.size(), p, bad));
    assert(ram == original); // duplicate addresses are ambiguous, even guarded
    p[1].addr = 2;
    p[1].oldval = 30;
    assert(cruisn::apply_checked_patch(ram.data(), ram.size(), p, bad));
    assert(ram[0] == 99 && ram[2] == 88 && ram[1] == 20 && ram[3] == 40);
}
