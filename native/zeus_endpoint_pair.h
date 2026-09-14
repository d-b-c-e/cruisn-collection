// SPDX-License-Identifier: BSD-3-Clause
// Original/private quad pair at the SAME command position. The consumer draws
// the original only to its normal target and the replacement only to the private
// target, using the unchanged material bindings at this exact stream position.
#pragma once
#include "zeus_model.h"
namespace cruisn { namespace zeus_endpoint_pair {
struct Pair {
    uint32_t frame=0,model=0,index=0,count=0;
    zeus_model::Quad original,replacement;
};
inline bool valid(const Pair &p) {
    const auto &a=p.original,&b=p.replacement;
    if(!p.frame || !p.model || !p.count || p.count>131072 || p.index>=p.count ||
            a.state[0]!=b.state[0] || (a.state[0] && a.state[0]!=p.frame) ||
            a.state[1]<3 || a.state[1]>8 || (a.state[11]!=0 && a.state[11]!=400) ||
            a.state[7]>256 || a.state[8]>256 || b.state[7]>256 || b.state[8]>256 ||
            std::memcmp(a.vertices.data(),b.vertices.data(),sizeof(a.vertices)) || (a.state[9]^b.state[9])&~2U)return false;
    for(unsigned j=0;j<17;++j)if((j<7 || j>10) && a.state[j]!=b.state[j])return false;
    for(const auto &v:a.vertices)for(float f:v)if(!std::isfinite(f))return false;
    return true;
}
// Explicit little-endian word header followed by the existing 260-byte quads.
// The supported host already uses this quad representation for its normal stream.
inline bool encode(const Pair &p,std::array<uint8_t,544> &out) {
    static_assert(sizeof(zeus_model::Quad)==260,"quad ABI");
    if(!valid(p))return false;
    const uint32_t header[]={0x3150455a,p.frame,p.model,p.index,p.count,0};
    std::array<uint8_t,544> encoded{};
    for(unsigned i=0;i<6;++i)for(unsigned j=0;j<4;++j)encoded[i*4+j]=uint8_t(header[i]>>(j*8));
    std::memcpy(encoded.data()+24,&p.original,260);std::memcpy(encoded.data()+284,&p.replacement,260);
    out=encoded;return true;
}
inline bool decode(const uint8_t *data,size_t size,Pair &out) {
    if(!data || size!=544)return false;
    uint32_t h[6]={};for(unsigned i=0;i<6;++i)for(unsigned j=0;j<4;++j)h[i]|=uint32_t(data[i*4+j])<<(8*j);
    if(h[0]!=0x3150455a || h[5])return false;
    Pair p;p.frame=h[1];p.model=h[2];p.index=h[3];p.count=h[4];
    std::memcpy(&p.original,data+24,260);std::memcpy(&p.replacement,data+284,260);
    if(!valid(p))return false;
    out=p;return true;
}
class Order {
    uint32_t m_frame=0,m_model=0,m_next=0,m_count=0;
    bool m_pending=false;
    Pair m_pair;
public:
    bool complete()const{return !m_pending && m_next==m_count;}
    // A pair cannot be superseded or cross another model before its normal quad.
    bool expect(const Pair &p) {
        if(m_pending || !valid(p) || p.frame<m_frame)return false;
        if(p.model==m_model) {if(p.frame!=m_frame || p.count!=m_count || p.index!=m_next)return false;}
        else if(p.model<m_model || !complete() || p.index)return false;
        m_frame=p.frame;m_model=p.model;m_count=p.count;m_next=p.index;m_pair=p;m_pending=true;return true;
    }
    bool consume(const zeus_model::Quad &actual,zeus_model::Quad &replacement) {
        if(!m_pending || std::memcmp(&actual,&m_pair.original,sizeof(actual)))return false;
        replacement=m_pair.replacement;m_pending=false;++m_next;return true;
    }
    bool pending()const{return m_pending;}
};
} }
