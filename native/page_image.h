// SPDX-License-Identifier: BSD-3-Clause
// Owned, bounded image deltas for a delayed consumer. No guest or GPU access.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <utility>
#include <vector>

namespace cruisn {
template<std::size_t Bytes, std::size_t PageSize> class PageImage {
    static_assert(PageSize > 0 && Bytes > 0 && Bytes % PageSize == 0, "image dimensions");
    static_assert(Bytes <= UINT32_MAX, "wire image size");
public:
    static constexpr std::size_t page_count = Bytes / PageSize;
    static constexpr std::size_t header_bytes = 64;
    static constexpr std::size_t maximum_packet_bytes = header_bytes + page_count * (4 + PageSize);
    struct Update {
        uint32_t index = 0;
        std::array<uint8_t, PageSize> bytes{};
    };
    struct Packet {
        uint64_t base = 0, generation = 0, base_hash = 0, result_hash = 0;
        bool full = false;
        std::vector<Update> pages;
    };

    uint64_t generation() const { return generation_; }
    uint64_t image_hash() const { return root_hash_; }
    const std::vector<uint8_t> &bytes() const { return bytes_; }

    // Staging never advances the baseline. The caller must enqueue the WHOLE
    // owned scene successfully before committing its matching producer delta.
    // Source bytes must be stable for this call; no pointers escape it.
    bool stage(const uint8_t *source, std::size_t size, Packet &output) const {
        if (!source || size != Bytes || generation_ == UINT64_MAX) return false;
        Packet packet;
        packet.base = generation_;
        packet.generation = generation_ + 1;
        packet.full = generation_ == 0;
        packet.base_hash = packet.result_hash = root_hash_;
        for (std::size_t i = 0; i < page_count; ++i) {
            const auto *data = source + i * PageSize;
            if (packet.full || std::memcmp(data, bytes_.data() + i * PageSize, PageSize)) {
                Update update;
                update.index = uint32_t(i);
                std::memcpy(update.bytes.data(), data, PageSize);
                packet.result_hash ^= (packet.full ? 0 : page_hashes_[i]) ^ page_hash(update);
                packet.pages.push_back(std::move(update));
            }
        }
        output = std::move(packet);
        return true;
    }

    // Caller must report EVERY written page. Initial image remains full.
    // Missing marks cannot be inferred; validate each live writer separately.
    bool stage_selected_pages(const uint8_t *source, std::size_t size,
                              const std::vector<uint32_t> &dirty, Packet &output) const {
        if (!source || size != Bytes || generation_ == UINT64_MAX || dirty.size() > page_count) return false;
        for (std::size_t i=0;i<dirty.size();++i)
            if (dirty[i]>=page_count || (i && dirty[i-1]>=dirty[i])) return false;
        if (!generation_) return stage(source,size,output);
        Packet packet;
        packet.base=generation_;packet.generation=generation_+1;
        packet.base_hash=packet.result_hash=root_hash_;
        for (auto i:dirty) {
            const auto *data=source+std::size_t(i)*PageSize;
            if (std::memcmp(data,bytes_.data()+std::size_t(i)*PageSize,PageSize)) {
                Update update;update.index=i;
                std::memcpy(update.bytes.data(),data,PageSize);
                packet.result_hash^=page_hashes_[i]^page_hash(update);
                packet.pages.push_back(std::move(update));
            }
        }
        output=std::move(packet);return true;
    }

    bool apply(const Packet &packet) {
        if (!structure(packet) || generation_ == UINT64_MAX || packet.base != generation_ ||
            packet.generation != generation_ + 1 || packet.base_hash != root_hash_ ||
            packet.full != (generation_ == 0)) return false;
        uint64_t expected = root_hash_;
        std::vector<uint64_t> incoming;
        incoming.reserve(packet.pages.size());
        for (const auto &update : packet.pages) {
            const auto hash = page_hash(update);
            incoming.push_back(hash);
            expected ^= (packet.full ? 0 : page_hashes_[update.index]) ^ hash;
        }
        if (expected != packet.result_hash) return false;
        // Validate every page before changing any byte or advancing generation.
        if (packet.full) bytes_.resize(Bytes);
        for (std::size_t i = 0; i < packet.pages.size(); ++i) {
            const auto &update = packet.pages[i];
            std::memcpy(bytes_.data() + std::size_t(update.index) * PageSize,
                        update.bytes.data(), PageSize);
            page_hashes_[update.index] = incoming[i];
        }
        root_hash_ = expected;
        generation_ = packet.generation;
        return true;
    }

    // PIM1: little-endian dimensions/count, four 64-bit sequence/hash fields,
    // flags, three zero words, then sorted (index, full page bytes) records.
    // Exact length is required; this parser never trusts a count for allocation.
    static bool encode(const Packet &packet, std::vector<uint8_t> &output) {
        if (!structure(packet)) return false;
        std::vector<uint8_t> wire;
        wire.reserve(header_bytes + packet.pages.size() * (4 + PageSize));
        put(wire, 0x314d4950, 4);
        put(wire, Bytes, 4);
        put(wire, PageSize, 4);
        put(wire, packet.pages.size(), 4);
        put(wire, packet.base, 8);
        put(wire, packet.generation, 8);
        put(wire, packet.base_hash, 8);
        put(wire, packet.result_hash, 8);
        put(wire, packet.full ? 1 : 0, 4);
        put(wire, 0, 4); put(wire, 0, 4); put(wire, 0, 4);
        for (const auto &page : packet.pages) {
            put(wire, page.index, 4);
            wire.insert(wire.end(), page.bytes.begin(), page.bytes.end());
        }
        output = std::move(wire);
        return true;
    }

    static bool decode(const uint8_t *wire, std::size_t size, Packet &output) {
        if (!wire || size < header_bytes || size > maximum_packet_bytes ||
            get(wire, 4) != 0x314d4950 || get(wire + 4, 4) != Bytes ||
            get(wire + 8, 4) != PageSize || get(wire + 48, 4) > 1 ||
            get(wire + 52, 4) || get(wire + 56, 4) || get(wire + 60, 4)) return false;
        const auto count = get(wire + 12, 4);
        if (count > page_count || size != header_bytes + count * (4 + PageSize)) return false;
        Packet packet;
        packet.base = get(wire + 16, 8);
        packet.generation = get(wire + 24, 8);
        packet.base_hash = get(wire + 32, 8);
        packet.result_hash = get(wire + 40, 8);
        packet.full = get(wire + 48, 4) != 0;
        packet.pages.reserve(std::size_t(count));
        for (std::size_t i = 0; i < count; ++i) {
            const auto *data = wire + header_bytes + i * (4 + PageSize);
            Update update;
            update.index = uint32_t(get(data, 4));
            std::memcpy(update.bytes.data(), data + 4, PageSize);
            packet.pages.push_back(std::move(update));
        }
        if (!structure(packet)) return false;
        output = std::move(packet);
        return true;
    }

private:
    static bool structure(const Packet &packet) {
        if (packet.base == UINT64_MAX || packet.generation != packet.base + 1 ||
            packet.full != (packet.base == 0) || (packet.full && packet.base_hash) ||
            packet.pages.size() > page_count || (packet.full && packet.pages.size() != page_count))
            return false;
        uint32_t previous = 0;
        bool first = true;
        for (const auto &page : packet.pages) {
            if (page.index >= page_count || (!first && page.index <= previous)) return false;
            previous = page.index;
            first = false;
        }
        return true;
    }
    // Diagnostic corruption detection, not cryptographic authentication.
    // Include page position so an identical page at another index differs.
    static uint64_t page_hash(const Update &update) {
        uint64_t hash = UINT64_C(14695981039346656037);
        for (unsigned i = 0; i < 4; ++i)
            hash = (hash ^ uint8_t(update.index >> (i * 8))) * UINT64_C(1099511628211);
        for (auto byte : update.bytes) hash = (hash ^ byte) * UINT64_C(1099511628211);
        return hash;
    }
    static void put(std::vector<uint8_t> &wire, uint64_t value, unsigned size) {
        for (unsigned i = 0; i < size; ++i) wire.push_back(uint8_t(value >> (i * 8)));
    }
    static uint64_t get(const uint8_t *wire, unsigned size) {
        uint64_t value = 0;
        for (unsigned i = 0; i < size; ++i) value |= uint64_t(wire[i]) << (i * 8);
        return value;
    }
    std::array<uint64_t, page_count> page_hashes_{};
    uint64_t root_hash_ = 0, generation_ = 0;
    std::vector<uint8_t> bytes_;
};
}
