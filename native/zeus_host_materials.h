// SPDX-License-Identifier: BSD-3-Clause
// Private host materials. The caller provides a stable, current WaveRAM image.
#pragma once
#include "page_image.h"
#include <algorithm>
#include <map>

namespace cruisn { namespace zeus_host {
using WaveImage = PageImage<16777216, 4096>;
constexpr std::size_t max_palettes = 4096;
struct Palette {
    uint32_t base = 0, control = 0;
    std::array<uint32_t, 256> colors{};
};
struct PaletteSet {
    std::vector<Palette> rows;
    std::vector<uint32_t> instance_rows;
};

// Read RGB555 as explicit little-endian bytes. No palette-bank allowlist or
// inherited original-renderer row is used. Other palette layouts fail closed.
inline bool palette(const uint8_t *wave, std::size_t size, uint32_t base,
                    uint32_t control, Palette &output) {
    const uint64_t offset = uint64_t(base) * 8;
    if (!wave || size != 16777216 || control != 0x0084003f || offset + 512 > size)
        return false;
    Palette row;
    row.base = base; row.control = control;
    for (std::size_t i = 0; i < row.colors.size(); ++i) {
        const auto *p = wave + offset + i * 2;
        const uint32_t color = uint32_t(p[0]) | (uint32_t(p[1]) << 8);
        row.colors[i] = ((color & 0x7c00) << 9) | ((color & 0x3e0) << 6) | ((color & 0x1f) << 3);
    }
    output = row;
    return true;
}

template<class Instances>
bool palettes(const Instances &instances, const uint8_t *wave, std::size_t size, PaletteSet &output) {
    if (!wave || size != 16777216 || instances.size() > max_palettes) return false;
    PaletteSet result;
    std::map<std::pair<uint32_t, uint32_t>, uint32_t> indices;
    for (const auto &instance : instances) {
        const auto key = std::make_pair(instance.palette, instance.palette_control);
        auto found = indices.find(key);
        if (found == indices.end()) {
            Palette row;
            if (!palette(wave, size, key.first, key.second, row)) return false;
            found = indices.emplace(key, uint32_t(result.rows.size())).first;
            result.rows.push_back(row);
        }
        result.instance_rows.push_back(found->second);
    }
    output = std::move(result);
    return true;
}

// Native ring payload budget: full WaveRAM delta + every private palette +
// maximum raw scene geometry (131072 * 260 bytes) fits inside its 64 MiB limit.
constexpr std::size_t maximum_scene_bytes = 64 + WaveImage::maximum_packet_bytes +
    max_palettes * (8 + 256 * 4) + 131072 * (260 + 4);
static_assert(maximum_scene_bytes + 8 < (64u << 20), "whole host scene exceeds ring");

struct Packet {
    uint32_t frame = 0;
    uint64_t scene = 0;
    bool snapshot = false;
    WaveImage::Packet wave;
    std::vector<Palette> rows;
};
constexpr std::size_t packet_header_bytes = 32, palette_bytes = 1032;
constexpr std::size_t maximum_material_bytes = packet_header_bytes +
    WaveImage::maximum_packet_bytes + max_palettes * palette_bytes;

inline void put32(std::vector<uint8_t> &wire, uint32_t value) {
    for (unsigned i = 0; i < 4; ++i) wire.push_back(uint8_t(value >> (i * 8)));
}
inline uint32_t get32(const uint8_t *wire) {
    return uint32_t(wire[0]) | (uint32_t(wire[1]) << 8) |
        (uint32_t(wire[2]) << 16) | (uint32_t(wire[3]) << 24);
}
inline bool palette_shape(const Palette &row) {
    return row.control == 0x0084003f && uint64_t(row.base) * 8 + 512 <= 16777216;
}
inline bool encode(const Packet &packet, std::vector<uint8_t> &output) {
    if (!packet.scene || packet.frame < 1800 || packet.frame > 16001 || packet.rows.size() > max_palettes)
        return false;
    for (const auto &row : packet.rows) if (!palette_shape(row)) return false;
    std::vector<uint8_t> wave;
    if (!WaveImage::encode(packet.wave, wave)) return false;
    std::vector<uint8_t> wire;
    wire.reserve(packet_header_bytes + wave.size() + packet.rows.size() * palette_bytes);
    put32(wire, 0x31544d48); // HMT1: private material update, no draw commands
    put32(wire, packet.frame);
    put32(wire, uint32_t(packet.scene)); put32(wire, uint32_t(packet.scene >> 32));
    put32(wire, uint32_t(wave.size())); put32(wire, uint32_t(packet.rows.size()));
    put32(wire, packet.snapshot ? 1 : 0); put32(wire, 0);
    wire.insert(wire.end(), wave.begin(), wave.end());
    for (const auto &row : packet.rows) {
        put32(wire, row.base); put32(wire, row.control);
        for (auto color : row.colors) put32(wire, color);
    }
    output = std::move(wire);
    return true;
}
inline bool decode(const uint8_t *wire, std::size_t size, Packet &output) {
    if (!wire || size < packet_header_bytes || size > maximum_material_bytes ||
        get32(wire) != 0x31544d48 || get32(wire + 24) > 1 || get32(wire + 28)) return false;
    const uint32_t wave_bytes = get32(wire + 16), rows = get32(wire + 20);
    if (wave_bytes > WaveImage::maximum_packet_bytes || rows > max_palettes ||
        size != packet_header_bytes + std::size_t(wave_bytes) + std::size_t(rows) * palette_bytes)
        return false;
    Packet packet;
    packet.frame = get32(wire + 4);
    packet.scene = uint64_t(get32(wire + 8)) | (uint64_t(get32(wire + 12)) << 32);
    packet.snapshot = get32(wire + 24) != 0;
    if (!packet.scene || packet.frame < 1800 || packet.frame > 16001 ||
        !WaveImage::decode(wire + packet_header_bytes, wave_bytes, packet.wave)) return false;
    packet.rows.reserve(rows);
    for (std::size_t i = 0; i < rows; ++i) {
        const auto *data = wire + packet_header_bytes + wave_bytes + i * palette_bytes;
        Palette row;
        row.base = get32(data); row.control = get32(data + 4);
        if (!palette_shape(row)) return false;
        for (std::size_t j = 0; j < 256; ++j) row.colors[j] = get32(data + 8 + j * 4);
        packet.rows.push_back(row);
    }
    output = std::move(packet);
    return true;
}

// Validate colors against the proposed WaveRAM generation BEFORE modifying the
// consumer. Changed pages are owned by this packet; others use its exact baseline.
inline bool accept(const Packet &packet, WaveImage &image) {
    const auto &delta = packet.wave;
    if (delta.base != image.generation() || delta.base_hash != image.image_hash() ||
        packet.rows.size() > max_palettes) return false;
    for (std::size_t i = 0; i < delta.pages.size(); ++i)
        if (delta.pages[i].index >= WaveImage::page_count || (i && delta.pages[i-1].index >= delta.pages[i].index))
            return false;
    auto byte = [&](std::size_t offset, uint8_t &value) {
        const uint32_t page = uint32_t(offset / 4096);
        const auto found = std::lower_bound(delta.pages.begin(), delta.pages.end(), page,
            [](const WaveImage::Update &row, uint32_t index) { return row.index < index; });
        if (found != delta.pages.end() && found->index == page) value = found->bytes[offset % 4096];
        else if (offset < image.bytes().size()) value = image.bytes()[offset];
        else return false;
        return true;
    };
    for (const auto &row : packet.rows) {
        if (!palette_shape(row)) return false;
        for (std::size_t i = 0; i < 256; ++i) {
            const std::size_t offset = std::size_t(row.base) * 8 + i * 2;
            uint8_t low = 0, high = 0;
            if (!byte(offset, low) || !byte(offset + 1, high)) return false;
            const uint32_t c = uint32_t(low) | (uint32_t(high) << 8);
            if (row.colors[i] != (((c & 0x7c00) << 9) | ((c & 0x3e0) << 6) | ((c & 0x1f) << 3)))
                return false;
        }
    }
    return image.apply(delta);
}
}}
