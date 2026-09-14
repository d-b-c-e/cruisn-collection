// SPDX-License-Identifier: BSD-3-Clause
// Differential numeric contract: bits and boundary floating-point behavior.
#include "zeus_state.h"
#include "zeus_model_bounds.h"
#include <cassert>
#include <cerrno>
#include <cfenv>
#include <iostream>
#include <limits>
static uint32_t bits(float x){uint32_t w;std::memcpy(&w,&x,4);return w;}
static float value(uint32_t w){float x;std::memcpy(&x,&w,4);return x;}
static float reference(uint32_t w) {
    const auto f=cruisn::scenery::Float::load(w);
    return f.e==-128?0.0f:float(std::ldexp(double(int64_t(f.m)^INT64_C(0x80000000)),f.e-31));
}
static float reference_down(float x){return std::nextafter(x,-std::numeric_limits<float>::infinity());}
static float reference_up(float x){return std::nextafter(x,std::numeric_limits<float>::infinity());}
template<class A,class B> void boundary(A a,B b) {
    errno=0;std::feclearexcept(FE_ALL_EXCEPT);volatile float x=a();
    const auto xb=bits(x);const int xe=errno,xf=std::fetestexcept(FE_ALL_EXCEPT);
    errno=0;std::feclearexcept(FE_ALL_EXCEPT);volatile float y=b();
    const auto yb=bits(y);const int ye=errno,yf=std::fetestexcept(FE_ALL_EXCEPT);
    assert(xb==yb && xe==ye && xf==yf);
}
int main() {
    using namespace cruisn;
    const auto inf=std::numeric_limits<float>::infinity();
    // Keep exception checks as two actual calls even under the ordinary build
    // flags; the compiler must not reuse a prior result after clearing flags.
    float (*volatile convert_old)(uint32_t)=reference;
    float (*volatile convert_new)(uint32_t)=zeus_state::floating;
    float (*volatile down_old)(float)=reference_down;
    float (*volatile up_old)(float)=reference_up;
    float (*volatile down_new)(float)=zeus_bounds::down;
    float (*volatile up_new)(float)=zeus_bounds::up;
    const uint32_t mantissas[]={0,1,2,3,0x3fffff,0x400000,0x7ffffe,0x7fffff,
        0x800000,0x800001,0xbfffff,0xc00000,0xfffffc,0xfffffd,0xfffffe,0xffffff};
    const uint32_t ieee[]={0,0x80000000,1,2,0x80000001,0x80000002,0x007fffff,
        0x00800000,0x00800001,0x807fffff,0x80800000,0x80800001,
        0x3f7fffff,0x3f800000,0x3f800001,0xbf800000,
        0x7f7ffffe,0x7f7fffff,0xff7ffffe,0xff7fffff,0x7f800000,0xff800000,
        0x7fc12345,0xffc12345,0x7f812345,0xff812345};
    for(int mode:{FE_TONEAREST,FE_DOWNWARD,FE_UPWARD,FE_TOWARDZERO}) {
        assert(!std::fesetround(mode));
        for(uint32_t e=0;e<256;++e)for(auto m:mantissas) {
            const auto w=(e<<24)|m;
            boundary([&](){return convert_old(w);},[&](){return convert_new(w);});
        }
        for(auto w:ieee) {
            const float f=value(w);
            boundary([&](){return down_old(f);},[&](){return down_new(f);});
            boundary([&](){return up_old(f);},[&](){return up_new(f);});
        }
    }
    assert(!std::fesetround(FE_TONEAREST));
    uint32_t w=0x7139a5c2;
    for(unsigned i=0;i<1000000;++i) {
        w=w*1664525U+1013904223U;
        assert(bits(reference(w))==bits(zeus_state::floating(w)));
        const auto f=value(w);
        assert(bits(std::nextafter(f,-inf))==bits(zeus_bounds::down(f)));
        assert(bits(std::nextafter(f,inf))==bits(zeus_bounds::up(f)));
    }
    assert(zeus_state::floating(0)==1.f && zeus_state::floating(0x80000000)==0.f);
    assert(bits(zeus_bounds::up(-0.f))==1 && bits(zeus_bounds::down(0.f))==0x80000001);
    std::cout<<"PASS 16384 C31 boundary cases, 208 IEEE neighbors across four rounding modes, one million differential words\n";
}
