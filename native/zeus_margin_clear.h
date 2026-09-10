// license:BSD-3-Clause
#pragma once
#include <cstdint>
#include <algorithm>

namespace cruisn {
struct zeus_margin_span { uint32_t row, count; bool expanded; };

// Enhanced canvas only. The guest sometimes clears the road's lower rows,
// leaving old geometry/depth in the upper widescreen margins. Expand to the
// same known 400-row page, never the other page or the guest's 512-wide center.
// Keep unknown/unaligned/spanning clear layouts on the legacy path.
inline zeus_margin_span zeus_margin_clear(uint32_t address, uint32_t pixels, bool page_clear)
{
    constexpr uint32_t width=512, height=1024, page_height=400;
    const uint32_t start=address & (width*height-1);
    const uint32_t row=start/width;
    const uint32_t count=std::min(pixels/width,height-row);
    zeus_margin_span span{row,count,false};
    if (!page_clear || start%width || pixels%width || !count || pixels>width*height)
        return span;
    const uint32_t page=(row/page_height)*page_height;
    if (page>=2*page_height || pixels/width>page+page_height-row)
        return span;
    span.expanded=row!=page || count!=page_height;
    span.row=page; span.count=page_height;
    return span;
}
}
