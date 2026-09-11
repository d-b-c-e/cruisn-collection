// SPDX-License-Identifier: BSD-3-Clause
// Proposal-owned materials for a later private draw; no live memory access.
#pragma once
#include "zeus_host_materials.h"

namespace cruisn { namespace zeus_host {
// A later draw may advance the packet sequence while retaining the exact
// proposal-time image. It owns its palette colors, carries no replacement
// pages, and cannot accept a newer live image as an equivalent baseline.
// The caller separately enforces scene/frame/page ordering and one completion
// per proposal; this helper cannot identify a device command fence.
inline bool retained_shape(const Packet &packet, const WaveImage &image) {
    const auto &delta = packet.wave;
    return packet.scene && packet.frame >= 1800 && packet.frame <= 16001 &&
        image.generation() && image.generation() != UINT64_MAX &&
        delta.base == image.generation() && delta.generation == delta.base + 1 &&
        delta.base_hash == image.image_hash() && delta.result_hash == delta.base_hash &&
        !delta.full && delta.pages.empty();
}
inline bool retain(Packet &packet, const WaveImage &image) {
    if (!packet.scene || packet.frame < 1800 || packet.frame > 16001 ||
        !image.generation() || image.bytes().size() != 16777216) return false;
    WaveImage::Packet delta;
    if (!image.stage_selected_pages(image.bytes().data(), image.bytes().size(), {}, delta)) return false;
    // Validate palette bytes before exposing a usable packet to the caller.
    if (packet.rows.size() > max_palettes) return false;
    for (const auto &row : packet.rows) {
        Palette expected;
        if (!palette(image.bytes().data(), image.bytes().size(), row.base, row.control, expected) ||
            row.colors != expected.colors) return false;
    }
    packet.wave = std::move(delta);
    return true;
}
inline bool accept_retained(const Packet &packet, WaveImage &image) {
    return retained_shape(packet, image) && accept(packet, image);
}
}}
