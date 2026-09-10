// SPDX-License-Identifier: BSD-3-Clause
// Conservative byte residency checks for an owned old Zeus scene.
#pragma once
#include "zeus_model.h"
#include <limits>
namespace cruisn { namespace zeus_lease {
constexpr size_t wave_bytes=16777216,page_bytes=4096;
class Coverage {
    std::array<bool,wave_bytes/page_bytes> used_{};
    size_t work_=0;
    bool full_=false;
    void all(){used_.fill(true);full_=true;}
    void span(size_t offset,size_t bytes) {
        for(size_t p=offset/page_bytes;p<=(offset+bytes-1)/page_bytes;++p) {
            used_[p]=true;
            if(++work_>=262144){all();return;}
        }
    }
    static int64_t offset(unsigned flags,unsigned type,int64_t x,int64_t y,int64_t w) {
        if(flags&(64|128))return 2*((y/2)*(w*2)+(x/2)*4+(y%2)*2+x%2);
        if(type==0)return (y/4)*(w*4)+(x/4)*8+(y%4)*2+(x/2)%2;
        if(type==1)return (y/2)*(w*2)+(x/4)*8+(y%2)*4+x%4;
        return (y/4)*(w*4)+(x/2)*8+(y%4)*2+x%2;
    }
public:
    // Positive perspective weights bound the UV ratio by vertex extrema.
    // Clamp negative coordinates as the real shader does; include bilinear
    // neighbors and two texels of rounding padding. Large UVs conservatively
    // require the entire image, rather than pretending this padding is exact.
    bool add(const zeus_model::Quad &q) {
        if(q.state[1]<3 || q.state[1]>8)return false;
        const auto flags=q.state[9];if(full_ || flags&(1|256))return true;
        const auto width=q.state[4];
        if(width<16 || width>256 || (width&(width-1)))return false;
        double lo[2]={std::numeric_limits<double>::infinity(),std::numeric_limits<double>::infinity()};
        double hi[2]={-lo[0],-lo[1]};bool large=false;
        for(unsigned i=0;i<q.state[1];++i) {
            const auto &v=q.vertices[i];
            if(!std::isfinite(v[5]) || v[5]<=0)return false;
            for(unsigned c=0;c<2;++c) {
                const double uv=double(v[3+c])/double(v[5])/256.;
                if(!std::isfinite(uv))return false;
                large=large || std::abs(uv)>65536.;
                lo[c]=std::min(lo[c],uv);hi[c]=std::max(hi[c],uv);
            }
        }
        if(large){all();return true;}
        int64_t minimum[2],maximum[2];
        for(unsigned c=0;c<2;++c) {
            minimum[c]=int64_t(std::max(0.,std::floor(lo[c])-2.));
            maximum[c]=int64_t(std::max(1.,std::ceil(hi[c])+2.));
        }
        // Every swizzle is monotone in nonnegative x/y for supported widths.
        // The contiguous range includes row gaps; extra pages are acceptable.
        const auto first=offset(flags,q.state[2]&3,minimum[0],minimum[1],width);
        const auto last=offset(flags,q.state[2]&3,maximum[0],maximum[1],width)+((flags&(64|128))?1:0);
        if(first<0 || last<first)return false;
        const uint64_t bytes=uint64_t(last-first)+1;
        if(bytes>=wave_bytes){all();return true;}
        const size_t start=size_t((uint64_t(q.state[3])*8+uint64_t(first))&(wave_bytes-1));
        const size_t n=std::min(size_t(bytes),wave_bytes-start);
        span(start,n);if(!full_ && n<bytes)span(0,size_t(bytes)-n);
        return true;
    }
    const std::array<bool,wave_bytes/page_bytes> &pages()const{return used_;}
    size_t count()const{return std::count(used_.begin(),used_.end(),true);}
    bool equal(const uint8_t *sealed,const uint8_t *ready,size_t bytes)const {
        if(!sealed || !ready || bytes!=wave_bytes)return false;
        for(size_t p=0;p<used_.size();++p)
            if(used_[p] && std::memcmp(sealed+p*page_bytes,ready+p*page_bytes,page_bytes))return false;
        return true;
    }
};
inline bool model_equal(const uint8_t *sealed,const uint8_t *ready,size_t bytes,uint32_t base,uint32_t count) {
    const uint64_t offset=8*(uint64_t(base%1024)+uint64_t((base>>16)%2048)*1024),size=8*(uint64_t(count)+1);
    return sealed && ready && bytes==wave_bytes && count<=0xc800 && offset<bytes && size<=bytes-offset &&
        std::memcmp(sealed+offset,ready+offset,size)==0;
}
inline bool palette_equal(const uint8_t *sealed,const uint8_t *ready,size_t bytes,uint32_t base) {
    const uint64_t offset=uint64_t(base)*8;
    return sealed && ready && bytes==wave_bytes && offset+512<=bytes &&
        std::memcmp(sealed+offset,ready+offset,512)==0;
}
} }
