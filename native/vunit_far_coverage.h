// SPDX-License-Identifier: BSD-3-Clause
// Coverage-only far-plane prototype for the explicitly gated private renderer.
// Preserve the original quad and its UV interpolation; clip only pixel coverage.
// Inputs are the renderer's inclusive screen corners and positive camera depths.
// Reciprocal-depth interpolation approximates the quantized V-Unit projection;
// this is not a reconstruction of the game's own clipping routine.
#pragma once
#include <array>
#include <cmath>
#include <cstdint>
#include <cstddef>

namespace cruisn { namespace vunit_far {
using Point=std::array<float,2>;
// Shader layout: count (-1 reject, 0 unchanged, 3..6 clipped), three padding
// floats, then six screen points. No palette, texture, owner or target identity.
using Mask=std::array<float,16>;
struct Input { uint32_t far=0;std::array<uint32_t,4> words{}; };
static_assert(sizeof(Input)==20,"far coverage input layout");
struct Packet {
    uint32_t frame=0;uint16_t pc=0,pad=0;uint16_t dma[16]{};Input coverage;
};
static_assert(offsetof(Packet,coverage)==40 && sizeof(Packet)==60,"far quad wire layout");
// Wire inputs currently permit only the independently screened World 3x range.
// Positive normal C31 depths convert exactly to double, without emulated flags.
inline bool decode(const Input &input,std::array<double,4> &depths)
{
    depths={};if(input.far!=240000)return false;
    std::array<double,4> values{};unsigned inside=0;
    for(unsigned i=0;i<4;++i) {
        const uint32_t w=input.words[i];const int e=int8_t(w>>24);
        if((w&0x800000) || e<9 || e>18)return false;
        values[i]=std::ldexp(double((w&0x7fffff)|0x800000),e-23);
        if(values[i]<1000 || values[i]>=480000)return false;
        inside+=values[i]<input.far;
    }
    if(inside==0 || inside==4)return false;
    depths=values;return true;
}
inline bool coverage(const std::array<Point,4> &xy,const std::array<double,4> &z,
    double far,Mask &output)
{
    output=Mask{};
    if(!std::isfinite(far) || far<=0 || far>1e9)return false;
    unsigned inside=0;
    for(unsigned i=0;i<4;++i) {
        if(!std::isfinite(z[i]) || z[i]<=0 || z[i]>1e9)return false;
        for(float v:xy[i])if(!std::isfinite(v) || std::abs(v)>65536.f)return false;
        inside+=z[i]<far;
    }
    if(inside==4)return true;
    if(!inside){output[0]=-1;return true;}
    Mask result{};unsigned count=0;
    const auto append=[&](double x,double y)->bool {
        if(count>=6 || !std::isfinite(x) || !std::isfinite(y))return false;
        result[4+count*2]=float(x);result[5+count*2]=float(y);++count;return true;
    };
    for(unsigned i=0;i<4;++i) {
        const unsigned j=(i+3)%4;
        if((z[j]<far)!=(z[i]<far)) {
            // Keep these double operations in reference order. Replacing them
            // with a world-linear fraction changes the projected boundary.
            const double t=(1.0/far-1.0/z[j])/(1.0/z[i]-1.0/z[j]);
            if(!std::isfinite(t) || t<0 || t>1)return false;
            if(!append(double(xy[j][0])+t*(double(xy[i][0])-xy[j][0]),
                       double(xy[j][1])+t*(double(xy[i][1])-xy[j][1])))return false;
        }
        if(z[i]<far && !append(xy[i][0],xy[i][1]))return false;
    }
    if(count<3){output[0]=-1;return true;}
    result[0]=float(count);output=result;return true;
}
} }
