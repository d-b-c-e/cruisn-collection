#pragma once
#include <algorithm>
#include <cstdint>
#include <vector>

namespace cruisn {
// Consecutive CPU writes may be combined only until the next ordered message.
// Track every touched pixel: filling a bounding rectangle would overwrite GPU
// quad pixels in untouched holes with stale CPU-shadow data.
class cpu_upload_spans {
public:
    cpu_upload_spans(unsigned width, unsigned height)
        : width_(width), size_(width * height), dirty_(2 * size_, 0), first_{size_,size_} {}

    void mark(unsigned page, unsigned first, unsigned count) {
        if (page > 1 || first >= size_ || !count) return;
        unsigned const end = first + std::min(count, size_ - first);
        std::fill(dirty_.begin() + page * size_ + first,
                  dirty_.begin() + page * size_ + end, uint8_t(1));
        first_[page] = std::min(first_[page], first);
        end_[page] = std::max(end_[page], end);
    }

    bool pending(unsigned page) const { return first_[page] < end_[page]; }
    const uint8_t *mask(unsigned page) const { return dirty_.data() + page * size_; }
    void clear(unsigned page) {
        if (!pending(page)) return;
        std::fill(dirty_.begin() + page * size_ + first_[page],
                  dirty_.begin() + page * size_ + end_[page], uint8_t(0));
        first_[page] = size_;
        end_[page] = 0;
    }

    template <typename Upload> void flush(Upload upload) {
        for (unsigned page = 0; page < 2; ++page) {
            auto *bits = dirty_.data() + page * size_;
            unsigned at = first_[page];
            while (at < end_[page]) {
                if (!bits[at]) { ++at; continue; }
                unsigned const start = at;
                unsigned const row_end = std::min(end_[page], (at / width_ + 1) * width_);
                while (at < row_end && bits[at]) bits[at++] = 0;
                upload(page, start, at - start);
            }
            first_[page] = size_;
            end_[page] = 0;
        }
    }
private:
    unsigned width_, size_;
    std::vector<uint8_t> dirty_;
    unsigned first_[2], end_[2] = {};
};
}
