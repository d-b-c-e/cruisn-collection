#include "zeus_model_bounds.h"
#include <cassert>
#include <cstring>
#include <limits>
#include <iostream>

static uint32_t word(float f) { uint32_t w; std::memcpy(&w, &f, 4); return w; }
static uint32_t pair(int a, int b) { return uint16_t(a) | uint32_t(uint16_t(b)) << 16; }
int main()
{
    using namespace cruisn;
    const std::vector<uint32_t> quad = {0x38000000, 0, pair(-1, 1), pair(-1, -1),
        0, 0, 0, 0, pair(1, -1), pair(1, 1)};
    zeus_bounds::Bounds b;
    assert(zeus_bounds::prepare(quad, 10, b));
    assert(!b.empty && b.low[0] == -1 && b.high[0] == 1 && b.low[2] == 0);
    zeus_model::Context c;
    c.quad_size = 10; c.regs[0x66] = 0x8e; c.regs[0x68] = 0x9d; c.regs[0x6c] = 9;
    c.regs[0x6a] = word(256); c.regs[0x6b] = word(200); c.regs[0x78] = word(1);
    c.matrix = {{1, 0, 0, 0, 1, 0, 0, 0, 1}}; c.translation = {{0, 0, 100}};
    assert(!zeus_bounds::outside(b, c, 86));
    for (unsigned axis = 0; axis < 2; ++axis)
        for (float far : {-1000000.f, 1000000.f})
        {
            auto changed = c; changed.translation[axis] = far;
            assert(zeus_bounds::outside(b, changed, 86));
        }
    auto crossed = b; crossed.low[2] = -2; crossed.high[2] = 2;
    auto near = c; near.translation[2] = 1;
    assert(!zeus_bounds::outside(crossed, near, 86));
    near.translation[2] = -10;
    assert(zeus_bounds::outside(crossed, near, 86));
    near.translation[2] = std::numeric_limits<float>::infinity();
    assert(!zeus_bounds::outside(b, near, 86));
    assert(!zeus_bounds::outside(b, c, -1));
    assert(!zeus_bounds::outside(b, c, std::numeric_limits<float>::quiet_NaN()));
    auto invalid = quad; invalid.pop_back();
    assert(!zeus_bounds::prepare(invalid, 10, b));
    assert(!zeus_bounds::prepare(quad, 8, b));
    assert(!zeus_bounds::prepare({0x36660000, 0}, 10, b));
    assert(!zeus_bounds::prepare({0x36200000, 0x08000000}, 10, b));
    assert(zeus_bounds::prepare({}, 10, b) && b.empty);
    assert(zeus_bounds::outside(b, c, 86));
    assert(zeus_bounds::prepare(quad, 10, b));

    // Compare a conservative whole-model rejection with the existing exact
    // clipped polygon projector at viewport edges and the near plane.
    unsigned visible = 0, rejected = 0;
    for (int depth = -2; depth < 400; depth += 3)
        for (int x = -180; x <= 180; x += 3)
        {
            auto moved = c; moved.translation = {{float(x), float(x % 67), float(depth)}};
            const bool outside = zeus_bounds::outside(b, moved, 86);
            zeus_model::Result decoded;
            assert(zeus_model::decode(quad, moved, decoded));
            rejected += outside;
            for (const auto &q : decoded.quads)
            {
                float left = q.vertices[0][0], right = left, top = q.vertices[0][1], bottom = top;
                for (unsigned i = 1; i < q.state[1]; ++i)
                {
                    left = std::min(left, q.vertices[i][0]); right = std::max(right, q.vertices[i][0]);
                    top = std::min(top, q.vertices[i][1]); bottom = std::max(bottom, q.vertices[i][1]);
                }
                const bool onscreen = right >= -86 && left <= 598 && bottom >= 0 && top <= 400;
                visible += onscreen;
                assert(!onscreen || !outside);
            }
        }
    assert(visible && rejected);
    std::cout << "PASS viewport/near-plane bounds; visible=" << visible << " rejected=" << rejected << '\n';
}
