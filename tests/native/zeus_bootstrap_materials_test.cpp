// SPDX-License-Identifier: BSD-3-Clause
#include "zeus_wide_packet.h"
#include "zeus_margin_packet.h"
#include "zeus_retained_materials.h"
#include <cassert>
#include <vector>
int main() {
    using namespace cruisn;using namespace zeus_host;
    const auto ready=FramePolicy::guest_ready;
    WaveImage image;std::vector<uint8_t> wave(16777216);
    Packet seed;seed.frame=5000;seed.scene=1;
    assert(image.stage(wave.data(),wave.size(),seed.wave) && image.apply(seed.wave));
    Packet p;p.frame=1385;p.scene=2;
    assert(!retain(p,image));assert(retain(p,image,ready));
    assert(!retained_shape(p,image) && retained_shape(p,image,ready));
    std::vector<uint8_t> bytes{42},copy;Packet decoded;
    assert(!encode(p,bytes) && bytes==std::vector<uint8_t>{42});
    assert(encode(p,bytes,ready));
    assert(!decode(bytes.data(),bytes.size(),decoded));assert(decode(bytes.data(),bytes.size(),decoded,ready));
    assert(encode(decoded,copy,ready) && copy==bytes);
    zeus_wide::Packet wide;wide.materials=p;wide.margin=88;wide.multiplier=2;
    zeus_wide::Packet wd;assert(!zeus_wide::encode(wide,copy));assert(zeus_wide::encode(wide,copy,ready));
    assert(!zeus_wide::decode(copy.data(),copy.size(),wd));assert(zeus_wide::decode(copy.data(),copy.size(),wd,ready));
    zeus_margin::Packet margin;margin.materials=p;margin.margin=88;
    zeus_margin::Packet md;assert(!zeus_margin::encode(margin,copy));assert(zeus_margin::encode(margin,copy,ready));
    assert(!zeus_margin::decode(copy.data(),copy.size(),md));assert(zeus_margin::decode(copy.data(),copy.size(),md,ready));
    for(uint32_t frame:{0u,16002u,UINT32_MAX}) {
        p.frame=frame;assert(!encode(p,copy,ready) && !retain(p,image,ready));
    }
    for(uint32_t frame:{1800u,5000u,16001u}) {
        p.frame=frame;assert(encode(p,bytes) && encode(p,copy,ready) && bytes==copy);
    }
    p.frame=1385;const auto hash=image.image_hash();
    assert(!accept_retained(p,image) && image.generation()==1);
    assert(accept_retained(p,image,ready) && image.generation()==2 && image.image_hash()==hash);
    assert(!accept_retained(p,image,ready));
    assert(!frame_valid(1385,static_cast<FramePolicy>(99)));
    // The same packet layout is used after the former diagnostic upper bound.
    const auto runtime=FramePolicy::continuous;
    for(uint32_t frame:{1u,1385u,1800u,16001u,16002u,1000000u,UINT32_MAX}) {
        p.frame=frame;p.scene=3;
        assert(retain(p,image,runtime));
        assert(encode(p,bytes,runtime) && decode(bytes.data(),bytes.size(),decoded,runtime));
        assert(decoded.frame==frame && encode(decoded,copy,runtime) && bytes==copy);
        if(frame>=1800 && frame<=16001)assert(encode(p,copy) && copy==bytes);
        else assert(!decode(bytes.data(),bytes.size(),decoded));
        wide.materials=p;margin.materials=p;
        assert(zeus_wide::encode(wide,copy,runtime) && zeus_wide::decode(copy.data(),copy.size(),wd,runtime));
        assert(wd.materials.frame==frame);
        assert(zeus_margin::encode(margin,copy,runtime) && zeus_margin::decode(copy.data(),copy.size(),md,runtime));
        assert(md.materials.frame==frame);
    }
    p.frame=0;assert(!retain(p,image,runtime) && !encode(p,copy,runtime));
}
