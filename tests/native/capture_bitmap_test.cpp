#include "capture_bitmap.h"
#include <cassert>
#include <climits>
#include <array>
#include <algorithm>
#include <utility>

int main()
{
    std::vector<uint8_t> encoded;
    const uint8_t pixels[] = {1, 2, 3, 4, 5, 6};
    // Independent complete file fixture: two bottom-up rows, one pixel each.
    const std::array<uint8_t, 62> expected = {
        66,77,62,0,0,0,0,0,0,0,54,0,0,0,40,0,0,0,1,0,0,0,2,0,0,0,
        1,0,24,0,0,0,0,0,8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        1,2,3,0,4,5,6,0};
    assert(cruisn::encode_capture_bitmap(1, 2, pixels, sizeof(pixels), encoded));
    assert(encoded.size() == expected.size());
    assert(std::equal(encoded.begin(), encoded.end(), expected.begin()));
    const auto original = encoded;
    for (auto dimensions : {std::pair<int,int>{0,2}, {-1,2}, {1,0}, {1,-2}, {INT_MAX,INT_MAX}}) {
        assert(!cruisn::encode_capture_bitmap(dimensions.first, dimensions.second, pixels, 6, encoded));
        assert(encoded == original);
    }
    assert(!cruisn::encode_capture_bitmap(1, 2, nullptr, 6, encoded));
    assert(!cruisn::encode_capture_bitmap(1, 2, pixels, 5, encoded));
    assert(!cruisn::encode_capture_bitmap(1, 2, pixels, 7, encoded));
    assert(encoded == original);
    // Reused, dirty scratch exercises every padding size and aligned bulk path.
    for (int width : {1, 2, 3, 4, 512, 513, 1279, 1921, 3825, 3840}) {
        const int height = 7;
        std::vector<uint8_t> input(size_t(width) * height * 3);
        for (size_t i = 0; i < input.size(); ++i) input[i] = uint8_t(i * 19 + i / 23);
        std::fill(encoded.begin(), encoded.end(), 0xcc);
        assert(cruisn::encode_capture_bitmap(width, height, input.data(), input.size(), encoded));
        const size_t stride = (width * 3 + 3) / 4 * 4;
        assert(encoded.size() == 54 + stride * height);
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width * 3; ++x)
                assert(encoded[54 + y * stride + x] == input[size_t(y) * width * 3 + x]);
            for (size_t x = width * 3; x < stride; ++x) assert(encoded[54 + y * stride + x] == 0);
        }
    }
}
